"""
Embedding Model using sentence-transformers.
Works without Ollama - runs directly in Python.
"""
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from src.utils.logger import setup_logger

logger = setup_logger("EmbeddingModel")

class EmbeddingModel:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", base_url: str = None):
        self.model_name = "all-MiniLM-L6-v2"
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.vector_size = 384
        logger.info(f"Embedding model ready: {self.model_name}")

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")
        text = text[:8000] if len(text) > 8000 else text
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        logger.info(f"Embedded {len(texts)} chunks")
        return embeddings.tolist()

    def is_available(self) -> bool:
        return True

    def get_vector_size(self) -> Optional[int]:
        return self.vector_size
