# mind-r3 RAG — Document-Based Retrieval-Augmented Generation (Psychology Knowledge Assistant)

A complete, modular, production-style Document-Based RAG (Retrieval-Augmented
Generation) system. Upload/provide documents, persist their embeddings in a local
FAISS vector database, and ask natural-language questions answered **grounded in
retrieved document context** — with source attribution, similarity scores, and
retrieval confidence.

Specialised for **psychology knowledge** (books, research, theories) with a
strict evidence-grounding prompt that prevents hallucination and instructs the
NVIDIA Nemotron LLM to say "insufficient information" when the documents don't
support an answer.

Built as a Senior AI/ML Engineer LLM Systems Architecture reference project.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [RAG Workflow](#rag-workflow)
- [Technology Stack](#technology-stack)
- [Directory Structure](#directory-structure)
- [Installation](#installation)
- [Environment Configuration](#environment-configuration)
- [Document Ingestion](#document-ingestion)
- [Asking Questions (CLI)](#asking-questions-cli)
- [Asking Questions (REST API)](#asking-questions-rest-api)
- [Frontend (React + Vite)](#frontend-react--vite)
- [Example Queries](#example-queries)
- [Testing](#testing)
- [Architectural Decisions](#architectural-decisions)
- [Troubleshooting](#troubleshooting)
- [Known Gaps / Missing Items](#known-gaps--missing-items)

---

## Overview

The system reads multiple document formats (PDF, TXT, CSV, HTML, XLSX, JSON),
parses them into a standardised LangChain `Document` structure (content +
metadata), chunks the text, embeds it with a Sentence Transformer model
(`sentence-transformers/all-MiniLM-L6-v2`, 384-dimensional vectors), stores the
vectors in a persistent FAISS CPU index, and answers user questions by:

1. Embedding the user query with the **same** model.
2. Searching the persisted FAISS index (Top-K + similarity threshold).
3. Building a context-grounding prompt from the retrieved chunks.
4. Invoking the NVIDIA LLM (Nemotron) via `requests` to generate the answer.
5. Returning the answer **plus** sources, similarity scores, retrieval
   confidence, and optional full context.

Answers are grounded in retrieved context; when the documents do not contain
enough information, the system says so explicitly instead of hallucinating.

---

## Architecture

```text
┌─────────────────┐      ┌──────────────────────────┐      ┌─────────────────┐
│   USER QUERY    │─────▶│   QUERY EMBEDDING        │─────▶│   FAISS INDEX   │
│  (natural lang) │      │   all-MiniLM-L6-v2       │      │  (384-dim, L2)  │
└─────────────────┘      └──────────────────────────┘      └────────┬────────┘
                                                                   │
                                                          ┌────────▼────────┐
                                                          │   TOP-K +       │
                                                          │   THRESHOLD     │
                                                          └────────┬────────┘
                                                                   │
                                                          ┌────────▼────────┐
                                                          │   CONTEXT       │
                                                          │   ASSEMBLY      │
                                                          └────────┬────────┘
                                                                   │
                                                          ┌────────▼────────┐
                                                          │   GROUNDING     │
                                                          │   PROMPT        │
                                                          └────────┬────────┘
                                                                   │
                                                          ┌────────▼────────┐
                                                          │   NVIDIA LLM    │
                                                          │  Nemotron-3     │
                                                          └────────┬────────┘
                                                                   │
                                                          ┌────────▼────────┐
                                                          │  ANSWER +       │
                                                          │  SOURCES +      │
                                                          │  CONFIDENCE     │
                                                          └─────────────────┘
```

**Ingestion pipeline**
```text
Documents (PDF/TXT/CSV/HTML/XLSX/JSON)
        │
        ▼
load_all_documents()   → LangChain Document (content + metadata)
        │
        ▼
chunk_documents()      → RecursiveCharacterTextSplitter (1000 / 200 overlap)
        │
        ▼
EmbeddingPipeline      → SentenceTransformer all-MiniLM-L6-v2 (384-dim)
        │
        ▼
FAISSVectorStore       → build + save → storage/faiss/
```

**Module responsibilities**

| Module | Responsibility |
|---|---|
| `config.py` | Central config, paths, NVIDIA API key read from `~/Desktop/API_KEYs` file or env |
| `data_loader.py` | Multi-format document loading, metadata preservation, per-file error handling |
| `embedding.py` | `EmbeddingPipeline` + `chunk_documents()` (RecursiveCharacterTextSplitter) |
| `vector_store.py` | `FAISSVectorStore`: build/add/save/load/search, local persistence (IndexFlatL2) |
| `retriever.py` | `RAGRetriever`: query embedding, Top-K, similarity threshold |
| `search.py` | `rag_search()`: grounding prompt, NVIDIA LLM call, structured response |
| `api.py` | FastAPI REST layer: `/health`, `/status`, `/ingest`, `/ask` |
| `cli.py` | CLI entry point: `ingest` and `ask` commands |

---

## RAG Workflow

### Document Ingestion
1. Discover supported files under `backend/data/documents/` (recursive).
2. Load each into LangChain `Document` objects (content + metadata: source, filename, page, author, timestamps).
3. Chunk into 1000-char / 200-char-overlap pieces (configurable).
4. Embed chunks with `all-MiniLM-L6-v2` (384-dim, normalized).
5. Build the FAISS `IndexFlatL2` index and persist it to `backend/storage/faiss/`.
6. Existing indexes are reused — documents are not re-embedded unless you re-run `ingest`.

### Question Answering
1. Receive user query.
2. Embed query with the **same** model (so query and document vectors live in the same space).
3. Search persisted FAISS index (Top-K, min similarity).
4. Return `answer`, `sources`, `retrieval_scores`, `retrieval_confidence`.
5. When nothing relevant is found: answer states insufficient info, `sources` is empty, `retrieval_confidence` is 0.

---

## Technology Stack

- **Python 3.14** (backend)
- **LangChain / langchain-core / langchain-community**
- **Sentence Transformers** (`all-MiniLM-L6-v2`, 384-dim)
- **FAISS CPU** (`IndexFlatL2`, L2 distance; primary vector store)
- **NVIDIA Integrate API** (Nemotron LLM) via raw `requests`
- **PyMuPDF / pypdf**, **pandas**, **openpyxl**, **beautifulsoup4**
- **FastAPI** (REST API)
- **React 18 + Vite + Tailwind CSS** (frontend)

---

## Directory Structure

```text
mind-r3/
├── backend/                    # FastAPI + RAG pipeline (Python)
│   ├── api.py                  # FastAPI app (/health, /status, /ingest, /ask)
│   ├── cli.py                  # CLI entry point (ingest | ask)
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment configuration template
│   ├── src/
│   │   ├── __init__.py
│   │   ├── config.py           # Central config, paths, NVIDIA API key
│   │   ├── data_loader.py      # Multi-format document loading
│   │   ├── embedding.py        # EmbeddingPipeline + chunk_documents()
│   │   ├── vector_store.py     # FAISSVectorStore (persist/load/search)
│   │   ├── retriever.py        # RAGRetriever (Top-K + threshold)
│   │   └── search.py           # rag_search() + NVIDIA LLM call
│   ├── data/
│   │   ├── documents/          # ingestion drop folder (user documents)
│   │   ├── psychology_books/   # ~100 psychology PDFs (staged corpus)
│   │   ├── books_catalog.json
│   │   ├── data_col.py
│   │   └── DATA_COLLECTION_REPORT.md
│   ├── storage/
│   │   └── faiss/              # persisted FAISS index + metadata
│   │       ├── index.faiss
│   │       ├── documents.json
│   │       └── id_map.json
│   ├── tests/
│   │   ├── test_loader.py
│   │   ├── test_embedding.py
│   │   ├── test_vector_store.py
│   │   ├── test_retrieval.py
│   │   └── test_search.py
│   └── tools_book_collector.py
├── frontend/                   # React + Tailwind CSS frontend
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   ├── main.html
│   ├── .env.example
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── index.css
│   │   ├── components/
│   │   │   ├── Logo.jsx
│   │   │   ├── ChatInput.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── EmptyState.jsx
│   │   │   ├── Header.jsx
│   │   │   ├── Message.tsx
│   │   │   ├── SourceCard.tsx
│   │   │   ├── SourceStrip.jsx
│   │   │   ├── ThemeToggle.jsx
│   │   │   └── layout/
│   │   │       ├── Sidebar.tsx
│   │   │       └── TopBar.jsx
│   │   ├── context/
│   │   │   └── ChatContext.tsx
│   │   ├── pages/
│   │   │   ├── ChatPage.tsx
│   │   │   ├── HistoryPage.tsx
│   │   │   ├── DocumentsPage.tsx
│   │   │   └── SettingsPage.tsx
│   │   └── services/
│   │       └── api.ts
│   └── design-system/mind-r3/MASTER.md
├── notebooks/
│   ├── data_loading.ipynb
│   └── document.ipynb
├── .gitignore
├── README.md
└── MISSING.md
```

---

## Installation

Run from the project root:

```bash
cd /home/pranjal/Desktop/Heaven/Freelancing/resumes_building/projects/mind-r3

# 1. Install backend dependencies (Kali: use --break-system-packages)
cd backend
pip install --break-system-packages -r requirements.txt

# 2. Install frontend dependencies
cd ../frontend
npm install

# 3. Configure the NVIDIA API key (see Environment Configuration below)

# 4. Start the backend (from backend/)
cd ../backend
python3 backend/api.py        # OR: cd backend && python3 api.py
# Serves FastAPI on http://0.0.0.0:8000

# 5. Start the frontend (from frontend/, in another terminal)
cd ../frontend
npm run dev                   # Vite dev server on http://localhost:5173
# or: npx serve -s dist -l 5173   (after `npm run build`)

# 6. Or use the CLI directly (from backend/)
cd backend
python3 cli.py ingest
python3 cli.py ask "What does Milgram's obedience experiment demonstrate?"
```

### Alternative: run backend via uvicorn

```bash
cd backend
python3 -m uvicorn src.api:app --host 0.0.0.0 --port 8000
```

> Note: `api.py` is run directly (`python3 api.py`) from `backend/`, and `cli.py` likewise (`python3 cli.py ...`). There is no `src/app.py` — the CLI entry point is `backend/cli.py`.

---

## Environment Configuration

Copy `backend/.env.example` to `backend/.env` and fill in values, **OR** set the
`NVIDIA_API_KEY` environment variable. The preferred location for the key is the
`API_KEYs` file (read automatically by `config.py`):

```
~/Desktop/API_KEYs
```
containing a line that starts with `nvapi-`.

**Relevant settings** (in `backend/.env.example`):

| Setting | Default | Notes |
|---|---|---|
| `NVIDIA_API_KEY` | (from API_KEYs file / env) | **Required** |
| `NVIDIA_MODEL` | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | Configurable |
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1/chat/completions` | NVIDIA Integrate API |
| `TEMPERATURE` | `0.0` | LLM temperature |
| `MAX_TOKENS` | `65536` | Max generation tokens |
| `REASONING_BUDGET` | `16384` | Nemotron reasoning budget |
| `TOP_P` | `0.95` | Nucleus sampling |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | 384-dim |
| `EMBEDDING_DIMENSION` | `384` | Vector dimension |
| `CHUNK_SIZE` | `1000` | characters |
| `CHUNK_OVERLAP` | `200` | characters |
| `TOP_K` | `5` | chunks retrieved per query |
| `MIN_SCORE` | `0.0` | min similarity [0,1] |
| `CORS_ALLOW_ORIGINS` | `http://localhost:5174/,...` | FastAPI CORS origins |

Never hardcode API keys in source code.

---

## Document Ingestion

Place your documents in `backend/data/documents/` (PDF, TXT, CSV, HTML, XLSX,
JSON supported), then:

```bash
cd backend
python3 cli.py ingest
```

This discovers all supported files, loads them with metadata, chunks them,
embeds them, builds the FAISS index, and persists it to
`backend/storage/faiss/`. Existing indexes are reused — documents are not
re-embedded unless you rebuild.

A staged psychology corpus (~100 PDFs) already exists in
`backend/data/psychology_books/`.

---

## Asking Questions (CLI)

```bash
cd backend
python3 cli.py ask "Your question here"
```

Options:

```bash
python3 cli.py ask "Explain obedience to authority" --top-k 8 --min-score 0.25
python3 cli.py ask "..." --context    # also print full retrieved context
```

Sample output:

```
=== ANSWER ===
Milgram's obedience experiment demonstrates that ordinary people are
willing to administer what they believe are painful electric shocks to
another person when instructed by an authority figure...
[Source: Obedience to Authority PDF, Page: 12]

Retrieval confidence (heuristic): 0.73
Retrieval scores: [0.82, 0.76, 0.71, 0.68, 0.61]
Sources (5):
  - Obedience to Authority PDF (page 12) | similarity=0.82
    excerpt: ...
```

---

## Asking Questions (REST API)

Start the backend (`python3 api.py`), then call:

### `GET /health`
```bash
curl http://127.0.0.1:8000/health
# {"status": "ok", "service": "mind-r3-rag-api"}
```

### `GET /status`
```bash
curl http://127.0.0.1:8000/status
# {"index_exists": true, "vectors": 12450, "dimension": 384, "storage_folder": "..."}
```

### `POST /ingest`
```bash
curl -X POST http://127.0.0.1:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{}'
```

### `POST /ask`
```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What does Milgram\'s obedience experiment demonstrate?",
    "top_k": 5,
    "min_score": 0.0,
    "return_context": false
  }'
```

Response shape:
```json
{
  "answer": "string",
  "sources": [
    {"filename": "...", "page": 12, "similarity": 0.82, "distance": 0.22, "excerpt": "...", "doc_id": "..."}
  ],
  "retrieval_scores": [0.82, 0.76, ...],
  "retrieval_confidence": 0.73,
  "context": "..."   // only when return_context=true
}
```

---

## Frontend (React + Vite)

A single-page chat interface that talks to the FastAPI backend.

```bash
cd frontend
npm install          # install dependencies
npm run dev          # start Vite dev server (http://localhost:5173)
npm run build        # production build to dist/
npm run preview      # preview production build
```

Key features:
- Chat interface with streaming-style message history (via `ChatContext`)
- Source cards showing filename, page, and similarity per retrieved chunk
- Settings page for top-k / min-score tuning
- Documents page listing ingested corpus
- Tailwind CSS theming with light/dark toggle

The API client lives in `frontend/src/services/api.ts` (`healthCheck`,
`getStatus`, `ingestDocuments`, `askQuestion`) and calls `http://127.0.0.1:8000`
by default (set `VITE_API_BASE` for other origins).

> The frontend `AskResponse`/`SourceOut` TypeScript interfaces mirror the
> FastAPI Pydantic models in `backend/api.py`, so both sides stay in sync.

---

## Example Queries (against the staged psychology corpus)

- "What does Milgram's obedience experiment demonstrate?"
- "Summarize Daniel Kahneman's Thinking Fast and Slow."
- "What is emotional intelligence according to Goleman?"
- "Describe the bystander effect."
- "What are the 48 laws of power?"
- "What does The Body Keeps the Score say about trauma?"

---

## Testing

Every major module is tested independently (mocked LLM calls — no paid API
usage required):

```bash
cd backend
PYTHONPATH=. python3 -m unittest discover -s tests -v
```

Covered: PDF/TXT loading, metadata extraction, chunk generation, embedding
dimensions, vector index creation/persistence/loading, query embedding,
similarity search, threshold filtering, answer generation, source attribution,
and empty-context handling.

---

## Architectural Decisions

- **Same model for queries and documents** — query and document vectors must
  live in the same embedding space to be comparable.
- **FAISS `IndexFlatL2` (L2 distance)** — smaller distance = more similar.
  Similarity is derived as `1 / (1 + distance)`, which is a heuristic in
  [0,1] and is **not** a calibrated probability of factual correctness.
- **Retrieval confidence heuristic** — mean of retrieved similarities, clamped
  to [0,1]; 0 when no context is found. Documented explicitly so it is never
  mistaken for a guarantee.
- **No rebuild when an index exists** — `ask` loads the persisted index;
  re-ingestion only happens on explicit `ingest`.
- **NVIDIA LLM via raw `requests`** — matches the specified
  `integrate.api.nvidia.com` invocation exactly; the key is read from
  `~/Desktop/API_KEYs` or `NVIDIA_API_KEY`.
- **One Document per PDF page** — preserves page-level source attribution for
  citations in answers.
- **Per-file error handling** — a corrupted or unsupported file never aborts
  the whole ingestion run.
- **Psychology-specific grounding prompt** — mandatory source citations
  (`[Source: filename, Page: N]`), no hallucination, explicit insufficiency
  handling, and no clinical diagnosis/advice.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `NVIDIA_API_KEY not found` | Add an `nvapi-` key to `~/Desktop/API_KEYs` or `export NVIDIA_API_KEY=...` |
| `No persisted FAISS index found` | Run `python3 cli.py ingest` first |
| `ImportError: ...text_splitter` | `embedding.py` falls back to a built-in splitter if `langchain-text-splitter` is missing |
| Embedding model download fails | Ensure network access; set `HF_TOKEN` if rate-limited |
| Empty answers / low confidence | Lower `--min-score`, raise `--top-k`, or confirm documents were ingested |
| Module import errors | Run from `backend/` with `PYTHONPATH=.` |
| Frontend can't reach backend | Confirm FastAPI is on `127.0.0.1:8000`; check `VITE_API_BASE` / CORS |
| `npx serve` not found | Run `npm install` in `frontend/` first, or use `npm run dev` |

---

## Known Gaps / Missing Items

See [`MISSING.md`](MISSING.md) for a detailed list of features, infra, and
hardening items not yet implemented in this project.

---
