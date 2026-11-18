#!/usr/bin/env python3
"""
mind-r3 Book Collector
----------------------
A legitimate, ethical tool to organize and collect psychology / dark psychology /
human behaviour / manipulation / peak-performance books into the mind-r3 data
directory.

ETHICS / LEGAL NOTICE:
- This tool does NOT scrape or download copyrighted material automatically.
- It only downloads from URLs YOU explicitly provide from legitimate sources
  (Project Gutenberg, Open Library, Internet Archive, official publisher/author
  sites, your library, etc.).
- Commercial titles must be purchased or borrowed from a library. Do not use
  this tool to facilitate piracy.

Usage:
    python3 src/book_collector.py init
    python3 src/book_collector.py list
    python3 src/book_collector.py download --id 8 --url "https://..."  # legitimate URL only
    python3 src/book_collector.py report
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CATALOG_PATH = DATA_DIR / "books_catalog.json"
REPORT_PATH = DATA_DIR / "DATA_COLLECTION_REPORT.md"
BOOKS_DIR = DATA_DIR / "books"

# Category -> folder mapping (sanitized)
CATEGORY_FOLDERS = {
    "Dark Psychology / Manipulation": "dark_psychology_manipulation",
    "Dark Psychology / Safety": "dark_psychology_safety",
    "Dark Psychology": "dark_psychology",
    "Human Behaviour": "human_behaviour",
    "Human Behaviour": "human_behaviour",
    "Psychology": "psychology",
    "Psychology / Behavioural Economics": "psychology_behavioural_economics",
    "Psychology / Cognitive": "psychology_cognitive",
    "Psychology / Emotions": "psychology_emotions",
    "Psychology / Foundations": "psychology_foundations",
    "Psychology / Happiness": "psychology_happiness",
    "Psychology / Health": "psychology_health",
    "Psychology / Psychoanalysis": "psychology_psychoanalysis",
    "Psychology / Relationships": "psychology_relationships",
    "Psychology / Self-Control": "psychology_self_control",
    "Psychology / Trauma": "psychology_trauma",
    "Psychology / Transactional Analysis": "psychology_transactional_analysis",
    "Influence / Persuasion": "influence_persuasion",
    "Influence / Social Skills": "influence_social_skills",
    "Strategy / Psychology": "strategy_psychology",
    "Peak Performance": "peak_performance",
    "Peak Performance / Mindset": "peak_performance_mindset",
    "Peak Performance / Psychology": "peak_performance_psychology",
    "Negotiation / Psychology": "negotiation_psychology",
}

LEGIT_DOMAINS = [
    "gutenberg.org",
    "openlibrary.org",
    "archive.org",
    "standardbooks.org",
    "gutenberg.ca",
    "authorama.com",
    "bartleby.com",
]


def sanitize_folder(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"[\s_-]+", "_", name)
    return name.strip("_")


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_-]+", "_", text).strip("_")


def load_catalog() -> Dict[str, Any]:
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_catalog(catalog: Dict[str, Any]) -> None:
    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)


def init_folders() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BOOKS_DIR.mkdir(parents=True, exist_ok=True)
    catalog = load_catalog()
    seen = set()
    for book in catalog["books"]:
        folder = CATEGORY_FOLDERS.get(book["category"], sanitize_folder(book["category"]))
        if folder in seen:
            continue
        seen.add(folder)
        (BOOKS_DIR / folder).mkdir(parents=True, exist_ok=True)
    save_catalog(catalog)
    print(f"[init] Category folders created under {BOOKS_DIR}")


def list_books() -> None:
    catalog = load_catalog()
    print(f"\n{'ID':<4} {'Title':<45} {'Author':<25} {'Category':<35} {'Source':<12} {'Downloaded'}")
    print("-" * 130)
    for b in catalog["books"]:
        print(
            f"{b['id']:<4} {b['title']:<45} {b['author']:<25} "
            f"{b['category']:<35} {b['source_type']:<12} {b['is_downloaded']}"
        )
    print(f"\nTotal: {catalog['catalog_metadata']['total_books']} books")
    print(f"Catalog: {CATALOG_PATH}")


def is_legitimate_url(url: Optional[str]) -> bool:
    if not url:
        return False
    try:
        from urllib.parse import urlparse
        host = urlparse(url).netloc.lower()
        return any(d in host for d in LEGIT_DOMAINS)
    except Exception:
        return False


def download_book(book_id: int, url: str) -> str:
    catalog = load_catalog()
    book = next((b for b in catalog["books"] if b["id"] == book_id), None)
    if not book:
        raise SystemExit(f"[error] Book id {book_id} not found in catalog.")

    if not is_legitimate_url(url):
        raise SystemExit(
            f"[error] URL not from a recognized legitimate domain: {url}\n"
            f"Allowed domains: {', '.join(LEGIT_DOMAINS)}\n"
            "Provide a URL from Project Gutenberg, Open Library, Internet Archive, "
            "or another legitimate source you have rights to access."
        )

    folder = CATEGORY_FOLDERS.get(book["category"], sanitize_folder(book["category"]))
    target_dir = BOOKS_DIR / folder
    target_dir.mkdir(parents=True, exist_ok=True)

    ext = ".txt"
    if url.lower().endswith((".pdf", ".epub", ".mobi", ".html", ".htm")):
        ext = os.path.splitext(url)[1]
    safe_name = f"{book['id']:02d}_{slugify(book['title'])}{ext}"
    target_path = target_dir / safe_name

    print(f"[download] {book['title']} by {book['author']}")
    print(f"[download] From: {url}")
    print(f"[download] To: {target_path}")

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "mind-r3-book-collector/1.0 (educational)"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp, open(target_path, "wb") as out:
            shutil.copyfileobj(resp, out, length=1024 * 1024)
    except Exception as exc:
        raise SystemExit(f"[error] Download failed: {exc}")

    book["is_downloaded"] = True
    book["file_path"] = str(target_path)
    book["downloaded_at"] = datetime.now(timezone.utc).isoformat()
    book["source_url"] = url
    save_catalog(catalog)
    print(f"[ok] Saved to {target_path}")
    return str(target_path)


def generate_report() -> str:
    catalog = load_catalog()
    meta = catalog["catalog_metadata"]
    books = catalog["books"]

    total = len(books)
    downloaded = sum(1 for b in books if b["is_downloaded"])
    pending = total - downloaded
    public_domain = sum(1 for b in books if b["source_type"] == "public_domain")
    commercial = sum(1 for b in books if b["source_type"] == "commercial")

    # category counts
    from collections import Counter
    cat_counts = Counter(b["category"] for b in books)

    lines: List[str] = []
    lines.append("# Data Collection Report — mind-r3 Book Collection")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"**Project:** {meta['title']}")
    lines.append(f"**Target Directory:** `{meta['target_directory']}`")
    lines.append(f"**Catalog File:** `data/books_catalog.json`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total books catalogued: **{total}**")
    lines.append(f"- Books downloaded: **{downloaded}**")
    lines.append(f"- Books pending download: **{pending}**")
    lines.append(f"- Public-domain titles: **{public_domain}**")
    lines.append(f"- Commercial titles: **{commercial}**")
    lines.append("")
    lines.append("## Collection by Category")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|----------|-------|")
    for cat, count in cat_counts.most_common():
        lines.append(f"| {cat} | {count} |")
    lines.append("")
    lines.append("## Legitimate Sources Recommended")
    lines.append("")
    lines.append("- [Project Gutenberg](https://www.gutenberg.org/) — free public-domain ebooks")
    lines.append("- [Open Library](https://openlibrary.org/) — borrow books digitally")
    lines.append("- [Internet Archive](https://archive.org/) — free books and texts")
    lines.append("- Official publisher / author websites")
    lines.append("- Your local or institutional library (physical or digital)")
    lines.append("")
    lines.append("## Ethics & Legal Compliance")
    lines.append("")
    lines.append("- Only public-domain or legitimately free books were/should be downloaded.")
    lines.append("- Commercial titles (e.g., Robert Greene, Cialdini, Kahneman) must be purchased")
    lines.append("  or borrowed from a library.")
    lines.append("- Do not scrape copyrighted material from unauthorized sources.")
    lines.append("- This tool only downloads from URLs you explicitly provide from recognized")
    lines.append("  legitimate domains.")
    lines.append("")
    lines.append("## Book Catalogue")
    lines.append("")
    lines.append("| ID | Title | Author | Category | Source Type | Status | File Path |")
    lines.append("|----|-------|--------|----------|-------------|--------|-----------|")
    for b in books:
        status = "Downloaded" if b["is_downloaded"] else "Pending"
        fpath = b["file_path"] or "—"
        lines.append(
            f"| {b['id']} | {b['title']} | {b['author']} | {b['category']} | "
            f"{b['source_type']} | {status} | {fpath} |"
        )
    lines.append("")
    lines.append("## Next Steps")
    lines.append("")
    lines.append("1. For public-domain books, run: `python3 src/book_collector.py download --id <id> --url <legitimate-url>`")
    lines.append("2. For commercial books, purchase or borrow them, then place the file in the")
    lines.append("   appropriate category folder under `data/books/` and mark it downloaded in the catalog.")
    lines.append("3. Re-run `python3 src/book_collector.py report` to refresh this report.")

    report = "\n".join(lines) + "\n"
    REPORT_PATH.write_text(report, encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="mind-r3 Book Collector (ethical/legitimate use only)")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="Initialize category folders under data/books/")
    sub.add_parser("list", help="List all books in the catalogue")
    sub.add_parser("report", help="Generate the data collection report")

    p_dl = sub.add_parser("download", help="Download a book from a legitimate URL you provide")
    p_dl.add_argument("--id", type=int, required=True, help="Book id from the catalogue")
    p_dl.add_argument("--url", type=str, required=True, help="Legitimate source URL")

    args = parser.parse_args()

    if not CATALOG_PATH.exists():
        print(f"[error] Catalogue not found at {CATALOG_PATH}. Run 'init' first after placing books_catalog.json in data/.")
        sys.exit(1)

    if args.command == "init":
        init_folders()
    elif args.command == "list":
        list_books()
    elif args.command == "report":
        rep = generate_report()
        print(rep)
        print(f"\n[ok] Report written to {REPORT_PATH}")
    elif args.command == "download":
        download_book(args.id, args.url)
        generate_report()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
