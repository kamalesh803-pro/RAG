"""
vector_store.py
───────────────
Manages the FAISS vector index and SentenceTransformer embeddings.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from typing import List


# ── Embedding wrapper ────────────────────────────────────────────────
class SentenceTransformerEmbeddings(Embeddings):
    """LangChain-compatible wrapper around a SentenceTransformer model."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        embedding = self.model.encode([text], show_progress_bar=False)
        return embedding[0].tolist()


# ── Vector Store Manager ─────────────────────────────────────────────
class VectorStoreManager:
    """Thin manager around a LangChain FAISS vector store."""

    def __init__(self):
        self.embeddings = SentenceTransformerEmbeddings()
        self.vector_store: FAISS | None = None

    # ── public API ───────────────────────────────────────────────────
    def add_documents(self, chunks: List[Document]) -> int:
        """Embed *chunks* and upsert them into the FAISS index.
        Returns the total number of vectors in the store."""
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        else:
            self.vector_store.add_documents(chunks)
        return self.vector_store.index.ntotal

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """Return the *k* most relevant chunks for *query*."""
        if self.vector_store is None:
            return []
        return self.vector_store.similarity_search(query, k=k)

    def clear(self) -> None:
        """Drop the current index so a fresh one can be built."""
        self.vector_store = None

    @property
    def is_empty(self) -> bool:
        return self.vector_store is None
