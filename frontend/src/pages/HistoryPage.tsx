import React from 'react'
import { Link } from 'react-router-dom'
import { useChat } from '../context/ChatContext'
import { Clock } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export default function HistoryPage() {
  const { state, loadSession, deleteSession } = useChat()
  const sessions = Object.entries(state.sessions).reverse()

  return (
    <div className="flex flex-col h-full min-w-0">
      <section className="px-6 md:px-12 pb-12 border-b border-border-default">
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-2">
            <div>
              <span className="kicker">history</span>
              <h1 className="text-4xl font-xbold text-ink-primary mb-2 tracking-tight">
                Conversations
              </h1>
              <p className="text-ink-muted text-lg">
                Your past conversations with Mind-R3. All history is stored locally.
              </p>
            </div>
            <Link to="/" className="btn-blue self-start sm:self-center">
              New chat
            </Link>
          </div>
        </div>
      </section>

      <div className="flex-1 overflow-y-auto px-6 md:px-12">
        <div className="max-w-4xl mx-auto">
          {sessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 text-center">
              <div className="w-20 h-20 rounded-full bg-bg-subtle flex items-center justify-center mb-6">
                <Clock size={32} className="text-ink-muted" />
              </div>
              <h2 className="text-2xl font-bold text-ink-secondary mb-3">No history yet</h2>
              <p className="text-ink-muted text-lg max-w-md mb-8">
                Start a conversation from the{' '}
                <Link to="/" className="text-blue-600 font-bold dark:text-blue-400 underline decoration-blue-200/50 dark:decoration-blue-800/50">
                  Chat
                </Link>{' '}
                page.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {sessions.map(([id, msgs]) => {
                const lastMsg = msgs[msgs.length - 1]
                const firstMsg = msgs[0]
                return (
                  <div
                    key={id}
                    onClick={() => loadSession(id)}
                    className="flex items-center justify-between gap-4 px-5 py-4 rounded-md bg-bg-white border border-border-default hover:bg-blue-50 dark:bg-bg-subtle dark:border-border-default dark:hover:bg-blue-900/20 transition-colors cursor-pointer group"
                  >
                    <Link
                      to={`/?session=${id}`}
                      onClick={(e) => {
                        e.stopPropagation()
                        loadSession(id)
                      }}
                      className="flex-1 flex items-center gap-4"
                    >
                      <div className="w-10 h-10 rounded-md bg-blue-50 flex items-center justify-center border border-blue-100 dark:bg-blue-900/20 dark:border-blue-800 shrink-0">
                        <Clock size={16} className="text-blue-600 dark:text-blue-400" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-ink-primary truncate">
                          {firstMsg?.content.slice(0, 60) || 'Empty chat'}
                        </p>
                        <p className="text-[10px] text-ink-muted truncate">
                          {msgs.length} message{msgs.length !== 1 ? 's' : ''} •
                          {formatDistanceToNow(new Date(lastMsg?.createdAt || 0), { addSuffix: true })}
                        </p>
                      </div>
                    </Link>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteSession(id)
                      }}
                      className="p-2 text-ink-muted hover:text-error hover:bg-error/5 dark:hover:text-error-400 dark:hover:bg-error/10 rounded-md transition-colors"
                      title="Delete conversation"
                      aria-label="Delete conversation"
                    >
                      <span className="sr-only">Delete</span>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      </svg>
                    </button>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
