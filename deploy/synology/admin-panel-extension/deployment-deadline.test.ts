import { test, expect, spyOn } from 'bun:test';
import { withDeploymentDeadline } from './deployment-deadline';

for (const phase of ['headers', 'body']) {
  test(`apply deadline bounds stalled ${phase} and aborts downstream`, async () => {
    const original = globalThis.setTimeout;
    const timer = spyOn(globalThis, 'setTimeout').mockImplementation((fn, ms, ...args) =>
      original(fn, ms === 1_900_000 ? 30 : ms, ...args));
    let cancelled = false;
    const timeouts: number[] = [];
    try {
      const result = await withDeploymentDeadline(
        new Request('http://example.test/deployment-control/api/apply', { method: 'POST' }),
        { timeout: (_, value) => { timeouts.push(value); } },
        '/deployment-control/api/apply',
        async (request) => {
          request.signal.addEventListener('abort', () => { cancelled = true; });
          if (phase === 'headers') return new Promise<Response>(() => {});
          return new Response(new ReadableStream({ start(c) { c.enqueue(new Uint8Array([1])); } }));
        },
      );
      expect(result.status).toBe(504);
      expect(cancelled).toBe(true);
      expect(timeouts).toEqual([0, 10]);
    } finally { timer.mockRestore(); }
  });
}

test('ordinary requests retain Bun defaults and streamed response', async () => {
  const response = new Response('unchanged');
  const result = await withDeploymentDeadline(new Request('http://example.test/health'),
    { timeout: () => { throw new Error('ordinary timeout changed'); } }, '/health', async () => response);
  expect(result).toBe(response);
});

test('client cancellation reaches downstream and does not expose errors', async () => {
  const client = new AbortController();
  let cancelled = false;
  const pending = withDeploymentDeadline(
    new Request('http://example.test/deployment-control/api/apply', {method: 'POST', signal: client.signal}),
    {timeout: () => {}}, '/deployment-control/api/apply', async (request) => {
      request.signal.addEventListener('abort', () => { cancelled = true; });
      return new Promise<Response>(() => {});
    });
  client.abort();
  const response = await pending;
  expect(cancelled).toBe(true);
  expect(response.status).toBe(499);
});

test('oversized response is cancelled instead of buffered without a bound', async () => {
  let cancelled = false;
  const response = await withDeploymentDeadline(
    new Request('http://example.test/deployment-control/api/apply', {method: 'POST'}),
    {timeout: () => {}}, '/deployment-control/api/apply', async () =>
      new Response(new ReadableStream({start(c) { c.enqueue(new Uint8Array(1024 * 1024 + 1)); }, cancel() { cancelled = true; }})));
  expect(response.status).toBe(502);
  expect(cancelled).toBe(true);
});
