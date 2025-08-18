# app/services/ml_pipeline_service.py

from pathlib import Path
from typing import List

# ... (keep existing imports) ...
from ..models import RecommendationData
from ..utils.pdf_parser import parse_pdf_to_blocks
from ..utils.document_structurer import structure_document
from ..utils.relevance_analyzer import relevance_analyzer

def run_analysis_pipeline(
    pdf_paths: List[Path], 
    query: str
) -> RecommendationData:
    """
    Orchestrates the analysis pipeline on a COLLECTION of documents.
    """
    print("--- Starting ML Analysis Pipeline ---")
    
    # 1. Parse ALL documents in the collection into a single list of blocks
    print(f"Step 1: Parsing {len(pdf_paths)} PDF(s)...")
    all_blocks = []
    for pdf_path in pdf_paths:
        all_blocks.extend(parse_pdf_to_blocks(str(pdf_path)))

    if not all_blocks:
        raise ValueError("Could not extract any content from the provided documents.")

    # 2. Structure the combined document content
    print("Step 2: Structuring combined document content...")
    structured_document = structure_document(all_blocks)
    
    # 3. Analyze for relevance using the provided persona and job
    print("Step 3: Analyzing for relevance...")
    # analyzer = relevance_analyzer()
    
    analyzed_sections = relevance_analyzer.analyze(
        structured_document, 
        query
    )
    
    # 4. Assemble the final output
    doc_filenames = [path.name for path in pdf_paths]
    final_output = RecommendationData(
        metadata={
            "input_documents": doc_filenames,
            "persona": "N/A",
            "job_to_be_done": query,
        },
        # extracted_sections=extracted_sections,
        # subsection_analysis=subsection_analysis
        analyzed_sections=analyzed_sections
    )
    
    print("--- ML Analysis Pipeline Finished ---")
    
    print(f"DEBUG: About to return object of type: {type(final_output)}")

    return final_output