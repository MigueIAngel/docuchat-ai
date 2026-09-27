import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Markdown } from './markdown'

const citation = (id: number, key: string) => (
  <button key={key} type="button">
    cite-{id}
  </button>
)

describe('Markdown', () => {
  it('renders lists, bold text and citations', () => {
    render(<Markdown text={'Summary:\n\n- **Three** days [1]\n- VPN required [2]'} renderCitation={citation} />)
    expect(screen.getAllByRole('listitem')).toHaveLength(2)
    expect(screen.getByText('Three').tagName).toBe('STRONG')
    expect(screen.getByRole('button', { name: 'cite-1' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'cite-2' })).toBeInTheDocument()
  })

  it('never renders raw HTML from the model', () => {
    const { container } = render(<Markdown text={'<img src=x onerror="alert(1)"> hi'} renderCitation={citation} />)
    expect(container.querySelector('img')).toBeNull()
    expect(container.textContent).toContain('<img src=x')
  })
})
