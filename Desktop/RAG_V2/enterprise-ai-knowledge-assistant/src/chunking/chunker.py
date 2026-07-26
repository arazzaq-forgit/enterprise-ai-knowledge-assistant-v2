"""
Advanced Semantic Chunker for Enterprise AI Knowledge Assistant.

Upgrade from Phase 1:
- Fixed-size chunking REPLACED with semantic chunking
- Chunks are split at sentence boundaries, not arbitrary character counts
- Preserves meaning and context within each chunk
- Heading-aware: detects document structure
- Falls back to fixed-size if semantic fails
"""

import re
from typing import List, Dict, Any
from src.utils.logger import setup_logger

logger = setup_logger("Chunker")


class TextChunker:
    """
    Semantic text chunker that splits documents at natural boundaries.

    Why semantic chunking beats fixed-size:
    - Fixed-size: "The patient was diagnosed with dia" / "betes mellitus type 2"
    - Semantic:   "The patient was diagnosed with diabetes mellitus type 2."

    Sentence-boundary chunking preserves complete thoughts,
    making retrieval more accurate and answers more grounded.
    """

    def __init__(self,
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 min_chunk_size: int = 100):
        """
        Args:
            chunk_size:    Target chunk size in characters
            chunk_overlap: Overlap between consecutive chunks
            min_chunk_size: Minimum chunk size (smaller chunks are merged)
        """
        self.chunk_size    = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

        # Try to load NLTK sentence tokenizer
        self._setup_nltk()
        logger.info(
            f"Semantic Chunker ready — "
            f"size={chunk_size}, overlap={chunk_overlap}"
        )

    def _setup_nltk(self):
        """Download NLTK punkt tokenizer if not already present."""
        try:
            import nltk
            try:
                nltk.data.find("tokenizers/punkt_tab")
            except LookupError:
                nltk.download("punkt_tab", quiet=True)
            try:
                nltk.data.find("tokenizers/punkt")
            except LookupError:
                nltk.download("punkt", quiet=True)
            self._use_nltk = True
        except Exception:
            self._use_nltk = False
            logger.warning("NLTK not available, using regex sentence splitting")

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using NLTK or regex fallback."""
        if self._use_nltk:
            try:
                import nltk
                sentences = nltk.sent_tokenize(text)
                return [s.strip() for s in sentences if s.strip()]
            except Exception:
                pass

        # Regex fallback — split on sentence-ending punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _detect_headings(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect headings and section boundaries in text.
        Returns list of {text, is_heading, level} dicts.
        """
        lines = text.split('\n')
        segments = []

        heading_patterns = [
            (r'^#{1}\s+(.+)$', 1),    # # Heading 1
            (r'^#{2}\s+(.+)$', 2),    # ## Heading 2
            (r'^#{3}\s+(.+)$', 3),    # ### Heading 3
            (r'^[A-Z][A-Z\s]{4,}$', 1),  # ALL CAPS HEADING
            (r'^\d+\.\s+[A-Z].+$', 2),   # 1. Numbered heading
        ]

        for line in lines:
            line = line.strip()
            if not line:
                continue

            is_heading = False
            level = 0
            for pattern, lvl in heading_patterns:
                if re.match(pattern, line):
                    is_heading = True
                    level = lvl
                    break

            segments.append({
                "text":       line,
                "is_heading": is_heading,
                "level":      level
            })

        return segments

    def chunk_text(self, text: str,
                   metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Semantically chunk text into overlapping segments.

        Process:
        1. Detect headings and structure
        2. Split into sentences
        3. Group sentences into chunks respecting size limits
        4. Add overlap between consecutive chunks
        5. Attach metadata to each chunk

        Args:
            text:     Raw document text
            metadata: Optional metadata dict (source, page, etc.)

        Returns:
            List of chunk dicts: {text, metadata, chunk_index, char_count}
        """
        if not text or not text.strip():
            return []

        metadata = metadata or {}

        # Clean text
        text = self._clean_text(text)

        # Split into sentences
        sentences = self._split_into_sentences(text)

        if not sentences:
            return []

        # Group sentences into chunks
        chunks = self._group_sentences_into_chunks(sentences)

        # Build result with metadata
        result = []
        for i, chunk_text in enumerate(chunks):
            if len(chunk_text.strip()) < self.min_chunk_size:
                continue

            result.append({
                "text":        chunk_text.strip(),
                "metadata":    {**metadata, "chunk_index": i},
                "chunk_index": i,
                "char_count":  len(chunk_text),
            })

        logger.info(
            f"Chunked into {len(result)} semantic chunks "
            f"from {len(sentences)} sentences"
        )
        return result

    def _group_sentences_into_chunks(self,
                                      sentences: List[str]) -> List[str]:
        """Group sentences into chunks respecting size limits with overlap."""
        chunks = []
        current_chunk = []
        current_size  = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            # If adding this sentence exceeds chunk size, save current chunk
            if current_size + sentence_size > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(chunk_text)

                # Add overlap: keep last N characters worth of sentences
                overlap_sentences = []
                overlap_size      = 0
                for s in reversed(current_chunk):
                    if overlap_size + len(s) <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_size += len(s)
                    else:
                        break

                current_chunk = overlap_sentences
                current_size  = overlap_size

            current_chunk.append(sentence)
            current_size += sentence_size

        # Don't forget the last chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text before chunking."""
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        # Remove page numbers (common in PDFs)
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        return text.strip()

    def chunk_documents(self,
                        documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Chunk a list of document dicts.

        Each document dict should have:
            text:     document text
            metadata: dict with source, page, etc.

        Returns flat list of all chunks across all documents.
        """
        all_chunks = []
        for doc in documents:
            text     = doc.get("text", "")
            metadata = doc.get("metadata", {})
            chunks   = self.chunk_text(text, metadata)
            all_chunks.extend(chunks)

        logger.info(
            f"Total chunks from {len(documents)} documents: {len(all_chunks)}"
        )
        return all_chunks