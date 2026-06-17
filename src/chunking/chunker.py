"""
Text Chunker for Enterprise AI Knowledge Assistant.
Splits large documents into smaller chunks for vector storage.
"""

from typing import List, Dict, Any
from src.utils.logger import setup_logger

logger = setup_logger("Chunker")


class TextChunker:
    """
    Splits documents into overlapping chunks.

    Why chunking?
        LLMs have token limits — we can't feed
        a 100 page PDF all at once. We split it
        into small overlapping pieces so nothing
        important gets cut off at boundaries.

    Example:
        chunk_size=1000, chunk_overlap=200 means:
        Chunk 1: characters 0    → 1000
        Chunk 2: characters 800  → 1800
        Chunk 3: characters 1600 → 2600
        (200 character overlap keeps context)
    """

    def __init__(self,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        """
        Args:
            chunk_size:    Max characters per chunk
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size    = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.info(
            f"Chunker ready — "
            f"size={chunk_size}, overlap={chunk_overlap}"
        )

    def split_text(self, text: str) -> List[str]:
        """
        Split a single text string into chunks.

        Args:
            text: Raw text to split

        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []

        chunks = []
        start  = 0
        text   = text.strip()

        while start < len(text):
            end = start + self.chunk_size

            # ── Don't cut in middle of word ──────────────────────
            if end < len(text):
                # Find last space before end
                last_space = text.rfind(" ", start, end)
                if last_space > start:
                    end = last_space

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # ── Move forward with overlap ────────────────────────
            start = end - self.chunk_overlap
            if start >= len(text):
                break

        return chunks

    def split_documents(self,
                        documents: List[Dict[str, Any]]
                        ) -> List[Dict[str, Any]]:
        """
        Split a list of documents into chunks.
        Each chunk keeps the original metadata.

        Args:
            documents: List of document dicts with
                      'content' and 'metadata' keys

        Returns:
            List of chunk dicts with content and metadata
        """
        all_chunks = []

        for doc in documents:
            content  = doc.get("content", "")
            metadata = doc.get("metadata", {})

            if not content.strip():
                continue

            # ── Split content into chunks ────────────────────────
            text_chunks = self.split_text(content)

            # ── Add metadata to each chunk ───────────────────────
            for i, chunk_text in enumerate(text_chunks):
                all_chunks.append({
                    "content": chunk_text,
                    "metadata": {
                        **metadata,
                        "chunk_index":  i,
                        "total_chunks": len(text_chunks),
                        "chunk_size":   len(chunk_text),
                    }
                })

        logger.info(
            f"Split {len(documents)} documents "
            f"into {len(all_chunks)} chunks"
        )
        return all_chunks

    def get_stats(self,
                  chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about created chunks.

        Returns useful info to show in the UI.
        """
        if not chunks:
            return {}

        sizes = [len(c["content"]) for c in chunks]

        return {
            "total_chunks":    len(chunks),
            "avg_chunk_size":  round(sum(sizes) / len(sizes)),
            "min_chunk_size":  min(sizes),
            "max_chunk_size":  max(sizes),
            "total_characters": sum(sizes),
            "total_words": sum(
                len(c["content"].split())
                for c in chunks
            ),
        }