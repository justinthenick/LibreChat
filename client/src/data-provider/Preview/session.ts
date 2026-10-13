import type { PreviewJob, PreviewReply, PreviewStartRequest } from 'librechat-data-provider';

export const PREVIEW_STORAGE_PREFIX = 'librechat.preview.';
export type PreviewSession = {
  request: PreviewStartRequest;
  generation: string;
  jobId?: string;
};

export function readSession(owner: string): PreviewSession | null {
  try {
    const value: PreviewSession | null = JSON.parse(
      sessionStorage.getItem(PREVIEW_STORAGE_PREFIX + owner) ?? 'null',
    );
    if (
      !value ||
      !/^preview:[a-f0-9]{64}$/.test(value.generation) ||
      typeof value.request?.prompt !== 'string' ||
      typeof value.request.idempotency_key !== 'string' ||
      !/^[A-Za-z0-9][A-Za-z0-9_.:@-]{0,127}$/.test(value.request.scope?.repository_alias) ||
      value.request.scope.task_mode !== 'read_only' ||
      value.request.max_requests !== 10 ||
      value.request.timeout_seconds !== 300 ||
      (value.jobId !== undefined && !/^[a-f0-9]{32}$/.test(value.jobId))
    ) {
      return null;
    }
    return value;
  } catch {
    return null;
  }
}

export function writeSession(owner: string, session: PreviewSession | null): void {
  const key = PREVIEW_STORAGE_PREFIX + owner;
  if (session) sessionStorage.setItem(key, JSON.stringify(session));
  else sessionStorage.removeItem(key);
}

export async function newSession(prompt: string, repository: string): Promise<PreviewSession> {
  const key = crypto.randomUUID();
  const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(key));
  const digest = Array.from(new Uint8Array(hash), (byte) =>
    byte.toString(16).padStart(2, '0'),
  ).join('');
  return {
    generation: `preview:${digest}`,
    request: {
      prompt,
      idempotency_key: key,
      scope: { repository_alias: repository, task_mode: 'read_only' },
      max_requests: 10,
      timeout_seconds: 300,
    },
  };
}

export function acceptJob(
  reply: PreviewReply,
  session: PreviewSession,
  previous?: PreviewJob,
): PreviewJob {
  if (reply.version !== 1 || !reply.ok) throw new Error('preview_unavailable');
  const job = reply.job;
  if (
    !/^[a-f0-9]{32}$/.test(job.job_id) ||
    (session.jobId !== undefined && job.job_id !== session.jobId) ||
    job.generation_id !== session.generation ||
    job.generation_epoch !== 0 ||
    job.metadata.repository_alias !== session.request.scope.repository_alias ||
    job.metadata.task_mode !== session.request.scope.task_mode ||
    job.metadata.max_requests !== session.request.max_requests ||
    job.metadata.timeout_seconds !== session.request.timeout_seconds ||
    (previous !== undefined &&
      (job.updated_at < previous.updated_at ||
        (settled(previous) && job.state !== previous.state) ||
        (previous.state === 'cancelling' && ['queued', 'running'].includes(job.state))))
  ) {
    throw new Error('preview_identity');
  }
  return job;
}

export function settled(job?: PreviewJob): boolean {
  return (
    job !== undefined &&
    ['completed', 'failed', 'cancelled', 'timed_out', 'interrupted'].includes(job.state) &&
    job.error_code !== 'execution_stop_unconfirmed' &&
    job.error_code !== 'job_monitor_interrupted'
  );
}
