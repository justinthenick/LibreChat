import { randomUUID } from 'node:crypto';
import { decodePreviewReply } from './frame';
import type { Readable, Writable } from 'node:stream';
import type { PreviewOptions, PreviewPrincipal, PreviewStartRequest } from './types';

type Grant = { principal: PreviewPrincipal; repositories: readonly string[] };
type PipeOptions = {
  /** Dedicated private pipes owned by the trusted embedding process, never a public socket. */
  readable: Readable;
  writable: Writable;
  grants: readonly Grant[];
  /** Trusted, bounded text/rate admission. Get/cancel do not consume start admission. */
  admitStart: (principal: PreviewPrincipal, request: PreviewStartRequest) => Promise<boolean>;
  enabled?: boolean;
  timeoutMs?: number;
};

const identifier = (value: unknown): value is string =>
  typeof value === 'string' && /^[A-Za-z0-9][A-Za-z0-9_.:@-]{0,127}$/.test(value);
const owner = (principal: PreviewPrincipal) =>
  JSON.stringify([principal.user_id, principal.tenant_id]);
const unavailable = () => new Error('job_service_unavailable');
const INPUT_LIMIT = 49152;
const OUTPUT_LIMIT = 270336;

/** Dormant single-flight adapter. Closing a pipe never confirms remote execution stopped.
 * The caller owns process lifecycle and must create a NEW adapter after disconnect; no replay.
 */
export function createPreviewPipe(options: PipeOptions): PreviewOptions & { close: () => void } {
  const { readable, writable, admitStart, enabled = false, timeoutMs = 5000 } = options;
  if (
    typeof enabled !== 'boolean' ||
    typeof admitStart !== 'function' ||
    !Number.isSafeInteger(timeoutMs) ||
    timeoutMs < 1 ||
    timeoutMs > 30000
  )
    throw unavailable();
  const grants = new Map<string, ReadonlySet<string>>();
  for (const grant of options.grants) {
    const { user_id, tenant_id } = grant.principal;
    if (
      !identifier(user_id) ||
      (tenant_id !== '' && !identifier(tenant_id)) ||
      !grant.repositories.every(identifier) ||
      grants.has(owner(grant.principal))
    )
      throw unavailable();
    grants.set(owner({ user_id, tenant_id }), new Set(grant.repositories));
  }
  let closed = false;
  let buffer = Buffer.alloc(0);
  let pending:
    | {
        id: string;
        principal: PreviewPrincipal;
        resolve: (value: unknown) => void;
        reject: (error: Error) => void;
        timer: ReturnType<typeof setTimeout>;
      }
    | undefined;
  const close = () => {
    if (closed) return;
    closed = true;
    buffer = Buffer.alloc(0);
    if (pending) {
      clearTimeout(pending.timer);
      pending.reject(unavailable());
      pending = undefined;
    }
    readable.destroy();
    writable.destroy();
  };
  readable.on('error', close);
  readable.on('end', close);
  readable.on('close', close);
  writable.on('error', close);
  writable.on('close', close);
  readable.on('data', (chunk: unknown) => {
    try {
      if (
        closed ||
        !pending ||
        !Buffer.isBuffer(chunk) ||
        buffer.length + chunk.length > OUTPUT_LIMIT
      ) {
        throw unavailable();
      }
      buffer = Buffer.concat([buffer, chunk]);
      const newline = buffer.indexOf(10);
      if (newline === -1) return;
      if (newline !== buffer.length - 1) throw unavailable();
      const result = decodePreviewReply(buffer, pending.id, pending.principal);
      const current = pending;
      pending = undefined;
      buffer = Buffer.alloc(0);
      clearTimeout(current.timer);
      current.resolve(result);
    } catch {
      close();
    }
  });
  return {
    enabled,
    timeoutMs,
    close,
    authorize: async (principal, scope, context) => {
      if (
        closed ||
        !enabled ||
        scope.task_mode !== 'read_only' ||
        !grants.get(owner(principal))?.has(scope.repository_alias)
      )
        return false;
      return (
        context.operation !== 'start' || (await admitStart(principal, context.request)) === true
      );
    },
    transport: {
      exchange: async ({ principal, payload }) => {
        if (closed || !enabled || pending || !grants.has(owner(principal))) throw unavailable();
        const identity = Object.freeze({
          user_id: principal.user_id,
          tenant_id: principal.tenant_id,
        });
        const id = randomUUID();
        const line = Buffer.from(
          JSON.stringify({ version: 1, request_id: id, principal: identity, payload }) + '\n',
        );
        if (line.length > INPUT_LIMIT) throw unavailable();
        return new Promise<unknown>((resolve, reject) => {
          pending = {
            id,
            principal: identity,
            resolve,
            reject,
            timer: setTimeout(close, timeoutMs),
          };
          try {
            writable.write(line, (error) => {
              if (error) close();
            });
          } catch {
            close();
          }
        });
      },
    },
  };
}
