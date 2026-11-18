import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Send, AlertCircle, Wifi, RefreshCw } from 'lucide-react'
import Message from './Message'
import EmptyState from './EmptyState'
import { useChat } from '../context/ChatContext'
import { askQuestion, healthCheck } from '../services/api'

export default function ChatInterface() {
  const { state, addMessage, replaceLast } = useChat()
  const [input, setInput] = useState('')
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [state.messages])

  useEffect(() => {
    let mounted = true
    let timer: ReturnType<typeof setInterval>
    const check = async () => {
      if (!mounted) return
      try {
        await healthCheck()
        if (!mounted) return
        setBackendOnline(true)
      } catch {
        if (!mounted) return
        setBackendOnline(false)
      }
    }
    check()
    timer = setInterval(check, 30000)
    return () => {
      mounted = false
      clearInterval(timer)
    }
  }, [])

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault()
      const q = input.trim()
      if (!q || state.isLoading || !backendOnline) return

      setInput('')
      const userMsg = {
        id: crypto.randomUUID?.() || `${Date.now()}`,
        role: 'user' as const,
        content: q,
        createdAt: Date.now(),
      }
      addMessage(userMsg)

      const placeholder = {
        id: crypto.randomUUID?.() || `${Date.now()}-b`,
        role: 'assistant' as const,
        content: '',
        createdAt: Date.now(),
        sources: [],
        retrieval_scores: [],
        retrieval_confidence: 0,
      }
      addMessage(placeholder)

      try {
        const res = await askQuestion({
          question: q,
          top_k: 5,
          min_score: 0.0,
          return_context: false,
        })
        replaceLast({
          ...placeholder,
          content: res.answer,
          sources: res.sources,
          retrieval_scores: res.retrieval_scores,
          retrieval_confidence: res.retrieval_confidence,
        })
      } catch (err: any) {
        replaceLast({
          ...placeholder,
          content:
            "I couldn't reach the RAG backend. Make sure the FastAPI server is running (http://127.0.0.1:8000).",
          sources: [],
          retrieval_scores: [],
          retrieval_confidence: 0,
        })
        console.error(err)
      }
    },
    [input, state.isLoading, backendOnline, addMessage, replaceLast]
  )

  if (backendOnline === null) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-ink-muted" role="status">
        Connecting to the backend…
      </div>
    )
  }

  if (!backendOnline) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-6 text-center">
        <div className="w-12 h-12 rounded-full bg-error/10 flex items-center justify-center mb-4 border border-error/20">
          <Wifi size={24} className="text-error-400" />
        </div>
        <h3 className="text-2xl font-bold text-error mb-2">Backend unreachable</h3>
        <p className="text-ink-muted mb-6 max-w-xs">
          From the project root, run the API server:
          <br />
          <code className="text-blue-600 dark:text-blue-400">uvicorn src.api:app --reload</code>
        </p>
        <button
          onClick={() => {
            setBackendOnline(null)
            void healthCheck()
              .then(() => setBackendOnline(true))
              .catch(() => setBackendOnline(false))
          }}
          className="btn-blue"
        >
          <RefreshCw size={16} className="mr-2" />
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-8 md:p-12 scroll-smooth">
        {state.messages.length === 0 ? (
          <EmptyState />
        ) : (
          <>
            {state.messages.map((m) => (
              <Message key={m.id} message={m} />
            ))}
            <div ref={messagesEndRef} className="h-8" />
          </>
        )}
      </div>
      <div className="border-t border-border-default bg-bg-secondary/80 backdrop-blur-md p-6">
        <form onSubmit={handleSubmit} className="flex gap-4 max-w-6xl mx-auto">
          <input
            className="input-field bg-transparent border-b-0 border-t-0 border-l-0 border-r-0 shadow-none rounded-none py-4 pr-5 text-base"
            placeholder="Ask a question about your documents…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={state.isLoading || !backendOnline}
          />
          <button
            type="submit"
            className="btn-blue"
            disabled={!input.trim() || state.isLoading || !backendOnline}
          >
            <Send size={18} />
            <span className="hidden sm:inline">Ask</span>
          </button>
        </form>
        {state.error && (
          <div className="mx-auto max-w-6xl mt-4 px-6 py-3 rounded-md bg-error/10 border border-error/20 text-sm text-error-400">
            {state.error}
          </div>
        )}
      </div>
    </div>
  )
}
