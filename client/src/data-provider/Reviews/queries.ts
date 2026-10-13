import { useMutation, useQuery } from '@tanstack/react-query';
import { dataService, QueryKeys } from 'librechat-data-provider';
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

/** Identity scopes cached discovery only; the server derives authorization from the session. */
export function useReviewConfigQuery(identity?: { userId: string; tenantId?: string }) {
  return useQuery(
    [QueryKeys.reviewConfig, identity?.userId, identity?.tenantId ?? null],
    ({ signal }) => dataService.getReviewConfig(signal),
    {
      enabled: identity !== undefined,
      retry: false,
      cacheTime: 0,
      staleTime: 0,
      keepPreviousData: false,
    },
  );
}
