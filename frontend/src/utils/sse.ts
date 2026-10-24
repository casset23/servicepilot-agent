// Buffer complete SSE frames before parsing so network chunks cannot truncate JSON or UTF-8.
export async function* readSseEvents(reader: ReadableStreamDefaultReader<Uint8Array>): AsyncGenerator<unknown> {
  const decoder = new TextDecoder();
  let buffer = '';
  const payload = (frame: string) => frame.split(/\r?\n/)
    .filter(line => line.startsWith('data:'))
    .map(line => line.slice(5).replace(/^ /, ''))
    .join('\n');
  try {
    while (true) {
      const { done, value } = await reader.read();
      buffer += done ? decoder.decode() : decoder.decode(value, { stream: true });
      let separator: RegExpExecArray | null;
      while ((separator = /\r?\n\r?\n/.exec(buffer))) {
        const data = payload(buffer.slice(0, separator.index));
        buffer = buffer.slice(separator.index + separator[0].length);
        if (data === '[DONE]') return;
        if (data) yield JSON.parse(data);
      }
      if (done) {
        const data = payload(buffer);
        if (data && data !== '[DONE]') yield JSON.parse(data);
        return;
      }
    }
  } finally {
    reader.releaseLock();
  }
}
