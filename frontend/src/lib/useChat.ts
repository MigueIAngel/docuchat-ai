import { useCallback, useRef, useState } from 'react'
import { streamChat } from '../api/client'
import type { ChatMessage } from '../api/types'

const uid = () => Math.random().toString(36).slice(2)

export function useChat(errorMessage: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setStreaming] = useState(false)
  const controller = useRef<AbortController | null>(null)

  const update = (id: string, change: (message: ChatMessage) => ChatMessage) =>
    setMessages((all) => all.map((message) => (message.id === id ? change(message) : message)))

  const send = useCallback(
    async (question: string, documentIds: string[]) => {
      const history = messages
        .filter((m) => m.status !== 'error')
        .map(({ role, content }) => ({ role, content }))
      const assistantId = uid()
      setMessages((all) => [
        ...all,
        { id: uid(), role: 'user', content: question },
        { id: assistantId, role: 'assistant', content: '', status: 'streaming' },
      ])
      setStreaming(true)
      controller.current = new AbortController()
      try {
        await streamChat(
          { question, document_ids: documentIds.length ? documentIds : undefined, history },
          {
            onSources: (sources) => update(assistantId, (m) => ({ ...m, sources })),
            onToken: (token) => update(assistantId, (m) => ({ ...m, content: m.content + token })),
            // A fallback model took over: drop the incomplete answer.
            onRestart: () => update(assistantId, (m) => ({ ...m, content: '' })),
            onError: (message) => update(assistantId, (m) => ({ ...m, content: message, status: 'error' })),
          },
          controller.current.signal,
        )
        update(assistantId, (m) => (m.status === 'error' ? m : { ...m, status: 'done' }))
      } catch (error) {
        const aborted = error instanceof DOMException && error.name === 'AbortError'
        update(assistantId, (m) =>
          aborted ? { ...m, status: 'done' } : { ...m, content: errorMessage, status: 'error' },
        )
      } finally {
        setStreaming(false)
        controller.current = null
      }
    },
    [messages, errorMessage],
  )

  const stop = useCallback(() => controller.current?.abort(), [])
  const reset = useCallback(() => {
    controller.current?.abort()
    setMessages([])
  }, [])

  return { messages, isStreaming, send, stop, reset }
}
