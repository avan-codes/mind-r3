import React from 'react'
import { BrowserRouter } from 'react-router-dom'
import { ChatProvider } from './context/ChatContext'
import TopBar from './components/layout/TopBar'
import ChatPage from './pages/ChatPage'

export default function App() {
  return (
    <ChatProvider>
      <BrowserRouter>
        <div className="flex h-screen flex-col bg-bg-secondary text-ink-primary">
          <TopBar />
          <main className="flex-1 overflow-y-auto relative">
            <ChatPage />
          </main>
        </div>
      </BrowserRouter>
    </ChatProvider>
  )
}
