# backend/src/services/vector_store.py

import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from ..config import UPLOAD_DIR, settings
from ..models import AnalyzedSection


# Supported: flat_cosine, flat_l2, hnsw_cosine, hnsw_l2
INDEX_NAME = "hnsw_cosine"

HNSW_M = 32
HNSW_EF_CONSTRUCTION = 200
HNSW_EF_SEARCH = 64

# Increment this when the text used to create embeddings changes.
STORE_SCHEMA_VERSION = 2


_embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)


def get_embedding_model():
    """Return the shared sentence-embedding model."""
    return _embedding_model


def create_faiss_index(
    index_name: str,
    dimension: int,
    hnsw_m: int = HNSW_M,
    ef_construction: int = HNSW_EF_CONSTRUCTION,
    ef_search: int = HNSW_EF_SEARCH,
):
    """Create a configured FAISS index with stable integer IDs."""
    index_name = index_name.strip().lower()

    if index_name == "flat_cosine":
        base_index = faiss.IndexFlatIP(dimension)
    elif index_name == "flat_l2":
        base_index = faiss.IndexFlatL2(dimension)
    elif index_name == "hnsw_cosine":
        base_index = faiss.IndexHNSWFlat(
            dimension, hnsw_m, faiss.METRIC_INNER_PRODUCT
        )
        base_index.hnsw.efConstruction = ef_construction
        base_index.hnsw.efSearch = ef_search
    elif index_name == "hnsw_l2":
        base_index = faiss.IndexHNSWFlat(
            dimension, hnsw_m, faiss.METRIC_L2
        )
        base_index.hnsw.efConstruction = ef_construction
        base_index.hnsw.efSearch = ef_search
    else:
        raise ValueError(
            f"Unsupported FAISS index '{index_name}'. Choose "
            "flat_cosine, flat_l2, hnsw_cosine, or hnsw_l2."
        )

    return faiss.IndexIDMap2(base_index)


class VectorStore:
    """
    Persistent vector store for one user session.

    Accepts either AnalyzedSection objects or dictionaries returned by
    structure_document(). Only paragraph records are indexed; heading
    records update the current heading context but are not indexed alone.
    """

    def __init__(self, session_id: str, index_name: str = INDEX_NAME):
        self.session_id = session_id
        self.index_name = index_name.strip().lower()

        self.store_dir = UPLOAD_DIR / session_id / "vector_store"
        self.store_dir.mkdir(parents=True, exist_ok=True)

        self.index_path = self.store_dir / f"{self.index_name}.faiss"
        self.metadata_path = self.store_dir / f"{self.index_name}.json"

        self.model = get_embedding_model()
        self.dimension = settings.EMBEDDING_DIMENSION
        self.use_cosine = self.index_name.endswith("_cosine")

        self.index = create_faiss_index(self.index_name, self.dimension)
        self.document_store: Dict[int, dict] = {}
        self.indexed_files: Dict[str, dict] = {}
        self.next_id = 0
        self.lock = threading.RLock()

        self._load()

    # ---------------------------------------------------------
    # Input normalization and embedding text
    # ---------------------------------------------------------

    @staticmethod
    def _value(section: Union[AnalyzedSection, Dict[str, Any]], key: str, default=None):
        if isinstance(section, dict):
            return section.get(key, default)
        return getattr(section, key, default)

    @classmethod
    def _normalize_sections(
        cls,
        sections: List[Union[AnalyzedSection, Dict[str, Any]]],
    ) -> List[dict]:
        """
        Convert structurer dictionaries and AnalyzedSection objects into
        one internal record format. The last heading is carried forward.
        """
        normalized = []
        last_heading = ""

        for section in sections:
            block_type = cls._value(section, "type", "paragraph")

            # A heading updates context but is not itself a searchable chunk.
            if block_type == "heading":
                last_heading = (
                    cls._value(section, "text", "")
                    or cls._value(section, "heading", "")
                    or ""
                ).strip()
                continue

            # Ignore non-paragraph records from document_structurer.
            if block_type not in ("paragraph", None):
                continue

            text = (
                cls._value(section, "refined_text", None)
                or cls._value(section, "text", "")
                or ""
            ).strip()

            if not text:
                continue

            section_title = (
                cls._value(section, "section_title", "")
                or cls._value(section, "heading", "")
                or last_heading
                or ""
            ).strip()

            # An explicit section title becomes the current heading context.
            if section_title:
                last_heading = section_title

            document = (
                cls._value(section, "document", "")
                or cls._value(section, "source_file", "")
                or ""
            )
            page_number = cls._value(
                section, "page_number",
                cls._value(section, "page", 0)
            )

            normalized.append({
                "document": document,
                "page_number": int(page_number or 0),
                "section_title": last_heading,
                "refined_text": text,
            })

        return normalized

    @staticmethod
    def _embedding_text(record: dict) -> str:
        """Embed heading context together with the paragraph text."""
        heading = (record.get("section_title") or "").strip()
        paragraph = (record.get("refined_text") or "").strip()

        if heading:
            return f"Section: {heading}\nContent: {paragraph}"
        return paragraph

    def _embed(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=self.use_cosine,
            show_progress_bar=False,
        )
        embeddings = np.asarray(embeddings, dtype=np.float32)

        if embeddings.ndim != 2:
            raise ValueError("Embedding model must return a 2D array.")

        if embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Expected embedding dimension {self.dimension}, "
                f"got {embeddings.shape[1]}."
            )

        return np.ascontiguousarray(embeddings)

    # ---------------------------------------------------------
    # Add documents
    # ---------------------------------------------------------

    def add_documents(
        self,
        sections: List[Union[AnalyzedSection, Dict[str, Any]]],
        source_file: str,
    ) -> int:
        """Normalize, embed and index the paragraphs from one source file."""
        with self.lock:
            if source_file in self.indexed_files:
                return 0

            records = self._normalize_sections(sections)

            if not records:
                self.indexed_files[source_file] = {
                    "chunk_ids": [],
                    "status": "empty",
                }
                self._save()
                return 0

            embedding_texts = [
                self._embedding_text(record) for record in records
            ]
            embeddings = self._embed(embedding_texts)

            ids = np.arange(
                self.next_id,
                self.next_id + len(records),
                dtype=np.int64,
            )

            new_records = {}
            for chunk_id, record in zip(ids, records):
                record["source_file"] = source_file
                if not record.get("document"):
                    record["document"] = source_file
                new_records[int(chunk_id)] = record

            self.index.add_with_ids(embeddings, ids)
            self.document_store.update(new_records)

            self.next_id += len(records)
            self.indexed_files[source_file] = {
                "chunk_ids": ids.tolist(),
                "status": "indexed",
            }

            self._save()
            print(
                f"Indexed {len(records)} paragraphs from '{source_file}' "
                f"using '{self.index_name}'."
            )
            return len(records)

    # ---------------------------------------------------------
    # Search
    # ---------------------------------------------------------

    def search(
        self,
        query_text: str,
        k: int = 10,
    ) -> List[Tuple[int, AnalyzedSection, float]]:
        """Return the top-k matching paragraphs and their metadata."""
        with self.lock:
            if (
                self.index.ntotal == 0
                or not query_text
                or not query_text.strip()
                or k <= 0
            ):
                return []

            query_embedding = self._embed([query_text.strip()])
            k = min(k, self.index.ntotal)

            scores, ids = self.index.search(query_embedding, k)
            results = []

            for chunk_id, score in zip(ids[0], scores[0]):
                if chunk_id == -1:
                    continue

                record = self.document_store.get(int(chunk_id))
                if record is None:
                    continue

                section = AnalyzedSection(
                    document=record["document"],
                    page_number=record["page_number"],
                    section_title=record["section_title"],
                    refined_text=record["refined_text"],
                    importance_rank=len(results) + 1,
                    relevance_score=float(score),
                )
                results.append((int(chunk_id), section, float(score)))

            return results

    # ---------------------------------------------------------
    # Remove document and rebuild index
    # ---------------------------------------------------------

    def remove_document(self, source_file: str) -> bool:
        """Remove one source file and rebuild the index from remaining records."""
        with self.lock:
            file_info = self.indexed_files.get(source_file)
            if file_info is None:
                return False

            for chunk_id in file_info.get("chunk_ids", []):
                self.document_store.pop(int(chunk_id), None)

            del self.indexed_files[source_file]

            new_index = create_faiss_index(
                self.index_name,
                self.dimension,
            )

            if self.document_store:
                sorted_ids = sorted(self.document_store)
                ids_array = np.asarray(sorted_ids, dtype=np.int64)
                texts = [
                    self._embedding_text(self.document_store[chunk_id])
                    for chunk_id in sorted_ids
                ]
                embeddings = self._embed(texts)
                new_index.add_with_ids(embeddings, ids_array)

            self.index = new_index
            self._save()

            print(
                f"Removed {source_file}. "
                f"Remaining vectors: {self.index.ntotal}"
            )
            return True

    # ---------------------------------------------------------
    # Save and load
    # ---------------------------------------------------------

    def _save(self):
        """Persist FAISS vectors and their associated metadata."""
        faiss.write_index(self.index, str(self.index_path))

        metadata = {
            "schema_version": STORE_SCHEMA_VERSION,
            "session_id": self.session_id,
            "index_name": self.index_name,
            "embedding_model_name": settings.EMBEDDING_MODEL_NAME,
            "next_id": self.next_id,
            "indexed_files": self.indexed_files,
            "documents": {
                str(chunk_id): record
                for chunk_id, record in self.document_store.items()
            },
        }

        temporary_path = self.metadata_path.with_suffix(".json.tmp")
        with open(temporary_path, "w", encoding="utf-8") as file:
            json.dump(metadata, file, ensure_ascii=False)

        temporary_path.replace(self.metadata_path)

    def _rebuild_loaded_index(self):
        """
        Re-embed saved records when loading an older store schema.
        This is required because schema v2 embeds heading + paragraph,
        whereas the earlier implementation embedded paragraph text only.
        """
        new_index = create_faiss_index(self.index_name, self.dimension)

        if self.document_store:
            sorted_ids = sorted(self.document_store)
            ids_array = np.asarray(sorted_ids, dtype=np.int64)
            texts = [
                self._embedding_text(self.document_store[chunk_id])
                for chunk_id in sorted_ids
            ]
            embeddings = self._embed(texts)
            new_index.add_with_ids(embeddings, ids_array)

        self.index = new_index

    def _load(self):
        """Load the persisted index and metadata for this session."""
        if not (self.index_path.exists() and self.metadata_path.exists()):
            return

        try:
            with open(self.metadata_path, "r", encoding="utf-8") as file:
                metadata = json.load(file)

            stored_index_name = metadata.get("index_name", self.index_name)
            if stored_index_name != self.index_name:
                raise ValueError(
                    f"Stored index '{stored_index_name}' does not match "
                    f"requested index '{self.index_name}'."
                )

            stored_model = metadata.get("embedding_model_name")
            if stored_model and stored_model != settings.EMBEDDING_MODEL_NAME:
                raise ValueError(
                    "The saved vector store was created with a different "
                    "embedding model. Re-index the source documents."
                )

            self.next_id = int(metadata.get("next_id", 0))
            self.indexed_files = metadata.get("indexed_files", {})
            self.document_store = {
                int(chunk_id): record
                for chunk_id, record in metadata.get("documents", {}).items()
            }

            schema_version = int(metadata.get("schema_version", 1))

            if schema_version != STORE_SCHEMA_VERSION:
                # Old stores used paragraph-only embeddings. Rebuild them
                # using the new heading-aware embedding text.
                self._rebuild_loaded_index()
                self._save()
            else:
                loaded_index = faiss.read_index(str(self.index_path))

                if loaded_index.d != self.dimension:
                    raise ValueError(
                        "Stored index dimension does not match the "
                        "configured embedding dimension."
                    )

                if loaded_index.ntotal != len(self.document_store):
                    raise ValueError(
                        "FAISS index and metadata have different numbers "
                        "of vectors and paragraph records."
                    )

                self.index = loaded_index

            print(
                f"Restored '{self.index_name}' index for session "
                f"'{self.session_id}': {self.index.ntotal} vectors."
            )

        except Exception as error:
            raise RuntimeError(
                f"Failed to restore vector store for session "
                f"'{self.session_id}' using '{self.index_name}': {error}"
            ) from error
