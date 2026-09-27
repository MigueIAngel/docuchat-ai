export interface DocumentInfo {
  id: string
  filename: string
  pages: number
  chunks: number
  created_at: string
}

export interface Source {
  id: number
  document_id: string
  filename: string
  page: number
  score: number
  text: string
}

export interface Health {
  status: string
  provider: 'nvidia' | 'gemini' | 'demo'
  chat_model: string
  embedding_model: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  status?: 'streaming' | 'done' | 'error'
}
