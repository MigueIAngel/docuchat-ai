import clsx from 'clsx'
import { useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { DocumentInfo, Health } from '../api/types'

interface SidebarProps {
  documents: DocumentInfo[]
  selected: string[]
  health?: Health
  uploading: string | null
  error: string | null
  onToggle: (id: string) => void
  onUpload: (file: File) => void
  onDelete: (doc: DocumentInfo) => void
  onSample: () => void
}

export function Sidebar({ documents, selected, health, uploading, error, onToggle, onUpload, onDelete, onSample }: SidebarProps) {
  const { t } = useTranslation()
  const input = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  return (
    <aside className="flex h-full flex-col gap-4 overflow-hidden">
      <div
        role="button"
        tabIndex={0}
        onClick={() => input.current?.click()}
        onKeyDown={(event) => event.key === 'Enter' && input.current?.click()}
        onDragOver={(event) => {
          event.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault()
          setDragging(false)
          const file = event.dataTransfer.files[0]
          if (file) onUpload(file)
        }}
        className={clsx(
          'cursor-pointer rounded-2xl border-2 border-dashed p-5 text-center text-sm transition',
          dragging ? 'border-cyan-400 bg-cyan-400/10' : 'border-slate-300 hover:border-cyan-400 dark:border-white/15',
        )}
      >
        <div className="text-2xl">📄</div>
        <p className="mt-1 font-semibold">{t('upload')}</p>
        <p className="text-xs text-slate-500">{t('dropHint')}</p>
        <input
          ref={input}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={(event) => {
            const file = event.target.files?.[0]
            if (file) onUpload(file)
            event.target.value = ''
          }}
        />
      </div>

      {uploading && (
        <p className="flex items-center gap-2 text-xs text-cyan-600 dark:text-cyan-300">
          <span className="h-3 w-3 animate-spin rounded-full border-2 border-current border-t-transparent" />
          {t('uploading', { name: uploading })}
        </p>
      )}
      {error && <p role="alert" className="text-xs text-rose-500">{error}</p>}

      <div className="flex items-center justify-between">
        <h2 className="text-xs font-semibold tracking-wider text-slate-500 uppercase">{t('documents')}</h2>
        <span className="text-xs text-slate-400">{documents.length}</span>
      </div>

      <ul className="-mx-1 flex-1 space-y-1 overflow-y-auto px-1">
        {documents.length === 0 && (
          <li className="space-y-3 text-sm text-slate-500">
            <p>{t('noDocuments')}</p>
            <button type="button" onClick={onSample} className="text-cyan-600 underline dark:text-cyan-300">
              {t('sample')}
            </button>
          </li>
        )}
        {documents.map((doc) => (
          <li key={doc.id} className="group flex items-start gap-2 rounded-xl p-2 hover:bg-slate-100 dark:hover:bg-white/5">
            <input
              type="checkbox"
              className="mt-1 accent-cyan-500"
              checked={selected.includes(doc.id)}
              onChange={() => onToggle(doc.id)}
              aria-label={doc.filename}
            />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium" title={doc.filename}>
                {doc.filename}
              </p>
              <p className="text-xs text-slate-500">
                {t('pages', { count: doc.pages })} · {t('chunks', { count: doc.chunks })}
              </p>
            </div>
            <button
              type="button"
              className="text-slate-400 opacity-0 transition group-hover:opacity-100 hover:text-rose-500 focus:opacity-100"
              title={t('delete')}
              aria-label={`${t('delete')} ${doc.filename}`}
              onClick={() => onDelete(doc)}
            >
              ✕
            </button>
          </li>
        ))}
      </ul>

      {health && (
        <div className="rounded-xl bg-slate-100 p-3 text-xs dark:bg-white/5">
          {health.provider === 'demo' ? (
            <p className="text-amber-600 dark:text-amber-300">⚠️ {t('demoMode')}</p>
          ) : (
            <>
              <p className="font-semibold capitalize">
                {t('provider')}: {health.provider === 'nvidia' ? 'NVIDIA NIM' : 'Gemini'}
              </p>
              <p className="truncate font-mono text-slate-500">{health.chat_model}</p>
              <p className="truncate font-mono text-slate-500">{health.embedding_model}</p>
            </>
          )}
        </div>
      )}
    </aside>
  )
}
