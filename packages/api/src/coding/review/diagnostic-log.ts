import path from 'node:path';
import { constants } from 'node:fs';
import { constants as osConstants } from 'node:os';
import { lstat, open, realpath, readdir } from 'node:fs/promises';
import type { ReviewWorkerDiagnostic } from './worker';
import { reviewRunIdSchema } from './identity';

const stages = new Set([
  'evidence_validated',
  'provider_ready',
  'conversation_started',
  'conversation_finished',
  'result_validated',
  'schema_validated',
]);
const classifications = new Set([
  'success',
  'invalid_request',
  'forbidden',
  'configuration',
  'busy',
  'cancelled',
  'timeout',
  'output_limit',
  'worker_failed',
  'invalid_response',
]);
const MAX_RECORD_BYTES = 1024;

export interface ReviewDiagnosticLogConfig {
  /** Existing, empty, operator-owned 0700 directory outside Git. */
  directory: string;
  /** All repository, credential, scratch and journal roots; never log there. */
  protectedRoots: readonly string[];
  /** Per-directory lifetime budget. No append/reopen, rotation or deletion. */
  maxBytes?: number;
  maxPendingRecords?: number;
}

export interface ReviewDiagnosticLog {
  onDiagnostic: (event: ReviewWorkerDiagnostic) => void;
  health: () => Readonly<{
    state: 'open' | 'capacity' | 'failed' | 'closed';
    accepted: number;
    dropped: number;
    writtenBytes: number;
  }>;
  /** Operator shutdown only; never awaited on the review execution path. */
  close: () => Promise<void>;
}

function bounded(value: unknown): value is number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0;
}

/** Reconstruct known scalar fields; never stringify an input object or error. */
function sanitize(event: ReviewWorkerDiagnostic) {
  // Read once: hostile getters must not substitute an object after validation.
  const { type, reviewId: suppliedId } = event;
  const parsedId =
    typeof suppliedId === 'string' ? reviewRunIdSchema.safeParse(suppliedId) : undefined;
  const reviewId = parsedId?.success ? parsedId.data : null;
  if (type === 'stage') {
    const { stage } = event;
    return stages.has(stage) ? { type: 'stage', reviewId, stage } : null;
  }
  if (type !== 'exit') return null;
  const { classification, exitCode, signal, stdoutBytes, stderrBytes } = event;
  if (
    !classifications.has(classification) ||
    !(exitCode === null || (bounded(exitCode) && exitCode <= 255)) ||
    !(
      signal === null ||
      (typeof signal === 'string' &&
        Object.prototype.hasOwnProperty.call(osConstants.signals, signal))
    ) ||
    !bounded(stdoutBytes) ||
    !bounded(stderrBytes)
  )
    return null;
  return {
    type: 'child_exit',
    reviewId,
    exitCode,
    signal,
    stdoutBytes: Math.min(stdoutBytes, 128000),
    stderrBytes: Math.min(stderrBytes, 64000),
    classification,
  };
}

function overlaps(a: string, b: string): boolean {
  return (
    a === b ||
    a.startsWith(b + path.sep) ||
    b.startsWith(a + path.sep) ||
    a === path.parse(a).root ||
    b === path.parse(b).root
  );
}

/**
 * Explicit development composition only. Trusted operator filesystem required:
 * permission/ancestry checks are not a sandbox against concurrent path replacement.
 * This sink has no journal, approval, dispatch or reconciliation capabilities.
 */
export async function createReviewDiagnosticLog(
  config: ReviewDiagnosticLogConfig,
): Promise<ReviewDiagnosticLog> {
  const maxBytes = config.maxBytes ?? 1048576;
  const maxPending = config.maxPendingRecords ?? 64;
  let file: Awaited<ReturnType<typeof open>> | undefined;
  try {
    if (
      process.platform !== 'linux' ||
      !path.isAbsolute(config.directory) ||
      !bounded(maxBytes) ||
      maxBytes < MAX_RECORD_BYTES ||
      maxBytes > 16777216 ||
      !bounded(maxPending) ||
      maxPending < 1 ||
      maxPending > 256 ||
      !config.protectedRoots.length
    )
      throw new Error();
    const directory = path.resolve(config.directory);
    // Reject symlinks in every component and Git worktree/checkout ancestors.
    for (let current = directory; ; current = path.dirname(current)) {
      const info = await lstat(current);
      if (!info.isDirectory() || info.isSymbolicLink()) throw new Error();
      try {
        await lstat(path.join(current, '.git'));
        throw new Error('git');
      } catch (error) {
        if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw new Error();
      }
      if (current === path.dirname(current)) break;
    }
    const info = await lstat(directory);
    if (info.uid !== process.getuid?.() || (info.mode & 0o7777) !== 0o700) throw new Error();
    for (const root of config.protectedRoots) {
      if (!path.isAbsolute(root) || overlaps(directory, await realpath(root))) throw new Error();
    }
    if ((await readdir(directory)).length !== 0) throw new Error();
    // O_EXCL rejects existing files, hardlinks, symlinks and other file types.
    // A stopped log is never reopened: operators retain it and choose a new directory.
    file = await open(
      path.join(directory, 'review-diagnostics.jsonl'),
      constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL | constants.O_NOFOLLOW,
      0o600,
    );
    const stat = await file.stat();
    if (
      !stat.isFile() ||
      stat.nlink !== 1 ||
      stat.uid !== process.getuid?.() ||
      (stat.mode & 0o7777) !== 0o600
    )
      throw new Error();
  } catch {
    await file?.close().catch(() => undefined);
    throw new Error('Review diagnostic log configuration unavailable');
  }
  const handle = file;
  let state: 'open' | 'capacity' | 'failed' | 'closed' = 'open';
  let accepted = 0,
    dropped = 0,
    writtenBytes = 0,
    reservedBytes = 0,
    pending = 0;
  let tail = Promise.resolve();
  let closing: Promise<void> | undefined;
  const incrementDropped = () => {
    dropped = Math.min(Number.MAX_SAFE_INTEGER, dropped + 1);
  };
  const onDiagnostic = (event: ReviewWorkerDiagnostic): void => {
    try {
      if (state !== 'open' || pending >= maxPending) {
        incrementDropped();
        return;
      }
      const clean = sanitize(event);
      if (!clean) {
        incrementDropped();
        return;
      }
      const line =
        JSON.stringify({
          version: 1,
          timestamp: new Date().toISOString(),
          sequence: accepted + 1,
          ...clean,
        }) + '\n';
      const size = Buffer.byteLength(line);
      if (size > MAX_RECORD_BYTES) {
        incrementDropped();
        return;
      }
      if (reservedBytes + size > maxBytes) {
        state = 'capacity';
        incrementDropped();
        return;
      }
      reservedBytes += size;
      accepted++;
      pending++;
      tail = tail
        .then(async () => {
          if (state === 'failed') {
            incrementDropped();
            return;
          }
          const buffer = Buffer.from(line);
          let offset = 0;
          while (offset < buffer.length) {
            const result = await handle.write(buffer, offset, buffer.length - offset);
            if (!result.bytesWritten) throw new Error();
            offset += result.bytesWritten;
            writtenBytes += result.bytesWritten;
          }
        })
        .catch(() => {
          state = 'failed';
          incrementDropped();
        })
        .finally(() => {
          pending--;
        });
    } catch {
      incrementDropped();
    }
  };
  return {
    onDiagnostic,
    health: () => ({ state, accepted, dropped, writtenBytes }),
    close: () => {
      if (!closing) {
        if (state === 'open') state = 'closed';
        closing = tail
          .then(() => handle.close())
          .catch(() => {
            state = 'failed';
          });
      }
      return closing;
    },
  };
}
