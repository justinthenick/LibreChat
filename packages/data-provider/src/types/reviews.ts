export interface CodeReviewRequest {
  repository: string;
  base: string;
  head: string;
  pullRequest?: { number: number; repositoryId: number };
}

export interface CodeReviewFinding {
  severity: 'blocker' | 'major' | 'minor';
  path: string;
  line: number;
  title: string;
  evidence: string;
  recommendation: string;
}

export interface CodeReviewResult extends CodeReviewRequest {
  status: 'human_review_required';
  provider: 'chatgpt_subscription';
  model: string;
  findings: CodeReviewFinding[];
  /** App route rechecked PR identity immediately before returning this result. */
  prCheckedAt?: string;
}

export type CodeReviewFailure =
  | 'stale_review'
  | 'invalid_request'
  | 'forbidden'
  | 'busy'
  | 'cancelled'
  | 'timeout'
  | 'output_limit'
  | 'worker_failed'
  | 'invalid_response'
  | 'configuration';

/** Unknown or interrupted never authorizes resubmission. Durable storage is opt-in. */
export type CodeReviewRecovery =
  | { id: string; state: 'unknown' }
  | { id: string; state: 'interrupted'; request: CodeReviewRequest; cancelRequested: boolean }
  | { id: string; state: 'running'; request: CodeReviewRequest; cancelRequested: boolean }
  | {
      id: string;
      state: 'completed';
      request: CodeReviewRequest;
      result: CodeReviewResult;
      expiresAt: number;
    }
  | {
      id: string;
      state: 'failed';
      request: CodeReviewRequest;
      code: CodeReviewFailure;
      expiresAt: number;
    };

/** Safe per-session discovery; never includes service credentials or filesystem paths. */
export interface CodeReviewConfig {
  enabled: boolean;
  repositories: string[];
}

/** A point-in-time lookup, not a lease or authorization to publish/run a review. */
export interface CodeReviewSelection {
  request: CodeReviewRequest;
  pullRequest: number;
  status: 'resolved' | 'current' | 'stale' | 'closed';
  checkedAt: string;
}

export interface CodeReviewSelectionRequest {
  repository: string;
  pullRequest: number;
  expected?: Pick<CodeReviewRequest, 'base' | 'head'>;
}
