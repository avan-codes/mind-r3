import React from 'react'
import { Send, Paperclip } from 'lucide-react'

interface ChatInputProps {
  onSubmit: (question: string) => void
  disabled?: boolean
}

export default function ChatInput({ onSubmit, disabled }: ChatInputProps) {
  const [value, setValue] = React.useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const q = value.trim()
    if (!q || disabled) return
    onSubmit(q)
    setValue('')
  }

  return (
    <form onSubmit={handleSubmit} className="border-t border-border-default bg-bg-secondary px-6 py-4">
      <div className="max-w-6xl mx-auto flex gap-4">
        <div className="relative flex-1">
          <Paperclip size={18} className="absolute left-5 top-4 text-ink-muted" />
          <input
            type="text"
            placeholder="Ask a question about your documents…"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            disabled={disabled}
            className="input-field pl-12 bg-transparent border-b-0 border-t-0 border-l-0 border-r-0 shadow-none rounded-none py-4 pr-5 text-base"
          />
        </div>
        <button
          type="submit"
          className="btn-blue"
          disabled={!value.trim() || disabled}
        >
          <Send size={18} />
          <span className="hidden sm:inline">Ask</span>
        </button>
      </div>
    </form>
  )
}
