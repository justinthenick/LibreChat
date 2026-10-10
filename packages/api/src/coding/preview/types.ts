import type {
  PreviewPrincipal,
  PreviewScope,
  PreviewStartRequest,
  PreviewJobMessage,
} from 'librechat-data-provider';
import type { RequestHandler } from 'express';
export type {
  PreviewPrincipal,
  PreviewScope,
  PreviewStartRequest,
  PreviewJobMessage,
  PreviewErrorCode,
  PreviewState,
  PreviewProof,
  PreviewTask,
  PreviewEvidence,
  PreviewJob,
  PreviewReply,
} from 'librechat-data-provider';

/** An injected server capability must authenticate origin and preserve principal integrity. */
export interface PreviewTransport {
  exchange(message: { principal: PreviewPrincipal; payload: PreviewJobMessage }): Promise<unknown>;
}
export type PreviewAuthorizationContext =
  | { operation: 'start'; request: PreviewStartRequest }
  | { operation: 'get' | 'cancel' };
export type PreviewOptions = {
  enabled?: boolean;
  transport?: PreviewTransport;
  /** Must enforce repository ACLs and start text/rate admission before model transfer. */
  authorize?: (
    principal: PreviewPrincipal,
    scope: PreviewScope,
    context: PreviewAuthorizationContext,
  ) => Promise<boolean>;
  timeoutMs?: number;
};
export type PreviewHandlers = Record<'start' | 'get' | 'cancel' | 'unsupported', RequestHandler>;
