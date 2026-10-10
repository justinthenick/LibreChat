import { request } from 'node:https';
import { checkServerIdentity } from 'node:tls';
import { createHash, randomUUID } from 'node:crypto';
import type { SecureContext, ConnectionOptions } from 'node:tls';
import type { RequestOptions } from 'node:https';
import type { PreviewOptions } from './types';
import { decodePreviewReply } from './frame';

type BrokerOptions = {
  /** Fixed trusted configuration; never selected from HTTP request fields. */
  endpoint: string;
  secureContext: SecureContext;
  serverSha256: string;
  authorize: NonNullable<PreviewOptions['authorize']>;
  enabled?: boolean;
  timeoutMs?: number;
};

/** Dormant one-shot mTLS adapter. No files, listener, retries or persistent connections. */
export function createPreviewHttps(options: BrokerOptions): PreviewOptions {
  const { secureContext, serverSha256, authorize, enabled = false, timeoutMs = 5000 } = options;
  const endpoint = new URL(options.endpoint);
  const unavailable = () => new Error('job_service_unavailable');
  if (
    endpoint.protocol !== 'https:' ||
    endpoint.pathname !== '/preview/v1' ||
    endpoint.username ||
    endpoint.password ||
    endpoint.search ||
    endpoint.hash ||
    !secureContext ||
    !/^[a-f0-9]{64}$/.test(serverSha256) ||
    typeof authorize !== 'function' ||
    typeof enabled !== 'boolean' ||
    !Number.isSafeInteger(timeoutMs) ||
    timeoutMs < 1 ||
    timeoutMs > 30000
  )
    throw unavailable();
  let active = false;
  return {
    enabled,
    timeoutMs,
    authorize: (principal, scope, context) =>
      enabled ? authorize(principal, scope, context) : Promise.resolve(false),
    transport: {
      exchange: async ({ principal, payload }) => {
        if (!enabled || active) throw unavailable();
        const identity = Object.freeze({
          user_id: principal.user_id,
          tenant_id: principal.tenant_id,
        });
        const id = randomUUID();
        const body = Buffer.from(
          JSON.stringify({ version: 1, request_id: id, principal: identity, payload }) + '\n',
        );
        if (body.length > 49152) throw unavailable();
        active = true;
        try {
          return await new Promise<unknown>((resolve, reject) => {
            let settled = false;
            const finish = (error?: Error, value?: unknown) => {
              if (settled) return;
              settled = true;
              clearTimeout(timer);
              outgoing.destroy();
              if (error) reject(unavailable());
              else resolve(value);
            };
            const connectionOptions: RequestOptions & Pick<ConnectionOptions, 'secureContext'> = {
              method: 'POST',
              agent: false,
              secureContext,
              rejectUnauthorized: true,
              minVersion: 'TLSv1.2',
              maxHeaderSize: 8192,
              checkServerIdentity: (host, certificate) =>
                checkServerIdentity(host, certificate) ||
                (createHash('sha256').update(certificate.raw).digest('hex') === serverSha256
                  ? undefined
                  : unavailable()),
              headers: {
                'Content-Type': 'application/json',
                'Content-Length': body.length,
                Connection: 'close',
              },
            };
            const outgoing = request(endpoint, connectionOptions, (response) => {
              const chunks: Buffer[] = [];
              let size = 0;
              if (
                response.statusCode !== 200 ||
                response.headers['content-type'] !== 'application/json'
              ) {
                response.destroy();
                finish(unavailable());
                return;
              }
              response.on('data', (chunk: Buffer) => {
                size += chunk.length;
                if (size > 270336) {
                  response.destroy();
                  finish(unavailable());
                  return;
                }
                chunks.push(chunk);
              });
              response.on('error', () => finish(unavailable()));
              response.on('aborted', () => finish(unavailable()));
              response.on('end', () => {
                try {
                  finish(undefined, decodePreviewReply(Buffer.concat(chunks), id, identity));
                } catch {
                  finish(unavailable());
                }
              });
            });
            outgoing.on('error', () => finish(unavailable()));
            const timer = setTimeout(() => finish(unavailable()), timeoutMs);
            outgoing.end(body);
          });
        } finally {
          active = false;
        }
      },
    },
  };
}
