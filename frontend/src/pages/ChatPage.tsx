import React from 'react'
import { Link } from 'react-router-dom'
import { Send } from 'lucide-react'
import { useChat } from '../context/ChatContext'
import { askQuestion, healthCheck } from '../services/api'
import Message from '../components/Message'
import EmptyState from '../components/EmptyState'

export default function ChatPage() {
  const { state, addMessage, replaceLast } = useChat()
  const [backendOnline, setBackendOnline] = React.useState<boolean | null>(null)
  const [input, setInput] = React.useState('')

  React.useEffect(() => {
    let mounted = true
    let timer: NodeJS.Timeout
    const check = async () => {
      if (!mounted) return
      try {
        await healthCheck()
        setBackendOnline(true)
      } catch {
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

  const handleSubmit = React.useCallback(
    async (question: string) => {
      if (!question.trim() || state.isLoading || !backendOnline) return

      const userMsg = {
        id: crypto.randomUUID?.() || `${Date.now()}`,
        role: 'user' as const,
        content: question,
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
          question,
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
          content: "I couldn't reach the RAG backend. Please make sure the FastAPI server is running.",
          sources: [],
          retrieval_scores: [],
          retrieval_confidence: 0,
        })
      }
    },
    [state.isLoading, backendOnline, addMessage, replaceLast]
  )

  return (
    <div className="flex flex-col h-full min-w-0">
      {backendOnline === false ? (
        <div className="flex flex-col items-center justify-center h-full p-8 text-center">
          <div className="w-16 h-16 rounded-full bg-error/10 flex items-center justify-center mb-6 border border-error/20">
            <span className="text-error-400 text-2xl" role="img">
              ⚠
            </span>
          </div>
          <h2 className="text-3xl font-bold text-error mb-3">Backend unreachable</h2>
          <p className="text-ink-secondary max-w-md mb-8 leading-relaxed">
            Start the FastAPI server from the project root:
          </p>
          <code className="text-blue-600 dark:text-blue-400 font-mono text-sm bg-blue-50 dark:bg-blue-900/20 px-3 py-2 rounded-md inline-block mb-8">
            uvicorn src.api:app --reload
          </code>
          <button
            onClick={() => {
              setBackendOnline(null)
              void healthCheck()
                .then(() => setBackendOnline(true))
                .catch(() => setBackendOnline(false))
            }}
            className="btn-blue"
          >
            Retry connection
          </button>
        </div>
      ) : (
        <>
          <section className="px-6 md:px-12 pb-12 border-b border-border-default">
            <div className="max-w-4xl mx-auto">
              <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-6 mb-10">
                <div>
                  <span className="kicker">mind-r3</span>
                  <h1 className="text-5xl font-xbold text-ink-primary mb-2 tracking-tight leading-[1]">
                    Document Q&A
                  </h1>
                  <p className="text-ink-muted text-lg">
                    Ask questions about your indexed knowledge base. Get grounded
                    answers with source citations.
                  </p>
                </div>
                <Link
                  to="/documents"
                  className="btn-outline self-start sm:self-center"
                >
                  Browse library
                </Link>
              </div>
            </div>
          </section>

          {state.messages.length === 0 ? (
            <div className="flex-1 overflow-y-auto p-6 md:p-12">
              <EmptyState />
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto p-6 md:p-12 scroll-smooth">
              {state.messages.map((m) => (
                <Message key={m.id} message={m} />
              ))}
              <div ref={messagesEndRef} className="h-8" />
            </div>
          )}
          <div className="border-t border-border-default bg-bg-secondary/80 backdrop-blur-md p-6">
            <form onSubmit={handleSubmit} className="flex gap-4 max-w-6xl mx-auto">
              <input
                className="input-field bg-transparent border-b-0 border-t-0 border-l-0 border-r-0 shadow-none rounded-none py-4 pr-5 text-base"
                placeholder="Ask a question about your documents…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={!backendOnline || state.isLoading}
              />
              <button
                type="submit"
                className="btn-blue"
                disabled={!input.trim() || !backendOnline || state.isLoading}
              >
                <Send size={18} />
                <span className="hidden sm:inline">Ask</span>
              </button>
            </form>
          </div>
        </>
      )}
    </div>
  )
}

const messagesEndRef = React.createRef<HTMLDivElement>()
