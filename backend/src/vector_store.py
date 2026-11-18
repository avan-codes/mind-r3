"""
mind-r3 RAG - persistent vector database (FAISS CPU).

Builds, persists, reloads and searches a FAISS index. Documents and their ids
are stored alongside the index so the store can be reloaded without
re-processing or re-embedding anything.
"""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import List, Optional, Sequence

import numpy as np
import faiss

from langchain_core.documents import Document

from .config import FAISS_DIR, INDEX_PATH, META_PATH, ID_MAP_PATH

logger = logging.getLogger("mindr3.vector_store")


def _make_id(source: str | None, page: Optional[int], index: int) -> str:
    """Stable, human-readable document id."""
    src = Path(source).name if source else "unknown"
    loc = f"#p{page}" if page is not None else ""
    return f"{src}{loc}#{index}"


class FAISSVectorStore:
    """FAISS CPU vector store with local persistence."""

    def __init__(self, dimension: int, storage_folder: str | Path = FAISS_DIR) -> None:
        self.dimension = int(dimension)
        self.storage_folder = Path(storage_folder)
        self.storage_folder.mkdir(parents=True, exist_ok=True)
        self.index_path = self.storage_folder / "index.faiss"
        self.meta_path = self.storage_folder / "documents.json"
        self.id_map_path = self.storage_folder / "id_map.json"

        # in-memory state
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents: List[Document] = []
        self.ids: List[str] = []

    # ------------------------------------------------------------------ #
    # Build / add
    # ------------------------------------------------------------------ #
    def add(
        self,
        embeddings: Sequence[Sequence[float]],
        documents: Sequence[Document],
        ids: Optional[Sequence[str]] = None,
    ) -> List[str]:
        """Add embeddings + documents to the index. Returns the ids used."""
        if len(embeddings) != len(documents):
            raise ValueError("embeddings and documents must have the same length")
        if not embeddings:
            return []

        arr = np.asarray(embeddings, dtype="float32")
        if arr.shape[1] != self.dimension:
            raise ValueError(
                f"Embedding dimension {arr.shape[1]} != index dimension {self.dimension}"
            )

        if ids is None:
            ids = [
                _make_id(d.metadata.get("source") if d.metadata else None,
                         d.metadata.get("page") if d.metadata else None, i)
                for i, d in enumerate(documents, start=len(self.documents))
            ]
        else:
            ids = list(ids)

        self.index.add(arr)
        self.documents.extend(documents)
        self.ids.extend(ids)
        logger.info("Added %d vectors to FAISS index (total %d)", len(embeddings), self.index.ntotal)
        return list(ids)

    def build(
        self,
        embeddings: Sequence[Sequence[float]],
        documents: Sequence[Document],
        ids: Optional[Sequence[str]] = None,
    ) -> List[str]:
        """Create a fresh index from embeddings + documents (replaces current)."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        self.ids = []
        return self.add(embeddings, documents, ids)

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def save(self) -> None:
        """Persist the index, documents and ids to disk."""
        faiss.write_index(self.index, str(self.index_path))
        with open(self.meta_path, "w", encoding="utf-8") as fh:
            json.dump([as_serializable(d) for d in self.documents], fh, ensure_ascii=False, indent=2)
        with open(self.id_map_path, "w", encoding="utf-8") as fh:
            json.dump(self.ids, fh, ensure_ascii=False, indent=2)
        logger.info("Saved FAISS index (%d vectors) to %s", self.index.ntotal, self.storage_folder)

    def load(self) -> bool:
        """Load an existing index from disk. Returns True if loaded."""
        if not (self.index_path.exists() and self.meta_path.exists() and self.id_map_path.exists()):
            logger.warning("No persisted FAISS index found at %s", self.storage_folder)
            return False
        try:
            self.index = faiss.read_index(str(self.index_path))
            with open(self.meta_path, "r", encoding="utf-8") as fh:
                raw_docs = json.load(fh)
            self.documents = [Document(page_content=d["page_content"], metadata=d.get("metadata", {})) for d in raw_docs]
            with open(self.id_map_path, "r", encoding="utf-8") as fh:
                self.ids = json.load(fh)
            logger.info("Loaded FAISS index (%d vectors) from %s", self.index.ntotal, self.storage_folder)
            return True
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to load FAISS index: %s", exc)
            return False

    def exists(self) -> bool:
        return self.index_path.exists() and self.meta_path.exists() and self.id_map_path.exists()

    # ------------------------------------------------------------------ #
    # Search
    # ------------------------------------------------------------------ #
    def search(
        self,
        query_embedding: Sequence[float],
        top_k: int = 5,
    ) -> List[dict]:
        """Search the index. Returns results sorted by distance (closest first).

        Each result:
            content, source, filename, page, metadata, id, distance, similarity
        """
        if self.index.ntotal == 0:
            return []

        q = np.asarray([query_embedding], dtype="float32")
        if q.shape[1] != self.dimension:
            raise ValueError(f"Query embedding dimension {q.shape[1]} != index dimension {self.dimension}")

        top_k = max(1, min(top_k, self.index.ntotal))
        distances, indices = self.index.search(q, top_k)

        results: List[dict] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            idx = int(idx)
            doc = self.documents[idx]
            meta = doc.metadata or {}
            distance = float(dist)
            # Heuristic similarity (NOT a calibrated probability): L2 distance -> [0,1]
            similarity = 1.0 / (1.0 + distance)
            results.append({
                "content": doc.page_content,
                "source": meta.get("source"),
                "filename": meta.get("filename"),
                "page": meta.get("page"),
                "metadata": meta,
                "id": self.ids[idx],
                "distance": distance,
                "similarity": similarity,
            })
        return results


def as_serializable(doc: Document) -> dict:
    return {"page_content": doc.page_content, "metadata": doc.metadata or {}}
