"""
Embedding store for schema/context RAG.
"""
from typing import Any

class EmbeddingStore:
    def __init__(self, embedder):
        self.embedder = embedder
        self.index = []

    def add(self, chunk: Any):
        embedding = self.embedder.embed(chunk)
        self.index.append((chunk, embedding))

    def search(self, query: str):
        # Placeholder: Return most similar chunk
        return self.index[0][0] if self.index else None
