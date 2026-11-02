# backend/src/document_structurer.py

import math
import re
import statistics
from collections import defaultdict
from typing import Any, Dict, List

from .config import MIN_WORDS_FOR_PARAGRAPH


HELPING_VERBS = {
    "is", "are", "was", "were", "be", "being", "been",
    "has", "have", "had", "do", "does", "did", "can",
    "could", "will", "would", "shall", "should", "may",
    "might", "must",
}


def _filter_table_of_contents(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove pages that are very likely to be a table of contents."""
    pages = sorted({block.get("page") for block in blocks if block.get("page") is not None})
    toc_pages = set()

    for page_num in pages:
        page_blocks = [b for b in blocks if b.get("page") == page_num]
        has_toc_title = any(
            re.search(r"^(table of )?contents$", str(b.get("text", "")).strip(), re.I)
            for b in page_blocks
        )
        dot_leaders = sum(
            1 for b in page_blocks
            if re.search(r"\.{2,}", str(b.get("text", "")))
            and len(str(b.get("text", ""))) > 10
        )

        if has_toc_title or dot_leaders > 4:
            toc_pages.add(page_num)

    return [b for b in blocks if b.get("page") not in toc_pages]


def _filter_running_headers_footers(
    blocks: List[Dict[str, Any]],
    body_size: float,
) -> List[Dict[str, Any]]:
    """
    Conservatively remove repeated short text near page tops/bottoms.
    Blocks without usable bounding boxes are left untouched.
    """
    pages = {b.get("page") for b in blocks if b.get("page") is not None}
    page_count = len(pages)

    if page_count < 3:
        return blocks

    occurrences = defaultdict(set)

    for block in blocks:
        text = str(block.get("text", "")).strip()
        bbox = block.get("bbox")

        if not text or not bbox or len(bbox) < 4:
            continue

        # Do not treat prominent or bold text as a running header/footer.
        if block.get("size", 0) > body_size * 1.1 or block.get("bold", False):
            continue

        # Only consider short text, which is typical of headers and footers.
        if len(text.split()) > 8 or text.endswith((".", ";")):
            continue

        y_top = float(bbox[1])
        y_bottom = float(bbox[3])
        position = "top" if y_top < 100 else "bottom" if y_bottom > 700 else None

        if position:
            key = (re.sub(r"\s+", " ", text).casefold(), position)
            occurrences[key].add(block.get("page"))

    required_pages = max(2, math.ceil(page_count / 3))
    repeated_text = {
        text for (text, _position), seen_pages in occurrences.items()
        if len(seen_pages) >= required_pages
    }

    return [
        block for block in blocks
        if re.sub(r"\s+", " ", str(block.get("text", "")).strip()).casefold()
        not in repeated_text
    ]


def _is_heading(
    block: Dict[str, Any],
    body_size: float,
    space_above: float = 0.0,
) -> bool:
    """Decide whether a text block is a heading; no heading levels are assigned."""
    text = str(block.get("text", "")).strip()

    if not text:
        return False

    words = text.split()
    word_count = len(words)
    size = float(block.get("size") or body_size)
    score = 0.0

    # A numbered section title is a useful heading signal.
    if re.match(r"^\d+(?:\.\d+)*\.?(?:\s+|$)", text):
        score += 3.0

    if size > body_size * 1.15:
        score += (size / body_size) * 3.0

    if block.get("bold", False):
        score += 3.0

    if text.isupper() and word_count > 1:
        score += 1.0

    # Extra vertical space before a block can indicate a new section.
    if space_above > size * 0.5:
        score += 2.0

    # Penalize sentence-like or excessively long blocks.
    if text.endswith((".", ";")):
        score -= 2.0

    if any(word.strip(".,:;()[]").lower() in HELPING_VERBS for word in words):
        score -= 1.0

    if word_count > 20:
        score -= 5.0

    return score > 3.5


def structure_document(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect headings without assigning H1/H2/H3/H4 levels.

    Each paragraph receives the most recently detected heading as its
    section_title. Heading records are retained in the output, while the
    vector store indexes only records whose type is 'paragraph'.
    """
    if not blocks:
        return []

    valid_sizes = [
        float(b["size"])
        for b in blocks
        if b.get("size") is not None
        and 50 < len(str(b.get("text", ""))) < 400
        and float(b["size"]) > 0
    ]
    body_size = statistics.median(valid_sizes) if valid_sizes else 10.0

    cleaned_blocks = _filter_table_of_contents(blocks)
    cleaned_blocks = _filter_running_headers_footers(cleaned_blocks, body_size)

    structured_content = []
    last_heading = ""

    previous_block = None

    for block in cleaned_blocks:
        text = str(block.get("text", "")).strip()
        if not text:
            previous_block = block
            continue

        # Only compare blocks on the same page; otherwise page breaks
        # can look like unusually large spacing.
        space_above = 0.0
        bbox = block.get("bbox")
        previous_bbox = previous_block.get("bbox") if previous_block else None
        if (
            bbox and previous_bbox
            and block.get("page") == previous_block.get("page")
            and len(bbox) >= 4 and len(previous_bbox) >= 4
        ):
            space_above = max(0.0, float(bbox[1]) - float(previous_bbox[3]))

        page_number = block.get("page", block.get("page_number", 0))
        document = block.get("document", "")

        if _is_heading(block, body_size, space_above):
            last_heading = text
            structured_content.append({
                "type": "heading",
                "text": text,
                "page": page_number,
                "document": document,
                "section_title": last_heading,
                "heading": last_heading,
            })
            previous_block = block
            continue

        word_count = len(text.split())
        block_type = (
            "paragraph"
            if word_count >= MIN_WORDS_FOR_PARAGRAPH
            else "other"
        )

        structured_content.append({
            "type": block_type,
            "text": text,
            "page": page_number,
            "document": document,
            "section_title": last_heading,
            "heading": last_heading,
        })

        previous_block = block

    return structured_content
