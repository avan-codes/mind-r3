"""
mind-r3 RAG - tests for data_loader.

Run:  python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from src.data_loader import (
    load_file,
    load_all_documents,
    discover_files,
    SUPPORTED_EXTENSIONS,
)


class TestLoader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _write(self, name, content, mode="w"):
        p = Path(self.tmp) / name
        p.write_text(content, encoding="utf-8") if mode == "w" else p.write_bytes(content)
        return p

    def test_discover_files(self):
        self._write("a.txt", "hello")
        self._write("b.pdf", "not a real pdf")
        self._write("c.xyz", "unsupported")
        files = discover_files(self.tmp)
        names = {f.name for f in files}
        self.assertIn("a.txt", names)
        self.assertIn("b.pdf", names)
        self.assertNotIn("c.xyz", names)

    def test_txt_loading_and_metadata(self):
        p = self._write("note.txt", "The quick brown fox jumps over the lazy dog.")
        docs = load_file(p)
        self.assertEqual(len(docs), 1)
        self.assertIn("quick brown fox", docs[0].page_content)
        meta = docs[0].metadata
        self.assertEqual(meta["filename"], "note.txt")
        self.assertEqual(meta["file_type"], "txt")
        self.assertEqual(meta["source"], str(p.resolve()))
        self.assertIsNone(meta["page"])

    def test_unsupported_raises(self):
        p = self._write("weird.xyz", "content")
        with self.assertRaises(ValueError):
            load_file(p)

    def test_empty_txt_returns_empty(self):
        p = self._write("empty.txt", "")
        self.assertEqual(load_file(p), [])

    def test_load_all_documents_skips_bad(self):
        self._write("good.txt", "readable content")
        self._write("bad.xyz", "x")
        docs = load_all_documents(self.tmp)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].metadata["filename"], "good.txt")

    def test_supported_extensions(self):
        self.assertIn(".pdf", SUPPORTED_EXTENSIONS)
        self.assertIn(".txt", SUPPORTED_EXTENSIONS)
        self.assertIn(".csv", SUPPORTED_EXTENSIONS)
        self.assertIn(".json", SUPPORTED_EXTENSIONS)


if __name__ == "__main__":
    unittest.main()
