"""
mind-r3 RAG - command-line application.

Usage:
    python3 backend/cli.py ingest                 # build / refresh the FAISS index
    python3 backend/cli.py ask "your question"    # ask a question against the index
    python3 backend/cli.py ask "..." --top-k 8 --min-score 0.25
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import List

# Allow running both as `python3 backend/cli.py` and via `python3 -m backend.cli`.
_BACKEND_ROOT = os.path.dirname(os.path.abspath(__file__))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

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
logger = logging.getLogger("mindr3.app")


def cmd_ingest(config) -> int:
    ensure_dirs()
    logger.info("Starting ingestion from %s", DOCUMENTS_DIR)

    # 1-4. Load documents
    documents: List = load_all_documents(DOCUMENTS_DIR)
    if not documents:
        logger.error("No documents loaded. Put files in %s and re-run.", DOCUMENTS_DIR)
        return 1

    # 5. Chunk
    chunks = chunk_documents(
        documents,
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )
    if not chunks:
        logger.error("No chunks produced from documents.")
        return 1

    # 6. Embed
    emb = EmbeddingPipeline(config)
    embeddings = emb.embed_chunks(chunks, batch_size=32)
    dim = emb.get_embedding_dimension()
    logger.info("Embedding dimension: %d | chunks: %d", dim, len(chunks))

    # 7. Build + persist FAISS index
    store = FAISSVectorStore(dimension=dim)
    store.build(embeddings, chunks)
    store.save()
    logger.info("Ingestion complete. Index saved to %s", store.storage_folder)
    return 0


def cmd_ask(config, question: str, top_k: int, min_score: float, return_context: bool) -> int:
    ensure_dirs()
    # Load existing index (never re-embed if we can reuse it).
    dim = EmbeddingPipeline(config).get_embedding_dimension()
    store = FAISSVectorStore(dimension=dim)
    if not store.load():
        logger.error(
            "No persisted FAISS index found. Run 'ingest' first: python3 src/app.py ingest"
        )
        return 1

    emb = EmbeddingPipeline(config)
    retriever = RAGRetriever(store, emb, config)

    response = rag_search(
        question,
        retriever,
        config=config,
        top_k=top_k,
        min_score=min_score,
        return_context=return_context,
    )

    print("\n=== ANSWER ===")
    print(response["answer"])
    print(f"\nRetrieval confidence (heuristic): {response['retrieval_confidence']}")
    print(f"Retrieval scores: {response['retrieval_scores']}")
    print(f"Sources ({len(response['sources'])}):")
    for s in response["sources"]:
        loc = s["filename"] or "unknown"
        loc += f" (page {s['page']})" if s.get("page") is not None else ""
        print(f"  - {loc} | similarity={s['similarity']}")
        print(f"      excerpt: {s['excerpt']}")

    if return_context:
        print("\n=== FULL CONTEXT ===")
        print(response.get("context", ""))
    print()
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="mind-r3 modular RAG (NVIDIA LLM backend)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ingest = sub.add_parser("ingest", help="Ingest documents and build the FAISS index")
    p_ingest.set_defaults(func=lambda config, args: cmd_ingest(config))

    p_ask = sub.add_parser("ask", help="Ask a question against the persisted index")
    p_ask.add_argument("question", type=str, help="Your question")
    p_ask.add_argument("--top-k", type=int, default=5, help="Top-K chunks to retrieve")
    p_ask.add_argument("--min-score", type=float, default=0.0, help="Min similarity [0,1]")
    p_ask.add_argument("--context", action="store_true", help="Also print full retrieved context")
    p_ask.set_defaults(func=lambda config, args: cmd_ask(config, args.question, args.top_k, args.min_score, args.context))

    args = parser.parse_args(argv)
    config = load_config()
    if config.nvidia_api_key is None:
        logger.error(
            "NVIDIA_API_KEY not found. Add an nvapi- key to ~/Desktop/API_KEYs or export NVIDIA_API_KEY."
        )
        return 1
    return args.func(config, args)


if __name__ == "__main__":
    sys.exit(main())
