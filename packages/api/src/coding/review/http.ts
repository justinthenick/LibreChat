import { Readable } from 'node:stream';
import type { RequestListener } from 'node:http';
import type { ReviewServiceConfig } from './transport';
import { createReviewService, reviewRunIdSchema } from './transport';

/** Builds a listener callback; never creates or binds a server. */
export function createReviewHttpHandler(config: ReviewServiceConfig): RequestListener {
  const service = createReviewService(config);
  const destination = config.enabled === true ? new URL(config.url) : undefined;
  return async (incoming, outgoing) => {
    outgoing.setHeader('cache-control', 'no-store');
    const reject = (status: number, code: string) => {
      if (outgoing.destroyed) return;
      outgoing.writeHead(status, { 'content-type': 'application/json' });
      outgoing.end(JSON.stringify({ code }));
    };
    if (!destination) return reject(503, 'configuration');
    if (
      incoming.headers.host !== destination.host ||
      incoming.method !== 'POST' ||
      !['/review', '/review/cancel', '/review/status'].includes(incoming.url ?? '') ||
      (incoming.url === '/review' &&
        !reviewRunIdSchema.safeParse(incoming.headers['x-review-id']).success)
    )
      return reject(400, 'invalid_request');
    try {
      const headers = new Headers();
      for (const name of ['authorization', 'content-type', 'x-review-id']) {
        const value = incoming.headers[name];
        if (typeof value === 'string') headers.set(name, value);
      }
      const request = new Request(new URL(incoming.url!, destination).href, {
        method: 'POST',
        headers,
        // Node and DOM declare incompatible BYOB overloads for the same runtime Web Stream.
        body: Readable.toWeb(incoming) as unknown as ReadableStream<Uint8Array>,
        duplex: 'half',
      } as RequestInit & { duplex: 'half' });
      const result = await service(request);
      if (outgoing.destroyed) return;
      outgoing.writeHead(result.status, { 'content-type': 'application/json' });
      outgoing.end(await result.text());
    } catch {
      reject(400, 'invalid_request');
    }
  };
}
