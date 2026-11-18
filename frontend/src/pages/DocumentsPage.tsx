import React from 'react'
import { FileText, Search } from 'lucide-react'

const DOCUMENTS = [
  { name: 'Thinking, Fast and Slow', type: 'pdf', pages: 499, size: '3.2 MB', source: 'Daniel Kahneman' },
  { name: 'Emotional Intelligence', type: 'pdf', pages: 352, size: '2.1 MB', source: 'Daniel Goleman' },
  { name: 'Atomic Habits', type: 'pdf', pages: 320, size: '1.8 MB', source: 'James Clear' },
  { name: "Man's Search for Meaning", type: 'pdf', pages: 184, size: '1.2 MB', source: 'Viktor Frankl' },
  { name: 'The Power of Habit', type: 'pdf', pages: 400, size: '2.4 MB', source: 'Charles Duhigg' },
  { name: 'Maps of Meaning', type: 'pdf', pages: 690, size: '4.1 MB', source: 'Jordan Peterson' },
  { name: 'Blink', type: 'pdf', pages: 288, size: '1.6 MB', source: 'Malcolm Gladwell' },
  { name: 'Outliers', type: 'pdf', pages: 320, size: '1.9 MB', source: 'Malcolm Gladwell' },
  { name: 'Read People Like a Book', type: 'pdf', pages: 220, size: '1.3 MB', source: 'Patrick King' },
  { name: 'Behave', type: 'pdf', pages: 800, size: '5.4 MB', source: 'Robert Sapolsky' },
]

export default function DocumentsPage() {
  const [query, setQuery] = React.useState('')

  const filtered = DOCUMENTS.filter((d) =>
    d.name.toLowerCase().includes(query.toLowerCase())
  )

  return (
    <div className="flex flex-col h-full min-w-0">
      <section className="px-6 md:px-12 pb-12 border-b border-border-default">
        <div className="max-w-4xl mx-auto">
          <div className="relative mb-10">
            <span className="kicker">library</span>
            <h1 className="text-4xl font-xbold text-ink-primary mb-3 tracking-tight">
              Documents
            </h1>
            <p className="text-ink-muted text-lg">
              Indexed knowledge base. {DOCUMENTS.length} documents available for retrieval.
            </p>
          </div>
          <div className="relative">
            <Search size={18} className="absolute left-5 top-1/2 -translate-y-1/2 text-ink-muted" />
            <input
              type="text"
              placeholder="Search documents…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="input-field pl-11"
            />
          </div>
        </div>
      </section>

      <div className="flex-1 overflow-y-auto px-6 md:px-12">
        <div className="max-w-4xl mx-auto">
          <div className="space-y-3">
            {filtered.map((doc) => (
              <div
                key={doc.name}
                className="flex items-center justify-between gap-4 px-5 py-4 rounded-md bg-bg-white border border-border-default hover:bg-blue-50 dark:bg-bg-subtle dark:border-border-default dark:hover:bg-blue-900/20 transition-colors"
              >
                <div className="flex items-center gap-4 flex-1 min-w-0">
                  <div className="w-10 h-10 rounded-md bg-blue-50 flex items-center justify-center border border-blue-100 dark:bg-blue-900/20 dark:border-blue-800 shrink-0">
                    <FileText size={18} className="text-blue-600 dark:text-blue-400" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-ink-primary truncate">
                      {doc.name}
                    </p>
                    <p className="text-[10px] text-ink-muted flex items-center gap-1.5">
                      <span className="w-px h-3 bg-border-default rounded-full" />
                      <span className="font-medium">{doc.source}</span>
                      <span className="w-px h-3 bg-border-default rounded-full" />
                      <span className="font-medium">{doc.pages} pages</span>
                      <span className="w-px h-3 bg-border-default rounded-full" />
                      <span className="font-medium">{doc.size}</span>
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <span className="badge badge-blue text-[10px]">PDF</span>
                  <button className="p-2 text-ink-muted hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-md transition-colors">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="2" y="6" width="20" height="14" rx="2" ry="2" />
                      <path d="M16 2V10" />
                      <path d="M8 2V10" />
                      <path d="M12 2V10" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
            {filtered.length === 0 && (
              <div className="py-24 text-center">
                <div className="w-24 h-24 rounded-full bg-bg-subtle flex items-center justify-center mx-auto mb-6">
                  <FileText size={40} className="text-ink-muted/30" />
                </div>
                <h2 className="text-2xl font-bold text-ink-secondary mb-3">No documents found</h2>
                <p className="text-ink-muted text-lg">Try a different search.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
