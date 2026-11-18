"""mind-r3 RAG package."""

from .config import RAGConfig, load_config
from .data_loader import load_all_documents
from .embedding import EmbeddingPipeline, chunk_documents
from .vector_store import FAISSVectorStore
from .retriever import RAGRetriever, RetrievalResult
from .search import rag_search, build_prompt, nvidia_chat

__all__ = [
    "RAGConfig",
    "load_config",
    "load_all_documents",
    "EmbeddingPipeline",
    "chunk_documents",
    "FAISSVectorStore",
    "RAGRetriever",
    "RetrievalResult",
    "rag_search",
    "build_prompt",
    "nvidia_chat",
]
