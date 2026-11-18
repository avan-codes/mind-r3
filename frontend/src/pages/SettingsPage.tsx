import React from 'react'
import { Send, Settings, Database, Bell, Mail } from 'lucide-react'

const SETTINGS = [
  { icon: Settings, label: 'General', desc: 'Application preferences and appearance', key: 'general' },
  { icon: Database, label: 'Vector Store', desc: 'FAISS index management and settings', key: 'vector' },
  { icon: Bell, label: 'Notifications', desc: 'Alerts and system notifications', key: 'notifications' },
  { icon: Mail, label: 'Account', desc: 'Profile and authentication settings', key: 'account' },
]

export default function SettingsPage() {
  return (
    <div className="flex flex-col h-full min-w-0">
      <section className="px-6 md:px-12 pb-12 border-b border-border-default">
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-2">
            <div>
              <span className="kicker">settings</span>
              <h1 className="text-4xl font-xbold text-ink-primary mb-2 tracking-tight">
                Settings
              </h1>
              <p className="text-ink-muted text-lg">Configure your Mind-R3 experience.</p>
            </div>
          </div>
        </div>
      </section>

      <div className="flex-1 overflow-y-auto px-6 md:px-12">
        <div className="max-w-3xl mx-auto">
          <div className="space-y-3">
            {SETTINGS.map((item) => {
              const Icon = item.icon
              return (
                <div key={item.key} className="border-b border-border-default pb-6 last:border-b-0 last:pb-0">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-8 h-8 rounded-md bg-blue-50 flex items-center justify-center border border-blue-100 dark:bg-blue-900/20 dark:border-blue-800 shrink-0">
                      <Icon size={16} className="text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-ink-primary">{item.label}</h3>
                      <p className="text-xs text-ink-muted">{item.desc}</p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-ink-muted uppercase tracking-wider">
                      Coming soon
                    </span>
                    <span className="badge badge-blue text-[10px]">Beta</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
