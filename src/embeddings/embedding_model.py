"""
Embedding Model for Enterprise AI Knowledge Assistant.
Converts text into vector numbers using Ollama locally.
"""

from typing import List
import requests
import json
from src.utils.logger import setup_logger

logger = setup_logger("Embeddings")


class EmbeddingModel:
    """
    Converts text into vector embeddings using Ollama.

    What are embeddings?
        Text converted into numbers that capture meaning.
        Similar texts get similar numbers.

        "dog"  → [0.2, 0.8, 0.1, 0.9, ...]
        "cat"  → [0.2, 0.7, 0.1, 0.8, ...]  ← similar!
        "car"  → [0.9, 0.1, 0.7, 0.2, ...]  ← different!

        This lets us find relevant chunks for any question.
    """

    def __init__(self,
                 model_name: str = "nomic-embed-text",
                 base_url: str = "http://localhost:11434"):
        """
        Args:
            model_name: Ollama embedding model name
            base_url:   Ollama server URL
        """
        self.model_name = model_name
        self.base_url   = base_url
        self.embed_url  = f"{base_url}/api/embeddings"
        logger.info(f"Embedding model ready: {model_name}")

    def embed_text(self, text: str) -> List[float]:
        """
        Convert a single text into embedding vector.

        Args:
            text: Text to embed

        Returns:
            List of float numbers (the vector)
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        try:
            response = requests.post(
                self.embed_url,
                json={
                    "model":  self.model_name,
                    "prompt": text.strip()
                },
                timeout=30
            )
            response.raise_for_status()
            embedding = response.json().get("embedding", [])

            if not embedding:
                raise ValueError("Empty embedding returned")

            return embedding

        except requests.exceptions.ConnectionError:
            logger.error("Ollama not running! Start with: ollama serve")
            raise ConnectionError(
                "❌ Ollama is not running!\n"
                "Please start it with: ollama serve"
            )
        except Exception as e:
            logger.error(f"Embedding failed: {str(e)}")
            raise

    def embed_batch(self, texts: List[str],
                    batch_size: int = 10) -> List[List[float]]:
        """
        Convert multiple texts into embeddings.
        Processes in batches to avoid overloading Ollama.

        Args:
            texts:      List of texts to embed
            batch_size: How many to process at once

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        all_embeddings = []
        total = len(texts)

        logger.info(f"Embedding {total} texts in "
                    f"batches of {batch_size}...")

        for i in range(0, total, batch_size):
            batch = texts[i:i + batch_size]

            for text in batch:
                try:
                    embedding = self.embed_text(text)
                    all_embeddings.append(embedding)
                except Exception as e:
                    logger.error(f"Failed to embed text: {str(e)}")
                    # Add zero vector as placeholder
                    all_embeddings.append([0.0] * 768)

            logger.info(
                f"Embedded {min(i + batch_size, total)}"
                f"/{total} texts"
            )

        logger.info(f"Batch embedding complete: "
                    f"{len(all_embeddings)} vectors")
        return all_embeddings

    def is_available(self) -> bool:
        """
        Check if Ollama embedding model is running.

        Returns:
            True if available, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                available = any(
                    self.model_name in name
                    for name in model_names
                )
                if available:
                    logger.info(
                        f"✅ {self.model_name} is available"
                    )
                else:
                    logger.warning(
                        f"⚠️ {self.model_name} not found. "
                        f"Run: ollama pull {self.model_name}"
                    )
                return available
        except Exception:
            logger.error("❌ Ollama server not reachable")
            return False

    def get_embedding_size(self) -> int:
        """
        Get the dimension size of embeddings.
        nomic-embed-text returns 768 dimensions.
        """
        try:
            test_embed = self.embed_text("test")
            size = len(test_embed)
            logger.info(f"Embedding dimensions: {size}")
            return size
        except Exception:
            return 768  # Default for nomic-embed-text