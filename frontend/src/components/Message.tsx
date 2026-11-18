import React from 'react'
import { formatDistanceToNow } from 'date-fns'
import { Copy, CheckCircle2 } from 'lucide-react'
import SourceStrip from './SourceStrip'
import type { Source } from '../context/ChatContext'

interface MessageProps {
  message: {
    id: string
    role: 'user' | 'assistant'
    content: string
    createdAt: number
    sources?: Source[]
    retrieval_scores?: number[]
    retrieval_confidence?: number
    context?: string | null
  }
}

export default function Message({ message }: MessageProps) {
  const isUser = message.role === 'user'
  const [copied, setCopied] = React.useState(false)

  return (
    <div
      className={`flex w-full mb-12 animate-slide-up ${
        isUser ? 'flex-row-reverse' : ''
      }`}
    >
      {isUser ? (
        <div className="flex flex-col items-end gap-2">
          <div className="max-w-[75%] bg-blue-600 text-white rounded-md px-5 py-4 whitespace-pre-wrap text-sm leading-relaxed shadow-blue-glow">
            {message.content}
          </div>
          <div className="text-[10px] text-ink-muted text-right">
            {formatDistanceToNow(new Date(message.createdAt), { addSuffix: true })}
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-start gap-2">
          <div className="max-w-[85%] bg-blue-50 text-ink-primary border border-blue-100 rounded-md px-5 py-4 whitespace-pre-wrap text-sm leading-relaxed dark:bg-blue-900/30 dark:border-blue-800 dark:text-ink-inverted">
            {renderContent(message.content)}
          </div>

          {message.sources && message.sources.length > 0 && (
            <div className="mt-6 pt-4 border-t border-border-default">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-600" />
                <span className="text-[10px] font-bold text-ink-secondary uppercase tracking-wider">
                  Sources
                </span>
                <span className="ml-auto text-xs font-medium text-blue-700 bg-blue-100 px-2 py-1 rounded border border-blue-200 dark:bg-blue-800 dark:text-blue-400 dark:border-blue-700">
                  Confidence: {(message.retrieval_confidence ?? 0).toFixed(2)}
                </span>
              </div>
              <SourceStrip sources={message.sources} confidence={message.retrieval_confidence ?? 0} />
            </div>
          )}

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                navigator.clipboard.writeText(message.content)
                setCopied(true)
                setTimeout(() => setCopied(false), 2000)
              }}
              className="p-2 text-ink-muted hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-md transition-all"
              title="Copy"
            >
              {copied ? (
                <CheckCircle2 size={16} className="text-blue-500 dark:text-blue-400" />
              ) : (
                <Copy size={16} />
              )}
            </button>
          </div>
          <div className="text-[10px] text-ink-muted">
            {formatDistanceToNow(new Date(message.createdAt), { addSuffix: true })}
          </div>
        </div>
      )}
    </div>
  )
}

function renderContent(content: string): React.ReactNode {
  const blocks = content.split('\n\n').filter(Boolean)
  return blocks.map((block, i) => {
    if (block.startsWith('# ')) {
      return (
        <h2 key={i} className="text-lg font-bold text-ink-primary mb-3 mt-4 first:mt-0">
          {block.slice(2)}
        </h2>
      )
    }
    if (block.startsWith('## ')) {
      return (
        <h3 key={i} className="text-base font-bold text-ink-primary mb-3 mt-4 first:mt-0">
          {block.slice(3)}
        </h3>
      )
    }
    if (block.startsWith('- ')) {
      return (
        <ul key={i} className="list-disc list-inside text-sm text-ink-primary space-y-1.5 mb-4 first:mt-0">
          {block.split('\n').map((line, j) => (
            <li key={j}>{line.slice(2)}</li>
          ))}
        </ul>
      )
    }
    return (
      <p key={i} className="text-sm text-ink-primary leading-relaxed mb-4 first:mt-0">
        {block}
      </p>
    )
  })
}
