import { z } from 'zod';
import type { CodeReviewSelection, CodeReviewSelectionRequest } from 'librechat-data-provider';
import { reviewCommitSchema } from './schema';
import { ReviewWorkerError } from './worker';

export interface ReviewGitHubRepository {
  owner: string;
  name: string;
  repositoryId: number;
}

export const reviewGitHubRepositorySchema: z.ZodType<ReviewGitHubRepository> = z
  .object({
    owner: z
      .string()
      .min(1)
      .max(39)
      .regex(/^[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$/),
    name: z
      .string()
      .min(1)
      .max(100)
      .regex(/^[a-zA-Z0-9_-][a-zA-Z0-9._-]*$/),
    repositoryId: z.number().int().positive().safe(),
  })
  .strict();

export const reviewSelectionRequestSchema: z.ZodType<CodeReviewSelectionRequest> = z
  .object({
    repository: z.string().regex(/^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$/),
    pullRequest: z.number().int().positive().safe(),
    expected: z.object({ base: reviewCommitSchema, head: reviewCommitSchema }).strict().optional(),
  })
  .strict();

const responseSchema = z.object({
  number: z.number().int().positive().safe(),
  state: z.enum(['open', 'closed']),
  merged: z.boolean(),
  base: z.object({
    sha: reviewCommitSchema,
    repo: z.object({ id: z.number().int().positive().safe(), full_name: z.string().max(140) }),
  }),
  head: z.object({ sha: reviewCommitSchema }),
});
const MAX_BYTES = 65536;

/** Reads public GitHub metadata only. No ambient authentication, redirects or retries. */
export async function resolveReviewSelection(
  input: CodeReviewSelectionRequest,
  repository: ReviewGitHubRepository,
  fetcher: (url: string, options: RequestInit) => Promise<Response> = fetch,
): Promise<CodeReviewSelection> {
  const parsed = reviewSelectionRequestSchema.safeParse(input);
  if (!parsed.success) throw new ReviewWorkerError('invalid_request');
  const binding = reviewGitHubRepositorySchema.safeParse(repository);
  if (!binding.success) throw new ReviewWorkerError('configuration');
  const request = parsed.data;
  const { owner, name, repositoryId } = binding.data;
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  const timeout = new Promise<never>((_resolve, reject) => {
    timer = setTimeout(() => {
      controller.abort();
      reject(new ReviewWorkerError('timeout'));
    }, 5000);
  });
  const lookup = async (): Promise<CodeReviewSelection> => {
    const response = await fetcher(
      `https://api.github.com/repos/${encodeURIComponent(owner)}/${encodeURIComponent(name)}/pulls/${request.pullRequest}`,
      {
        method: 'GET',
        redirect: 'error',
        cache: 'no-store',
        credentials: 'omit',
        signal: controller.signal,
        headers: {
          Accept: 'application/vnd.github+json',
          'X-GitHub-Api-Version': '2026-03-10',
          'User-Agent': 'LibreChat-development-review',
        },
      },
    );
    if (response.status !== 200 || !response.body) throw new ReviewWorkerError('invalid_response');
    const length = response.headers.get('content-length');
    if (length !== null && (!/^\d+$/.test(length) || Number(length) > MAX_BYTES))
      throw new ReviewWorkerError('output_limit');
    const reader = response.body.getReader();
    const cancel = () => {
      void reader.cancel().catch(() => {});
    };
    controller.signal.addEventListener('abort', cancel, { once: true });
    const chunks: Uint8Array[] = [];
    let size = 0;
    try {
      while (true) {
        const { value, done } = await reader.read();
        controller.signal.throwIfAborted();
        if (done) break;
        size += value.byteLength;
        if (size > MAX_BYTES) throw new ReviewWorkerError('output_limit');
        chunks.push(value);
      }
    } finally {
      controller.signal.removeEventListener('abort', cancel);
      void reader.cancel().catch(() => {});
      reader.releaseLock();
    }
    const data = responseSchema.parse(
      JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks))),
    );
    if (
      data.number !== request.pullRequest ||
      data.base.repo.id !== repositoryId ||
      data.base.repo.full_name.toLowerCase() !== `${owner}/${name}`.toLowerCase()
    )
      throw new ReviewWorkerError('invalid_response');
    const pair = { repository: request.repository, base: data.base.sha, head: data.head.sha };
    let status: CodeReviewSelection['status'] = 'resolved';
    if (request.expected) {
      const matches = request.expected.base === pair.base && request.expected.head === pair.head;
      status = matches ? 'current' : 'stale';
    }
    if (data.state === 'closed' || data.merged) status = 'closed';
    return {
      request: pair,
      pullRequest: request.pullRequest,
      status,
      checkedAt: new Date().toISOString(),
    };
  };
  try {
    return await Promise.race([lookup(), timeout]);
  } catch (error) {
    if (error instanceof ReviewWorkerError) throw error;
    throw new ReviewWorkerError('invalid_response');
  } finally {
    clearTimeout(timer);
    controller.abort();
  }
}
