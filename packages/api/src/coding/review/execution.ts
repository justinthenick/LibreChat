import type { ReviewWorkerConfig, CodeReviewWorker } from './worker';
import { createCodeReviewWorker } from './worker';

export type ReviewExecutionMode = 'local' | 'supervisor';
export type ReviewExecutionBackend = (config: ReviewWorkerConfig) => CodeReviewWorker;

/** Supervisor has no registered execution backend. Unknown selections also refuse. */
export function selectReviewExecutionBackend(
  mode: ReviewExecutionMode | undefined,
): ReviewExecutionBackend | undefined {
  if (mode === undefined || mode === 'local') {
    return createCodeReviewWorker;
  }
  return undefined;
}
