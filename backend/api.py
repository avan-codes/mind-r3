"""
mind-r3 RAG - FastAPI REST layer.

Connects the existing modular RAG pipeline (src.config, src.data_loader,
src.embedding, src.vector_store, src.retriever, src.search) to a REST API.

Endpoints:
    GET  /health          - service health
    GET  /status          - vector index status
    POST /ingest          - (re)build the FAISS index from data/documents/
    POST /ask             - ask a grounded question; returns answer + sources
"""

from __future__ import annotations

import logging
import os
import sys
from typing import List, Optional

# Allow running both as `python3 backend/api.py` and via uvicorn import from backend/.
_BACKEND_ROOT = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import DOCUMENTS_DIR, ensure_dirs, load_config
from src.data_loader import load_all_documents
from src.embedding import EmbeddingPipeline, chunk_documents
from src.retriever import RAGRetriever
from src.search import rag_search
from src.vector_store import FAISSVectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("mindr3.api")

app = FastAPI(
    title="mind-r3 RAG API",
    description="Document-based Retrieval-Augmented Generation API (NVIDIA Nemotron backend)",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS — lets a frontend on another origin (Vite/React dev server, etc.)
# call this API. Comma-separated origins via CORS_ALLOW_ORIGINS env var;
# defaults to common local dev ports. Set CORS_ALLOW_ORIGINS=* to allow all.
# ---------------------------------------------------------------------------
_cors_origins = os.getenv(
    "CORS_ALLOW_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost:8080,"
    "http://127.0.0.1:5173,http://127.0.0.1:3000,http://127.0.0.1:8080",
)
allow_origins = ["*"] if _cors_origins.strip() == "*" else [
    o.strip() for o in _cors_origins.split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class IngestResponse(BaseModel):
    status: str
    documents_loaded: int
    chunks_created: int
    embedding_dimension: int
    vectors_stored: int
    index_path: str


class AskRequest(BaseModel):
    question: str = Field(..., description="Your natural-language question")
    top_k: int = Field(5, ge=1, le=50, description="Max chunks to retrieve")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="Min similarity [0,1]")
    return_context: bool = Field(False, description="Include full retrieved context")


class SourceOut(BaseModel):
    filename: Optional[str]
    page: Optional[int]
    similarity: float
    distance: float
    excerpt: str
    doc_id: Optional[str]


class AskResponse(BaseModel):
    answer: str
    sources: List[SourceOut]
    retrieval_scores: List[float]
    retrieval_confidence: float
    context: Optional[str] = None


class StatusResponse(BaseModel):
    index_exists: bool
    vectors: int
    dimension: int
    storage_folder: str


# ---------------------------------------------------------------------------
# Helpers (shared with app.py logic)
# ---------------------------------------------------------------------------
def _get_config() -> object:
    config = load_config()
    if config.nvidia_api_key is None:
        raise HTTPException(
            status_code=500,
            detail="NVIDIA_API_KEY not configured. Add an nvapi- key to ~/Desktop/API_KEYs "
            "or export NVIDIA_API_KEY.",
        )
    return config


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health", tags=["system"])
def health():
    return {"status": "ok", "service": "mind-r3-rag-api"}


@app.get("/status", response_model=StatusResponse, tags=["index"])
def status():
    config = _get_config()
    dim = EmbeddingPipeline(config).get_embedding_dimension()
    store = FAISSVectorStore(dimension=dim)
    exists = store.exists()
    vectors = 0
    if exists:
        store.load()
        vectors = store.index.ntotal
    return StatusResponse(
        index_exists=exists,
        vectors=vectors,
        dimension=dim,
        storage_folder=str(store.storage_folder),
    )


@app.post("/ingest", response_model=IngestResponse, tags=["index"])
def ingest():
    """Discover, load, chunk, embed and persist the FAISS index."""
    ensure_dirs()
    config = _get_config()

    documents = load_all_documents(DOCUMENTS_DIR)
    if not documents:
        raise HTTPException(
            status_code=400,
            detail=f"No documents found in {DOCUMENTS_DIR}. Add PDF/TXT/CSV/HTML/XLSX/JSON files.",
        )

    chunks = chunk_documents(
        documents,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )
    if not chunks:
        raise HTTPException(status_code=400, detail="No chunks produced from documents.")

    emb = EmbeddingPipeline(config)
    embeddings = emb.embed_chunks(chunks, batch_size=32)
    dim = emb.get_embedding_dimension()

    store = FAISSVectorStore(dimension=dim)
    store.build(embeddings, chunks)
    store.save()

    logger.info("Ingestion complete: %d vectors stored", store.index.ntotal)
    return IngestResponse(
        status="ok",
        documents_loaded=len(documents),
        chunks_created=len(chunks),
        embedding_dimension=dim,
        vectors_stored=store.index.ntotal,
        index_path=str(store.index_path),
    )


@app.post("/ask", response_model=AskResponse, tags=["query"])
def ask(req: AskRequest):
    """Ask a grounded question against the persisted FAISS index."""
    ensure_dirs()
    config = _get_config()

    dim = EmbeddingPipeline(config).get_embedding_dimension()
    store = FAISSVectorStore(dimension=dim)
    if not store.load():
        raise HTTPException(
            status_code=409,
            detail="No persisted FAISS index found. Call POST /ingest first.",
        )

    emb = EmbeddingPipeline(config)
    retriever = RAGRetriever(store, emb, config)

    response = rag_search(
        req.question,
        retriever,
        config=config,
        top_k=req.top_k,
        min_score=req.min_score,
        return_context=req.return_context,
    )

    sources = [
        SourceOut(
            filename=s["filename"],
            page=s["page"],
            similarity=s["similarity"],
            distance=s["distance"],
            excerpt=s["excerpt"],
            doc_id=s["doc_id"],
        )
        for s in response["sources"]
    ]

    return AskResponse(
        answer=response["answer"],
        sources=sources,
        retrieval_scores=response["retrieval_scores"],
        retrieval_confidence=response["retrieval_confidence"],
        context=response.get("context") if req.return_context else None,
    )


# ---------------------------------------------------------------------------
# Dev entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=False)
