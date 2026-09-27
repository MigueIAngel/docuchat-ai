export interface SSEEvent {
  event: string
  data: unknown
}

/**
 * Incremental Server-Sent Events parser. Network chunks can end in the middle
 * of an event, so incomplete data is buffered until the blank-line separator.
 */
export function createSSEParser(onEvent: (event: SSEEvent) => void) {
  let buffer = ''
  return (chunk: string) => {
    buffer += chunk.replace(/\r\n/g, '\n')
    let separator = buffer.indexOf('\n\n')
    while (separator !== -1) {
      const block = buffer.slice(0, separator)
      buffer = buffer.slice(separator + 2)
      let event = 'message'
      const data: string[] = []
      for (const line of block.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim()
        else if (line.startsWith('data:')) data.push(line.slice(5).trimStart())
      }
      if (data.length) {
        const raw = data.join('\n')
        let parsed: unknown = raw
        try {
          parsed = JSON.parse(raw)
        } catch {
          /* plain text payload */
        }
        onEvent({ event, data: parsed })
      }
      separator = buffer.indexOf('\n\n')
    }
  }
}
