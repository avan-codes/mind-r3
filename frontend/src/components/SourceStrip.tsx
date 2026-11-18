import React from 'react'
import { FileText } from 'lucide-react'
import type { Source } from '../context/ChatContext'

interface SourceStripProps {
  sources: Source[]
  confidence: number
}

export default function SourceStrip({ sources, confidence }: SourceStripProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
      {sources.map((src, i) => {
        const page = src.page != null ? `p.${src.page}` : '—'
        return (
          <div
            key={i}
            className="flex flex-col gap-1.5 px-4 py-3 rounded-md bg-bg-white border border-border-default hover:bg-blue-50 dark:bg-bg-subtle dark:border-border-default dark:hover:bg-blue-900/20 transition-colors cursor-default"
          >
            <div className="flex items-center gap-2">
              <FileText size={13} className="text-blue-500 shrink-0" />
              <span className="text-[10px] font-bold text-ink-secondary uppercase tracking-wider">
                Source {i + 1}
              </span>
            </div>
            <p className="text-xs font-medium text-ink-primary truncate leading-tight">
              {src.filename || 'unknown'}
            </p>
            <p className="text-[10px] text-ink-muted flex items-center gap-1">
              <span className="w-px h-3 bg-border-default rounded-full" />
              <span className="font-medium">{page}</span>
            </p>
          </div>
        )
      })}
    </div>
  )
}
