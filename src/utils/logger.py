"""
Professional logging system for Enterprise AI Knowledge Assistant.
Logs to both terminal and log file simultaneously.
"""

import logging
import os
from pathlib import Path
from datetime import datetime


def setup_logger(name: str = "RAG_Assistant") -> logging.Logger:
    """
    Create and configure a professional logger.
    
    Usage:
        from src.utils.logger import setup_logger
        logger = setup_logger(__name__)
        logger.info("Something happened")
        logger.error("Something went wrong")
    """

    # ── Create logs folder if not exists ────────────────────────
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # ── Log filename with today's date ───────────────────────────
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"app_{today}.log"

    # ── Create logger ────────────────────────────────────────────
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # ── Avoid duplicate handlers ─────────────────────────────────
    if logger.handlers:
        return logger

    # ── Format: time | level | file | message ───────────────────
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # ── Handler 1: Print to terminal ─────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # ── Handler 2: Save to log file ──────────────────────────────
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # ── Attach both handlers ─────────────────────────────────────
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# ── Convenience loggers for each module ─────────────────────────
def get_loader_logger():
    return setup_logger("Loader")

def get_pipeline_logger():
    return setup_logger("Pipeline")

def get_vectorstore_logger():
    return setup_logger("VectorStore")

def get_llm_logger():
    return setup_logger("LLM")

def get_ui_logger():
    return setup_logger("UI")