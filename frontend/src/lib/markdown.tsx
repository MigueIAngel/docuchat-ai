import { type CitationRenderer, renderInline } from './inline'

/**
 * Minimal, XSS-safe Markdown renderer for model answers: paragraphs, bullet
 * and numbered lists, quotes and inline formatting. No raw HTML is rendered.
 */
export function Markdown({ text, renderCitation }: { text: string; renderCitation: CitationRenderer }) {
  const blocks = text.split(/\n{2,}/)
  return (
    <>
      {blocks.map((block, b) => {
        const lines = block.split('\n').filter((line) => line.trim())
        if (!lines.length) return null
        if (lines.every((line) => /^\s*([-*•]|\d+[.)])\s+/.test(line))) {
          const ordered = /^\s*\d/.test(lines[0])
          const Tag = ordered ? 'ol' : 'ul'
          return (
            <Tag key={b} className={ordered ? 'my-2 list-decimal pl-5' : 'my-2 list-disc pl-5'}>
              {lines.map((line, l) => (
                <li key={l}>{renderInline(line.replace(/^\s*([-*•]|\d+[.)])\s+/, ''), renderCitation, `${b}-${l}`)}</li>
              ))}
            </Tag>
          )
        }
        if (lines.every((line) => line.startsWith('>'))) {
          return (
            <blockquote key={b} className="my-2 border-l-2 border-cyan-400 pl-3 text-slate-500 italic dark:text-slate-400">
              {renderInline(lines.map((line) => line.replace(/^>\s?/, '')).join(' '), renderCitation, `${b}`)}
            </blockquote>
          )
        }
        return (
          <p key={b} className="my-2 first:mt-0 last:mb-0">
            {lines.map((line, l) => (
              <span key={l}>
                {l > 0 && <br />}
                {renderInline(line.replace(/^#+\s*/, ''), renderCitation, `${b}-${l}`)}
              </span>
            ))}
          </p>
        )
      })}
    </>
  )
}
