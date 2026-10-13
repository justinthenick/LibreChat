export type PreviewPrincipal = Readonly<{ user_id: string; tenant_id: string }>;
export type PreviewScope = Readonly<{
  repository_alias: string;
  task_mode: 'read_only' | 'modification';
}>;
export type PreviewStartRequest = {
  prompt: string;
  idempotency_key: string;
  scope: PreviewScope;
  max_requests: number;
  timeout_seconds: number;
};
export type PreviewJobMessage =
  | { version: 1; operation: 'start'; request: PreviewStartRequest }
  | { version: 1; operation: 'get' | 'cancel'; request: { job_id: string } };
export type PreviewErrorCode =
  | 'invalid_job_message'
  | 'authenticated_principal_required'
  | 'preview_jobs_disabled'
  | 'scope_not_authorized'
  | 'job_not_found'
  | 'job_busy'
  | 'idempotency_conflict'
  | 'stale_generation'
  | 'worker_start_failed'
  | 'admission_deadline_exceeded'
  | 'job_service_unavailable';
export type PreviewState =
  | 'queued'
  | 'running'
  | 'cancelling'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'timed_out'
  | 'interrupted';
export type PreviewProof = {
  action_id: string;
  tool_call_id: string;
  started: number;
  completed: number;
};
export type PreviewTask = {
  task_id: string;
  branch: string;
  task_branch: string;
  task_mode: PreviewScope['task_mode'];
  source_repository: string;
  source_ref: string;
  source_branch: string;
  source_commit: string;
  source_status: string;
};
export type PreviewEvidence = {
  repository_alias: string;
  task: PreviewTask | null;
  checks: Array<
    PreviewProof & {
      command: string;
      exit_code: number;
      truncated: boolean;
      stdout_sha256: string;
      stderr_sha256: string;
    }
  >;
  final_diff: (PreviewProof & { text: string; sha256: string }) | null;
  final_status: (PreviewProof & { task_id: string; branch: string; status: string }) | null;
  observed_checks_status: 'not_run' | 'passed' | 'failed' | 'incomplete';
  evidence_complete: boolean;
  action_count: number;
  pending_count: number;
  errors: string[];
};
export type PreviewJob = {
  job_id: string;
  generation_id: string;
  generation_epoch: number;
  state: PreviewState;
  created_at: number;
  updated_at: number;
  deadline_at: number;
  metadata: PreviewScope & {
    profile_id: string;
    model: 'gpt-5.6-sol';
    max_requests: number;
    timeout_seconds: number;
  };
  result: {
    execution_status?: 'finished' | 'failed' | 'paused' | 'interrupted';
    final_response?: string;
    evidence: PreviewEvidence;
  } | null;
  error_code: string | null;
  request_count: number;
};
export type PreviewReply =
  | { version: 1; ok: true; job: PreviewJob }
  | { version: 1; ok: false; error: PreviewErrorCode };
