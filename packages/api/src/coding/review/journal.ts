import { z } from 'zod';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { realpath } from 'node:fs/promises';
import type { CodeReviewRequest, CodeReviewResult } from 'librechat-data-provider';
import type { IntegrationCommand, IntegrationReply } from './protocol';
import type { ReviewPrincipal } from './worker';
import {
  bindIntegrationReply,
  integrationCommandSchema,
  integrationReplySchema,
  protocolDigest,
  protocolId,
  protocolJson,
} from './protocol';
import { reviewRequestSchema, reviewResultSchema } from './schema';
import { reviewRunIdSchema } from './identity';
import { ReviewWorkerError } from './worker';

export interface ReviewJournalRecord {
  id: string;
  state: 'queued' | 'running' | 'cancelling' | 'completed' | 'cancelled' | 'interrupted';
  request?: CodeReviewRequest;
  model?: string;
  result?: CodeReviewResult;
  expiresAt: number;
  cancelRequested: boolean;
}

export interface ReviewJournal {
  readonly signal: AbortSignal;
  assertReady(): void;
  admit(
    id: string,
    request: CodeReviewRequest,
    principal: ReviewPrincipal,
    model: string,
  ): Promise<boolean>;
  get(id: string, principal: ReviewPrincipal): Promise<ReviewJournalRecord | null>;
  cancel(id: string, principal: ReviewPrincipal): Promise<void>;
  finish(id: string, principal: ReviewPrincipal, result?: CodeReviewResult): Promise<boolean>;
  close(): Promise<void>;
}

/** Explicit service-side configuration only. No credentials are passed to this helper. */
export interface ReviewJournalConfig {
  python: string;
  sourceRoot: string;
  path: string;
}

const recordSchema: z.ZodType<ReviewJournalRecord> = z
  .object({
    id: z.string().uuid(),
    state: z.enum(['queued', 'running', 'cancelling', 'completed', 'cancelled', 'interrupted']),
    request: reviewRequestSchema.optional(),
    model: z.string().min(1).max(100).optional(),
    result: reviewResultSchema.optional(),
    expiresAt: z.number().finite().positive(),
    cancelRequested: z.boolean(),
  })
  .strict();
const replySchema = z.discriminatedUnion('ok', [
  z
    .object({
      sequence: z.number().int().positive(),
      ok: z.literal(true),
      created: z.boolean().optional(),
      record: recordSchema.nullable().optional(),
      integration: integrationReplySchema.optional(),
    })
    .strict(),
  z
    .object({
      sequence: z.number().int().positive(),
      ok: z.literal(false),
      code: z.enum(['busy', 'forbidden', 'invalid_request']),
    })
    .strict(),
]);
type Reply = z.infer<typeof replySchema>;
type Command = {
  operation: 'admit' | 'get' | 'cancel' | 'finish';
  id: string;
  principal: ReviewPrincipal;
  payload?: { request: CodeReviewRequest; model: string };
  result?: CodeReviewResult;
};
type IntegrationWire = {
  operation: 'integration_v1';
  payload: IntegrationCommand;
  payloadDigest: string;
};
const MAX_BYTES = 132096;

/** A helper failure permanently fences this journal; mutation commands are never retried. */
async function createChannel(config: ReviewJournalConfig, namespace?: string) {
  if (
    process.platform !== 'linux' ||
    ![config.python, config.sourceRoot, config.path].every(path.isAbsolute)
  )
    throw new ReviewWorkerError('configuration');
  const sourceRoot = await realpath(config.sourceRoot);
  await realpath(config.python);
  const child = spawn(
    config.python,
    [
      '-B',
      '-S',
      '-s',
      path.join(sourceRoot, 'coding_orchestrator/review_journal.py'),
      config.path,
      ...(namespace ? ['--integration-v1', namespace] : []),
    ],
    {
      cwd: sourceRoot,
      shell: false,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {
        PATH: '/usr/bin:/bin',
        LANG: 'C.UTF-8',
        HOME: '/nonexistent',
        PYTHONNOUSERSITE: '1',
        PYTHONDONTWRITEBYTECODE: '1',
      },
    },
  );
  const controller = new AbortController();
  const pending = new Map<
    number,
    {
      resolve: (value: Reply) => void;
      reject: (error: Error) => void;
      timer: ReturnType<typeof setTimeout>;
      command: Command | IntegrationWire;
    }
  >();
  let sequence = 0;
  let buffer = Buffer.alloc(0);
  let ready = false;
  let readyResolve!: () => void;
  let readyReject!: (error: Error) => void;
  const started = new Promise<void>((resolve, reject) => {
    readyResolve = resolve;
    readyReject = reject;
  });
  const fence = () => {
    if (controller.signal.aborted) return;
    controller.abort();
    clearTimeout(startupTimer);
    const error = new ReviewWorkerError('configuration');
    readyReject(error);
    pending.forEach(({ reject, timer }) => {
      clearTimeout(timer);
      reject(error);
    });
    pending.clear();
    child.kill('SIGKILL');
  };
  const startupTimer = setTimeout(fence, 5000);
  const exited = new Promise<void>((resolve) =>
    child.once('close', () => {
      fence();
      resolve();
    }),
  );
  child.once('error', fence);
  child.stdin.on('error', fence);
  child.stderr.on('data', fence);
  child.stdout.on('data', (chunk: Buffer) => {
    buffer = Buffer.concat([buffer, chunk]);
    while (true) {
      const end = buffer.indexOf(10);
      if (end < 0) break;
      if (end > MAX_BYTES) {
        fence();
        return;
      }
      const line = buffer.subarray(0, end);
      buffer = buffer.subarray(end + 1);
      try {
        const raw: unknown = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(line));
        if (!ready) {
          if (namespace) {
            const greeting = z
              .object({
                ready: z.literal(true),
                version: z.literal(1),
                backend: z.literal('supervisor'),
                namespace: z.literal(namespace),
              })
              .strict()
              .parse(raw);
            if (line.toString('utf8') !== protocolJson(greeting))
              throw new Error('Noncanonical greeting');
          } else {
            z.object({ ready: z.literal(true) })
              .strict()
              .parse(raw);
          }
          ready = true;
          clearTimeout(startupTimer);
          readyResolve();
          continue;
        }
        const reply = replySchema.parse(raw);
        const command = pending.get(reply.sequence);
        if (!command) throw new Error('Unexpected journal reply');
        if (namespace) {
          if (
            !reply.ok ||
            !reply.integration ||
            Object.keys(reply).length !== 3 ||
            command.command.operation !== 'integration_v1'
          )
            throw new Error('Wrong protocol reply');
          if (
            line.toString('utf8') !==
            protocolJson({ sequence: reply.sequence, ok: true, integration: reply.integration })
          )
            throw new Error('Noncanonical reply');
          bindIntegrationReply(command.command.payload, reply.integration);
        } else if (reply.ok && reply.integration) {
          throw new Error('Wrong journal mode');
        }
        clearTimeout(command.timer);
        pending.delete(reply.sequence);
        command.resolve(reply);
      } catch {
        fence();
        return;
      }
    }
    if (buffer.length > MAX_BYTES) fence();
  });
  await started;
  const assertReady = () => {
    if (!ready || controller.signal.aborted) throw new ReviewWorkerError('configuration');
  };
  const send = async (command: Command | IntegrationWire) => {
    assertReady();
    if (pending.size >= 64) throw new ReviewWorkerError('busy');
    const next = ++sequence;
    if (!Number.isSafeInteger(next)) {
      fence();
      throw new ReviewWorkerError('configuration');
    }
    const body =
      (command.operation === 'integration_v1'
        ? protocolJson({ ...command, sequence: next })
        : JSON.stringify({ ...command, sequence: next })) + '\n';
    if (Buffer.byteLength(body) > MAX_BYTES) throw new ReviewWorkerError('output_limit');
    const reply = await new Promise<Reply>((resolve, reject) => {
      const timer = setTimeout(fence, 10_000);
      pending.set(next, { resolve, reject, timer, command });
      child.stdin.write(body, (error) => {
        if (error) fence();
      });
    });
    assertReady();
    if (!reply.ok) throw new ReviewWorkerError(reply.code);
    return reply;
  };
  return {
    signal: controller.signal,
    assertReady,
    send,
    fence,
    async close() {
      fence();
      await exited;
    },
  };
}

export interface IntegrationJournal {
  readonly signal: AbortSignal;
  assertReady(): void;
  execute(command: IntegrationCommand): Promise<IntegrationReply['result']>;
  close(): Promise<void>;
}

/** Private, unregistered storage channel. Loss after sending leaves the outcome unknown. */
export async function createIntegrationJournal(
  config: ReviewJournalConfig,
  namespace: string,
): Promise<IntegrationJournal> {
  if (!protocolId.safeParse(namespace).success) throw new ReviewWorkerError('configuration');
  const channel = await createChannel(config, namespace);
  return {
    signal: channel.signal,
    assertReady: channel.assertReady,
    close: channel.close,
    async execute(command) {
      const parsed = integrationCommandSchema.safeParse(command);
      if (!parsed.success || parsed.data.namespace !== namespace)
        throw new ReviewWorkerError('invalid_request');
      const reply = await channel.send({
        operation: 'integration_v1',
        payload: parsed.data,
        payloadDigest: protocolDigest(parsed.data),
      });
      if (!reply.integration) {
        channel.fence();
        throw new ReviewWorkerError('configuration');
      }
      return reply.integration.result;
    },
  };
}

export async function createReviewJournal(config: ReviewJournalConfig): Promise<ReviewJournal> {
  const { signal, assertReady, send, fence, close } = await createChannel(config);
  return {
    signal,
    assertReady,
    async admit(id, request, principal, model) {
      const parsedId = reviewRunIdSchema.safeParse(id);
      if (!parsedId.success) throw new ReviewWorkerError('invalid_request');
      id = parsedId.data;
      const reply = await send({ operation: 'admit', id, principal, payload: { request, model } });
      if (reply.created === undefined || reply.record?.id !== id) {
        fence();
        throw new ReviewWorkerError('configuration');
      }
      if (!reply.created && reply.record.state === 'cancelled')
        throw new ReviewWorkerError('cancelled');
      return reply.created;
    },
    async get(id, principal) {
      const parsedId = reviewRunIdSchema.safeParse(id);
      if (!parsedId.success) throw new ReviewWorkerError('invalid_request');
      id = parsedId.data;
      const reply = await send({ operation: 'get', id, principal });
      if (reply.record === undefined || (reply.record !== null && reply.record.id !== id)) {
        fence();
        throw new ReviewWorkerError('configuration');
      }
      return reply.record;
    },
    async cancel(id, principal) {
      const parsedId = reviewRunIdSchema.safeParse(id);
      if (!parsedId.success) throw new ReviewWorkerError('invalid_request');
      id = parsedId.data;
      await send({ operation: 'cancel', id, principal });
    },
    async finish(id, principal, result) {
      const parsedId = reviewRunIdSchema.safeParse(id);
      if (!parsedId.success) throw new ReviewWorkerError('invalid_request');
      id = parsedId.data;
      const reply = await send({
        operation: 'finish',
        id,
        principal,
        ...(result ? { result } : {}),
      });
      if (
        reply.record?.id !== id ||
        !['completed', 'cancelled', 'interrupted'].includes(reply.record.state)
      ) {
        fence();
        throw new ReviewWorkerError('configuration');
      }
      return reply.record.state === 'completed';
    },
    close,
  };
}
