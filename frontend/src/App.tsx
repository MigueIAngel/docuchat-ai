import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from './api/client'
import type { DocumentInfo, Health } from './api/types'
import { Chat } from './components/Chat'
import { Sidebar } from './components/Sidebar'
import { useChat } from './lib/useChat'

export default function App() {
  const { t, i18n } = useTranslation()
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [selected, setSelected] = useState<string[]>([])
  const [health, setHealth] = useState<Health>()
  const [uploading, setUploading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [dark, setDark] = useState(true)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const chat = useChat(t('errorGeneric'))

  useEffect(() => {
    api.health().then(setHealth).catch(() => undefined)
    api.documents().then(setDocuments).catch(() => setError(t('errorGeneric')))
  }, [t])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
  }, [dark])

  async function upload(file: File) {
    setUploading(file.name)
    setError(null)
    try {
      const doc = await api.upload(file)
      setDocuments((docs) => [doc, ...docs])
    } catch (err) {
      setError(err instanceof Error ? err.message : t('errorGeneric'))
    } finally {
      setUploading(null)
    }
  }

  async function uploadSample() {
    const blob = await fetch('/sample-remote-work-policy.pdf').then((r) => r.blob())
    await upload(new File([blob], 'remote-work-policy.pdf', { type: 'application/pdf' }))
  }

  async function remove(doc: DocumentInfo) {
    if (!window.confirm(t('confirmDelete', { name: doc.filename }))) return
    await api.remove(doc.id)
    setDocuments((docs) => docs.filter((d) => d.id !== doc.id))
    setSelected((ids) => ids.filter((id) => id !== doc.id))
  }

  const scopeLabel = selected.length ? t('scopeSome', { count: selected.length }) : t('scopeAll')

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-white/10">
        <div className="flex items-center gap-3">
          <button type="button" className="md:hidden" onClick={() => setSidebarOpen((v) => !v)} aria-label={t('documents')}>
            ☰
          </button>
          <img src="/favicon.svg" alt="" className="h-8 w-8" />
          <div>
            <h1 className="leading-tight font-bold">
              DocuChat <span className="gradient-text">AI</span>
            </h1>
            <p className="hidden text-xs text-slate-500 sm:block">{t('tagline')}</p>
          </div>
        </div>
        <div className="flex items-center gap-1 text-sm">
          {chat.messages.length > 0 && (
            <button type="button" onClick={chat.reset} className="rounded-lg px-3 py-1.5 hover:bg-slate-200 dark:hover:bg-white/10">
              ＋ {t('newChat')}
            </button>
          )}
          <button
            type="button"
            onClick={() => void i18n.changeLanguage(i18n.resolvedLanguage === 'es' ? 'en' : 'es')}
            className="rounded-lg px-3 py-1.5 hover:bg-slate-200 dark:hover:bg-white/10"
          >
            🌐 {t('language')}
          </button>
          <button
            type="button"
            onClick={() => setDark((v) => !v)}
            className="rounded-lg px-3 py-1.5 hover:bg-slate-200 dark:hover:bg-white/10"
            aria-label={t('theme')}
            title={t('theme')}
          >
            {dark ? '☀️' : '🌙'}
          </button>
        </div>
      </header>

      <div className="flex min-h-0 flex-1">
        <div
          className={`${sidebarOpen ? 'block' : 'hidden'} absolute inset-y-14 left-0 z-10 w-80 border-r border-slate-200 bg-slate-50 p-4 md:static md:block dark:border-white/10 dark:bg-[#0b0d12]`}
        >
          <Sidebar
            documents={documents}
            selected={selected}
            health={health}
            uploading={uploading}
            error={error}
            onToggle={(id) => setSelected((ids) => (ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id]))}
            onUpload={upload}
            onDelete={remove}
            onSample={uploadSample}
          />
        </div>
        <main className="min-w-0 flex-1">
          <Chat
            messages={chat.messages}
            isStreaming={chat.isStreaming}
            scopeLabel={scopeLabel}
            onSend={(question) => void chat.send(question, selected)}
            onStop={chat.stop}
          />
        </main>
      </div>
    </div>
  )
}
