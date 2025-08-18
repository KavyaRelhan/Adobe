# src/document_structurer.py

import re
import statistics
from collections import defaultdict
from typing import List, Dict, Any
from .config import MIN_WORDS_FOR_PARAGRAPH

# A set of common helping verbs. Headings are less likely to contain these.
HELPING_VERBS = {'is', 'are', 'was', 'were', 'be', 'being', 'been', 'has', 'have', 'had', 'do', 'does', 'did', 'can', 'could', 'will', 'would', 'shall', 'should', 'may', 'might', 'must'}

# --- Pre-processing Filters ---

def _filter_table_of_contents(blocks: List[Dict]) -> List[Dict]:
    """Identifies and removes pages that function as a Table of Contents."""
    toc_pages = set()
    for page_num in sorted(list(set(b['page'] for b in blocks))):
        blocks_on_page = [b for b in blocks if b['page'] == page_num]
        # Heuristic: A TOC has a clear title or many dot leaders
        has_toc_title = any(re.search(r'^(table of )?contents$', b['text'].lower().strip()) for b in blocks_on_page)
        dot_leader_count = sum(1 for b in blocks_on_page if '...' in b['text'] and len(b['text']) > 10)
        if has_toc_title or dot_leader_count > 4:
            toc_pages.add(page_num)
    return [b for b in blocks if b['page'] not in toc_pages]

def _filter_running_headers_footers(blocks: List[Dict], body_size: float) -> List[Dict]:
    """Removes repeating text at the top/bottom of pages."""
    text_positions = defaultdict(list)
    page_count = len(set(b['page'] for b in blocks))
    text = b['text']
    word_count = len(text.split())
    if page_count < 3: return blocks # Not enough pages to establish a pattern

    for b in blocks:
        # Ignore prominent text; it's likely a real heading
        if b.get('size', 0) > body_size * 1.1 or b.get('bold', False) or (word_count <= 5 and not text.endswith('.')): 
            continue
        # Key by text and approximate vertical position
        y_pos_key = round(b['bbox'][1] / 20)
        text_positions[(b['text'], y_pos_key)].append(b['page'])

    # A text is a runner if it appears on at least a third of the pages
    runner_texts = {key[0] for key, pages in text_positions.items() if len(set(pages)) >= page_count // 3 and len(set(pages)) > 1}
    return [b for b in blocks if b['text'] not in runner_texts]

# --- Main Structuring Logic ---

def structure_document(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Processes raw blocks into a full semantic structure (headings, paragraphs, etc.).
    """
    if not blocks:
        return []

    # 1. Determine document's baseline style
    try:
        body_size = statistics.median([b['size'] for b in blocks if 50 < len(b['text']) < 400])
    except statistics.StatisticsError:
        body_size = 10.0

    # 2. Pre-processing: Clean the blocks before analysis
    cleaned_blocks = _filter_table_of_contents(blocks)
    # cleaned_blocks = _filter_running_headers_footers(cleaned_blocks, body_size)

    # 3. Scoring Engine: Score each block for its "heading-ness"
    scored_blocks = []
    for i, block in enumerate(cleaned_blocks):
        score = 0
        text = block['text'].strip()
        size = block.get('size', 0)
        word_count = len(text.split())

        # --- Feature-based Scoring ---
        if size > body_size * 1.15: score += (size / body_size) * 3 # Size is a strong signal
        if block.get('bold', False): score += 3
        if re.match(r'^\d+(\.\d+)*\s', text): score += 3# Numbered lists are very likely headings
        if text.isupper() and word_count > 1: score += 1
        
        # Spacing is a powerful indicator of a new section
        space_above = block['bbox'][1] - cleaned_blocks[i-1]['bbox'][3] if i > 0 else 10
        if space_above > size * 0.5: score += 2

        # Negative signals
        if text.endswith(('.', ':', ';')): score -= 2
        if any(word.lower() in HELPING_VERBS for word in text.split()): score -= 1
        if word_count > 30: score -= 5 # Too long for a heading

        scored_blocks.append({'score': score, **block})

    # 4. Classification and Hierarchy Assignment
    structured_content = []
    heading_stack = []

    for block in scored_blocks:
        is_heading = block['score'] > 3.5 # This threshold works well

        if is_heading:
            level_num = 1
            size = block['size']
            
            # Determine level based on stack
            while heading_stack and size <= heading_stack[-1]['size'] * 0.98: # Use a tolerance
                heading_stack.pop()
            level_num = len(heading_stack) + 1

            # Override with numbering if present (most reliable)
            match = re.match(r'^(\d+(\.\d+)*)', block['text'])
            if match:
                level_num = match.group(1).count('.') + 1

            # Cap level to prevent excessive nesting
            if len(heading_stack) > 0 and level_num > heading_stack[-1]['level'] + 1:
                level_num = heading_stack[-1]['level'] + 1
            
            if level_num <= 4: # Consider up to H4
                heading_stack.append({'level': level_num, 'size': size})
                structured_content.append({
                    'type': 'heading',
                    'level': f"H{level_num}",
                    'text': block['text'],
                    'page': block['page'],
                    'document': block['document'] 
                })
        else:
            # Classify as paragraph or other based on length
            block_type = 'paragraph' if len(block['text'].split()) >= MIN_WORDS_FOR_PARAGRAPH else 'other'
            structured_content.append({
                'type': block_type,
                'text': block['text'],
                'page': block['page'],
                'document': block['document']
            })

    return structured_content