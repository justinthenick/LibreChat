import { z } from 'zod';
import { Router, json } from 'express';
import { rateLimit } from 'express-rate-limit';
import type { CodeReviewRequest } from 'librechat-data-provider';
import type { RequestHandler } from 'express';
import type { ReviewGitHubRepository } from './selection';
import type { ServerRequest } from '../../types/http';
import type { ReviewClientConfig } from './transport';
import {
  createReviewClient,
  reviewRunIdSchema,
  reviewPrincipalSchema,
  reviewFailureStatus,
} from './transport';
import { resolveReviewSelection, reviewSelectionRequestSchema } from './selection';
import { resolveRequestTenantId } from '../../middleware/tenant';
import { reviewRequestSchema } from './schema';
import { ReviewWorkerError } from './worker';

export interface ReviewRoutesConfig {
  enabled?: boolean;
  client: ReviewClientConfig;
  /** Explicit tenant-scoped IDs; paths and caller-supplied policy are never accepted. */
  repositories?: readonly { id: string; tenantId?: string; github?: ReviewGitHubRepository }[];
}

/** Mandatory existing middleware is supplied by the thin LibreChat JS wrapper. */
export function createReviewRouter(
  config: ReviewRoutesConfig,
  security: {
    authenticate: RequestHandler;
    checkBan: RequestHandler;
    authorize?: RequestHandler;
  },
): Router {
  const router = Router();
  const client = createReviewClient({
    ...config.client,
    enabled: config.enabled === true && config.client.enabled === true,
  });
  router.use(security.authenticate, security.checkBan);
  router.use((incoming, res, next) => {
    const req = incoming as ServerRequest;
    if (!req.user?.id) {
      res.status(401).json({ code: 'forbidden' });
      return;
    }
    if (
      !reviewPrincipalSchema.safeParse({
        userId: req.user.id,
        tenantId: resolveRequestTenantId(req),
      }).success
    ) {
      res.status(403).json({ code: 'forbidden' });
      return;
    }
    if (config.enabled !== true) {
      res.status(503).json({ code: 'configuration' });
      return;
    }
    res.setHeader('cache-control', 'no-store');
    next();
  });
  if (security.authorize) router.use(security.authorize);
  const repositoriesFor = (req: ServerRequest) =>
    config.repositories?.filter(({ tenantId }) => tenantId === resolveRequestTenantId(req));
  const requireRepository = (req: ServerRequest, repository: string) => {
    if (config.repositories && !repositoriesFor(req)?.some(({ id }) => id === repository))
      throw new ReviewWorkerError('forbidden');
  };
  const checkPullRequest = async (req: ServerRequest, request: CodeReviewRequest) => {
    if (!request.pullRequest) return undefined;
    const binding = repositoriesFor(req)?.find(({ id }) => id === request.repository)?.github;
    if (!binding || binding.repositoryId !== request.pullRequest.repositoryId)
      throw new ReviewWorkerError('invalid_request');
    const selection = await resolveReviewSelection(
      {
        repository: request.repository,
        pullRequest: request.pullRequest.number,
        expected: { base: request.base, head: request.head },
      },
      binding,
    );
    if (selection.status !== 'current') throw new ReviewWorkerError('stale_review');
    return selection.checkedAt;
  };
  router.get('/config', (incoming, res) => {
    const repositories = repositoriesFor(incoming as ServerRequest)?.map(({ id }) => id) ?? [];
    res.status(200).json({ enabled: repositories.length > 0, repositories });
  });
  router.use(json({ limit: 4096, strict: true }));
  const limit = (max: number) =>
    rateLimit({
      windowMs: 60_000,
      max,
      standardHeaders: true,
      legacyHeaders: false,
      keyGenerator: (incoming) => {
        const req = incoming as ServerRequest;
        return JSON.stringify([resolveRequestTenantId(req), req.user!.id]);
      },
      handler: (_req, res) => {
        res.status(429).json({ code: 'busy' });
      },
    });
  router.post('/selection', limit(30), async (incoming, res) => {
    const req = incoming as ServerRequest;
    try {
      const parsed = reviewSelectionRequestSchema.safeParse(req.body);
      if (!parsed.success || Buffer.byteLength(JSON.stringify(req.body) ?? '') > 4096)
        throw new ReviewWorkerError('invalid_request');
      requireRepository(req, parsed.data.repository);
      const binding = repositoriesFor(req)?.find(({ id }) => id === parsed.data.repository)?.github;
      if (!binding) throw new ReviewWorkerError('configuration');
      const selection = await resolveReviewSelection(parsed.data, binding);
      if (!res.destroyed) res.status(200).json(selection);
    } catch (error) {
      const code = error instanceof ReviewWorkerError ? error.code : 'invalid_response';
      if (!res.destroyed)
        res.status(code === 'busy' ? 429 : reviewFailureStatus[code]).json({ code });
    }
  });
  const handler =
    (cancel: boolean): RequestHandler =>
    async (incoming, res) => {
      const req = incoming as ServerRequest;
      try {
        if (Buffer.byteLength(JSON.stringify(req.body) ?? '') > 4096)
          throw new ReviewWorkerError('invalid_request');
        const principal = { userId: req.user!.id, tenantId: resolveRequestTenantId(req) };
        if (!cancel) {
          const body = z
            .object({ id: reviewRunIdSchema, request: reviewRequestSchema })
            .strict()
            .safeParse(req.body);
          if (!body.success) throw new ReviewWorkerError('invalid_request');
          requireRepository(req, body.data.request.repository);
          await checkPullRequest(req, body.data.request);
          const result = await client.run(body.data.request, principal, undefined, body.data.id);
          const prCheckedAt = await checkPullRequest(req, body.data.request);
          if (!res.destroyed)
            res.status(200).json({ ...result, ...(prCheckedAt ? { prCheckedAt } : {}) });
        } else {
          const body = z.object({ id: reviewRunIdSchema }).strict().safeParse(req.body);
          if (!body.success) throw new ReviewWorkerError('invalid_request');
          await client.cancel(body.data.id, principal);
          if (!res.destroyed) res.status(200).json({ cancelled: true });
        }
      } catch (error) {
        const code = error instanceof ReviewWorkerError ? error.code : 'worker_failed';
        if (!res.destroyed) res.status(reviewFailureStatus[code]).json({ code });
      }
    };
  router.post('/', limit(10), handler(false));
  router.post('/cancel', limit(60), handler(true));
  router.post('/status', limit(60), async (incoming, res) => {
    const req = incoming as ServerRequest;
    try {
      const body = z
        .object({ id: reviewRunIdSchema, request: reviewRequestSchema })
        .strict()
        .safeParse(req.body);
      if (!body.success || Buffer.byteLength(JSON.stringify(req.body) ?? '') > 4096)
        throw new ReviewWorkerError('invalid_request');
      requireRepository(req, body.data.request.repository);
      const record = await client.status(body.data.id, body.data.request, {
        userId: req.user!.id,
        tenantId: resolveRequestTenantId(req),
      });
      const prCheckedAt =
        record.state === 'unknown' ? undefined : await checkPullRequest(req, record.request);
      const checked =
        record.state === 'completed' && prCheckedAt
          ? { ...record, result: { ...record.result, prCheckedAt } }
          : record;
      if (!res.destroyed) res.status(200).json(checked);
    } catch (error) {
      const code = error instanceof ReviewWorkerError ? error.code : 'worker_failed';
      if (!res.destroyed) res.status(reviewFailureStatus[code]).json({ code });
    }
  });
  router.use(((error, _req, res, _next) => {
    res.status(400).json({ code: 'invalid_request' });
  }) satisfies import('express').ErrorRequestHandler);
  return router;
}
