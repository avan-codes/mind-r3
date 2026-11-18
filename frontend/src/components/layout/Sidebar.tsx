import React from 'react'
import { NavLink } from 'react-router-dom'
import Logo from '../Logo'
import { Send, Settings, Clock, Database, FileText } from 'lucide-react'

const ICONS: Record<string, React.ElementType> = {
  chat: Send,
  history: Clock,
  documents: FileText,
  settings: Settings,
}

const NAV_GROUPS = [
  {
    items: [
      { path: '/', label: 'Chat', icon: 'chat', key: 'chat' },
      { path: '/history', label: 'History', icon: 'history', key: 'history' },
      { path: '/documents', label: 'Documents', icon: 'documents', key: 'documents' },
      { path: '/settings', label: 'Settings', icon: 'settings', key: 'settings' },
    ],
  },
]

export default function Sidebar() {
  return (
    <aside className="hidden w-72 shrink-0 border-r border-border-default bg-bg-white flex-col md:flex z-20">
      <div className="flex h-full min-h-0 flex-col">
        <div className="flex items-center gap-2 px-6 py-6 border-b border-border-default">
          <Logo size={28} />
        </div>

        <nav className="flex-1 overflow-y-auto px-4">
          <div className="space-y-1">
            {NAV_GROUPS[0].items.map((item) => {
              const Icon = ICONS[item.icon]
              return (
                <NavLink
                  key={item.key}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-3 rounded-md text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
                        : 'text-ink-secondary hover:bg-bg-subtle hover:text-blue-600 dark:hover:text-blue-400'
                    }`
                  }
                >
                  <Icon size={16} />
                  <span>{item.label}</span>
                </NavLink>
              )
            })}
          </div>
        </nav>

        <div className="p-6 border-t border-border-default">
          <div className="flex items-center gap-3 px-2 mb-6">
            <div className="w-8 h-8 rounded-md bg-blue-50 flex items-center justify-center border border-blue-100 dark:bg-blue-900/20 dark:border-blue-800">
              <span className="text-blue-600 font-medium text-xs dark:text-blue-400">U</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-ink-primary truncate">Researcher</p>
              <p className="text-xs text-ink-muted truncate">mind-r3.ai</p>
            </div>
          </div>
          <button
            className="flex w-full items-center gap-2 px-4 py-3 rounded-md text-ink-secondary text-sm font-medium transition-all hover:bg-bg-subtle hover:text-blue-600 dark:hover:text-blue-400"
          >
            <Settings size={16} />
            <span>Settings</span>
          </button>
        </div>
      </div>
    </aside>
  )
}
