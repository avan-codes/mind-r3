// Use /api in development so Vite can proxy requests to FastAPI. Set
// VITE_API_BASE to an absolute backend URL for deployments without that proxy.
// const API_BASE = (import.meta.env.VITE_API_BASE || '/api').replace(/\/+$/, '')

const API_BASE = "http://127.0.0.1:8000"

function apiUrl(path: string) {
  return `${API_BASE}/${path.replace(/^\/+/, '')}`
}

export async function healthCheck() {
  const res = await fetch(apiUrl('health'))
  if (!res.ok) throw new Error('Health check failed')
  return res.json()
}

export async function getStatus() {
  const res = await fetch(apiUrl('status'))
  if (!res.ok) throw new Error('Status check failed')
  return res.json()
}

export interface IngestResponse {
  status: string
  documents_loaded: number
  chunks_created: number
  embedding_dimension: number
  vectors_stored: number
  index_path: string
}

export async function ingestDocuments(): Promise<IngestResponse> {
  const res = await fetch(apiUrl('ingest'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `Ingest failed (${res.status})`)
  }
  return res.json()
}

export interface AskRequest {
  question: string
  top_k?: number
  min_score?: number
  return_context?: boolean
}

export interface SourceOut {
  filename?: string | null
  page?: number | null
  similarity: number
  distance: number
  excerpt: string
  doc_id?: string | null
}

export interface AskResponse {
  answer: string
  sources: SourceOut[]
  retrieval_scores: number[]
  retrieval_confidence: number
  context?: string | null
}

export async function askQuestion(req: AskRequest): Promise<AskResponse> {
  const res = await fetch(apiUrl('ask'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `Ask failed (${res.status})`)
  }
  return res.json()
}
