import { z } from 'zod';
import { Router, json } from 'express';
import { rateLimit } from 'express-rate-limit';
import type { RequestHandler } from 'express';
import type { ServerRequest } from '../../types/http';
import type { ReviewClientConfig } from './transport';
import {
  createReviewClient,
  reviewRunIdSchema,
  reviewPrincipalSchema,
  reviewFailureStatus,
} from './transport';
import { resolveRequestTenantId } from '../../middleware/tenant';
import { reviewRequestSchema } from './schema';
import { ReviewWorkerError } from './worker';

export interface ReviewRoutesConfig {
  enabled?: boolean;
  client: ReviewClientConfig;
}

/** Mandatory existing middleware is supplied by the thin LibreChat JS wrapper. */
export function createReviewRouter(
  config: ReviewRoutesConfig,
  security: {
    authenticate: RequestHandler;
    checkBan: RequestHandler;
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
          const result = await client.run(body.data.request, principal, undefined, body.data.id);
          if (!res.destroyed) res.status(200).json(result);
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
      const record = await client.status(body.data.id, body.data.request, {
        userId: req.user!.id,
        tenantId: resolveRequestTenantId(req),
      });
      if (!res.destroyed) res.status(200).json(record);
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
