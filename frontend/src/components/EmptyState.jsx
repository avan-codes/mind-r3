import React from 'react'
import { Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full p-12 text-center max-w-2xl mx-auto">
      <div className="w-24 h-24 rounded-full bg-blue-50 flex items-center justify-center mb-8 border border-blue-200 dark:bg-blue-900/30 dark:border-blue-800">
        <Sparkles size={32} className="text-blue-600 dark:text-blue-400" />
      </div>
      <h2 className="text-5xl font-xbold text-ink-primary mb-4 tracking-tight">Start a conversation.</h2>
      <p className="text-ink-secondary text-lg max-w-xl mb-10 leading-relaxed">
        Ask anything about your indexed knowledge base. Get grounded answers
        with source citations.
      </p>
      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <Link to="/documents" className="btn-blue">
          Browse documents
        </Link>
        <Link to="/settings" className="btn-outline">
          Settings
        </Link>
      </div>
    </div>
  )
}
