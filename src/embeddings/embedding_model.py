"""
Embedding Model using HuggingFace Inference API.
"""
import os
import requests
from typing import List, Optional
from src.utils.logger import setup_logger

logger = setup_logger("EmbeddingModel")

class EmbeddingModel:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", base_url: str = None):
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.api_token = os.environ.get("HF_TOKEN", "")
        self.api_url = f"https://router.huggingface.co/hf-inference/models/{self.model_name}/pipeline/feature-extraction"
        self.vector_size = 384
        logger.info(f"Embedding model ready: HuggingFace/{self.model_name}")

    def _embed(self, texts: List[str]) -> List[List[float]]:
        headers = {"Authorization": f"Bearer {self.api_token}"}
        response = requests.post(
            self.api_url,
            headers=headers,
            json={"inputs": texts, "options": {"wait_for_model": True}},
            timeout=60
        )
        response.raise_for_status()
        return response.json()

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")
        text = text[:8000] if len(text) > 8000 else text
        result = self._embed([text])
        return result[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        all_embeddings = []
        batch_size = 10
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self._embed(batch)
            all_embeddings.extend(embeddings)
            logger.info(f"Embedded {min(i + batch_size, len(texts))}/{len(texts)} chunks")
        return all_embeddings

    def is_available(self) -> bool:
        return True

    def get_vector_size(self) -> Optional[int]:
        return self.vector_size
