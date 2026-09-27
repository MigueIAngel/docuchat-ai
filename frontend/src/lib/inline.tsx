import type { ReactNode } from 'react'

export type CitationRenderer = (id: number, key: string) => ReactNode

/** Renders **bold**, `code` and [n] citations inside a line of text. */
export function renderInline(text: string, renderCitation: CitationRenderer, keyPrefix = ''): ReactNode[] {
  const nodes: ReactNode[] = []
  const pattern = /(\*\*[^*]+\*\*|`[^`]+`|\[\d+\])/g
  let last = 0
  let match: RegExpExecArray | null
  let index = 0
  while ((match = pattern.exec(text))) {
    if (match.index > last) nodes.push(text.slice(last, match.index))
    const token = match[0]
    const key = `${keyPrefix}-${index++}`
    if (token.startsWith('**')) nodes.push(<strong key={key}>{token.slice(2, -2)}</strong>)
    else if (token.startsWith('`'))
      nodes.push(
        <code key={key} className="rounded bg-slate-200 px-1 font-mono text-[0.85em] dark:bg-white/10">
          {token.slice(1, -1)}
        </code>,
      )
    else nodes.push(renderCitation(Number(token.slice(1, -1)), key))
    last = match.index + token.length
  }
  if (last < text.length) nodes.push(text.slice(last))
  return nodes
}
