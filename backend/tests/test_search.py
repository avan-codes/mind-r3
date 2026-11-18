"""
mind-r3 RAG - tests for search / answer generation.

Run:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest

from langchain_core.documents import Document

from src.config import load_config
from src.embedding import EmbeddingPipeline
from src.retriever import RAGRetriever, RetrievalResult
from src.vector_store import FAISSVectorStore
import src.search as search_mod


class FakeRetriever:
    """Returns canned results so we never touch the vector store / embedder."""

    def __init__(self, results):
        self.results = results

    def retrieve(self, query, top_k=None, min_score=None):
        results = list(self.results)
        if min_score is not None:
            results = [r for r in results if r.similarity >= min_score]
        return results


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    def _fake_llm(self, messages, config):
        return "This is a grounded answer based on the context."

    def test_empty_context_grounded_refusal(self):
        retriever = FakeRetriever([])
        resp = search_mod.rag_search("anything?", retriever, config=self.config)
        self.assertEqual(resp["sources"], [])
        self.assertEqual(resp["retrieval_scores"], [])
        self.assertEqual(resp["retrieval_confidence"], 0.0)
        self.assertIn("sufficient information", resp["answer"])

    def test_empty_context_with_context_flag(self):
        retriever = FakeRetriever([])
        resp = search_mod.rag_search("q", retriever, config=self.config, return_context=True)
        self.assertEqual(resp["context"], "")

    def test_with_results_structured(self):
        docs = [
            Document(
                page_content="The capital of France is Paris.",
                metadata={"filename": "geo.pdf", "page": 4, "source": "/x/geo.pdf"},
            )
        ]
        result = RetrievalResult(
            content="The capital of France is Paris.",
            source="/x/geo.pdf",
            filename="geo.pdf",
            page=4,
            metadata={"filename": "geo.pdf", "page": 4},
            doc_id="geo.pdf#p4#0",
            distance=0.1,
            similarity=0.909,
        )
        retriever = FakeRetriever([result])

        # monkeypatch the NVIDIA call to avoid network
        search_mod.nvidia_chat = lambda messages, config: "Paris is the capital of France."

        resp = search_mod.rag_search(
            "What is the capital of France?", retriever, config=self.config, top_k=5
        )
        self.assertEqual(resp["answer"], "Paris is the capital of France.")
        self.assertEqual(len(resp["sources"]), 1)
        self.assertEqual(resp["sources"][0]["filename"], "geo.pdf")
        self.assertEqual(resp["sources"][0]["page"], 4)
        self.assertEqual(resp["retrieval_scores"], [0.909])
        self.assertGreater(resp["retrieval_confidence"], 0.0)

    def test_min_score_filters_in_search(self):
        docs = [
            Document(
                page_content="low relevance",
                metadata={"filename": "low.pdf", "page": 1, "source": "/x/low.pdf"},
            )
        ]
        result = RetrievalResult(
            content="low relevance",
            source="/x/low.pdf",
            filename="low.pdf",
            page=1,
            metadata={"filename": "low.pdf", "page": 1},
            doc_id="low.pdf#p1#0",
            distance=10.0,
            similarity=0.09,  # below threshold
        )
        retriever = FakeRetriever([result])
        # retriever.retrieve applies min_score; with min_score=0.5 it drops it
        resp = search_mod.rag_search("q", retriever, config=self.config, min_score=0.5)
        self.assertEqual(resp["sources"], [])
        self.assertEqual(resp["retrieval_confidence"], 0.0)


if __name__ == "__main__":
    unittest.main()
