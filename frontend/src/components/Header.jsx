import React from 'react'
import Logo from './Logo'
import { Menu, Send, Settings, Trash2, Clock, Database } from 'lucide-react'
import { useChat } from '../context/ChatContext'

export default function Header() {
  const { state, newSession, deleteSession, loadSession } = useChat()
  const [menuOpen, setMenuOpen] = React.useState(false)

  return (
    <header className="sticky top-0 z-20 border-b border-border-default/60 bg-bg-secondary/80 backdrop-blur-md">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden p-2 text-ink-muted hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-md transition-all"
            aria-label="Toggle menu"
          >
            <Menu size={20} />
          </button>
          <Logo size={30} />
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={newSession}
            className="btn-ghost flex items-center gap-2"
            title="New chat"
          >
            <Send size={18} />
            <span className="hidden sm:inline text-sm font-medium">New chat</span>
          </button>
          <button
            onClick={() => {
              if (
                state.currentSessionId &&
                window.confirm('Clear this conversation?')
              ) {
                deleteSession(state.currentSessionId)
              }
            }}
            className="btn-ghost text-ink-muted hover:text-error hover:border-error/50"
            title="Delete current chat"
          >
            <Trash2 size={18} />
          </button>
          <button className="btn-ghost" title="Settings">
            <Settings size={18} />
          </button>
        </div>
      </div>

      {menuOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 mt-1 bg-bg-white border border-border-default rounded-lg shadow-lg p-3 animate-fade-in dark:bg-bg-subtle dark:border-border-default">
          <div className="px-2 py-2 text-xs font-semibold text-ink-secondary uppercase tracking-wider mb-3">
            History
          </div>
          {Object.entries(state.sessions).map(([id, msgs]) => (
            <button
              key={id}
              onClick={() => {
                loadSession(id)
                setMenuOpen(false)
              }}
              className={`w-full flex items-center justify-between gap-2 px-3 py-2 rounded-md text-sm transition-all ${
                state.currentSessionId === id
                  ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
                  : 'text-ink-secondary hover:bg-bg-subtle hover:text-blue-600 dark:hover:text-blue-400'
              }`}
            >
              <div className="flex items-center gap-2 overflow-hidden">
                <Clock size={14} className="text-ink-muted" />
                <span className="truncate">
                  {msgs.length > 0 ? msgs[0].content.slice(0, 40) : 'Empty chat'}
                </span>
              </div>
              <span className="text-[10px] text-ink-muted">{msgs.length}</span>
            </button>
          ))}
          <div className="border-t border-border-default/50 mt-3 pt-3">
            <div className="flex items-center gap-2 px-3 py-2 text-xs text-ink-muted">
              <Database size={16} />
              <span>{state.indexStatus?.vectors ?? '--'} vectors indexed</span>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}
