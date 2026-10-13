import { useMutation } from '@tanstack/react-query';
import { dataService } from 'librechat-data-provider';
import type { CodeReviewRequest } from 'librechat-data-provider';

type Selection = { id: string; request: CodeReviewRequest; signal: AbortSignal };
type Cancellation = { id: string; signal: AbortSignal };

export function useReviewActions() {
  return {
    start: useMutation(({ signal, ...body }: Selection) => dataService.startReview(body, signal), {
      retry: false,
      networkMode: 'always',
    }),
    status: useMutation(
      ({ signal, ...body }: Selection) => dataService.retrieveReview(body, signal),
      { retry: false, networkMode: 'always' },
    ),
    cancel: useMutation(
      ({ signal, ...body }: Cancellation) => dataService.cancelReview(body, signal),
      { retry: false, networkMode: 'always' },
    ),
  };
}
