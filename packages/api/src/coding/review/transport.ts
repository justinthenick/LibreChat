import { z } from 'zod';
import { createHash, timingSafeEqual } from 'node:crypto';
import type {
  CodeReviewRequest,
  CodeReviewResult,
  CodeReviewRecovery,
} from 'librechat-data-provider';
import type {
  ReviewPrincipal,
  ReviewWorkerConfig,
  ReviewFailure,
  CodeReviewWorker,
} from './worker';
import type { ReviewJournal } from './journal';
import { createCodeReviewWorker, ReviewWorkerError } from './worker';
import { reviewRequestSchema, reviewResultSchema } from './schema';

const REQUEST_BYTES = 4096;
const RESPONSE_BYTES = 128_000;
const SERVICE_TIMEOUT_MS = 165_000;
const CLIENT_TIMEOUT_MS = 170_000;
const principalId = z
  .string()
  .min(1)
  .max(128)
  .refine((value) =>
    [...value].every((character) => {
      const code = character.codePointAt(0)!;
      return code > 31 && code !== 127 && !/\s/.test(character);
    }),
  );
export const reviewPrincipalSchema: z.ZodType<ReviewPrincipal> = z
  .object({ userId: principalId, tenantId: principalId.optional() })
  .strict();
export const reviewRunIdSchema: z.ZodString = z.string().uuid();
const envelopeSchema = z
  .object({
    request: reviewRequestSchema,
    principal: reviewPrincipalSchema,
  })
  .strict();
const errorSchema = z
  .object({
    code: z.enum([
      'stale_review',
      'invalid_request',
      'forbidden',
      'busy',
      'cancelled',
      'timeout',
      'output_limit',
      'worker_failed',
      'invalid_response',
      'configuration',
    ]),
  })
  .strict();
const recoverySchema: z.ZodType<CodeReviewRecovery> = z.discriminatedUnion('state', [
  z.object({ id: reviewRunIdSchema, state: z.literal('unknown') }).strict(),
  z
    .object({
      id: reviewRunIdSchema,
      state: z.literal('interrupted'),
      request: reviewRequestSchema,
      cancelRequested: z.boolean(),
    })
    .strict(),
  z
    .object({
      id: reviewRunIdSchema,
      state: z.literal('running'),
      request: reviewRequestSchema,
      cancelRequested: z.boolean(),
    })
    .strict(),
  z
    .object({
      id: reviewRunIdSchema,
      state: z.literal('completed'),
      request: reviewRequestSchema,
      result: reviewResultSchema,
      expiresAt: z.number().finite().positive(),
    })
    .strict(),
  z
    .object({
      id: reviewRunIdSchema,
      state: z.literal('failed'),
      request: reviewRequestSchema,
      code: errorSchema.shape.code,
      expiresAt: z.number().finite().positive(),
    })
    .strict(),
]);
const sameRequest = (left: CodeReviewRequest, right: CodeReviewRequest) =>
  left.repository === right.repository &&
  left.base === right.base &&
  left.head === right.head &&
  left.pullRequest?.number === right.pullRequest?.number &&
  left.pullRequest?.repositoryId === right.pullRequest?.repositoryId;

export const reviewFailureStatus: Record<ReviewFailure, number> = {
  stale_review: 409,
  invalid_request: 400,
  forbidden: 403,
  busy: 409,
  cancelled: 499,
  timeout: 504,
  output_limit: 502,
  worker_failed: 502,
  invalid_response: 502,
  configuration: 503,
};

interface ReviewTransportConfig {
  enabled?: boolean;
  /** Fixed operator-selected destination, never supplied in a review request. */
  url: string;
  token: string;
}

export interface ReviewServiceConfig extends ReviewTransportConfig {
  worker: ReviewWorkerConfig;
  /** Explicitly opened private durable store; no fallback if it fails. */
  journal?: ReviewJournal;
}

export interface ReviewClientConfig extends ReviewTransportConfig {
  model: string;
  /** In-memory transport seam for offline fixtures. Defaults to fetch. */
  send?: (request: Request) => Promise<Response>;
}

function validateTransport(config: ReviewTransportConfig): string {
  try {
    const url = new URL(config.url);
    const local =
      url.protocol === 'http:' && (url.hostname === '127.0.0.1' || url.hostname === '[::1]');
    if (
      (!local && url.protocol !== 'https:') ||
      url.username ||
      url.password ||
      url.search ||
      url.hash ||
      url.pathname !== '/review' ||
      !/^[A-Za-z0-9._~-]{32,256}$/.test(config.token)
    ) {
      throw new Error();
    }
    return url.href;
  } catch {
    throw new ReviewWorkerError('configuration');
  }
}

function digest(value: string): Buffer {
  return createHash('sha256').update(value).digest();
}

function aborted(signal: AbortSignal): ReviewWorkerError {
  return new ReviewWorkerError(
    signal.reason instanceof ReviewWorkerError ? signal.reason.code : 'cancelled',
  );
}

function interruptible<T>(operation: Promise<T>, signal: AbortSignal): Promise<T> {
  if (signal.aborted) {
    // Attach a rejection handler even when cancellation won before entry.
    void operation.catch(() => undefined);
    return Promise.reject(aborted(signal));
  }
  return new Promise((resolve, reject) => {
    const cancel = () => reject(aborted(signal));
    signal.addEventListener('abort', cancel, { once: true });
    operation.then(resolve, reject).finally(() => signal.removeEventListener('abort', cancel));
  });
}

function deadline(parent: AbortSignal | undefined, milliseconds: number) {
  const controller = new AbortController();
  const cancel = () => controller.abort(new ReviewWorkerError('cancelled'));
  if (parent?.aborted) {
    cancel();
  } else {
    parent?.addEventListener('abort', cancel, { once: true });
  }
  const timer = setTimeout(() => controller.abort(new ReviewWorkerError('timeout')), milliseconds);
  return {
    signal: controller.signal,
    cancel: () => controller.abort(new ReviewWorkerError('cancelled')),
    close: () => {
      clearTimeout(timer);
      parent?.removeEventListener('abort', cancel);
      controller.abort(new ReviewWorkerError('cancelled'));
    },
  };
}

async function readJson(
  message: Request | Response,
  limit: number,
  signal: AbortSignal,
  invalid: ReviewFailure,
): Promise<unknown> {
  if (
    message.headers.get('content-type')?.split(';')[0].trim() !== 'application/json' ||
    !message.body
  ) {
    void message.body?.cancel().catch(() => undefined);
    throw new ReviewWorkerError(invalid);
  }
  const reader = message.body.getReader();
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await interruptible(reader.read(), signal);
      if (done) break;
      size += value.byteLength;
      if (size > limit)
        throw new ReviewWorkerError(invalid === 'invalid_request' ? invalid : 'output_limit');
      chunks.push(value);
    }
    return JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks)));
  } catch (error) {
    if (error instanceof ReviewWorkerError) throw error;
    throw new ReviewWorkerError(invalid);
  } finally {
    void reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}

function failure(error: ReviewWorkerError): Response {
  const code = error.code;
  return Response.json(
    { code },
    { status: reviewFailureStatus[code], headers: { 'cache-control': 'no-store' } },
  );
}

/** Service-to-service adapter only. It neither listens nor accepts browser identity. */
export function createReviewService(
  config: ReviewServiceConfig,
): (request: Request) => Promise<Response> {
  if (config.enabled !== true) {
    return async () => failure(new ReviewWorkerError('configuration'));
  }
  const url = validateTransport(config);
  const credential = digest(`Bearer ${config.token}`);
  const worker = createCodeReviewWorker(config.worker);
  const journal = config.journal;
  let active = false;
  interface ReviewRun {
    principal: ReviewPrincipal;
    cancel: () => void;
    cancelled: boolean;
    expires: number;
    expiryTimer?: ReturnType<typeof setTimeout>;
    request?: CodeReviewRequest;
    result?: CodeReviewResult;
    code?: ReviewFailure;
  }
  const runs = new Map<string, ReviewRun>();
  const remove = (id: string) => {
    clearTimeout(runs.get(id)?.expiryTimer);
    runs.delete(id);
  };
  const retain = (id: string, entry: ReviewRun, expires: number) => {
    clearTimeout(entry.expiryTimer);
    entry.expires = expires;
    if (Number.isFinite(expires)) {
      entry.expiryTimer = setTimeout(
        () => {
          if (runs.get(id) === entry) remove(id);
        },
        Math.max(0, expires - Date.now()),
      );
      entry.expiryTimer.unref();
    }
  };
  const reserve = (
    id: string,
    principal: ReviewPrincipal,
    cancel: () => void,
    expires: number,
  ): ReviewRun => {
    for (const [key, entry] of runs) {
      if (entry.expires <= Date.now()) remove(key);
    }
    if (runs.size >= 1024) throw new ReviewWorkerError('busy');
    const entry: ReviewRun = { principal, cancel, cancelled: false, expires };
    runs.set(id, entry);
    retain(id, entry, expires);
    return entry;
  };

  return async (incoming) => {
    if (
      ![url, `${url}/cancel`, `${url}/status`].includes(incoming.url) ||
      incoming.method !== 'POST'
    ) {
      return failure(new ReviewWorkerError('invalid_request'));
    }
    if (!timingSafeEqual(credential, digest(incoming.headers.get('authorization') ?? ''))) {
      return failure(new ReviewWorkerError('forbidden'));
    }
    if (incoming.url === `${url}/status`) {
      const scope = deadline(incoming.signal, 10_000);
      try {
        const parsed = z
          .object({
            id: reviewRunIdSchema,
            request: reviewRequestSchema,
            principal: reviewPrincipalSchema,
          })
          .strict()
          .safeParse(await readJson(incoming, REQUEST_BYTES, scope.signal, 'invalid_request'));
        if (!parsed.success) throw new ReviewWorkerError('invalid_request');
        const { id, request, principal } = parsed.data;
        const entry = runs.get(id);
        const durable = journal ? await journal.get(id, principal) : undefined;
        const unknown = () =>
          Response.json({ id, state: 'unknown' }, { headers: { 'cache-control': 'no-store' } });
        if (journal) {
          if (!durable?.request) return unknown();
          if (!sameRequest(durable.request, request))
            throw new ReviewWorkerError('invalid_request');
          if (durable.model !== config.worker.model) throw new ReviewWorkerError('configuration');
          if (
            !config.worker.repositories.has(request.repository) ||
            (await interruptible(
              config.worker.authorize(principal, request.repository),
              scope.signal,
            )) !== true
          )
            throw new ReviewWorkerError('forbidden');
          journal.assertReady();
          let record: CodeReviewRecovery;
          if (durable.state === 'completed') {
            if (durable.expiresAt <= Date.now() || !durable.result) return unknown();
            if (
              !sameRequest(durable.result, request) ||
              durable.result.model !== config.worker.model
            )
              throw new ReviewWorkerError('invalid_response');
            record = {
              id,
              state: 'completed',
              request,
              result: durable.result,
              expiresAt: durable.expiresAt,
            };
          } else if (durable.state === 'cancelled') {
            if (durable.expiresAt <= Date.now()) return unknown();
            record = {
              id,
              state: 'failed',
              request,
              code: 'cancelled',
              expiresAt: durable.expiresAt,
            };
          } else if (durable.state === 'interrupted') {
            record = {
              id,
              state: 'interrupted',
              request,
              cancelRequested: durable.cancelRequested,
            };
          } else {
            record = { id, state: 'running', request, cancelRequested: durable.cancelRequested };
          }
          return Response.json(recoverySchema.parse(record), {
            headers: { 'cache-control': 'no-store' },
          });
        }
        if (!entry || entry.expires <= Date.now()) {
          if (entry) remove(id);
          return unknown();
        }
        if (
          entry.principal.userId !== principal.userId ||
          entry.principal.tenantId !== principal.tenantId ||
          !entry.request
        )
          return unknown();
        if (!sameRequest(entry.request, request)) throw new ReviewWorkerError('invalid_request');
        const allowed =
          config.worker.repositories.has(request.repository) &&
          (await interruptible(
            config.worker.authorize(principal, request.repository),
            scope.signal,
          ));
        if (allowed !== true) throw new ReviewWorkerError('forbidden');
        if (runs.get(id) !== entry) return unknown();
        if (entry.expires <= Date.now()) {
          remove(id);
          return unknown();
        }
        let record: CodeReviewRecovery = {
          id,
          state: 'running',
          request: entry.request,
          cancelRequested: entry.cancelled,
        };
        if (Number.isFinite(entry.expires) && entry.result) {
          record = {
            id,
            state: 'completed',
            request: entry.request,
            result: entry.result,
            expiresAt: entry.expires,
          };
        } else if (Number.isFinite(entry.expires) && entry.code) {
          record = {
            id,
            state: 'failed',
            request: entry.request,
            code: entry.code,
            expiresAt: entry.expires,
          };
        }
        const body = JSON.stringify(recoverySchema.parse(record));
        if (Buffer.byteLength(body) > RESPONSE_BYTES + REQUEST_BYTES)
          throw new ReviewWorkerError('output_limit');
        return new Response(body, {
          headers: { 'content-type': 'application/json', 'cache-control': 'no-store' },
        });
      } catch (error) {
        return failure(
          error instanceof ReviewWorkerError ? error : new ReviewWorkerError('forbidden'),
        );
      } finally {
        scope.close();
      }
    }
    if (incoming.url === `${url}/cancel`) {
      const scope = deadline(incoming.signal, 10_000);
      try {
        const parsed = z
          .object({ id: reviewRunIdSchema, principal: reviewPrincipalSchema })
          .strict()
          .safeParse(await readJson(incoming, REQUEST_BYTES, scope.signal, 'invalid_request'));
        if (!parsed.success) throw new ReviewWorkerError('invalid_request');
        const { id, principal } = parsed.data;
        if (journal) {
          try {
            await journal.cancel(id, principal);
          } catch (error) {
            const activeEntry = runs.get(id);
            if (
              activeEntry?.principal.userId === principal.userId &&
              activeEntry.principal.tenantId === principal.tenantId
            )
              activeEntry.cancel();
            throw error;
          }
        }
        if ((runs.get(id)?.expires ?? Infinity) <= Date.now()) remove(id);
        const entry = runs.get(id) ?? reserve(id, principal, () => undefined, Date.now() + 600_000);
        if (
          entry.principal.userId !== principal.userId ||
          entry.principal.tenantId !== principal.tenantId
        )
          throw new ReviewWorkerError('forbidden');
        if (!entry.request && Number.isFinite(entry.expires))
          retain(id, entry, Date.now() + 600_000);
        entry.cancelled = true;
        entry.cancel();
        return Response.json({ cancelled: true }, { headers: { 'cache-control': 'no-store' } });
      } catch (error) {
        return failure(
          error instanceof ReviewWorkerError ? error : new ReviewWorkerError('worker_failed'),
        );
      } finally {
        scope.close();
      }
    }
    if (journal) {
      try {
        journal.assertReady();
      } catch {
        return failure(new ReviewWorkerError('configuration'));
      }
    }
    if (active) return failure(new ReviewWorkerError('busy'));
    if (incoming.signal.aborted) return failure(new ReviewWorkerError('cancelled'));
    active = true;
    const idHeader = incoming.headers.get('x-review-id');
    if (
      (journal && idHeader === null) ||
      (idHeader !== null && !reviewRunIdSchema.safeParse(idHeader).success)
    ) {
      active = false;
      return failure(new ReviewWorkerError('invalid_request'));
    }
    const scope = deadline(idHeader ? undefined : incoming.signal, SERVICE_TIMEOUT_MS);
    let admitted: ReturnType<typeof reserve> | undefined;
    let persisted = false;
    journal?.signal.addEventListener('abort', scope.cancel, { once: true });
    const operation = (async () => {
      const envelope = envelopeSchema.safeParse(
        await readJson(incoming, REQUEST_BYTES, scope.signal, 'invalid_request'),
      );
      if (!envelope.success) throw new ReviewWorkerError('invalid_request');
      if (incoming.signal.aborted) throw new ReviewWorkerError('cancelled');
      if (idHeader) {
        const previous = runs.get(idHeader);
        if (previous && previous.expires > Date.now()) {
          if (
            previous.principal.userId !== envelope.data.principal.userId ||
            previous.principal.tenantId !== envelope.data.principal.tenantId
          )
            throw new ReviewWorkerError('forbidden');
          if (previous.request && !sameRequest(previous.request, envelope.data.request))
            throw new ReviewWorkerError('invalid_request');
          throw new ReviewWorkerError(previous.cancelled ? 'cancelled' : 'busy');
        }
        const retained = [...runs.values()].filter(
          (entry) => entry.request && entry.expires > Date.now(),
        ).length;
        if (retained >= 64) throw new ReviewWorkerError('busy');
        if (journal) {
          if (
            !config.worker.repositories.has(envelope.data.request.repository) ||
            (await interruptible(
              config.worker.authorize(envelope.data.principal, envelope.data.request.repository),
              scope.signal,
            )) !== true
          )
            throw new ReviewWorkerError('forbidden');
          const created = await journal.admit(
            idHeader,
            envelope.data.request,
            envelope.data.principal,
            config.worker.model,
          );
          journal.assertReady();
          if (!created) throw new ReviewWorkerError('busy');
          persisted = true;
        }
        admitted = reserve(idHeader, envelope.data.principal, scope.cancel, Infinity);
        admitted.request = envelope.data.request;
      }
      const result = await worker.run(envelope.data.request, envelope.data.principal, scope.signal);
      const validated = reviewResultSchema.parse(result);
      const body = JSON.stringify(validated);
      if (Buffer.byteLength(body) > RESPONSE_BYTES) throw new ReviewWorkerError('output_limit');
      if (journal && idHeader && admitted) {
        const completed = await journal.finish(idHeader, admitted.principal, validated);
        persisted = false;
        if (!completed) throw new ReviewWorkerError('cancelled');
      }
      if (admitted && !admitted.code) admitted.result = validated;
      return new Response(body, {
        headers: { 'content-type': 'application/json', 'cache-control': 'no-store' },
      });
    })()
      .catch(async (error) => {
        if (journal && persisted && admitted && idHeader) {
          try {
            await journal.finish(idHeader, admitted.principal);
          } catch {
            throw new ReviewWorkerError('configuration');
          }
        }
        if (admitted && !admitted.code)
          admitted.code = error instanceof ReviewWorkerError ? error.code : 'worker_failed';
        throw error;
      })
      .finally(() => {
        if (admitted && idHeader) retain(idHeader, admitted, Date.now() + 600_000);
        active = false;
        journal?.signal.removeEventListener('abort', scope.cancel);
      });
    try {
      return await interruptible(operation, scope.signal);
    } catch (error) {
      const failureError =
        error instanceof ReviewWorkerError ? error : new ReviewWorkerError('worker_failed');
      if (admitted && !admitted.result) admitted.code = failureError.code;
      return failure(failureError);
    } finally {
      scope.close();
    }
  };
}

export interface ReviewClient extends CodeReviewWorker {
  run(
    input: CodeReviewRequest,
    principal: ReviewPrincipal,
    signal?: AbortSignal,
    id?: string,
  ): Promise<CodeReviewResult>;
  cancel(id: string, principal: ReviewPrincipal): Promise<void>;
  status(
    id: string,
    input: CodeReviewRequest,
    principal: ReviewPrincipal,
  ): Promise<CodeReviewRecovery>;
}

/** Caller must derive principal from authenticated server context, never request JSON. */
export function createReviewClient(config: ReviewClientConfig): ReviewClient {
  const enabled = config.enabled === true;
  const url = enabled ? validateTransport(config) : '';
  const token = config.token;
  const model = config.model;
  const send = config.send ?? ((request: Request) => fetch(request));
  return {
    async status(id, input, principal) {
      if (!enabled) throw new ReviewWorkerError('configuration');
      const envelope = z
        .object({
          id: reviewRunIdSchema,
          request: reviewRequestSchema,
          principal: reviewPrincipalSchema,
        })
        .strict()
        .safeParse({ id, request: input, principal });
      if (!envelope.success) throw new ReviewWorkerError('invalid_request');
      const requested = envelope.data.request;
      const scope = deadline(undefined, 10_000);
      try {
        const response = await interruptible(
          send(
            new Request(`${url}/status`, {
              method: 'POST',
              redirect: 'error',
              signal: scope.signal,
              headers: { authorization: `Bearer ${token}`, 'content-type': 'application/json' },
              body: JSON.stringify(envelope.data),
            }),
          ),
          scope.signal,
        );
        const body = await readJson(
          response,
          RESPONSE_BYTES + REQUEST_BYTES,
          scope.signal,
          'invalid_response',
        );
        if (response.status !== 200) {
          const parsed = errorSchema.safeParse(body);
          if (!parsed.success || reviewFailureStatus[parsed.data.code] !== response.status)
            throw new ReviewWorkerError('invalid_response');
          throw new ReviewWorkerError(parsed.data.code);
        }
        const parsed = recoverySchema.safeParse(body);
        if (
          !parsed.success ||
          parsed.data.id !== id ||
          (parsed.data.state !== 'unknown' && !sameRequest(parsed.data.request, requested)) ||
          (parsed.data.state === 'completed' &&
            (!sameRequest(parsed.data.result, requested) || parsed.data.result.model !== model))
        )
          throw new ReviewWorkerError('invalid_response');
        return parsed.data;
      } catch (error) {
        if (scope.signal.aborted) throw aborted(scope.signal);
        throw error instanceof ReviewWorkerError ? error : new ReviewWorkerError('worker_failed');
      } finally {
        scope.close();
      }
    },
    async cancel(id, principal) {
      if (!enabled) throw new ReviewWorkerError('configuration');
      if (
        !reviewRunIdSchema.safeParse(id).success ||
        !reviewPrincipalSchema.safeParse(principal).success
      )
        throw new ReviewWorkerError('invalid_request');
      const scope = deadline(undefined, 10_000);
      try {
        const response = await interruptible(
          send(
            new Request(`${url}/cancel`, {
              method: 'POST',
              redirect: 'error',
              signal: scope.signal,
              headers: { authorization: `Bearer ${token}`, 'content-type': 'application/json' },
              body: JSON.stringify({ id, principal }),
            }),
          ),
          scope.signal,
        );
        const body = await readJson(response, RESPONSE_BYTES, scope.signal, 'invalid_response');
        if (
          response.status === 200 &&
          z
            .object({ cancelled: z.literal(true) })
            .strict()
            .safeParse(body).success
        )
          return;
        const error = errorSchema.safeParse(body);
        if (error.success && reviewFailureStatus[error.data.code] === response.status)
          throw new ReviewWorkerError(error.data.code);
        throw new ReviewWorkerError('invalid_response');
      } catch (error) {
        if (scope.signal.aborted) throw aborted(scope.signal);
        throw error instanceof ReviewWorkerError ? error : new ReviewWorkerError('worker_failed');
      } finally {
        scope.close();
      }
    },
    async run(
      input: CodeReviewRequest,
      principal: ReviewPrincipal,
      signal?: AbortSignal,
      id?: string,
    ): Promise<CodeReviewResult> {
      if (!enabled) throw new ReviewWorkerError('configuration');
      const envelope = envelopeSchema.safeParse({ request: input, principal });
      if (!envelope.success) throw new ReviewWorkerError('invalid_request');
      if (id !== undefined && !reviewRunIdSchema.safeParse(id).success)
        throw new ReviewWorkerError('invalid_request');
      const requested = envelope.data.request;
      const scope = deadline(signal, CLIENT_TIMEOUT_MS);
      try {
        if (scope.signal.aborted) throw aborted(scope.signal);
        const response = await interruptible(
          send(
            new Request(url, {
              method: 'POST',
              redirect: 'error',
              signal: scope.signal,
              headers: {
                authorization: `Bearer ${token}`,
                'content-type': 'application/json',
                ...(id ? { 'x-review-id': id } : {}),
              },
              body: JSON.stringify(envelope.data),
            }),
          ),
          scope.signal,
        );
        const raw = await readJson(response, RESPONSE_BYTES, scope.signal, 'invalid_response');
        if (!response.ok) {
          const parsed = errorSchema.safeParse(raw);
          if (!parsed.success || reviewFailureStatus[parsed.data.code] !== response.status) {
            throw new ReviewWorkerError('invalid_response');
          }
          throw new ReviewWorkerError(parsed.data.code);
        }
        const parsed = reviewResultSchema.safeParse(raw);
        if (
          response.status !== 200 ||
          !parsed.success ||
          !sameRequest(parsed.data, requested) ||
          parsed.data.model !== model
        ) {
          throw new ReviewWorkerError('invalid_response');
        }
        return parsed.data;
      } catch (error) {
        if (scope.signal.aborted) throw aborted(scope.signal);
        if (error instanceof ReviewWorkerError) throw error;
        throw new ReviewWorkerError('worker_failed');
      } finally {
        scope.close();
      }
    },
  };
}
