"""
PDF Document Loader for Enterprise AI Knowledge Assistant.
Extracts text, metadata and page information from PDF files.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Any
from src.utils.logger import get_loader_logger

logger = get_loader_logger()


class PDFLoader:
    """
    Loads and extracts content from PDF files.
    
    Features:
        ✅ Extracts text page by page
        ✅ Captures metadata (title, author, pages)
        ✅ Handles encrypted/corrupted PDFs gracefully
        ✅ Returns structured document chunks
    """

    def __init__(self):
        self.supported_extensions = [".pdf"]

    def load(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load a PDF file and extract all text with metadata.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of page documents with text and metadata
        """
        path = Path(file_path)

        # ── Validate file ────────────────────────────────────────
        if not path.exists():
            logger.error(f"PDF file not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        if path.suffix.lower() != ".pdf":
            logger.error(f"Not a PDF file: {file_path}")
            raise ValueError(f"Not a PDF file: {file_path}")

        logger.info(f"Loading PDF: {path.name}")

        try:
            documents = []
            pdf = fitz.open(str(path))

            # ── Extract metadata ─────────────────────────────────
            metadata = pdf.metadata or {}
            total_pages = pdf.page_count

            logger.info(f"PDF has {total_pages} pages")

            # ── Extract text page by page ────────────────────────
            for page_num in range(total_pages):
                page = pdf[page_num]
                text = page.get_text("text").strip()

                # Skip empty pages
                if not text:
                    continue

                documents.append({
                    "content": text,
                    "metadata": {
                        "source":      path.name,
                        "file_path":   str(path),
                        "file_type":   "pdf",
                        "page_number": page_num + 1,
                        "total_pages": total_pages,
                        "title":       metadata.get("title", path.stem),
                        "author":      metadata.get("author", "Unknown"),
                    }
                })

            pdf.close()
            logger.info(f"Successfully extracted {len(documents)} pages from {path.name}")
            return documents

        except Exception as e:
            logger.error(f"Failed to load PDF {path.name}: {str(e)}")
            raise

    def load_from_bytes(self, file_bytes: bytes,
                        filename: str) -> List[Dict[str, Any]]:
        """
        Load PDF directly from uploaded bytes (for Streamlit uploads).
        
        Args:
            file_bytes: Raw bytes of the PDF file
            filename:   Original filename
        """
        logger.info(f"Loading PDF from bytes: {filename}")

        try:
            documents = []
            pdf = fitz.open(stream=file_bytes, filetype="pdf")
            metadata   = pdf.metadata or {}
            total_pages = pdf.page_count

            for page_num in range(total_pages):
                page = pdf[page_num]
                text = page.get_text("text").strip()

                if not text:
                    continue

                documents.append({
                    "content": text,
                    "metadata": {
                        "source":      filename,
                        "file_type":   "pdf",
                        "page_number": page_num + 1,
                        "total_pages": total_pages,
                        "title":       metadata.get("title", filename),
                        "author":      metadata.get("author", "Unknown"),
                    }
                })

            pdf.close()
            logger.info(f"Extracted {len(documents)} pages from {filename}")
            return documents

        except Exception as e:
            logger.error(f"Failed to load PDF bytes {filename}: {str(e)}")
            raise

    def get_page_count(self, file_path: str) -> int:
        """Quick way to get total pages without full extraction."""
        pdf = fitz.open(str(file_path))
        count = pdf.page_count
        pdf.close()
        return count