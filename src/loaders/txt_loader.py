"""
Text & CSV File Loader for Enterprise AI Knowledge Assistant.
Handles .txt, .md and .csv files with smart encoding detection.
"""

import csv
import io
from pathlib import Path
from typing import List, Dict, Any
from src.utils.logger import get_loader_logger

logger = get_loader_logger()


class TxtLoader:
    """
    Loads and extracts content from text based files.

    Features:
        ✅ Handles .txt and .md files
        ✅ Handles .csv files as readable text
        ✅ Smart encoding detection (UTF-8, Latin-1)
        ✅ Loads from file path or Streamlit bytes
    """

    def __init__(self):
        self.supported_extensions = [".txt", ".md", ".csv"]
        self.encodings = ["utf-8", "latin-1", "cp1252"]

    def load(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load a text file and extract all content.

        Args:
            file_path: Path to the text file

        Returns:
            List of documents with text and metadata
        """
        path = Path(file_path)

        # ── Validate file ────────────────────────────────────────
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = path.suffix.lower()
        if suffix not in self.supported_extensions:
            raise ValueError(f"Unsupported file type: {suffix}")

        logger.info(f"Loading text file: {path.name}")

        # ── Route to correct loader ──────────────────────────────
        if suffix == ".csv":
            return self._load_csv(path)
        else:
            return self._load_text(path)

    def _load_text(self, path: Path) -> List[Dict[str, Any]]:
        """Load plain text or markdown file."""
        text = None

        # ── Try different encodings ──────────────────────────────
        for encoding in self.encodings:
            try:
                text = path.read_text(encoding=encoding)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            raise ValueError(f"Could not decode file: {path.name}")

        text = text.strip()
        if not text:
            logger.warning(f"Empty file: {path.name}")
            return []

        logger.info(f"Successfully loaded {path.name}")
        return [{
            "content": text,
            "metadata": {
                "source":    path.name,
                "file_path": str(path),
                "file_type": path.suffix.lower().replace(".", ""),
                "title":     path.stem,
                "author":    "Unknown",
            }
        }]

    def _load_csv(self, path: Path) -> List[Dict[str, Any]]:
        """Load CSV file and convert to readable text."""
        rows = []

        for encoding in self.encodings:
            try:
                with open(path, "r", encoding=encoding) as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames or []
                    rows = list(reader)
                break
            except UnicodeDecodeError:
                continue

        if not rows:
            logger.warning(f"Empty CSV: {path.name}")
            return []

        # ── Convert CSV rows to readable text ────────────────────
        lines = []
        lines.append(f"CSV File: {path.name}")
        lines.append(f"Columns: {', '.join(headers)}")
        lines.append(f"Total Rows: {len(rows)}")
        lines.append("-" * 40)

        for i, row in enumerate(rows[:500]):  # Max 500 rows
            row_text = " | ".join(
                f"{k}: {v}" for k, v in row.items() if v
            )
            lines.append(f"Row {i+1}: {row_text}")

        text = "\n".join(lines)
        logger.info(f"Loaded CSV with {len(rows)} rows from {path.name}")

        return [{
            "content": text,
            "metadata": {
                "source":    path.name,
                "file_path": str(path),
                "file_type": "csv",
                "title":     path.stem,
                "rows":      len(rows),
                "columns":   len(headers),
            }
        }]

    def load_from_bytes(self, file_bytes: bytes,
                        filename: str) -> List[Dict[str, Any]]:
        """
        Load text file from Streamlit uploaded bytes.

        Args:
            file_bytes: Raw bytes of the file
            filename:   Original filename
        """
        logger.info(f"Loading text file from bytes: {filename}")
        suffix = Path(filename).suffix.lower()

        try:
            # ── CSV from bytes ───────────────────────────────────
            if suffix == ".csv":
                text_io = io.StringIO(
                    file_bytes.decode("utf-8", errors="replace")
                )
                reader = csv.DictReader(text_io)
                headers = reader.fieldnames or []
                rows = list(reader)

                lines = []
                lines.append(f"CSV File: {filename}")
                lines.append(f"Columns: {', '.join(headers)}")
                lines.append(f"Total Rows: {len(rows)}")
                lines.append("-" * 40)

                for i, row in enumerate(rows[:500]):
                    row_text = " | ".join(
                        f"{k}: {v}" for k, v in row.items() if v
                    )
                    lines.append(f"Row {i+1}: {row_text}")

                return [{
                    "content": "\n".join(lines),
                    "metadata": {
                        "source":    filename,
                        "file_type": "csv",
                        "title":     filename,
                        "rows":      len(rows),
                    }
                }]

            # ── Plain text from bytes ────────────────────────────
            else:
                text = file_bytes.decode("utf-8", errors="replace").strip()
                if not text:
                    return []

                return [{
                    "content": text,
                    "metadata": {
                        "source":    filename,
                        "file_type": suffix.replace(".", ""),
                        "title":     filename,
                    }
                }]

        except Exception as e:
            logger.error(f"Failed to load {filename}: {str(e)}")
            raise