import { createHash } from 'node:crypto';
import type { Request, RequestHandler } from 'express';
import type {
  PreviewAuthorizationContext,
  PreviewErrorCode,
  PreviewHandlers,
  PreviewJob,
  PreviewJobMessage,
  PreviewOptions,
  PreviewPrincipal,
  PreviewReply,
  PreviewScope,
  PreviewStartRequest,
} from './types';

type Json = null | string | boolean | number | Json[] | { [key: string]: Json };
type ObjectValue = { [key: string]: Json };
type AuthenticatedRequest = Request & { user?: { id?: string; tenantId?: string } };
const INPUT_LIMIT = 40960;
const OUTPUT_LIMIT = 262144;
const ID = /^[A-Za-z0-9][A-Za-z0-9_.:@-]{0,127}$/;
const JOB_ID = /^[0-9a-f]{32}$/;
const HASH = /^[0-9a-f]{64}$/;
const ERROR_STATUS: Record<PreviewErrorCode, number> = {
  invalid_job_message: 400,
  authenticated_principal_required: 401,
  preview_jobs_disabled: 404,
  scope_not_authorized: 403,
  job_not_found: 404,
  job_busy: 409,
  idempotency_conflict: 409,
  stale_generation: 409,
  worker_start_failed: 503,
  admission_deadline_exceeded: 504,
  job_service_unavailable: 503,
};
const JOB_ERRORS = new Set([
  'cancel_requested',
  'cancelled',
  'deadline_exceeded',
  'worker_limit',
  'worker_failed',
  'worker_start_failed',
  'worker_interrupted',
  'restart_interrupted',
  'invalid_profile_result',
  'execution_stop_unconfirmed',
  'job_monitor_interrupted',
]);
const EVIDENCE_ERRORS = new Set([
  'invalid_repository',
  'invalid_action_limit',
  'malformed_payload',
  'payload_too_large',
  'unexpected_tool',
  'invalid_identity',
  'duplicate_action',
  'action_limit',
  'malformed_arguments',
  'task_identity_mismatch',
  'invalid_task_metadata',
  'unmatched_observation',
  'duplicate_observation',
  'observation_mismatch',
  'tool_error',
  'invalid_check',
  'action_mismatch',
  'malformed_action',
  'malformed_observation',
]);
const PROOF_KEYS = ['action_id', 'tool_call_id', 'started', 'completed'];

class BoundaryError extends Error {
  constructor(
    readonly code: PreviewErrorCode,
    readonly status = ERROR_STATUS[code],
  ) {
    super(code);
  }
}
function requireValue(condition: boolean): asserts condition {
  if (!condition) throw new BoundaryError('invalid_job_message');
}
function object(value: Json): value is ObjectValue {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}
function keys(value: Json, required: string[], optional: string[] = []): value is ObjectValue {
  return (
    object(value) &&
    required.every((key) => Object.hasOwn(value, key)) &&
    Object.keys(value).every((key) => required.includes(key) || optional.includes(key))
  );
}
function text(value: Json, maximum: number): value is string {
  return typeof value === 'string' && Buffer.byteLength(value, 'utf8') <= maximum;
}
function identifier(value: Json): value is string {
  return typeof value === 'string' && ID.test(value);
}
function number(value: Json, maximum: number, minimum = 0): value is number {
  return (
    typeof value === 'number' && Number.isFinite(value) && value >= minimum && value <= maximum
  );
}
function integer(value: Json, maximum: number, minimum = 0): value is number {
  return number(value, maximum, minimum) && Number.isSafeInteger(value);
}
function member(value: Json, choices: readonly string[]): value is string {
  return typeof value === 'string' && choices.includes(value);
}
function json(value: unknown, depth = 0): value is Json {
  if (depth > 16) return false;
  if (value === null || typeof value === 'boolean') return true;
  if (typeof value === 'string') return Buffer.from(value, 'utf8').toString('utf8') === value;
  if (typeof value === 'number') return Number.isFinite(value);
  if (typeof value !== 'object') return false;
  if (Array.isArray(value))
    return (
      Object.getPrototypeOf(value) === Array.prototype &&
      Reflect.ownKeys(value).length === value.length + 1 &&
      Array.from(value).every((child: unknown) => json(child, depth + 1))
    );
  if (Object.getPrototypeOf(value) !== Object.prototype && Object.getPrototypeOf(value) !== null)
    return false;
  return Reflect.ownKeys(value).every((key) => {
    const descriptor = Object.getOwnPropertyDescriptor(value, key);
    return (
      typeof key === 'string' &&
      !['__proto__', 'constructor', 'prototype'].includes(key) &&
      descriptor !== undefined &&
      descriptor.enumerable === true &&
      'value' in descriptor &&
      json(descriptor.value, depth + 1)
    );
  });
}
function boundary(value: unknown, maximum: number): Json {
  requireValue(json(value));
  const encoded = JSON.stringify(value);
  requireValue(Buffer.byteLength(encoded, 'utf8') <= maximum);
  return JSON.parse(encoded) as Json;
}
function scope(value: Json): asserts value is PreviewScope {
  requireValue(
    keys(value, ['repository_alias', 'task_mode']) &&
      identifier(value.repository_alias) &&
      member(value.task_mode, ['read_only', 'modification']),
  );
}
function startRequest(raw: unknown): PreviewStartRequest {
  const value = boundary(raw, INPUT_LIMIT);
  requireValue(
    keys(value, ['prompt', 'idempotency_key', 'scope'], ['max_requests', 'timeout_seconds']),
  );
  requireValue(
    text(value.prompt, 32768) &&
      value.prompt.trim().length > 0 &&
      identifier(value.idempotency_key),
  );
  scope(value.scope);
  const max_requests = value.max_requests === undefined ? 10 : value.max_requests;
  const timeout_seconds = value.timeout_seconds === undefined ? 300 : value.timeout_seconds;
  requireValue(integer(max_requests, 10, 1) && number(timeout_seconds, 300) && timeout_seconds > 0);
  return Object.freeze({
    prompt: value.prompt,
    idempotency_key: value.idempotency_key,
    scope: Object.freeze({ ...value.scope }),
    max_requests,
    timeout_seconds,
  });
}
function proof(value: ObjectValue): void {
  requireValue(
    typeof value.action_id === 'string' &&
      /^[A-Za-z0-9_.:-]{1,128}$/.test(value.action_id) &&
      typeof value.tool_call_id === 'string' &&
      /^[A-Za-z0-9_.:-]{1,128}$/.test(value.tool_call_id) &&
      integer(value.started, 64, 1) &&
      integer(value.completed, 64, 1) &&
      value.completed > value.started,
  );
}
function evidence(value: Json, expected: PreviewScope): void {
  requireValue(
    keys(value, [
      'repository_alias',
      'task',
      'checks',
      'final_diff',
      'final_status',
      'observed_checks_status',
      'evidence_complete',
      'action_count',
      'pending_count',
      'errors',
    ]),
  );
  requireValue(
    value.repository_alias === expected.repository_alias &&
      member(value.observed_checks_status, ['not_run', 'passed', 'failed', 'incomplete']) &&
      typeof value.evidence_complete === 'boolean' &&
      integer(value.action_count, 32) &&
      integer(value.pending_count, value.action_count) &&
      Array.isArray(value.errors) &&
      value.errors.every((code) => typeof code === 'string' && EVIDENCE_ERRORS.has(code)),
  );
  const task = value.task;
  if (task !== null) {
    requireValue(
      keys(task, [
        'task_id',
        'branch',
        'task_branch',
        'task_mode',
        'source_repository',
        'source_ref',
        'source_branch',
        'source_commit',
        'source_status',
      ]),
    );
    requireValue(
      text(task.task_id, 80) &&
        /^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$/.test(task.task_id) &&
        !task.task_id.includes('..') &&
        task.branch === `agent/${task.task_id}` &&
        task.task_branch === task.branch &&
        task.task_mode === expected.task_mode &&
        task.source_repository === expected.repository_alias &&
        text(task.source_ref, 200) &&
        text(task.source_branch, 200) &&
        typeof task.source_commit === 'string' &&
        /^[0-9a-fA-F]{40}$/.test(task.source_commit) &&
        task.source_status === '',
    );
  }
  requireValue(Array.isArray(value.checks) && value.checks.length <= 32);
  for (const check of value.checks) {
    requireValue(
      keys(check, [
        ...PROOF_KEYS,
        'command',
        'exit_code',
        'truncated',
        'stdout_sha256',
        'stderr_sha256',
      ]),
    );
    proof(check);
    requireValue(
      text(check.command, 512) &&
        check.command.length > 0 &&
        integer(check.exit_code, 255, -255) &&
        typeof check.truncated === 'boolean' &&
        typeof check.stdout_sha256 === 'string' &&
        HASH.test(check.stdout_sha256) &&
        typeof check.stderr_sha256 === 'string' &&
        HASH.test(check.stderr_sha256),
    );
  }
  if (value.final_diff !== null) {
    requireValue(keys(value.final_diff, [...PROOF_KEYS, 'text', 'sha256']));
    proof(value.final_diff);
    requireValue(
      text(value.final_diff.text, 65536) &&
        typeof value.final_diff.sha256 === 'string' &&
        HASH.test(value.final_diff.sha256) &&
        createHash('sha256').update(value.final_diff.text).digest('hex') ===
          value.final_diff.sha256,
    );
  }
  if (value.final_status !== null) {
    requireValue(keys(value.final_status, [...PROOF_KEYS, 'task_id', 'branch', 'status']));
    proof(value.final_status);
    requireValue(
      object(task) &&
        value.final_status.task_id === task.task_id &&
        value.final_status.branch === task.branch &&
        text(value.final_status.status, 4096),
    );
  }
}
function job(value: Json): asserts value is PreviewJob {
  requireValue(
    keys(value, [
      'job_id',
      'generation_id',
      'generation_epoch',
      'state',
      'created_at',
      'updated_at',
      'deadline_at',
      'metadata',
      'result',
      'error_code',
      'request_count',
    ]),
  );
  requireValue(
    typeof value.job_id === 'string' &&
      JOB_ID.test(value.job_id) &&
      typeof value.generation_id === 'string' &&
      /^preview:[0-9a-f]{64}$/.test(value.generation_id) &&
      value.generation_epoch === 0 &&
      member(value.state, [
        'queued',
        'running',
        'cancelling',
        'completed',
        'failed',
        'cancelled',
        'timed_out',
        'interrupted',
      ]),
  );
  requireValue(
    number(value.created_at, Number.MAX_SAFE_INTEGER) &&
      number(value.updated_at, Number.MAX_SAFE_INTEGER) &&
      number(value.deadline_at, Number.MAX_SAFE_INTEGER) &&
      value.updated_at >= value.created_at &&
      value.deadline_at >= value.created_at,
  );
  const metadata = value.metadata;
  requireValue(
    keys(metadata, [
      'profile_id',
      'repository_alias',
      'task_mode',
      'model',
      'max_requests',
      'timeout_seconds',
    ]),
  );
  const jobScope = { repository_alias: metadata.repository_alias, task_mode: metadata.task_mode };
  scope(jobScope);
  requireValue(
    identifier(metadata.profile_id) &&
      metadata.model === 'gpt-5.6-sol' &&
      integer(metadata.max_requests, 10, 1) &&
      number(metadata.timeout_seconds, 300) &&
      metadata.timeout_seconds > 0 &&
      integer(value.request_count, metadata.max_requests) &&
      (value.error_code === null ||
        (typeof value.error_code === 'string' && JOB_ERRORS.has(value.error_code))),
  );
  if (value.result === null) {
    requireValue(value.state !== 'completed');
    return;
  }
  requireValue(keys(value.result, ['evidence'], ['execution_status', 'final_response']));
  requireValue(
    value.result.execution_status === undefined ||
      member(value.result.execution_status, ['finished', 'failed', 'paused', 'interrupted']),
  );
  requireValue(
    value.result.final_response === undefined || text(value.result.final_response, 8192),
  );
  requireValue(Buffer.byteLength(JSON.stringify(value.result), 'utf8') <= 131072);
  requireValue(value.state !== 'completed' || value.result.execution_status === 'finished');
  evidence(value.result.evidence, jobScope);
}
function reply(raw: unknown): PreviewReply {
  try {
    const value = boundary(raw, OUTPUT_LIMIT);
    requireValue(object(value) && value.version === 1);
    if (value.ok === false) {
      requireValue(
        keys(value, ['version', 'ok', 'error']) &&
          typeof value.error === 'string' &&
          Object.hasOwn(ERROR_STATUS, value.error),
      );
      return { version: 1, ok: false, error: value.error as PreviewErrorCode };
    }
    requireValue(keys(value, ['version', 'ok', 'job']) && value.ok === true);
    job(value.job);
    return { version: 1, ok: true, job: value.job };
  } catch {
    throw new BoundaryError('job_service_unavailable', 502);
  }
}
async function bounded<T>(operation: () => Promise<T>, timeoutMs: number): Promise<T> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  try {
    return await Promise.race([
      Promise.resolve().then(operation),
      new Promise<never>((_resolve, reject) => {
        timer = setTimeout(
          () => reject(new BoundaryError('job_service_unavailable', 504)),
          timeoutMs,
        );
      }),
    ]);
  } finally {
    if (timer !== undefined) clearTimeout(timer);
  }
}

/** Standalone preview control only; transport failures never imply execution stopped. */
export function createPreviewJobHandlers(options: PreviewOptions = {}): PreviewHandlers {
  const { enabled = false, transport, authorize, timeoutMs = 5000 } = options;
  const handler =
    (operation: 'start' | 'get' | 'cancel' | 'unsupported'): RequestHandler =>
    async (req, res) => {
      res.set('Cache-Control', 'no-store');
      try {
        const user = (req as AuthenticatedRequest).user;
        if (
          !user ||
          typeof user.id !== 'string' ||
          !identifier(user.id) ||
          (user.tenantId !== undefined && user.tenantId !== '' && !identifier(user.tenantId))
        )
          throw new BoundaryError('authenticated_principal_required');
        const principal: PreviewPrincipal = Object.freeze({
          user_id: user.id,
          tenant_id: user.tenantId ?? '',
        });
        if (enabled !== true) throw new BoundaryError('preview_jobs_disabled');
        if (
          !transport ||
          typeof transport.exchange !== 'function' ||
          typeof authorize !== 'function' ||
          !Number.isSafeInteger(timeoutMs) ||
          timeoutMs <= 0 ||
          timeoutMs > 30000
        ) {
          throw new BoundaryError('job_service_unavailable');
        }
        if (operation === 'unsupported') throw new BoundaryError('invalid_job_message', 405);
        requireValue(Object.keys(req.query).length === 0);
        const contentLength = req.get('content-length');
        requireValue(
          contentLength === undefined ||
            (/^\d+$/.test(contentLength) && Number(contentLength) <= INPUT_LIMIT),
        );
        const authorizeScope = async (
          expected: PreviewScope,
          context: PreviewAuthorizationContext,
        ): Promise<void> => {
          const allowed = await bounded(() => authorize(principal, expected, context), timeoutMs);
          if (allowed !== true) throw new BoundaryError('scope_not_authorized');
        };
        const exchange = async (payload: PreviewJobMessage): Promise<PreviewJob> => {
          boundary(payload, INPUT_LIMIT);
          const result = reply(
            await bounded(() => transport.exchange({ principal, payload }), timeoutMs),
          );
          if (!result.ok) throw new BoundaryError(result.error);
          return result.job;
        };
        let result: PreviewJob;
        if (operation === 'start') {
          const request = startRequest(req.body);
          await authorizeScope(request.scope, { operation, request });
          result = await exchange({ version: 1, operation, request });
          if (
            result.generation_id !==
              `preview:${createHash('sha256').update(request.idempotency_key).digest('hex')}` ||
            result.metadata.repository_alias !== request.scope.repository_alias ||
            result.metadata.task_mode !== request.scope.task_mode ||
            result.metadata.max_requests !== request.max_requests ||
            result.metadata.timeout_seconds !== request.timeout_seconds
          ) {
            throw new BoundaryError('job_service_unavailable', 502);
          }
        } else {
          requireValue(req.body === undefined || keys(boundary(req.body, INPUT_LIMIT), []));
          requireValue(
            req.body !== undefined ||
              ((contentLength === undefined || Number(contentLength) === 0) &&
                req.get('transfer-encoding') === undefined),
          );
          const jobId = req.params.jobId;
          requireValue(typeof jobId === 'string' && JOB_ID.test(jobId));
          result = await exchange({ version: 1, operation: 'get', request: { job_id: jobId } });
          if (result.job_id !== jobId) throw new BoundaryError('job_service_unavailable', 502);
          const expected = Object.freeze({
            repository_alias: result.metadata.repository_alias,
            task_mode: result.metadata.task_mode,
          });
          await authorizeScope(expected, { operation });
          if (operation === 'cancel') {
            const before = result;
            result = await exchange({ version: 1, operation, request: { job_id: jobId } });
            if (
              result.job_id !== jobId ||
              result.generation_id !== before.generation_id ||
              result.metadata.repository_alias !== expected.repository_alias ||
              result.metadata.task_mode !== expected.task_mode
            ) {
              throw new BoundaryError('job_service_unavailable', 502);
            }
          }
        }
        res.status(200).json({ version: 1, ok: true, job: result });
      } catch (error) {
        const failure =
          error instanceof BoundaryError ? error : new BoundaryError('job_service_unavailable');
        res.status(failure.status).json({ version: 1, ok: false, error: failure.code });
      }
    };
  return {
    start: handler('start'),
    get: handler('get'),
    cancel: handler('cancel'),
    unsupported: handler('unsupported'),
  };
}
