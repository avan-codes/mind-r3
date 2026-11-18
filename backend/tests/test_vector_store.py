"""
mind-r3 RAG - tests for FAISSVectorStore.

Run:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import math
import os
import tempfile
import unittest
from pathlib import Path

from langchain_core.documents import Document

from src.vector_store import FAISSVectorStore


def make_store(dim, folder):
    return FAISSVectorStore(dimension=dim, storage_folder=folder)


class TestVectorStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.dim = 8

    def _docs(self, n):
        return [
            Document(
                page_content=f"document {i} content",
                metadata={"filename": f"f{i}.txt", "page": i + 1, "file_type": "txt"},
            )
            for i in range(n)
        ]

    def test_build_and_search(self):
        store = make_store(self.dim, self.tmp)
        import numpy as np

        vecs = np.eye(self.dim, dtype="float32").tolist()[:4]  # 4 orthonormal vecs
        docs = self._docs(4)
        ids = store.build(vecs, docs)
        self.assertEqual(len(ids), 4)
        self.assertEqual(store.index.ntotal, 4)

        # query == first vector -> distance 0 -> similarity 1.0
        res = store.search(vecs[0], top_k=4)
        self.assertEqual(len(res), 4)
        best = res[0]
        self.assertAlmostEqual(best["distance"], 0.0, places=5)
        self.assertAlmostEqual(best["similarity"], 1.0, places=5)
        self.assertEqual(best["filename"], "f0.txt")
        self.assertEqual(best["page"], 1)
        self.assertIn("id", best)

    def test_add_increments(self):
        store = make_store(self.dim, self.tmp)
        import numpy as np

        v1 = [[1.0] + [0.0] * 7]
        v2 = [[0.0] + [1.0] + [0.0] * 6]
        store.build(v1, self._docs(1))
        store.add(v2, self._docs(1))
        self.assertEqual(store.index.ntotal, 2)

    def test_invalid_dimension_raises(self):
        store = make_store(self.dim, self.tmp)
        with self.assertRaises(ValueError):
            store.build([[1.0, 2.0]], [Document(page_content="x")])

    def test_save_and_load_roundtrip(self):
        import numpy as np

        store1 = make_store(self.dim, self.tmp)
        vecs = np.eye(self.dim, dtype="float32").tolist()[:3]
        store1.build(vecs, self._docs(3))
        store1.save()

        # files exist
        self.assertTrue((Path(self.tmp) / "index.faiss").exists())
        self.assertTrue((Path(self.tmp) / "documents.json").exists())
        self.assertTrue((Path(self.tmp) / "id_map.json").exists())

        store2 = make_store(self.dim, self.tmp)
        self.assertTrue(store2.load())
        self.assertEqual(store2.index.ntotal, 3)
        self.assertEqual(len(store2.documents), 3)
        self.assertEqual(len(store2.ids), 3)
        res = store2.search(vecs[0], top_k=1)
        self.assertEqual(len(res), 1)

    def test_empty_store_search_returns_empty(self):
        store = make_store(self.dim, self.tmp)
        self.assertEqual(store.search([0.0] * self.dim, top_k=5), [])

    def test_load_missing_returns_false(self):
        store = make_store(self.dim, self.tmp)
        self.assertFalse(store.load())


if __name__ == "__main__":
    unittest.main()
