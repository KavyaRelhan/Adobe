# backend/src/services/ml_pipeline_service.py

from pathlib import Path
from typing import List, Dict, Any

from ..utils.pdf_parser import parse_pdf_to_blocks
from ..utils.document_structurer import structure_document


def process_documents(
    pdf_paths: List[Path]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract and structure paragraphs from uploaded PDFs.

    This function is called during upload.

    It does NOT:
    - Generate embeddings.
    - Calculate similarity.
    - Search FAISS.
    - Depend on a user query.

    The vector store handles embedding generation and indexing.
    """

    processed_documents = {}

    for pdf_path in pdf_paths:

        print(f"Processing uploaded PDF: {pdf_path.name}")

        # 1. Extract text blocks from this PDF.
        blocks = parse_pdf_to_blocks(
            str(pdf_path)
        )

        if not blocks:
            raise ValueError(
                f"No readable text could be extracted "
                f"from {pdf_path.name}."
            )

        # 2. Structure the extracted blocks.
        structured_content = structure_document(
            blocks
        )

        # 3. Track the latest heading for each paragraph.
        paragraphs = []
        current_heading = "General Information"

        for item in structured_content:

            if item["type"] == "heading":

                current_heading = item["text"]

            elif item["type"] == "paragraph":

                text = item["text"].strip()

                if not text:
                    continue

                paragraphs.append({
                    "document": pdf_path.name,
                    "page_number": item.get("page", 0),
                    "section_title": current_heading,
                    "refined_text": text
                })

        processed_documents[pdf_path.name] = paragraphs

        print(
            f"Extracted {len(paragraphs)} paragraphs "
            f"from {pdf_path.name}"
        )

    return processed_documents
