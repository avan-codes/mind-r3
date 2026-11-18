"""
mind-r3 RAG - retrieval pipeline.

Embeds a natural-language query with the same model used for documents, searches
the persistent FAISS index, applies Top-K + a similarity threshold, and returns
the retrieved chunks with scores and metadata.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Sequence

from langchain_core.documents import Document

from .config import RAGConfig, load_config
from .embedding import EmbeddingPipeline
from .vector_store import FAISSVectorStore

logger = logging.getLogger("mindr3.retriever")


class RetrievalResult:
    """A single retrieved chunk with its score and provenance."""

    def __init__(
        self,
        content: str,
        source: Optional[str],
        filename: Optional[str],
        page: Optional[int],
        metadata: dict,
        doc_id: str,
        distance: float,
        similarity: float,
    ) -> None:
        self.content = content
        self.source = source
        self.filename = filename
        self.page = page
        self.metadata = metadata
        self.doc_id = doc_id
        self.distance = distance
        self.similarity = similarity

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "source": self.source,
            "filename": self.filename,
            "page": self.page,
            "metadata": self.metadata,
            "doc_id": self.doc_id,
            "distance": self.distance,
            "similarity": self.similarity,
        }


class RAGRetriever:
    def __init__(
        self,
        vector_store: FAISSVectorStore,
        embedding: EmbeddingPipeline,
        config: RAGConfig | None = None,
    ) -> None:
        self.vector_store = vector_store
        self.embedding = embedding
        self.config = config or load_config()

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> List[RetrievalResult]:
        """Retrieve the most relevant chunks for a query.

        Args:
            query: natural-language user question.
            top_k: max chunks to return (defaults to config.top_k).
            min_score: minimum similarity in [0,1] to keep a result
                       (defaults to config.min_score).

        Returns:
            List of RetrievalResult sorted by similarity descending.
        """
        if not query or not query.strip():
            logger.warning("Empty query passed to retriever")
            return []

        top_k = top_k if top_k is not None else self.config.top_k
        min_score = self.config.min_score if min_score is None else min_score

        # Embed the query with the SAME model used for documents.
        query_embedding = self.embedding.generate_embeddings([query.strip()], batch_size=1)[0]

        raw = self.vector_store.search(query_embedding, top_k=top_k)

        results: List[RetrievalResult] = []
        for item in raw:
            if item["similarity"] < min_score:
                continue
            results.append(
                RetrievalResult(
                    content=item["content"],
                    source=item["source"],
                    filename=item["filename"],
                    page=item["page"],
                    metadata=item["metadata"],
                    doc_id=item["id"],
                    distance=item["distance"],
                    similarity=item["similarity"],
                )
            )

        logger.info("Retrieved %d chunks for query (top_k=%d, min_score=%.2f)",
                    len(results), top_k, min_score)
        return results
