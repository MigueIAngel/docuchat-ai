import clsx from 'clsx'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { ChatMessage } from '../api/types'
import { Markdown } from '../lib/markdown'

export function Message({ message }: { message: ChatMessage }) {
  const { t } = useTranslation()
  const [active, setActive] = useState<number | null>(null)

  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <p className="max-w-[80%] rounded-2xl rounded-br-md bg-gradient-to-br from-cyan-500 to-violet-500 px-4 py-2.5 whitespace-pre-wrap text-white">
          {message.content}
        </p>
      </div>
    )
  }

  const sources = message.sources ?? []
  const citation = (id: number, key: string) => {
    const source = sources.find((s) => s.id === id)
    if (!source) return <sup key={key}>[{id}]</sup>
    return (
      <button
        key={key}
        type="button"
        onClick={() => setActive(active === id ? null : id)}
        className="mx-0.5 inline-flex h-5 min-w-5 items-center justify-center rounded-md bg-cyan-500/15 px-1 align-text-top text-[11px] font-bold text-cyan-700 hover:bg-cyan-500/30 dark:text-cyan-300"
        title={`${source.filename} · ${t('page', { page: source.page })}`}
      >
        {id}
      </button>
    )
  }

  return (
    <div className="flex gap-3">
      <div className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-gradient-to-br from-cyan-400 to-violet-500 text-sm text-white">
        ✦
      </div>
      <div className="min-w-0 flex-1">
        <div className={clsx('leading-relaxed', message.status === 'error' && 'text-rose-500')}>
          {message.content ? (
            <Markdown text={message.content} renderCitation={citation} />
          ) : (
            <span className="inline-flex gap-1" aria-label="…">
              {[0, 1, 2].map((i) => (
                <span key={i} className="h-2 w-2 animate-bounce rounded-full bg-cyan-400" style={{ animationDelay: `${i * 120}ms` }} />
              ))}
            </span>
          )}
          {message.status === 'streaming' && message.content && <span className="ml-0.5 inline-block h-4 w-1.5 animate-pulse bg-cyan-400 align-middle" />}
        </div>

        {sources.length > 0 && message.status !== 'streaming' && (
          <div className="mt-3">
            <p className="mb-2 text-xs font-semibold tracking-wider text-slate-500 uppercase">{t('sources')}</p>
            <div className="flex flex-wrap gap-2">
              {sources.map((source) => (
                <button
                  key={source.id}
                  type="button"
                  onClick={() => setActive(active === source.id ? null : source.id)}
                  className={clsx(
                    'glass rounded-lg px-2.5 py-1 text-xs transition',
                    active === source.id && 'ring-2 ring-cyan-400',
                  )}
                >
                  <span className="font-bold text-cyan-600 dark:text-cyan-300">[{source.id}]</span> {source.filename} ·{' '}
                  {t('page', { page: source.page })}
                </button>
              ))}
            </div>
            {active !== null && (
              <blockquote className="glass mt-2 rounded-xl p-3 text-sm text-slate-600 dark:text-slate-300">
                {sources.find((s) => s.id === active)?.text}
              </blockquote>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
