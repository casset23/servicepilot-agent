import test from 'node:test';
import assert from 'node:assert/strict';
import { readSseEvents } from '../frontend/src/utils/sse.ts';

function reader(parts) {
  return new ReadableStream({ start(controller) { for (const p of parts) controller.enqueue(p); controller.close(); } }).getReader();
}
const bytes = text => new TextEncoder().encode(text);
const collect = async r => { const events = []; for await (const event of readSseEvents(r)) events.push(event); return events; };

test('SSE preserves JSON text split at every UTF-8 byte boundary', async () => {
  const text = '您好\n订单"123"';
  const encoded = bytes(`data: ${JSON.stringify(text)}\n\n`);
  assert.deepEqual(await collect(reader([...encoded].map(value => new Uint8Array([value])))), [text]);
});

test('multiple CRLF events preserve interruption metadata and stop at DONE', async () => {
  const encoded = bytes('data: "查询中"\r\n\r\ndata: {"interruption":true,"conversation_id":"c-1"}\r\n\r\ndata: [DONE]\r\n\r\ndata: "忽略"\r\n\r\n');
  assert.deepEqual(await collect(reader([encoded])), ['查询中', { interruption: true, conversation_id: 'c-1' }]);
});

test('SSE ignores comment frames and flushes a final JSON event at EOF', async () => {
  assert.deepEqual(await collect(reader([bytes(': keepalive\n\ndata: "完成"')])), ['完成']);
});

test('malformed JSON becomes an explicit stream error', async () => {
  await assert.rejects(collect(reader([bytes('data: {broken}\n\n')])), SyntaxError);
});
