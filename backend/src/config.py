# app/config.py
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

UPLOAD_DIR = Path("uploads")
GENERATED_ASSETS_DIR_NAME = "generated"
RELEVANCE_THRESHOLD = 0.25  # Example value, adjust as needed
MAX_RESULTS = 10         # Example value, adjust as needed

class Settings:
    # LLM Provider Settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL:str= os.getenv("GEMINI_MODEL")
    # Embedding Model Settings
    EMBEDDING_MODEL_NAME: str = 'all-MiniLM-L6-v2'
    EMBEDDING_DIMENSION: int = 384

# Instantiate settings to be imported by other modules
settings = Settings()