"""
mind-r3 RAG - document loading.

Converts PDF / TXT / CSV / HTML / XLSX / JSON files into a standardised list of
LangChain ``Document`` objects (page_content + metadata). Every loader runs in
its own try/except so a single corrupted file never aborts the whole ingestion.

Metadata keys preserved on every Document:
    source        - absolute file path
    filename      - original file name
    file_type     - extension (lowercase, no dot)
    page          - page number (1-based) when applicable, else None
    total_pages   - total page count (PDF) when available
    author        - document author when available
    created       - creation timestamp when available
    modified      - modification timestamp when available
"""

from __future__ import annotations

import json
import mimetypes
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

from langchain_core.documents import Document

from .config import DOCUMENTS_DIR

# ---------------------------------------------------------------------------
# Supported extensions
# ---------------------------------------------------------------------------
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".csv", ".html", ".htm", ".xlsx", ".json"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base_metadata(path: Path, file_type: str) -> dict:
    stat = path.stat()
    return {
        "source": str(path.resolve()),
        "filename": path.name,
        "file_type": file_type,
        "page": None,
        "total_pages": None,
        "author": None,
        "created": _iso_from_ts(stat.st_ctime),
        "modified": _iso_from_ts(stat.st_mtime),
    }


def _iso_from_ts(ts: float) -> Optional[str]:
    try:
        return datetime.fromtimestamp(ts, timezone.utc).isoformat()
    except (OSError, ValueError, OverflowError):
        return None


# ---------------------------------------------------------------------------
# Individual loaders
# ---------------------------------------------------------------------------
def _load_pdf(path: Path) -> List[Document]:
    docs: List[Document] = []
    try:
        import fitz  # PyMuPDF
    except ImportError:
        fitz = None  # type: ignore[assignment]

    metadata = _base_metadata(path, "pdf")
    total_pages = 0

    if fitz is not None:
        try:
            doc = fitz.open(str(path))
            total_pages = doc.page_count
            meta = doc.metadata or {}
            metadata["author"] = meta.get("author") or metadata["author"]
            metadata["created"] = meta.get("creationDate") or metadata["created"]
            metadata["modified"] = meta.get("modDate") or metadata["modified"]
            for i, page in enumerate(doc):
                text = page.get_text() or ""
                page_meta = dict(metadata)
                page_meta["page"] = i + 1
                page_meta["total_pages"] = total_pages
                if text.strip():
                    docs.append(Document(page_content=text, metadata=page_meta))
            doc.close()
            return docs
        except Exception:
            # fall through to pypdf below
            pass

    # Fallback: PyPDF
    try:
        from pypdf import PdfReader
    except ImportError:
        from PyPDF2 import PdfReader  # type: ignore[no-redef]

    try:
        reader = PdfReader(str(path))
        total_pages = len(reader.pages)
        info = reader.metadata or {}
        metadata["author"] = getattr(info, "author", None) or metadata["author"]
        metadata["created"] = (
            getattr(info, "creation_date", None) or metadata["created"]
        )
        metadata["modified"] = (
            getattr(info, "modification_date", None) or metadata["modified"]
        )
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            page_meta = dict(metadata)
            page_meta["page"] = i + 1
            page_meta["total_pages"] = total_pages
            if text.strip():
                docs.append(Document(page_content=text, metadata=page_meta))
    except Exception as exc:  # pragma: no cover - defensive
        raise RuntimeError(f"Failed to read PDF {path}: {exc}") from exc

    return docs


def _load_txt(path: Path) -> List[Document]:
    metadata = _base_metadata(path, "txt")
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        raise RuntimeError(f"Failed to read TXT {path}: {exc}") from exc
    if not text.strip():
        return []
    return [Document(page_content=text, metadata=metadata)]


def _load_csv(path: Path) -> List[Document]:
    import csv

    metadata = _base_metadata(path, "csv")
    docs: List[Document] = []
    try:
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as fh:
            reader = csv.DictReader(fh)
            for row_idx, row in enumerate(reader):
                parts = [f"{k}: {v}" for k, v in row.items() if v is not None]
                text = " | ".join(parts)
                if not text.strip():
                    continue
                row_meta = dict(metadata)
                row_meta["page"] = row_idx + 1  # reuse page field as row number
                docs.append(Document(page_content=text, metadata=row_meta))
    except Exception as exc:
        raise RuntimeError(f"Failed to read CSV {path}: {exc}") from exc
    return docs


def _load_html(path: Path) -> List[Document]:
    metadata = _base_metadata(path, "html")
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        BeautifulSoup = None  # type: ignore[assignment]

    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        raise RuntimeError(f"Failed to read HTML {path}: {exc}") from exc

    if BeautifulSoup is not None:
        try:
            soup = BeautifulSoup(raw, "html.parser")
            # drop script/style
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text(separator="\n")
        except Exception:
            text = raw
    else:
        text = raw

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    text = "\n".join(lines)
    if not text.strip():
        return []
    return [Document(page_content=text, metadata=metadata)]


def _load_xlsx(path: Path) -> List[Document]:
    import openpyxl

    metadata = _base_metadata(path, "xlsx")
    docs: List[Document] = []
    try:
        wb = openpyxl.load_workbook(str(path), data_only=True, read_only=True)
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
                parts = [
                    f"{c}: {v}"
                    for c, v in zip(ws.iter_cols(min_col=1, max_col=len(row), max_row=1).__next__(), row)
                    if v is not None
                ]
                # Simpler: just join all non-None cell values
                parts = [str(v) for v in row if v is not None]
                text = " | ".join(parts)
                if not text.strip():
                    continue
                row_meta = dict(metadata)
                row_meta["page"] = row_idx
                row_meta["sheet"] = sheet_name
                docs.append(Document(page_content=text, metadata=row_meta))
        wb.close()
    except Exception as exc:
        raise RuntimeError(f"Failed to read XLSX {path}: {exc}") from exc
    return docs


def _load_json(path: Path) -> List[Document]:
    metadata = _base_metadata(path, "json")
    docs: List[Document] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception as exc:
        raise RuntimeError(f"Failed to read JSON {path}: {exc}") from exc

    def _flatten(obj, prefix=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield from _flatten(v, f"{prefix}.{k}" if prefix else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                yield from _flatten(v, f"{prefix}[{i}]")
        else:
            yield prefix, obj

    items = list(_flatten(data))
    for key, value in items:
        text = f"{key}: {value}"
        if not text.strip():
            continue
        item_meta = dict(metadata)
        item_meta["page"] = key  # JSON path as locator
        docs.append(Document(page_content=text, metadata=item_meta))
    return docs


_EXTENSION_LOADERS = {
    ".pdf": _load_pdf,
    ".txt": _load_txt,
    ".csv": _load_csv,
    ".html": _load_html,
    ".htm": _load_html,
    ".xlsx": _load_xlsx,
    ".json": _load_json,
}


def load_file(path: str | Path) -> List[Document]:
    """Load a single file into Documents. Raises on unsupported/unreadable."""
    path = Path(path)
    ext = path.suffix.lower()
    if ext not in _EXTENSION_LOADERS:
        raise ValueError(f"Unsupported file type: {ext}")
    return _EXTENSION_LOADERS[ext](path)


def discover_files(data_directory: str | Path = DOCUMENTS_DIR) -> List[Path]:
    """Recursively find all supported files under data_directory."""
    data_directory = Path(data_directory)
    if not data_directory.exists():
        return []
    found: List[Path] = []
    for path in data_directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            found.append(path)
    return sorted(found)


def load_all_documents(
    data_directory: str | Path = DOCUMENTS_DIR,
) -> List[Document]:
    """Auto-discover and load every supported file in data_directory.

    Corrupted / unsupported / empty files are skipped gracefully (logged) and
    never abort the whole run. Returns a flat list of LangChain Documents.
    """
    import logging

    logger = logging.getLogger("mindr3.loader")
    data_directory = Path(data_directory)
    if not data_directory.exists():
        logger.warning("Data directory does not exist: %s", data_directory)
        return []

    files = discover_files(data_directory)
    logger.info("Discovered %d supported files in %s", len(files), data_directory)

    documents: List[Document] = []
    for path in files:
        try:
            file_docs = load_file(path)
            if file_docs:
                documents.extend(file_docs)
                logger.debug("Loaded %d docs from %s", len(file_docs), path.name)
            else:
                logger.debug("Skipped empty file: %s", path.name)
        except Exception as exc:  # one bad file must not stop ingestion
            logger.error("Failed to load %s: %s", path, exc)
            continue

    logger.info("Loaded %d total document chunks from %d files", len(documents), len(files))
    return documents


__all__ = [
    "load_file",
    "discover_files",
    "load_all_documents",
    "SUPPORTED_EXTENSIONS",
]
