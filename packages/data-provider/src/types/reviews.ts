export interface CodeReviewRequest {
  repository: string;
  base: string;
  head: string;
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
}

export type CodeReviewFailure =
  | 'invalid_request'
  | 'forbidden'
  | 'busy'
  | 'cancelled'
  | 'timeout'
  | 'output_limit'
  | 'worker_failed'
  | 'invalid_response'
  | 'configuration';

/** Process-local recovery only. Unknown never authorizes resubmission. */
export type CodeReviewRecovery =
  | { id: string; state: 'unknown' }
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
