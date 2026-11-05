import { z } from 'zod';
import { createHash } from 'node:crypto';

type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

/** Canonical ASCII protocol JSON; consistency digests do not authenticate evidence. */
export function protocolJson(value: Json): string {
  if (Array.isArray(value)) return `[${value.map(protocolJson).join(',')}]`;
  if (value !== null && typeof value === 'object') {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${protocolJson(value[key])}`)
      .join(',')}}`;
  }
  return JSON.stringify(value);
}

export function protocolDigest(value: Json): string {
  return createHash('sha256').update(protocolJson(value), 'ascii').digest('hex');
}

export const protocolId = z.string().regex(/^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}(?![\s\S])/);
const counter = z.number().int().min(0).max(Number.MAX_SAFE_INTEGER);
const positive = counter.min(1);
const digest = z.string().regex(/^[0-9a-f]{64}(?![\s\S])/);
const text = z
  .string()
  .max(256)
  .regex(/^(?:[\x21-\x7e](?:[\x20-\x7e]*[\x21-\x7e])?)?(?![\s\S])/);
export const integrationMappingSchema = z
  .object({
    review_id: protocolId,
    attempt_id: protocolId,
    logical_generation: positive,
    user_id: text.min(1),
    tenant_id: text,
    repository_alias: text.min(1),
    base: z.string().regex(/^[0-9a-f]{40}(?![\s\S])/),
    head: z.string().regex(/^[0-9a-f]{40}(?![\s\S])/),
    profile_id: text.min(1),
    model: text.min(1),
  })
  .strict();
const common = { version: z.literal(1), backend: z.literal('supervisor'), namespace: protocolId };
const target = { mapping: integrationMappingSchema, operation_id: protocolId };
const fence = { owner_epoch: positive, expected_version: counter };
const observation = {
  evidence_id: protocolId,
  producer: z.enum(['guest', 'host']),
  producer_epoch: protocolId,
  sequence: positive,
  prior_binding_head: digest,
  data: z.string().min(1).max(87384).refine((value) => {
    const bytes = Buffer.from(value, 'base64');
    return bytes.length > 0 && bytes.length <= 65536 && bytes.toString('base64') === value;
  }),
};
export const integrationCommandSchema = z.discriminatedUnion('kind', [
  z.object({ ...common, kind: z.literal('snapshot') }).strict(),
  z.object({ ...common, kind: z.literal('query'), ...target }).strict(),
  z.object({ ...common, kind: z.literal('admit'), ...target, ...fence }).strict(),
  z.object({ ...common, kind: z.literal('cancel'), ...target, ...fence }).strict(),
  z.object({ ...common, kind: z.literal('observe'), ...target, ...fence, ...observation }).strict(),
  z.object({
    ...common,
    kind: z.literal('finish'),
    mapping: integrationMappingSchema,
    ...fence,
    verification_receipt_id: protocolId,
  }).strict(),
]);
export type IntegrationCommand = z.infer<typeof integrationCommandSchema>;
const receipt = z.object({
  operation_id: protocolId,
  namespace: protocolId,
  review_id: protocolId,
  kind: z.enum(['admission_recorded', 'cancellation_intent_only', 'unverified_observation_recorded']),
  version: positive,
  owner_epoch: positive,
  live_authority: z.literal(false),
  stop_confirmed: z.literal(false),
  reservation_released: z.literal(false),
}).strict();
const bit = z.union([z.literal(0), z.literal(1)]);
const snapshot = z.object({
  singleton: z.literal(1),
  namespace: protocolId,
  schema_version: z.literal(1),
  backend: z.literal('supervisor'),
  owner_epoch: positive,
  version: counter,
  recovery: bit,
  embargo: bit,
  quarantine: bit,
  schema_digest: digest,
  evidence_intact: z.boolean(),
}).strict();
export const integrationReplySchema = z.object({
  ...common,
  kind: z.enum(['snapshot', 'query', 'admit', 'cancel', 'observe', 'finish']),
  requestDigest: digest,
  resultDigest: digest,
  result: z.discriminatedUnion('status', [
    z.object({ status: z.literal('snapshot'), snapshot }).strict(),
    z.object({ status: z.literal('recorded'), receipt }).strict(),
    z.object({ status: z.literal('found'), receipt }).strict(),
    z.object({ status: z.literal('not_found') }).strict(),
    z.object({ status: z.literal('verification_unavailable') }).strict(),
    z.object({ status: z.literal('rejected'), code: z.enum(['busy', 'forbidden', 'conflict']) }).strict(),
  ]),
}).strict();
export type IntegrationReply = z.infer<typeof integrationReplySchema>;

export function bindIntegrationReply(command: IntegrationCommand, reply: IntegrationReply): void {
  const result = reply.result;
  if (reply.namespace !== command.namespace || reply.kind !== command.kind ||
      reply.requestDigest !== protocolDigest(command) || reply.resultDigest !== protocolDigest(result)) {
    throw new Error('Protocol reply binding mismatch');
  }
  if (result.status === 'rejected') return;
  if (command.kind === 'snapshot' && result.status === 'snapshot' &&
      result.snapshot.namespace === command.namespace) return;
  if (command.kind === 'finish' && result.status === 'verification_unavailable') return;
  if (command.kind === 'query' && result.status === 'not_found') return;
  if ((command.kind === 'query' && result.status === 'found') ||
      (['admit', 'cancel', 'observe'].includes(command.kind) && result.status === 'recorded')) {
    if (!('operation_id' in command) || !('receipt' in result)) throw new Error('Missing receipt');
    if (result.receipt.operation_id !== command.operation_id ||
        result.receipt.namespace !== command.namespace ||
        result.receipt.review_id !== command.mapping.review_id) throw new Error('Receipt target mismatch');
    const kinds = { admit: 'admission_recorded', cancel: 'cancellation_intent_only', observe: 'unverified_observation_recorded' };
    if (command.kind !== 'query' && command.kind in kinds &&
        result.receipt.kind !== kinds[command.kind as keyof typeof kinds]) throw new Error('Receipt kind mismatch');
    return;
  }
  throw new Error('Unexpected protocol result');
}
