import path from 'node:path';
import { spawn } from 'node:child_process';
import { lstat, realpath, mkdtemp, mkdir, rm } from 'node:fs/promises';
import type {
  CodeReviewRequest,
  CodeReviewResult,
  CodeReviewFailure,
} from 'librechat-data-provider';
import { reviewRequestSchema, reviewResponseSchema } from './schema';

export type ReviewFailure = CodeReviewFailure;

const REVIEW_STAGES = new Set([
  'evidence_validated',
  'provider_ready',
  'conversation_started',
  'conversation_finished',
  'result_validated',
]);

/** Fixed stage labels and bounded counters, never child text or credentials. */
export type ReviewWorkerDiagnostic =
  | { type: 'stage'; stage: string; reviewId?: string | null }
  | {
      type: 'exit';
      reviewId?: string | null;
      exitCode: number | null;
      signal: string | null;
      stdoutBytes: number;
      stderrBytes: number;
      classification: 'success' | ReviewFailure;
    };

function emitDiagnostic(
  listener: ((event: ReviewWorkerDiagnostic) => void) | undefined,
  event: ReviewWorkerDiagnostic,
): void {
  try {
    const pending: unknown = listener?.(event);
    if (pending && typeof (pending as PromiseLike<unknown>).then === 'function') {
      // Attach rejection handling immediately: an async logging failure must
      // never become an unhandled rejection or change the worker outcome.
      void Promise.resolve(pending).catch(() => {});
    }
  } catch {
    // Observability must not affect authorization, dispatch, or cleanup.
  }
}

export class ReviewWorkerError extends Error {
  constructor(public readonly code: ReviewFailure) {
    super(`Code review failed: ${code}`);
    this.name = 'ReviewWorkerError';
  }
}

export interface ReviewPrincipal {
  userId: string;
  tenantId?: string;
}

export interface ReviewWorkerConfig {
  python: string;
  sourceRoot: string;
  scratchRoot: string;
  authRoot: string;
  model: string;
  repositories: ReadonlyMap<string, string>;
  authorize: (principal: ReviewPrincipal, repository: string) => Promise<boolean>;
  /** Operator-owned sink. Never include stderr or provider output. */
  onDiagnostic?: (event: ReviewWorkerDiagnostic) => void;
}

const WALL_TIME_MS = 150_000;
const MAX_OUTPUT_BYTES = 128_000;
const MAX_STDERR_BYTES = 64_000;

async function trustedPath(value: string): Promise<string> {
  if (!path.isAbsolute(value)) {
    throw new ReviewWorkerError('configuration');
  }
  return realpath(value);
}

export interface CodeReviewWorker {
  run(
    input: CodeReviewRequest,
    principal: ReviewPrincipal,
    signal?: AbortSignal,
    reviewId?: string,
  ): Promise<CodeReviewResult>;
}

/** One instance per worker process; callers supply authenticated principal context. */
export function createCodeReviewWorker(config: ReviewWorkerConfig): CodeReviewWorker {
  const repositories = new Map(config.repositories);
  const settings = { ...config };
  let active = false;

  async function run(
    input: CodeReviewRequest,
    principal: ReviewPrincipal,
    signal?: AbortSignal,
    reviewId?: string,
  ): Promise<CodeReviewResult> {
    const diagnostic = (event: ReviewWorkerDiagnostic) =>
      emitDiagnostic(settings.onDiagnostic, {
        ...event,
        reviewId:
          typeof reviewId === 'string' &&
          /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(
            reviewId,
          )
            ? reviewId
            : null,
      });
    const parsed = reviewRequestSchema.safeParse(input);
    if (!parsed.success) {
      throw new ReviewWorkerError('invalid_request');
    }
    const request = parsed.data;
    const repository = repositories.get(request.repository);
    if (!principal.userId || principal.tenantId === '' || !repository) {
      throw new ReviewWorkerError('forbidden');
    }
    let authorized = false;
    try {
      authorized = await settings.authorize(principal, request.repository);
    } catch {
      throw new ReviewWorkerError('forbidden');
    }
    if (authorized !== true) {
      throw new ReviewWorkerError('forbidden');
    }
    if (signal?.aborted) {
      throw new ReviewWorkerError('cancelled');
    }
    if (active) {
      throw new ReviewWorkerError('busy');
    }
    active = true;
    let workspace: string | undefined;
    try {
      if (
        process.platform !== 'linux' ||
        !/^[a-zA-Z0-9][a-zA-Z0-9._-]{0,99}$/.test(settings.model)
      ) {
        throw new ReviewWorkerError('configuration');
      }
      const [python, sourceRoot, scratchRoot, authRoot, repo] = await Promise.all([
        trustedPath(settings.python).then(() => settings.python),
        trustedPath(settings.sourceRoot),
        trustedPath(settings.scratchRoot),
        trustedPath(settings.authRoot),
        trustedPath(repository),
      ]);
      const scratchInfo = await lstat(scratchRoot);
      if (
        !scratchInfo.isDirectory() ||
        (scratchInfo.mode & 0o077) !== 0 ||
        scratchInfo.uid !== process.getuid?.()
      ) {
        throw new ReviewWorkerError('configuration');
      }
      workspace = await mkdtemp(path.join(scratchRoot, 'worker-'));
      const home = path.join(workspace, 'home');
      await mkdir(home, { mode: 0o700 });
      const environment = {
        PATH: '/usr/bin:/bin',
        LANG: 'C.UTF-8',
        HOME: home,
        TMPDIR: workspace,
        PYTHONPATH: sourceRoot,
        PYTHONNOUSERSITE: '1',
        PYTHONDONTWRITEBYTECODE: '1',
        OPENHANDS_SUPPRESS_BANNER: '1',
        LITELLM_LOCAL_MODEL_COST_MAP: 'True',
        OTEL_SDK_DISABLED: 'true',
        OH_PERSISTENCE_DIR: authRoot,
        CODING_OPENHANDS_PROVIDER: 'chatgpt_subscription',
        CODING_OPENHANDS_MODEL: settings.model,
        CODING_OPENHANDS_SCRATCH_ROOT: path.join(workspace, 'scratch'),
        CODING_REVIEW_STAGE_FD: '3',
      };
      const output = await execute(
        python,
        repo,
        request,
        workspace,
        environment,
        signal,
        diagnostic,
      );
      let response: ReturnType<typeof reviewResponseSchema.parse>;
      try {
        response = reviewResponseSchema.parse(JSON.parse(output));
      } catch {
        throw new ReviewWorkerError('invalid_response');
      }
      if (
        response.base !== request.base ||
        response.head !== request.head ||
        response.model !== settings.model
      ) {
        throw new ReviewWorkerError('invalid_response');
      }
      diagnostic({ type: 'stage', stage: 'schema_validated' });
      return {
        ...request,
        status: response.status,
        provider: response.provider,
        model: response.model,
        findings: response.findings,
      };
    } catch (error) {
      if (error instanceof ReviewWorkerError) {
        throw error;
      }
      throw new ReviewWorkerError('worker_failed');
    } finally {
      try {
        if (workspace) {
          await rm(workspace, { recursive: true, force: true }).catch(() => {
            throw new ReviewWorkerError('worker_failed');
          });
        }
      } finally {
        active = false;
      }
    }
  }

  return { run };
}

function execute(
  python: string,
  repo: string,
  request: CodeReviewRequest,
  workspace: string,
  environment: NodeJS.ProcessEnv,
  signal?: AbortSignal,
  onDiagnostic?: (event: ReviewWorkerDiagnostic) => void,
): Promise<string> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new ReviewWorkerError('cancelled'));
      return;
    }
    const child = spawn(
      '/usr/bin/prlimit',
      [
        '--as=4294967296',
        '--cpu=120',
        '--fsize=16777216',
        '--nofile=128',
        '--core=0',
        '--',
        python,
        '-B',
        '-s',
        '-m',
        'coding_orchestrator.review_cli',
        'review',
        '--repo',
        repo,
        '--base',
        request.base,
        '--head',
        request.head,
      ],
      {
        cwd: workspace,
        env: environment,
        shell: false,
        detached: true,
        stdio: ['ignore', 'pipe', 'pipe', 'pipe'],
      },
    );
    let failure: ReviewFailure | undefined;
    let stdoutBytes = 0;
    let stderrBytes = 0;
    const chunks: Buffer[] = [];

    // Only fixed labels on a private diagnostics pipe. Never parse stderr.
    let stageBytes = 0;
    let stageBuffer = '';
    child.stdio[3]?.on('data', (chunk: Buffer) => {
      stageBytes += chunk.length;
      if (stageBytes > 512) return;
      stageBuffer += chunk.toString('utf8');
      while (stageBuffer.includes('\n')) {
        const end = stageBuffer.indexOf('\n');
        const stage = stageBuffer.slice(0, end);
        stageBuffer = stageBuffer.slice(end + 1);
        if (REVIEW_STAGES.has(stage)) emitDiagnostic(onDiagnostic, { type: 'stage', stage });
      }
    });
    const killGroup = () => {
      if (child.pid) {
        try {
          process.kill(-child.pid, 'SIGKILL');
        } catch {
          // ESRCH is expected if the process group has already exited.
        }
      }
    };
    const stop = (code: ReviewFailure) => {
      failure ??= code;
      killGroup();
    };
    const cancel = () => stop('cancelled');
    const timer = setTimeout(() => stop('timeout'), WALL_TIME_MS);
    signal?.addEventListener('abort', cancel, { once: true });
    child.stdout?.on('data', (chunk: Buffer) => {
      stdoutBytes += chunk.length;
      if (stdoutBytes > MAX_OUTPUT_BYTES) {
        stop('output_limit');
      } else if (!failure) {
        chunks.push(chunk);
      }
    });
    child.stderr?.on('data', (chunk: Buffer) => {
      stderrBytes += chunk.length;
      if (stderrBytes > MAX_STDERR_BYTES) {
        stop('output_limit');
      }
    });
    child.on('error', () => stop('worker_failed'));
    child.on('exit', killGroup);
    child.on('close', (code, signalName) => {
      emitDiagnostic(onDiagnostic, {
        type: 'exit',
        exitCode: code,
        signal: signalName,
        stdoutBytes,
        stderrBytes,
        classification: failure ?? (code === 0 ? 'success' : 'worker_failed'),
      });
      clearTimeout(timer);
      signal?.removeEventListener('abort', cancel);
      if (failure || code !== 0) {
        reject(new ReviewWorkerError(failure ?? 'worker_failed'));
        return;
      }
      try {
        resolve(new TextDecoder('utf-8', { fatal: true }).decode(Buffer.concat(chunks)));
      } catch {
        reject(new ReviewWorkerError('invalid_response'));
      }
    });
  });
}
