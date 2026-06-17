"""
Configuration settings for Enterprise AI Knowledge Assistant.
Loads and validates all settings from configs.yaml
"""

import yaml
import os
from pathlib import Path
from dataclasses import dataclass


# ── Root path of project ────────────────────────────────────────
ROOT_DIR = Path(__file__).parent.parent.parent
CONFIG_FILE = ROOT_DIR / "configs.yaml"


def load_config() -> dict:
    """Load configuration from configs.yaml"""
    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Config file not found at {CONFIG_FILE}")
    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f)


# Load once at startup
CONFIG = load_config()


class AppSettings:
    """Application level settings"""
    NAME        = CONFIG["app"]["name"]
    VERSION     = CONFIG["app"]["version"]
    DESCRIPTION = CONFIG["app"]["description"]
    AUTHOR      = CONFIG["app"]["author"]
    THEME       = CONFIG["app"]["theme"]


class OllamaSettings:
    """Ollama model settings"""
    BASE_URL        = CONFIG["ollama"]["base_url"]
    LLM_MODEL       = CONFIG["ollama"]["llm_model"]
    EMBEDDING_MODEL = CONFIG["ollama"]["embedding_model"]
    TEMPERATURE     = CONFIG["ollama"]["temperature"]
    MAX_TOKENS      = CONFIG["ollama"]["max_tokens"]
    STREAMING       = CONFIG["ollama"]["streaming"]


class VectorStoreSettings:
    """Vector database settings"""
    TYPE            = CONFIG["vectorstore"]["type"]
    PERSIST_DIR     = ROOT_DIR / CONFIG["vectorstore"]["persist_directory"]
    COLLECTION_NAME = CONFIG["vectorstore"]["collection_name"]
    CHUNK_SIZE      = CONFIG["vectorstore"]["chunk_size"]
    CHUNK_OVERLAP   = CONFIG["vectorstore"]["chunk_overlap"]
    TOP_K           = CONFIG["vectorstore"]["top_k_results"]


class LoaderSettings:
    """Document loader settings"""
    SUPPORTED_FORMATS = CONFIG["loaders"]["supported_formats"]
    MAX_FILE_SIZE_MB  = CONFIG["loaders"]["max_file_size_mb"]
    URL_TIMEOUT       = CONFIG["loaders"]["url_timeout_seconds"]


class UISettings:
    """Streamlit UI settings"""
    PAGE_TITLE       = CONFIG["ui"]["page_title"]
    PAGE_ICON        = CONFIG["ui"]["page_icon"]
    LAYOUT           = CONFIG["ui"]["layout"]
    MAX_CHAT_HISTORY = CONFIG["ui"]["max_chat_history"]
    SHOW_SOURCES     = CONFIG["ui"]["show_sources"]
    SHOW_CONFIDENCE  = CONFIG["ui"]["show_confidence"]
    STREAMING        = CONFIG["ui"]["streaming_enabled"]


class LogSettings:
    """Logging settings"""
    LEVEL         = CONFIG