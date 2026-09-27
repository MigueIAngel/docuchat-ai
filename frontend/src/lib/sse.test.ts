import { describe, expect, it } from 'vitest'
import { createSSEParser, type SSEEvent } from './sse'

describe('createSSEParser', () => {
  it('parses complete events with JSON payloads', () => {
    const events: SSEEvent[] = []
    const parse = createSSEParser((event) => events.push(event))
    parse('event: sources\ndata: [{"id":1}]\n\nevent: token\ndata: "Hola"\n\n')
    expect(events).toEqual([
      { event: 'sources', data: [{ id: 1 }] },
      { event: 'token', data: 'Hola' },
    ])
  })

  it('buffers events split across network chunks', () => {
    const events: SSEEvent[] = []
    const parse = createSSEParser((event) => events.push(event))
    parse('event: tok')
    parse('en\ndata: "a b')
    expect(events).toEqual([])
    parse('"\n\nevent: done\r\ndata: {}\r\n\r\n')
    expect(events).toEqual([
      { event: 'token', data: 'a b' },
      { event: 'done', data: {} },
    ])
  })

  it('keeps non-JSON data as text', () => {
    const events: SSEEvent[] = []
    createSSEParser((event) => events.push(event))('data: plain text\n\n')
    expect(events).toEqual([{ event: 'message', data: 'plain text' }])
  })
})
