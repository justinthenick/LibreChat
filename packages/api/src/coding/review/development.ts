import { z } from 'zod';
import type { ReviewRoutesConfig } from './routes';
import { createReviewClient, reviewPrincipalSchema } from './transport';
import { reviewGitHubRepositorySchema } from './selection';

export interface ReviewDevelopmentEnvironment {
  NODE_ENV?: string;
  CODING_REVIEW_DEVELOPMENT?: string;
  CODING_REVIEW_URL?: string;
  CODING_REVIEW_TOKEN?: string;
  CODING_REVIEW_MODEL?: string;
  CODING_REVIEW_REPOSITORIES?: string;
}

const repositoriesSchema = z
  .array(
    z
      .object({
        id: z.string().regex(/^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$/),
        github: reviewGitHubRepositorySchema.optional(),
        tenantId: z
          .string()
          .optional()
          .refine(
            (tenantId) =>
              reviewPrincipalSchema.safeParse({ userId: 'configuration', tenantId }).success,
          ),
      })
      .strict(),
  )
  .min(1)
  .max(64)
  .refine(
    (entries) =>
      new Set(entries.map(({ id, tenantId }) => JSON.stringify([id, tenantId]))).size ===
      entries.length,
  );

/** Parses only explicit development settings; never reads files or provisions credentials. */
export function getDevelopmentReviewConfig(env: ReviewDevelopmentEnvironment): ReviewRoutesConfig {
  const disabled: ReviewRoutesConfig = {
    enabled: false,
    repositories: [],
    client: { enabled: false, url: '', token: '', model: '' },
  };
  if (env.NODE_ENV !== 'development' || env.CODING_REVIEW_DEVELOPMENT !== 'true') return disabled;
  try {
    const raw = env.CODING_REVIEW_REPOSITORIES ?? '';
    if (Buffer.byteLength(raw) > 16384) return disabled;
    const repositories = repositoriesSchema.parse(JSON.parse(raw));
    const client = {
      enabled: true,
      url: env.CODING_REVIEW_URL ?? '',
      token: env.CODING_REVIEW_TOKEN ?? '',
      model: z
        .string()
        .min(1)
        .max(100)
        .regex(/^[a-zA-Z0-9._-]+$/)
        .parse(env.CODING_REVIEW_MODEL),
    };
    createReviewClient(client);
    return { enabled: true, client, repositories };
  } catch {
    return disabled;
  }
}
