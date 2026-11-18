import React from 'react'
import { FileText, ChevronRight } from 'lucide-react'
import type { Source } from '../context/ChatContext'

interface SourceCardProps {
  src: Source
}

export default function SourceCard({ src }: SourceCardProps) {
  const page = src.page != null ? `p.${src.page}` : '—'
  const [expanded, setExpanded] = React.useState(false)

  return (
    <div className="glass-card overflow-hidden group">
      <div className="flex items-center justify-between gap-3 p-4 cursor-pointer hover:bg-accent-50 transition-colors dark:hover:bg-bg-subtle" onClick={() => setExpanded(!expanded)}>
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <FileText size={14} className="text-accent-400 shrink-0" />
          <div className="min-w-0 flex-1">
            <p className="text-xs font-medium text-ink-primary truncate leading-tight">
              {src.filename || 'unknown'}
            </p>
            <p className="text-[10px] text-ink-muted flex items-center gap-1">
              <span className="w-px h-3 bg-border-default rounded-full" />
              <span className="font-medium">{page}</span>
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <span className="badge badge-orange text-[10px] font-semibold">
            sim {src.similarity.toFixed(2)}
          </span>
          <ChevronRight size={12} className={`text-ink-muted transition-transform duration-200 ${expanded ? 'rotate-90' : ''}`} />
        </div>
      </div>

      {expanded && (
        <div className="border-t border-border-default bg-bg-subtle p-3">
          <p className="text-xs text-ink-secondary italic leading-relaxed">
            {src.excerpt}
          </p>
        </div>
      )}
    </div>
  )
}
