"""
Document Manager for Enterprise AI Knowledge Assistant.
Central hub that routes files to correct loader automatically.
"""

import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from src.loaders.pdf_loader import PDFLoader
from src.loaders.docx_loader import DocxLoader
from src.loaders.txt_loader import TxtLoader
from src.utils.logger import get_loader_logger

logger = get_loader_logger()


class DocumentManager:
    """
    Master document loader that handles ALL file types.

    Automatically detects file type and routes to
    the correct loader. Also handles URL scraping.

    Supported:
        ✅ PDF  files → PDFLoader
        ✅ DOCX files → DocxLoader
        ✅ TXT  files → TxtLoader
        ✅ MD   files → TxtLoader
        ✅ CSV  files → TxtLoader
        ✅ URLs       → Web Scraper
    """

    def __init__(self):
        self.pdf_loader  = PDFLoader()
        self.docx_loader = DocxLoader()
        self.txt_loader  = TxtLoader()

        self.supported_formats = [
            ".pdf", ".docx", ".txt", ".md", ".csv"
        ]

    # ── Load from file path ──────────────────────────────────────
    def load_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load any supported file by detecting its type.

        Args:
            file_path: Path to the file

        Returns:
            List of document dicts with content and metadata
        """
        path = Path(file_path)
        suffix = path.suffix.lower()

        logger.info(f"Loading file: {path.name} (type: {suffix})")

        if suffix == ".pdf":
            return self.pdf_loader.load(file_path)
        elif suffix == ".docx":
            return self.docx_loader.load(file_path)
        elif suffix in [".txt", ".md", ".csv"]:
            return self.txt_loader.load(file_path)
        else:
            raise ValueError(
                f"Unsupported file type: {suffix}\n"
                f"Supported: {self.supported_formats}"
            )

    # ── Load from Streamlit upload bytes ────────────────────────
    def load_from_bytes(self, file_bytes: bytes,
                        filename: str) -> List[Dict[str, Any]]:
        """
        Load uploaded file from Streamlit bytes.

        Args:
            file_bytes: Raw bytes from st.file_uploader
            filename:   Original filename from upload

        Returns:
            List of document dicts
        """
        suffix = Path(filename).suffix.lower()
        logger.info(f"Loading uploaded file: {filename}")

        if suffix == ".pdf":
            return self.pdf_loader.load_from_bytes(file_bytes, filename)
        elif suffix == ".docx":
            return self.docx_loader.load_from_bytes(file_bytes, filename)
        elif suffix in [".txt", ".md", ".csv"]:
            return self.txt_loader.load_from_bytes(file_bytes, filename)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    # ── Load from URL ────────────────────────────────────────────
    def load_url(self, url: str,
                 timeout: int = 30) -> List[Dict[str, Any]]:
        """
        Scrape and load content from a web URL.

        Args:
            url:     Website URL to scrape
            timeout: Request timeout in seconds

        Returns:
            List of document dicts
        """
        logger.info(f"Scraping URL: {url}")

        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 Chrome/91.0 Safari/537.36"
                )
            }
            response = requests.get(url, headers=headers,
                                    timeout=timeout)
            response.raise_for_status()

            # ── Parse HTML ───────────────────────────────────────
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove unwanted tags
            for tag in soup(["script", "style", "nav",
                              "footer", "header", "aside"]):
                tag.decompose()

            # Extract clean text
            text = soup.get_text(separator="\n", strip=True)

            # Remove blank lines
            lines = [l for l in text.splitlines() if l.strip()]
            clean_text = "\n".join(lines)

            if not clean_text:
                logger.warning(f"No content found at URL: {url}")
                return []

            # Get page title
            title = soup.title.string if soup.title else url

            logger.info(f"Successfully scraped URL: {url}")
            return [{
                "content": clean_text,
                "metadata": {
                    "source":    url,
                    "file_type": "url",
                    "title":     title,
                    "author":    "Web",
                }
            }]

        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to URL: {url}")
            raise ConnectionError(f"Cannot connect to: {url}")
        except requests.exceptions.Timeout:
            logger.error(f"URL timed out: {url}")
            raise TimeoutError(f"URL timed out: {url}")
        except Exception as e:
            logger.error(f"Failed to scrape URL {url}: {str(e)}")
            raise

    # ── Load multiple files at once ──────────────────────────────
    def load_multiple(self,
                      file_paths: Optional[List[str]] = None,
                      urls: Optional[List[str]] = None
                      ) -> List[Dict[str, Any]]:
        """
        Load multiple files and URLs at once.

        Args:
            file_paths: List of file paths
            urls:       List of URLs

        Returns:
            Combined list of all documents
        """
        all_documents = []
        errors = []

        # ── Load files ───────────────────────────────────────────
        for path in (file_paths or []):
            try:
                docs = self.load_file(path)
                all_documents.extend(docs)
                logger.info(f"Loaded: {path}")
            except Exception as e:
                errors.append(f"File {path}: {str(e)}")
                logger.error(f"Failed: {path} — {str(e)}")

        # ── Load URLs ────────────────────────────────────────────
        for url in (urls or []):
            try:
                docs = self.load_url(url)
                all_documents.extend(docs)
                logger.info(f"Scraped: {url}")
            except Exception as e:
                errors.append(f"URL {url}: {str(e)}")
                logger.error(f"Failed: {url} — {str(e)}")

        if errors:
            logger.warning(f"Errors encountered: {errors}")

        logger.info(
            f"Total documents loaded: {len(all_documents)}"
        )
        return all_documents

    def get_supported_formats(self) -> List[str]:
        """Return list of supported file formats."""
        return self.supported_formats + ["URLs"]