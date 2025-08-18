# src/pdf_parser.py

import fitz  # PyMuPDF
from typing import List, Dict, Any
from pathlib import Path

def parse_pdf_to_blocks(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extracts all text blocks from a PDF with high precision by reading
    individual words and their properties, then reconstructing logical blocks.
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening or processing {pdf_path}: {e}")
        return []
        
    all_blocks = []
    
    for page_num, page in enumerate(doc):
        # Use 'dict' format for detailed info, including font flags
        page_dict = page.get_text("dict", flags=fitz.TEXTFLAGS_DICT)
        
        page_blocks = []
        for b in page_dict.get("blocks", []):
            # We only care about text blocks (type 0)
            if b['type'] == 0:
                block_text = ""
                # Get a representative style from the first span
                first_span = None
                if b.get("lines") and b["lines"][0].get("spans"):
                    first_span = b["lines"][0]["spans"][0]

                if not first_span:
                    continue

                # Reconstruct the full text of the block
                for l in b.get("lines", []):
                    for s in l.get("spans", []):
                        block_text += s['text'] + " "
                
                # Create our standardized block dictionary
                page_blocks.append({
                    "text": block_text.strip().replace('\n', ' '),
                    "size": first_span['size'],
                    "font": first_span['font'],
                    "bold": "bold" in first_span['font'].lower() or (first_span['flags'] & 2**4),
                    "page": page_num + 1,  # 1-based page number
                    "bbox": b['bbox'],
                    "document": Path(pdf_path).name
                })
        
        # Sort blocks by vertical position to ensure correct reading order
        all_blocks.extend(sorted(page_blocks, key=lambda x: x['bbox'][1]))
            
    return all_blocks