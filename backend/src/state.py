# backend/src/state.py

from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .services.vector_store import VectorStore


# Cache of vector stores loaded by this backend process.
#
# The actual FAISS index and metadata are persisted on disk,
# so the cache can be reconstructed after a restart.

session_stores: Dict[str, "VectorStore"] = {}


def get_vector_store(session_id: str) -> "VectorStore":
    """
    Return the existing vector store for a session.

    If the session has not been loaded in this process,
    initialize its store and restore its persisted index.
    """

    # Local import avoids circular imports.
    from .services.vector_store import VectorStore

    if session_id not in session_stores:
        session_stores[session_id] = VectorStore(session_id)

    return session_stores[session_id]
