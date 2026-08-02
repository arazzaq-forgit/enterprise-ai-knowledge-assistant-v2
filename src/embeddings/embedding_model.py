"""
Embedding Model for Enterprise AI Knowledge Assistant.
Converts text into vector numbers using the HuggingFace Inference API.
"""

import os
import time
from typing import List
import requests
from src.utils.logger import setup_logger

logger = setup_logger("Embeddings")


class EmbeddingModel:
    """
    Converts text into vector embeddings using HuggingFace's hosted
    Inference API (default model: sentence-transformers/all-MiniLM-L6-v2,
    384 dimensions).

    What are embeddings?
        Text converted into numbers that capture meaning.
        Similar texts get similar numbers.

        "dog"  -> [0.2, 0.8, 0.1, 0.9, ...]
        "cat"  -> [0.2, 0.7, 0.1, 0.8, ...]  <- similar!
        "car"  -> [0.9, 0.1, 0.7, 0.2, ...]  <- different!

        This lets us find relevant chunks for any question.

    NOTE: this replaces a previous implementation that called a LOCAL
    Ollama server (http://localhost:11434). That only worked when Ollama
    was running on the same machine as the app -- fine for local dev, but
    Render (and any other cloud host) has no Ollama process, so every
    embedding call there failed with a connection error. The HuggingFace
    Inference API is a plain HTTPS call, so it works identically in local
    dev and in production, using the HF_TOKEN env var already configured
    on Render.
    """

    EMBED_DIM = 384  # all-MiniLM-L6-v2 output size

    def __init__(self,
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 hf_token: str = None,
                 **_ignored):
        """
        Args:
            model_name: HuggingFace model id to use for embeddings
            hf_token:   HuggingFace API token. Falls back to the HF_TOKEN
                        env var if not passed explicitly.
            **_ignored: swallows old kwargs (e.g. base_url) so existing
                        call sites don't need to change.
        """
        self.model_name = model_name
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        if not self.hf_token:
            logger.warning(
                "HF_TOKEN is not set — embedding calls will fail with 401. "
                "Set it as an environment variable (see Render dashboard)."
            )
        # NOTE: api-inference.huggingface.co (the old endpoint) was fully
        # decommissioned by HuggingFace and no longer resolves in DNS at
        # all (returns a 410 Gone where it still resolves elsewhere).
        # router.huggingface.co is the replacement — same request/response
        # shape, different host + path prefix.
        self.api_url = (
            f"https://router.huggingface.co/hf-inference/models/"
            f"{model_name}/pipeline/feature-extraction"
        )
        self.headers = {"Authorization": f"Bearer {self.hf_token}"}
        logger.info(f"Embedding model ready: {model_name} (HuggingFace Router API)")

    def _post_with_retry(self, payload: dict, max_retries: int = 5) -> list:
        """
        POST to the HF Inference API, retrying while the model is
        cold-starting (HF returns 503 with an estimated_time the first
        time a model is called after being idle).
        """
        last_error = None
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.api_url, headers=self.headers, json=payload, timeout=30
                )
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.warning(f"HF API request failed (attempt {attempt + 1}): {e}")
                time.sleep(2)
                continue

            if response.status_code == 200:
                return response.json()

            if response.status_code == 503:
                wait_s = 5
                try:
                    wait_s = min(response.json().get("estimated_time", 5), 20)
                except Exception:
                    pass
                logger.warning(
                    f"HF model is loading, retrying in {wait_s:.0f}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(wait_s)
                continue

            if response.status_code == 401:
                raise ValueError(
                    "HuggingFace API rejected the request (401) — check that "
                    "HF_TOKEN is set correctly."
                )

            raise ValueError(
                f"HuggingFace API error {response.status_code}: {response.text[:200]}"
            )

        raise ConnectionError(
            f"HuggingFace embedding model still unavailable after "
            f"{max_retries} retries: {last_error}"
        )

    @staticmethod
    def _to_vector(raw) -> List[float]:
        """
        Normalize the HF response into a single flat vector. Depending on
        the model/pipeline version, the API returns either:
          - a pooled sentence vector:      [0.1, 0.2, ...]
          - a token-level matrix:          [[...], [...], ...]  (needs mean-pooling)
        """
        if not raw:
            raise ValueError("Empty embedding returned from HuggingFace API")

        if isinstance(raw[0], float):
            return raw

        if isinstance(raw[0], list):
            matrix = raw[0] if raw and isinstance(raw[0][0], list) else raw
            n_tokens = len(matrix)
            dim = len(matrix[0])
            summed = [0.0] * dim
            for token_vec in matrix:
                for i, v in enumerate(token_vec):
                    summed[i] += v
            return [v / n_tokens for v in summed]

        raise ValueError("Unexpected embedding response shape from HuggingFace API")

    def embed_text(self, text: str) -> List[float]:
        """
        Convert a single text into an embedding vector.

        Args:
            text: Text to embed

        Returns:
            List of float numbers (the vector)
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        raw = self._post_with_retry({
            "inputs": text.strip(),
            "options": {"wait_for_model": True},
        })
        return self._to_vector(raw)

    def embed_batch(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """
        Convert multiple texts into embeddings, in batches (one HTTP call
        per batch instead of one per text — much faster for uploads).

        Args:
            texts:      List of texts to embed
            batch_size: How many texts to send per HF API call

        Returns:
            List of embedding vectors, same order as input
        """
        if not texts:
            return []

        all_embeddings: List[List[float]] = []
        total = len(texts)
        logger.info(f"Embedding {total} texts in batches of {batch_size} (HuggingFace API)...")

        for i in range(0, total, batch_size):
            batch = [t.strip() for t in texts[i:i + batch_size] if t and t.strip()]
            if not batch:
                continue
            try:
                raw = self._post_with_retry({
                    "inputs": batch,
                    "options": {"wait_for_model": True},
                })
                for item in raw:
                    if item and isinstance(item[0], list):
                        all_embeddings.append(self._to_vector(item))
                    else:
                        all_embeddings.append(item)
            except Exception as e:
                logger.error(f"Batch embedding failed for batch starting at {i}: {e}")
                all_embeddings.extend([[0.0] * self.EMBED_DIM] * len(batch))

            logger.info(f"Embedded {min(i + batch_size, total)}/{total} texts")

        logger.info(f"Batch embedding complete: {len(all_embeddings)} vectors")
        return all_embeddings

    def is_available(self) -> bool:
        """
        Check if the HuggingFace embedding API is reachable and the token
        is valid (does a tiny real embed call as the check).
        """
        try:
            self.embed_text("connection test")
            logger.info(f"✅ {self.model_name} is available via HuggingFace API")
            return True
        except Exception as e:
            logger.error(f"❌ HuggingFace embedding API not reachable: {e}")
            return False

    def get_embedding_size(self) -> int:
        """
        Get the dimension size of embeddings.
        all-MiniLM-L6-v2 returns 384 dimensions.
        """
        try:
            test_embed = self.embed_text("test")
            size = len(test_embed)
            logger.info(f"Embedding dimensions: {size}")
            return size
        except Exception:
            return self.EMBED_DIM