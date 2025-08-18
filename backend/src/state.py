# src/state.py
from typing import Dict

# This is the complete and correct content for this file.
# The single quotes around 'VectorStore' are the essential fix.
session_stores: Dict[str, 'VectorStore'] = {}