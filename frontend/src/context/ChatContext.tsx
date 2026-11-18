import { createContext, useContext, useReducer, useCallback, useEffect } from 'react'

export type MessageRole = 'user' | 'assistant'

export interface Source {
  filename?: string | null
  page?: number | null
  similarity: number
  distance: number
  excerpt: string
  doc_id?: string | null
}

export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  createdAt: number
  sources?: Source[]
  retrieval_scores?: number[]
  retrieval_confidence?: number
  context?: string | null
}

interface ChatState {
  messages: ChatMessage[]
  currentSessionId: string | null
  sessions: Record<string, ChatMessage[]>
  isLoading: boolean
  error: string | null
  backendStatus: 'ok' | 'down' | 'unknown'
  indexStatus: { exists: boolean; vectors: number } | null
}

type ChatAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'ADD_MESSAGE'; payload: ChatMessage }
  | { type: 'REPLACE_LAST'; payload: ChatMessage }
  | { type: 'NEW_SESSION' }
  | { type: 'LOAD_SESSION'; payload: string }
  | { type: 'DELETE_SESSION'; payload: string }
  | { type: 'SET_BACKEND'; payload: 'ok' | 'down' | 'unknown' }
  | { type: 'SET_INDEX'; payload: { exists: boolean; vectors: number } | null }

const STORAGE_KEY = 'mindr3_chats'

const initialState: ChatState = {
  messages: [],
  currentSessionId: null,
  sessions: {},
  isLoading: false,
  error: null,
  backendStatus: 'unknown',
  indexStatus: null,
}

function loadSessions(): Record<string, ChatMessage[]> {
  if (typeof window === 'undefined') return {}
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

function saveSessions(sessions: Record<string, ChatMessage[]>) {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions))
  } catch {
    // ignore quota errors
  }
}

function newId() {
  return crypto.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`
}

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload }
    case 'SET_ERROR':
      return { ...state, error: action.payload }
    case 'SET_BACKEND':
      return { ...state, backendStatus: action.payload }
    case 'SET_INDEX':
      return { ...state, indexStatus: action.payload }
    case 'NEW_SESSION': {
      const id = newId()
      return {
        ...state,
        currentSessionId: id,
        messages: [],
        sessions: { ...state.sessions, [id]: [] },
        error: null,
      }
    }
    case 'LOAD_SESSION': {
      return {
        ...state,
        currentSessionId: action.payload,
        messages: [...(state.sessions[action.payload] || [])],
        error: null,
      }
    }
    case 'DELETE_SESSION': {
      const sessions = { ...state.sessions }
      delete sessions[action.payload]
      saveSessions(sessions)
      const nextId = state.currentSessionId === action.payload
        ? Object.keys(sessions).at(-1) || null
        : state.currentSessionId
      return {
        ...state,
        sessions,
        currentSessionId: nextId,
        messages: nextId ? [...(sessions[nextId] || [])] : [],
      }
    }
    case 'ADD_MESSAGE': {
      const msg = action.payload
      const sid = state.currentSessionId || newId()
      const sessions = {
        ...state.sessions,
        [sid]: [...(state.sessions[sid] || []), msg],
      }
      saveSessions(sessions)
      return {
        ...state,
        currentSessionId: sid,
        messages: [...state.messages, msg],
        sessions,
        error: null,
      }
    }
    case 'REPLACE_LAST': {
      const msg = action.payload
      const messages = [...state.messages]
      messages[messages.length - 1] = msg
      const sid = state.currentSessionId || newId()
      const sessions = {
        ...state.sessions,
        [sid]: [...(state.sessions[sid] || []).slice(0, -1), msg],
      }
      saveSessions(sessions)
      return { ...state, messages, sessions, isLoading: false }
    }
    default:
      return state
  }
}

const ChatContext = createContext<{
  state: ChatState
  dispatch: React.Dispatch<ChatAction>
  addMessage: (msg: ChatMessage) => void
  replaceLast: (msg: ChatMessage) => void
  newSession: () => void
  loadSession: (id: string) => void
  deleteSession: (id: string) => void
} | null>(null)

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, {
    ...initialState,
    sessions: loadSessions(),
  })

  // Hydrate first session if none exists
  useEffect(() => {
    const ids = Object.keys(state.sessions)
    if (!state.currentSessionId && ids.length > 0) {
      dispatch({ type: 'LOAD_SESSION', payload: ids[ids.length - 1] })
    }
  }, [])

  const addMessage = useCallback((msg: ChatMessage) => {
    dispatch({ type: 'ADD_MESSAGE', payload: msg })
  }, [])

  const replaceLast = useCallback((msg: ChatMessage) => {
    dispatch({ type: 'REPLACE_LAST', payload: msg })
  }, [])

  const newSession = useCallback(() => {
    dispatch({ type: 'NEW_SESSION' })
  }, [])

  const loadSession = useCallback((id: string) => {
    dispatch({ type: 'LOAD_SESSION', payload: id })
  }, [])

  const deleteSession = useCallback((id: string) => {
    dispatch({ type: 'DELETE_SESSION', payload: id })
  }, [])

  const value = {
    state,
    dispatch,
    addMessage,
    replaceLast,
    newSession,
    loadSession,
    deleteSession,
  }

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}

export const useChat = () => {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChat must be used within ChatProvider')
  return ctx
}
