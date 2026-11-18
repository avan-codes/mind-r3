"""
mind-r3 RAG - central configuration.

Reads secrets from the API_KEYs file (never hardcoded) and centralises every
model / path / retrieval setting used by the RAG pipeline.

Environment variables take precedence over the API_KEYs file.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
STORAGE_DIR = PROJECT_ROOT / "storage"
FAISS_DIR = STORAGE_DIR / "faiss"
INDEX_PATH = FAISS_DIR / "index.faiss"
META_PATH = FAISS_DIR / "documents.json"
ID_MAP_PATH = FAISS_DIR / "id_map.json"

# Default location of the secrets file the user asked us to read.
DEFAULT_API_KEYS_FILE = Path.home() / "Desktop" / "API_KEYs"

# ---------------------------------------------------------------------------
# NVIDIA API key loading (from the API_KEYs file)
# ---------------------------------------------------------------------------
_NVIDIA_TOKEN_RE = re.compile(r"nvapi-[A-Za-z0-9_-]+")


def load_nvidia_api_key(api_keys_file: str | Path | None = None) -> str | None:
    """Return the first NVIDIA API key found in the API_KEYs file.

    The file may contain several keys (e.g. one labelled "System:"). We scan
    every line for ``nvapi-<token>`` and return the first match so the caller
    never sees a hardcoded credential. An explicit ``NVIDIA_API_KEY`` env var
    wins over the file.
    """
    env_key = os.getenv("NVIDIA_API_KEY")
    if env_key:
        return env_key

    file_path = Path(api_keys_file) if api_keys_file else DEFAULT_API_KEYS_FILE
    if not file_path.exists():
        return None

    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None

    matches = _NVIDIA_TOKEN_RE.findall(text)
    return matches[0] if matches else None


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass
class RAGConfig:
    # --- NVIDIA LLM -------------------------------------------------------
    nvidia_api_key: str | None = field(default=None)
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1/chat/completions"
    nvidia_model: str = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
    temperature: float = 0.0
    max_tokens: int = 65536
    reasoning_budget: int = 16384
    top_p: float = 0.95
    stream: bool = False

    # --- Embedding --------------------------------------------------------
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # --- Chunking ---------------------------------------------------------
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # --- Retrieval --------------------------------------------------------
    top_k: int = 5
    min_score: float = 0.0

    def __post_init__(self) -> None:
        if self.nvidia_api_key is None:
            self.nvidia_api_key = load_nvidia_api_key()


def load_config() -> RAGConfig:
    return RAGConfig()


def ensure_dirs() -> None:
    """Create storage / data directories if they are missing."""
    for p in (DOCUMENTS_DIR, STORAGE_DIR, FAISS_DIR):
        p.mkdir(parents=True, exist_ok=True)
