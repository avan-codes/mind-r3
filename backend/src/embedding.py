"""
mind-r3 RAG - embedding pipeline.

Independent embedding module built on Sentence Transformers. The same model is
used for both document chunks and incoming user queries so query and document
vectors live in the same space.

Classes / functions:
    EmbeddingPipeline   - load model, embed texts/chunks, report dimension
    chunk_documents     - split Documents into chunks (RecursiveCharacterTextSplitter)
"""

from __future__ import annotations

import logging
from typing import List, Sequence

import re

from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer

try:  # LangChain 1.x moved this to langchain-text-splitter (not always available)
    from langchain.text_splitter import RecursiveCharacterTextSplitter  # type: ignore
except ImportError:  # pragma: no cover - fallback when the extra package is missing
    RecursiveCharacterTextSplitter = None  # type: ignore[assignment]


if RecursiveCharacterTextSplitter is None:
    class RecursiveCharacterTextSplitter:  # type: ignore[no-redef]
        """Self-contained recursive character text splitter.

        Mirrors LangChain's RecursiveCharacterTextSplitter: tries separators in
        order, recursively splits pieces that are still too large, and merges
        pieces back together with the configured overlap.
        """

        def __init__(
            self,
            chunk_size: int = 1000,
            chunk_overlap: int = 200,
            separators: Sequence[str] | None = None,
            length_function=len,
        ) -> None:
            self.chunk_size = int(chunk_size)
            self.chunk_overlap = int(chunk_overlap)
            self.separators = list(separators) if separators else ["\n\n", "\n", " ", ""]
            self.length_function = length_function

        def split_text(self, text: str) -> List[str]:
            return self._split_text(text, self.separators)

        def _split_text(self, text: str, separators: List[str]) -> List[str]:
            final_chunks: List[str] = []
            separator = separators[-1]
            new_separators: List[str] = []
            for i, s in enumerate(separators):
                if s == "":
                    separator = s
                    new_separators = []
                    break
                if re.search(re.escape(s), text):
                    separator = s
                    new_separators = separators[i + 1 :]
                    break

            if separator:
                splits = _split_with_separator(text, separator)
            else:
                splits = list(text)

            good_splits: List[str] = []
            for s in splits:
                if self.length_function(s) < self.chunk_size:
                    good_splits.append(s)
                else:
                    if good_splits:
                        final_chunks.extend(self._merge_splits(good_splits, separator))
                        good_splits = []
                    if new_separators:
                        final_chunks.extend(self._split_text(s, new_separators))
                    else:
                        final_chunks.append(s)
            if good_splits:
                final_chunks.extend(self._merge_splits(good_splits, separator))
            return final_chunks

        def _merge_splits(self, splits: List[str], separator: str) -> List[str]:
            docs: List[str] = []
            current: List[str] = []
            total = 0
            for s in splits:
                sep_len = len(separator) if current and separator else 0
                new_total = total + sep_len + self.length_function(s)
                if new_total > self.chunk_size and current:
                    docs.append(_join(current, separator))
                    # carry over an overlap from the end of the current chunk
                    while current and total > self.chunk_overlap:
                        removed = current.pop(0)
                        total -= self.length_function(removed) + (
                            len(separator) if current and separator else 0
                        )
                current.append(s)
                total = new_total
            if current:
                docs.append(_join(current, separator))
            return docs


def _split_with_separator(text: str, separator: str) -> List[str]:
    if not separator:
        return list(text)
    parts = re.split(f"({re.escape(separator)})", text)
    merged: List[str] = []
    for i in range(0, len(parts), 2):
        piece = parts[i]
        if i + 1 < len(parts):
            piece = piece + parts[i + 1]
        if piece:
            merged.append(piece)
    return merged


def _join(parts: List[str], separator: str) -> str:
    if not separator:
        return "".join(parts)
    return separator.join(parts)

from .config import RAGConfig, load_config

logger = logging.getLogger("mindr3.embedding")


class EmbeddingPipeline:
    """Encode text into embeddings with a configurable Sentence Transformer model.

    The model is loaded once and reused. ``embed_chunks`` and
    ``generate_embeddings`` share the same underlying encoder so document and
    query vectors are comparable.
    """

    def __init__(self, config: RAGConfig | None = None) -> None:
        self.config = config or load_config()
        self._model: SentenceTransformer | None = None

    # ------------------------------------------------------------------ #
    # Model lifecycle
    # ------------------------------------------------------------------ #
    def load_model(self) -> SentenceTransformer:
        """Load (or return the already-loaded) Sentence Transformer model."""
        if self._model is None:
            logger.info("Loading embedding model: %s", self.config.embedding_model)
            self._model = SentenceTransformer(self.config.embedding_model)
            logger.info("Embedding model loaded")
        return self._model

    @property
    def model(self) -> SentenceTransformer:
        return self.load_model()

    def get_embedding_dimension(self) -> int:
        """Return the embedding vector dimension (384 for the default model)."""
        model = self.load_model()
        dim = None
        for method in ("get_embedding_dimension", "get_sentence_embedding_dimension"):
            if hasattr(model, method):
                dim = getattr(model, method)()
                break
        if dim is None:
            dim = self.config.embedding_dimension
        return int(dim)

    # ------------------------------------------------------------------ #
    # Encoding
    # ------------------------------------------------------------------ #
    def generate_embeddings(self, texts: Sequence[str], batch_size: int = 32) -> List[List[float]]:
        """Embed a list of strings. Returns a list of float vectors."""
        model = self.load_model()
        texts = [t for t in texts]
        if not texts:
            return []
        embeddings = model.encode(
            list(texts),
            batch_size=batch_size,
            show_progress_bar=len(texts) > 50,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    def embed_chunks(self, chunks: Sequence[Document], batch_size: int = 32) -> List[List[float]]:
        """Embed the page_content of a sequence of Document chunks."""
        texts = [c.page_content for c in chunks]
        return self.generate_embeddings(texts, batch_size=batch_size)


def chunk_documents(
    documents: Sequence[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separators: Sequence[str] | None = None,
) -> List[Document]:
    """Split Documents into smaller chunks while preserving metadata.

    Uses LangChain's RecursiveCharacterTextSplitter. Metadata (source, page,
    file_type, ...) is copied onto every child chunk.
    """
    if separators is None:
        separators = ["\n\n", "\n", " ", ""]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=list(separators),
        length_function=len,
    )

    chunked: List[Document] = []
    for doc in documents:
        if not doc.page_content or not doc.page_content.strip():
            continue
        splits = splitter.split_text(doc.page_content)
        for split in splits:
            if not split.strip():
                continue
            chunk_meta = dict(doc.metadata or {})
            chunk = Document(page_content=split, metadata=chunk_meta)
            chunked.append(chunk)

    logger.info("Produced %d chunks from %d documents", len(chunked), len(documents))
    return chunked
