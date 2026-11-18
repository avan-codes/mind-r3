"""
mind-r3 RAG - tests for embedding + chunking.

Run:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import types
import unittest
from unittest.mock import patch

from langchain_core.documents import Document

from src.config import load_config
from src.embedding import EmbeddingPipeline, chunk_documents


class FakeModel:
    """Stand-in for SentenceTransformer so tests do not need to download weights."""

    def __init__(self, *args, **kwargs):
        self._dim = 384

    def get_sentence_embedding_dimension(self):
        return self._dim

    def encode(self, texts, **kwargs):
        import numpy as np

        n = len(texts) if isinstance(texts, list) else 1
        return np.zeros((n, self._dim), dtype="float32")


class TestEmbedding(unittest.TestCase):
    def setUp(self):
        self.config = load_config()

    @patch("src.embedding.SentenceTransformer", FakeModel)
    def test_dimension(self):
        emb = EmbeddingPipeline(self.config)
        self.assertEqual(emb.get_embedding_dimension(), 384)

    @patch("src.embedding.SentenceTransformer", FakeModel)
    def test_generate_embeddings_shape(self):
        emb = EmbeddingPipeline(self.config)
        vecs = emb.generate_embeddings(["hello world", "second text"], batch_size=2)
        self.assertEqual(len(vecs), 2)
        self.assertEqual(len(vecs[0]), 384)

    @patch("src.embedding.SentenceTransformer", FakeModel)
    def test_embed_chunks(self):
        emb = EmbeddingPipeline(self.config)
        docs = [Document(page_content="one", metadata={"file_type": "txt"}),
                Document(page_content="two", metadata={"file_type": "txt"})]
        vecs = emb.embed_chunks(docs)
        self.assertEqual(len(vecs), 2)

    def test_chunk_documents_preserves_metadata(self):
        docs = [
            Document(
                page_content="A" * 2500,
                metadata={"filename": "x.pdf", "page": 1, "file_type": "pdf"},
            )
        ]
        chunks = chunk_documents(docs, chunk_size=1000, chunk_overlap=200)
        self.assertGreaterEqual(len(chunks), 2)
        for c in chunks:
            self.assertEqual(c.metadata.get("filename"), "x.pdf")
            self.assertEqual(c.metadata.get("page"), 1)
            self.assertTrue(len(c.page_content) <= 1000)

    def test_chunk_documents_skips_empty(self):
        docs = [Document(page_content="   ", metadata={"file_type": "txt"})]
        self.assertEqual(chunk_documents(docs), [])


if __name__ == "__main__":
    unittest.main()
