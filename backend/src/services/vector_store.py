import threading
from typing import Any, Dict, List, Tuple, Union

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from ..config import settings
from ..models import AnalyzedSection


# Supported: flat_cosine, flat_l2, hnsw_cosine, hnsw_l2
INDEX_NAME = "hnsw_cosine"

HNSW_M = 32
HNSW_EF_CONSTRUCTION = 200
HNSW_EF_SEARCH = 64


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
    In-memory vector store for one user session.

    Accepts either AnalyzedSection objects or dictionaries returned by
    structure_document(). Only paragraph records are indexed; heading
    records update the current heading context but are not indexed alone.

    FAISS vectors and paragraph metadata are maintained in memory only.
    """

    def __init__(self, session_id: str, index_name: str = INDEX_NAME):
        self.session_id = session_id
        self.index_name = index_name.strip().lower()

        self.model = get_embedding_model()
        self.dimension = settings.EMBEDDING_DIMENSION
        self.use_cosine = self.index_name.endswith("_cosine")

        # In-memory FAISS index.
        self.index = create_faiss_index(
            self.index_name,
            self.dimension,
        )

        # In-memory paragraph metadata.
        self.document_store: Dict[int, dict] = {}

        # Tracks which files have already been indexed in this instance.
        self.indexed_files: Dict[str, dict] = {}

        self.next_id = 0
        self.lock = threading.RLock()

    # ---------------------------------------------------------
    # Input normalization and embedding text
    # ---------------------------------------------------------

    @staticmethod
    def _value(
        section: Union[AnalyzedSection, Dict[str, Any]],
        key: str,
        default=None,
    ):
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
                section,
                "page_number",
                cls._value(section, "page", 0),
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
        """Generate embeddings for the supplied texts."""
        if not texts:
            return np.empty(
                (0, self.dimension),
                dtype=np.float32,
            )

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=self.use_cosine,
            show_progress_bar=False,
        )

        embeddings = np.asarray(
            embeddings,
            dtype=np.float32,
        )

        if embeddings.ndim != 2:
            raise ValueError(
                "Embedding model must return a 2D array."
            )

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
        """
        Normalize, embed and index paragraphs from one source file.

        Embeddings are generated during upload, not during search.
        """
        with self.lock:

            # Avoid indexing the same file twice in this instance.
            if source_file in self.indexed_files:
                return 0

            records = self._normalize_sections(sections)

            if not records:
                self.indexed_files[source_file] = {
                    "chunk_ids": [],
                    "status": "empty",
                }
                return 0

            # Generate embeddings for heading + paragraph text.
            embedding_texts = [
                self._embedding_text(record)
                for record in records
            ]

            embeddings = self._embed(embedding_texts)

            # Assign unique integer IDs to the new vectors.
            ids = np.arange(
                self.next_id,
                self.next_id + len(records),
                dtype=np.int64,
            )

            # Prepare paragraph metadata.
            new_records = {}

            for chunk_id, record in zip(ids, records):
                record["source_file"] = source_file

                if not record.get("document"):
                    record["document"] = source_file

                new_records[int(chunk_id)] = record

            # Add vectors and metadata to the in-memory store.
            self.index.add_with_ids(embeddings, ids)
            self.document_store.update(new_records)

            self.next_id += len(records)

            self.indexed_files[source_file] = {
                "chunk_ids": ids.tolist(),
                "status": "indexed",
            }

            print(
                f"Indexed {len(records)} paragraphs from "
                f"'{source_file}' using '{self.index_name}'."
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
        """
        Return the top-k matching paragraphs and their metadata.

        Only the query is embedded here. Paragraph embeddings were
        already generated and added to FAISS during document upload.
        """
        with self.lock:

            if (
                self.index.ntotal == 0
                or not query_text
                or not query_text.strip()
                or k <= 0
            ):
                return []

            # Generate embedding only for the user query.
            query_embedding = self._embed([
                query_text.strip()
            ])

            k = min(k, self.index.ntotal)

            # Search the existing FAISS index.
            scores, ids = self.index.search(
                query_embedding,
                k,
            )

            results = []

            for chunk_id, score in zip(ids[0], scores[0]):

                if chunk_id == -1:
                    continue

                record = self.document_store.get(
                    int(chunk_id)
                )

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

                results.append((
                    int(chunk_id),
                    section,
                    float(score),
                ))

            return results

    # ---------------------------------------------------------
    # Remove document and rebuild index
    # ---------------------------------------------------------

    def remove_document(self, source_file: str) -> bool:
        """
        Remove one source file and rebuild the in-memory index
        using the remaining paragraph records.
        """
        with self.lock:

            file_info = self.indexed_files.get(source_file)

            if file_info is None:
                return False

            # Remove the file's paragraph metadata.
            for chunk_id in file_info.get("chunk_ids", []):
                self.document_store.pop(
                    int(chunk_id),
                    None,
                )

            del self.indexed_files[source_file]

            # Create a fresh FAISS index.
            new_index = create_faiss_index(
                self.index_name,
                self.dimension,
            )

            # Re-add vectors for the remaining documents.
            if self.document_store:

                sorted_ids = sorted(self.document_store)

                ids_array = np.asarray(
                    sorted_ids,
                    dtype=np.int64,
                )

                texts = [
                    self._embedding_text(
                        self.document_store[chunk_id]
                    )
                    for chunk_id in sorted_ids
                ]

                embeddings = self._embed(texts)

                new_index.add_with_ids(
                    embeddings,
                    ids_array,
                )

            self.index = new_index

            print(
                f"Removed {source_file}. "
                f"Remaining vectors: {self.index.ntotal}"
            )

            return True
