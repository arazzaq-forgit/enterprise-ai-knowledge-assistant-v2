"""
Helper utilities for Enterprise AI Knowledge Assistant.
Reusable functions used across the entire project.
"""

import os
import re
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class FileHelper:
    """Utilities for file operations."""

    @staticmethod
    def get_file_size_mb(file_bytes: bytes) -> float:
        """Get file size in MB."""
        return round(len(file_bytes) / (1024 * 1024), 2)

    @staticmethod
    def is_valid_file_size(file_bytes: bytes,
                           max_mb: float = 50.0) -> bool:
        """Check if file is within size limit."""
        return FileHelper.get_file_size_mb(file_bytes) <= max_mb

    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get lowercase file extension."""
        return Path(filename).suffix.lower()

    @staticmethod
    def is_supported_format(filename: str) -> bool:
        """Check if file format is supported."""
        supported = [".pdf", ".docx", ".txt", ".md", ".csv"]
        return FileHelper.get_file_extension(
            filename
        ) in supported

    @staticmethod
    def get_file_hash(file_bytes: bytes) -> str:
        """
        Generate unique hash for a file.
        Used to detect duplicate uploads.
        """
        return hashlib.md5(file_bytes).hexdigest()[:8]

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Remove special characters from filename."""
        name = Path(filename).stem
        clean = re.sub(r'[^\w\s-]', '', name)
        return clean.strip()

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Convert bytes to human readable format.

        Examples:
            1024        → "1.0 KB"
            1048576     → "1.0 MB"
            1073741824  → "1.0 GB"
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes/1024**2:.1f} MB"
        else:
            return f"{size_bytes/1024**3:.1f} GB"


class TextHelper:
    """Utilities for text processing."""

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean text by removing extra whitespace
        and special characters.
        """
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special chars but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:()\-\'\"]+', ' ', text)
        return text.strip()

    @staticmethod
    def truncate_text(text: str,
                      max_chars: int = 200,
                      suffix: str = "...") -> str:
        """Truncate text to max length with suffix."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars].rsplit(' ', 1)[0] + suffix

    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text."""
        return len(text.split()) if text else 0

    @staticmethod
    def count_sentences(text: str) -> int:
        """Count sentences in text."""
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])

    @staticmethod
    def extract_keywords(text: str,
                         top_n: int = 10) -> List[str]:
        """
        Extract most frequent meaningful words.
        Simple keyword extraction without ML.
        """
        # Common stop words to ignore
        stop_words = {
            "the", "a", "an", "and", "or", "but",
            "in", "on", "at", "to", "for", "of",
            "with", "by", "from", "is", "are", "was",
            "were", "be", "been", "have", "has", "had",
            "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "this", "that",
            "these", "those", "it", "its", "as", "if"
        }

        words = re.findall(r'\b[a-zA-Z]{4,}\b',
                           text.lower())
        freq: Dict[str, int] = {}
        for word in words:
            if word not in stop_words:
                freq[word] = freq.get(word, 0) + 1

        sorted_words = sorted(
            freq.items(), key=lambda x: x[1], reverse=True
        )
        return [w[0] for w in sorted_words[:top_n]]

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if string is a valid URL."""
        pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)'
            r'+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$',
            re.IGNORECASE
        )
        return bool(pattern.match(url))


class TimeHelper:
    """Utilities for time operations."""

    @staticmethod
    def get_timestamp() -> str:
        """Get current timestamp as string."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def get_date() -> str:
        """Get current date as string."""
        return datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def measure_time(func):
        """
        Decorator to measure function execution time.

        Usage:
            @TimeHelper.measure_time
            def my_function():
                ...
        """
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            duration = round(end - start, 2)
            print(f"⏱️ {func.__name__} took {duration}s")
            return result
        return wrapper

    @staticmethod
    def format_duration(seconds: float) -> str:
        """
        Format duration in human readable form.

        Examples:
            0.5   → "0.5 seconds"
            65    → "1 minute 5 seconds"
            3665  → "1 hour 1 minute"
        """
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins} minute{'s' if mins>1 else ''} " \
                   f"{secs} seconds"
        else:
            hours = int(seconds // 3600)
            mins  = int((seconds % 3600) // 60)
            return f"{hours} hour{'s' if hours>1 else ''} " \
                   f"{mins} minute{'s' if mins>1 else ''}"


class DisplayHelper:
    """Utilities for Streamlit UI display."""

    @staticmethod
    def get_file_icon(filename: str) -> str:
        """Get emoji icon for file type."""
        ext = FileHelper.get_file_extension(filename)
        icons = {
            ".pdf":  "📄",
            ".docx": "📝",
            ".txt":  "📃",
            ".md":   "📋",
            ".csv":  "📊",
        }
        return icons.get(ext, "📁")

    @staticmethod
    def get_similarity_color(score: float) -> str:
        """Get color based on similarity score."""
        if score >= 0.7:
            return "🟢"
        elif score >= 0.5:
            return "🟡"
        else:
            return "🔴"

    @staticmethod
    def format_stats_card(title: str,
                          value: Any,
                          icon: str = "📊") -> str:
        """Format a stats card for display."""
        return f"{icon} **{title}**: {value}"

    @staticmethod
    def clean_source_name(source: str,
                          max_length: int = 30) -> str:
        """Shorten long source names for display."""
        if len(source) <= max_length:
            return source
        return source[:max_length-3] + "..."