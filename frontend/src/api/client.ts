import { createSSEParser } from '../lib/sse'
import type { DocumentInfo, Health, Source } from './types'

const API = import.meta.env.VITE_API_URL ?? '/api'

async function json<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string }
    throw new Error(body.detail ?? `Request failed (${response.status})`)
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T)
}

export const api = {
  health: () => fetch(`${API}/health`).then((r) => json<Health>(r)),
  documents: () => fetch(`${API}/documents`).then((r) => json<DocumentInfo[]>(r)),
  upload: (file: File) => {
    const body = new FormData()
    body.append('file', file)
    return fetch(`${API}/documents`, { method: 'POST', body }).then((r) => json<DocumentInfo>(r))
  },
  remove: (id: string) => fetch(`${API}/documents/${id}`, { method: 'DELETE' }).then((r) => json<void>(r)),
}

export interface ChatHandlers {
  onSources: (sources: Source[]) => void
  onToken: (token: string) => void
  onRestart: () => void
  onError: (message: string) => void
}

export async function streamChat(
  payload: { question: string; document_ids?: string[]; history: { role: string; content: string }[] },
  handlers: ChatHandlers,
  signal: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API}/chat`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
    signal,
  })
  if (!response.ok || !response.body) throw new Error(`Request failed (${response.status})`)

  const parse = createSSEParser(({ event, data }) => {
    if (event === 'sources') handlers.onSources(data as Source[])
    else if (event === 'token') handlers.onToken(data as string)
    else if (event === 'restart') handlers.onRestart()
    else if (event === 'error') handlers.onError((data as { message: string }).message)
  })
  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader()
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    parse(value)
  }
}
