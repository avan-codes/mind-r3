# mind-r3 RAG — Missing Items / Gap Analysis

This document lists features, infrastructure, and hardening items that are **not
yet implemented** in the mind-r3 RAG project. Use it as a backlog for the next
iteration. Items are grouped by category.

## 1. Document Ingestion & Corpus

| # | Missing item | Why it matters | Suggested approach |
|---|---|---|---|
| 1.1 | **No document upload via API** | Ingestion only works by dropping files into `backend/data/documents/` and running `ingest`. Users can't upload documents through the API or frontend. | Add `POST /upload` endpoint (FastAPI `UploadFile`) that saves to `data/documents/` and optionally triggers re-indexing. |
| 1.2 | **No incremental / delta indexing** | Every `ingest` rebuilds the entire FAISS index from scratch. Large corpora (current index ~163 MB) make re-ingestion slow. | Track file hashes/mtime; only embed new/changed files and `add()` to the existing index instead of `build()`. |
| 1.3 | **No document deletion / re-ingestion of single file** | You can't remove one document from the index without rebuilding everything. | Maintain an id→document map and support `delete(ids)` + FAISS `id_map` (FAISS IDMap wrapper) or rebuild minus deleted docs. |
| 1.4 | **No document type beyond text** | Only text-extractable formats are supported (PDF/TXT/CSV/HTML/XLSX/JSON). Images, scanned PDFs, audio, video not supported. | Add OCR (Tesseract/pytesseract) for scanned PDFs; optional image/audio transcription pipelines. |

## 2. Retrieval & Search

| # | Missing item | Why it matters | Suggested approach |
|---|---|---|---|
| 2.1 | **Vector-only search (no hybrid)** | Pure semantic search misses exact keyword matches (names, dates, acronyms). | Add BM25 / keyword search (e.g. `rank_bm25` or Elasticsearch) and fuse scores (reciprocal rank fusion). |
| 2.2 | **No re-ranking** | Top-K from FAISS is retrieved by embedding similarity only; no cross-encoder re-ranking for precision. | Add a cross-encoder (e.g. `cross-encoder/ms-marco-MiniLM-L-6-v2`) to re-score the top-K before passing to the LLM. |
| 2.3 | **Fixed Top-K / static threshold** | `top_k` and `min_score` are static per request; no adaptive retrieval. | Implement adaptive retrieval (dynamic top-k based on confidence, or self-corrective retrieval / RAG-Fusion). |
| 2.4 | **No query expansion / rewriting** | Raw user queries may be ambiguous; no expansion to improve recall. | Add query expansion (synonyms, hypothetical document embedding / HyDE) before retrieval. |
| 2.5 | **No multi-hop / multi-query retrieval** | Complex questions requiring evidence across multiple documents are handled in a single retrieval pass. | Multi-query retrieval (generate several sub-queries) or iterative retrieval. |

## 3. Generation & Prompting

| # | Missing item | Why it matters | Suggested approach |
|---|---|---|---|
| 3.1 | **Prompt template is hardcoded** | `DEFAULT_PROMPT_TEMPLATE` lives in `search.py`; changing it requires code edits. | Move templates to config/YAML files; support template selection per request. |
| 3.2 | **No streaming responses** | NVIDIA API call is blocking; users wait for the full answer before seeing anything. | Enable `stream: true` in the NVIDIA payload and stream tokens via FastAPI `StreamingResponse` / SSE to the frontend. |
| 3.3 | **No citations rendered as clickable links** | Sources are returned as metadata; frontend shows them as plain cards. | Render `[Source: filename, Page: N]` as clickable links that jump to the document/page. |
| 3.4 | **No answer evaluation / confidence beyond heuristic** | `retrieval_confidence` is a mean-of-similarities heuristic, not a measure of answer correctness. | Add RAGAS / LLM-as-judge evaluation (faithfulness, answer relevance, context precision/recall). |

## 4. Frontend

| # | Missing item | Why it matters | Suggested approach |
|---|---|---|---|
| 4.1 | **No proxy configuration in Vite** | `api.ts` hardcodes `http://127.0.0.1:8000`; `vite.config.js` may not proxy `/api` to the backend, causing CORS issues in dev. | Configure Vite `server.proxy` to forward `/api` to `http://127.0.0.1:8000`, or set `VITE_API_BASE`. |
| 4.2 | **HistoryPage not backed by persistent storage** | Chat history lives in memory (`ChatContext`); it vanishes on refresh. | Persist conversations to `localStorage` or a backend `/conversations` endpoint. |
| 4.3 | **No document viewer** | DocumentsPage exists but there's no inline PDF/document viewer to inspect sources. | Add a PDF viewer (e.g. `react-pdf`) linked from source cards. |
| 4.4 | **No error UI / retry** | API failures show raw errors; no retry or offline state. | Add error boundaries, retry buttons, and offline/loading states. |
| 4.5 | **No settings persistence** | top-k / min-score changes aren't saved across sessions. | Save settings to `localStorage` or user profile. |

## 5. Infrastructure & Deployment

| # | Missing item | Why it matters | Suggested approach |
|---|---|---|---|
| 5.1 | **No Dockerfile / docker-compose** | Can't run the full stack (backend + frontend) with a single command. | Add `Dockerfile` (Python backend), `Dockerfile` (Node frontend), and `docker-compose.yml`. |
| 5.2 | **No CI/CD pipeline** | Tests aren't run automatically on push; no lint/type-check gates. | Add GitHub Actions: run tests, lint, build on push/PR. |
| 5.3 | **No reverse proxy / TLS** | Backend runs on plain HTTP (`0.0.0.0:8000`) with no HTTPS termination. | Deploy behind Nginx/Traefik with TLS; or use a cloud load balancer. |
| 5.4 | **No environment parity** | `.env` is secret-bearing and not committed; no staging/prod env samples beyond `.env.example`. | Add `.env.example.staging`, `.env.example.production`; document required secrets. |
| 5.5 | **No monitoring / logging** | No structured logs, metrics, or health beyond `/health`. | Add structured logging (JSON), request latency metrics, and Prometheus endpoint. |

## 6. Security & Auth

| # | Missing item | Why it matters | Suggested approach |
|---|---|---|---|
| 6.1 | **No authentication / authorization** | Anyone with network access can ingest documents and ask questions. | Add API-key auth or OAuth2 (JWT) for `/ingest` and `/ask`. |
| 6.2 | **No rate limiting** | No protection against abuse of the NVIDIA API (cost) or the endpoint. | Add rate limiting per IP/user (e.g. `slowapi` or Redis-backed). |
| 6.3 | **CORS is permissive by default** | `api.py` allows all origins unless overridden; fine for dev, risky for prod. | Restrict `CORS_ALLOW_ORIGINS` to known frontend domains in production. |
| 6.4 | **No input sanitization / prompt injection guardrails** | Retrieved documents are treated as untrusted in the prompt, but the user query isn't sanitized. | Add prompt-injection detection and input length limits. |

## 7. Testing & Quality

| # | Missing item | Why it matters | Suggested approach |
|---|---|---|---|
| 7.1 | **No API endpoint tests** | Tests cover modules (`test_loader.py`, etc.) but not FastAPI endpoints (`/health`, `/status`, `/ingest`, `/ask`). | Add FastAPI `TestClient` tests for all endpoints. |
| 7.2 | **No end-to-end tests** | No test that runs ingest → ask → asserts answer contains expected content. | Add E2E tests using a small fixture corpus and a mocked LLM. |
| 7.3 | **No test coverage reporting** | Coverage isn't measured or enforced. | Add `pytest-cov` with a coverage threshold in CI. |
| 7.4 | **No performance benchmarks** | Ingestion latency, retrieval latency, and LLM TTFT aren't measured. | Add benchmark scripts and track regressions. |

## 8. Project Hygiene

| # | Missing item | Why it matters | Suggested approach |
|---|---|---|---|
| 8.1 | **README says `python3 src/app.py ingest`** | The actual CLI entry point is `backend/cli.py`; the README command is wrong. | Fix README to `cd backend && python3 cli.py ingest` (already corrected in current README). |
| 8.2 | **`backend/.env` is secret-bearing** | Contains real NVIDIA keys; must never be committed. | Ensure `.env` is in `.gitignore` and only `.env.example` is tracked. |
| 8.3 | **No CHANGELOG / versioning** | No release history or version pinning. | Add semantic versioning and a `CHANGELOG.md`. |
| 8.4 | **Notebooks are scratch files** | `notebooks/data_loading.ipynb` and `document.ipynb` are exploratory, not part of the pipeline. | Either remove from repo or document them as experimental scratchpads. |

---

## Recommended priority order

1. **Fix Vite proxy / CORS** so frontend can actually talk to backend (blocks end-to-end use).
2. **Add API document upload** (`POST /upload`) — the core missing user-facing feature.
3. **Add FastAPI endpoint tests** — establishes a safety net before adding features.
4. **Add Docker + docker-compose** — reproducible, one-command local run.
5. **Add streaming responses** — materially improves user experience.
6. **Add hybrid search + re-ranking** — improves answer quality on the psychology corpus.

---
