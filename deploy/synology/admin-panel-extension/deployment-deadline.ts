import type { Server } from 'bun';

const APPLY_DEADLINE_MS = 1_900_000;
const MAX_RESPONSE_BYTES = 1024 * 1024;

export async function withDeploymentDeadline(
  request: Request,
  server: Pick<Server<undefined>, 'timeout'>,
  pathname: string,
  handle: (request: Request) => Promise<Response>,
): Promise<Response> {
  if (request.method !== 'POST' || pathname !== '/deployment-control/api/apply') {
    return handle(request);
  }

  const controller = new AbortController();
  const cancel = () => controller.abort();
  request.signal.addEventListener('abort', cancel, { once: true });
  if (request.signal.aborted) cancel();
  let rejectAbort: () => void;
  const aborted = new Promise<never>((_, reject) => {
    rejectAbort = () => reject(new Error('Deployment response interrupted'));
    controller.signal.addEventListener('abort', rejectAbort, { once: true });
    if (controller.signal.aborted) rejectAbort();
  });
  const timer = setTimeout(cancel, APPLY_DEADLINE_MS);
  try {
    server.timeout(request, 0);
    const response = async () => {
      const downstream = new Request(request, { signal: controller.signal });
      const result = await handle(downstream);
      const reader = result.body?.getReader();
      if (!reader) return result;
      const cancelBody = () => { void reader.cancel().catch(() => {}); };
      controller.signal.addEventListener('abort', cancelBody, { once: true });
      const chunks: Uint8Array[] = [];
      let size = 0;
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          size += value.byteLength;
          if (size > MAX_RESPONSE_BYTES) {
            cancelBody();
            throw new Error('Deployment response exceeds limit');
          }
          chunks.push(value);
        }
        const body = new Uint8Array(size);
        let offset = 0;
        for (const chunk of chunks) {
          body.set(chunk, offset);
          offset += chunk.byteLength;
        }
        return new Response(body, result);
      } finally {
        controller.signal.removeEventListener('abort', cancelBody);
        reader.releaseLock();
      }
    };
    return await Promise.race([response(), aborted]);
  } catch {
    return Response.json(
      { ok: false, error: 'Deployment response interrupted; check settings recovery status before retrying.' },
      { status: request.signal.aborted ? 499 : controller.signal.aborted ? 504 : 502,
        headers: { 'Cache-Control': 'no-store' } },
    );
  } finally {
    clearTimeout(timer);
    request.signal.removeEventListener('abort', cancel);
    controller.signal.removeEventListener('abort', rejectAbort!);
    if (!request.signal.aborted) server.timeout(request, 10);
  }
}
