# src/config.py

# --- Analysis Configuration ---
# The number of most relevant paragraphs to consider for analysis
TOP_N_PARAGRAPHS = 20

# The final number of sections to include in the output
TOP_N_SECTIONS = 7

# The minimum number of words a text block must have to be considered a 'paragraph'
MIN_WORDS_FOR_PARAGRAPH = 15

RELEVANCE_THRESHOLD = 0.25

# The maximum number of paragraphs to return in the final output.
MAX_RESULTS = 25

ENABLE_OCR = True

# The parser will skip OCR on images smaller than this size (in pixels) to save time.
MIN_IMAGE_SIZE_FOR_OCR = 100