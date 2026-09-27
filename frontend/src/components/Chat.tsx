import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import type { ChatMessage } from '../api/types'
import { Message } from './Message'

interface ChatProps {
  messages: ChatMessage[]
  isStreaming: boolean
  scopeLabel: string
  onSend: (question: string) => void
  onStop: () => void
}

export function Chat({ messages, isStreaming, scopeLabel, onSend, onStop }: ChatProps) {
  const { t } = useTranslation()
  const [question, setQuestion] = useState('')
  const bottom = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages])

  function submit(event?: FormEvent) {
    event?.preventDefault()
    const value = question.trim()
    if (!value || isStreaming) return
    onSend(value)
    setQuestion('')
  }

  const suggestions = t('suggestions', { returnObjects: true }) as string[]

  return (
    <section className="flex h-full min-h-0 flex-col">
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-3xl space-y-6">
          {messages.length === 0 ? (
            <div className="py-16 text-center">
              <h2 className="gradient-text text-3xl font-bold sm:text-4xl">{t('emptyTitle')}</h2>
              <p className="mx-auto mt-3 max-w-md text-slate-500">{t('emptyText')}</p>
              <div className="mt-8 grid gap-2 sm:grid-cols-3">
                {suggestions.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => onSend(suggestion)}
                    className="glass rounded-xl p-3 text-left text-sm transition hover:border-cyan-400"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message) => <Message key={message.id} message={message} />)
          )}
          <div ref={bottom} />
        </div>
      </div>

      <form onSubmit={submit} className="border-t border-slate-200 p-4 dark:border-white/10">
        <div className="glass mx-auto flex max-w-3xl items-end gap-2 rounded-2xl p-2">
          <textarea
            rows={1}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault()
                submit()
              }
            }}
            placeholder={t('placeholder')}
            aria-label={t('placeholder')}
            className="max-h-40 flex-1 resize-none bg-transparent px-2 py-2 outline-none placeholder:text-slate-400"
          />
          {isStreaming ? (
            <button type="button" onClick={onStop} className="rounded-xl bg-slate-200 px-4 py-2 text-sm font-semibold dark:bg-white/10">
              ■ {t('stop')}
            </button>
          ) : (
            <button
              type="submit"
              disabled={!question.trim()}
              className="rounded-xl bg-gradient-to-r from-cyan-500 to-violet-500 px-4 py-2 text-sm font-semibold text-white disabled:opacity-40"
            >
              {t('send')} ↑
            </button>
          )}
        </div>
        <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-slate-500">{scopeLabel}</p>
      </form>
    </section>
  )
}
