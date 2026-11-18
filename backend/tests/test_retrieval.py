"""
mind-r3 RAG - tests for RAGRetriever.

Run:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import numpy as np
import unittest

from langchain_core.documents import Document

from src.config import load_config
from src.embedding import EmbeddingPipeline
from src.retriever import RAGRetriever
from src.vector_store import FAISSVectorStore


class TestRetriever(unittest.TestCase):
    def setUp(self):
        self.tmp = "/tmp/mindr3_test_retriever_store"
        import shutil, os

        shutil.rmtree(self.tmp, ignore_errors=True)
        self.config = load_config()
        self.dim = 4
        self.store = FAISSVectorStore(dimension=self.dim, storage_folder=self.tmp)
        docs = [
            Document(page_content="alpha topic", metadata={"filename": "a.txt", "page": 1}),
            Document(page_content="beta topic", metadata={"filename": "b.txt", "page": 2}),
            Document(page_content="gamma topic", metadata={"filename": "c.txt", "page": 3}),
        ]
        # orthonormal vectors
        vecs = np.eye(self.dim, dtype="float32").tolist()[:3]
        self.store.build(vecs, docs)
        self.emb = EmbeddingPipeline(self.config)

    def _monkeypatch_query(self, vec):
        self.emb.generate_embeddings = lambda texts, **kw: [list(vec)] * len(texts)

    def test_retrieve_top_k(self):
        retriever = RAGRetriever(self.store, self.emb, self.config)
        self._monkeypatch_query([1.0, 0.0, 0.0, 0.0])  # matches doc 0 exactly
        results = retriever.retrieve("alpha", top_k=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].filename, "a.txt")
        self.assertAlmostEqual(results[0].similarity, 1.0, places=5)
        self.assertIsNotNone(results[0].doc_id)
        self.assertIsInstance(results[0].metadata, dict)

    def test_min_score_filters(self):
        retriever = RAGRetriever(self.store, self.emb, self.config)
        # query orthogonal to all -> similarity ~0.5 (1/(1+dist)) where dist=2 for orthonormal? 
        # Actually [1,0,0,0] vs [0,1,0,0]: L2 dist = sqrt(2)=1.414, sim=1/(1+1.414)=0.414
        self._monkeypatch_query([0.0, 1.0, 0.0, 0.0])  # matches doc 1 exactly actually
        results = retriever.retrieve("beta", top_k=3, min_score=0.9)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].filename, "b.txt")

    def test_empty_query(self):
        retriever = RAGRetriever(self.store, self.emb, self.config)
        self.assertEqual(retriever.retrieve(""), [])
        self.assertEqual(retriever.retrieve("   "), [])


if __name__ == "__main__":
    unittest.main()
