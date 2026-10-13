import { z } from 'zod';
import type { CodeReviewRequest, CodeReviewResult } from 'librechat-data-provider';

const sha = z
  .string()
  .length(40)
  .regex(/^[0-9a-f]{40}$/);
const text = z
  .string()
  .min(1)
  .max(2000)
  .refine((value) => value.trim().length > 0);
const safeText = text.refine((value) =>
  Array.from(value).every((character) => {
    const code = character.codePointAt(0) ?? 0;
    return (code === 9 || code >= 32) && code !== 127 && !(code >= 0xd800 && code <= 0xdfff);
  }),
);

export const reviewRequestSchema: z.ZodType<CodeReviewRequest> = z
  .object({
    repository: z.string().regex(/^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$/),
    base: sha,
    head: sha,
  })
  .strict();

const findingsSchema = z
  .array(
    z
      .object({
        severity: z.enum(['blocker', 'major', 'minor']),
        path: safeText.refine(
          (value) =>
            /^[a-zA-Z0-9._/-]+$/.test(value) &&
            value.split('/').every((part) => part !== '' && part !== '.' && part !== '..'),
        ),
        line: z.number().int().positive().max(Number.MAX_SAFE_INTEGER),
        title: safeText,
        evidence: safeText,
        recommendation: safeText,
      })
      .strict(),
  )
  .max(100);

export const reviewResponseSchema = z
  .object({
    ok: z.literal(true),
    mode: z.literal('review'),
    base: sha,
    head: sha,
    status: z.literal('human_review_required'),
    provider: z.literal('chatgpt_subscription'),
    model: z.string().min(1).max(100),
    finding_count: z.number().int().min(0).max(100),
    findings: findingsSchema,
  })
  .strict()
  .refine((value) => value.finding_count === value.findings.length);

export const reviewResultSchema: z.ZodType<CodeReviewResult> = z
  .object({
    repository: z.string().regex(/^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$/),
    base: sha,
    head: sha,
    status: z.literal('human_review_required'),
    provider: z.literal('chatgpt_subscription'),
    model: z.string().min(1).max(100),
    findings: findingsSchema,
  })
  .strict();
