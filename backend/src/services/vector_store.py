# app/services/vector_store.py
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple
from ..config import settings
from ..models import AnalyzedSection
from ..state import session_stores

class VectorStore:
    """
    A class to manage text embeddings and similarity search for a single session.
    It encapsulates the ML model for embeddings and the FAISS index.
    """
    def __init__(self):
        """
        Initializes the VectorStore. This is called once per session.
        It loads the sentence transformer model and creates an empty FAISS index.
        """
        print("Initializing new VectorStore for a session...")
        # Load the embedding model once per instance.
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        
        # Initialize FAISS, a library for efficient similarity search.
        self.index = faiss.IndexFlatL2(settings.EMBEDDING_DIMENSION)
        
        # A simple dictionary to store the original text data, keyed by its index ID.
        self.document_store: Dict[int, AnalyzedSection] = {}
        self.chunk_id_counter = 0

    def add_documents(self, subsections: List[AnalyzedSection]):
        """
        Takes processed text data, creates embeddings, and adds them to our store.
        This is the "learning" or "indexing" step.
        """
        if not subsections:
            return 0
        
        # 1. Get the text from each subsection object.
        texts_to_embed = [sub.refined_text for sub in subsections]
        
        # 2. Convert all texts to numerical vectors (embeddings) in a single batch.
        embeddings = self.model.encode(texts_to_embed, convert_to_tensor=False)
        
        # 3. Add each embedding and its corresponding original data to our stores.
        for subsection, embedding in zip(subsections, embeddings):
            current_id = self.chunk_id_counter
            self.document_store[current_id] = subsection
            self.index.add(np.array([embedding])) # Add the vector to FAISS.
            self.chunk_id_counter += 1
        
        print(f"Added {len(subsections)} documents to the vector store.")
        return len(subsections)

    def search(self, query_text: str, k: int = 10) -> List[Tuple[int, AnalyzedSection, float]]:
        """
        Searches for the top 'k' most similar documents to a given query text.
        This is the "retrieval" or "recommendation" step.
        """
        if self.index.ntotal == 0:
            return [] # Can't search if the store is empty.
            
        # 1. Convert the search query into an embedding.
        query_embedding = self.model.encode([query_text])
        
        # 2. Use FAISS to find the indices of the 'k' most similar vectors.
        distances, indices = self.index.search(query_embedding, k)
        
        # 3. Retrieve the original data for the found indices.
        results = []
        for i, dist in zip(indices[0], distances[0]):
            if i != -1: # FAISS returns -1 for invalid indices.
                retrieved_item = self.document_store[i]
                results.append((int(i), retrieved_item, float(dist)))
        
        return results