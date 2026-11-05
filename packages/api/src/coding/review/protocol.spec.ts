import os from 'node:os';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { createIntegrationJournal, createReviewJournal } from './journal';
import { integrationCommandSchema, integrationReplySchema, protocolDigest, protocolJson } from './protocol';

const mapping = {
  review_id: '550e8400-e29b-41d4-a716-446655440000',
  attempt_id: '550e8400-e29b-41d4-a716-446655440001',
  logical_generation: 1,
  user_id: 'fixture',
  tenant_id: '',
  repository_alias: 'fixture',
  base: 'a'.repeat(40),
  head: 'b'.repeat(40),
  profile_id: 'quote" slash\\',
  model: 'fixture',
};
const common = {
  version: 1 as const,
  backend: 'supervisor' as const,
  namespace: '550e8400-e29b-41d4-a716-446655440002',
};

it('agrees on canonical escaping and digest with the Python vector', () => {
  const vector = { tenant: '', text: 'quote" slash\\' };
  expect(protocolJson(vector)).toBe('{"tenant":"","text":"quote\\" slash\\\\"}');
  expect(protocolDigest(vector)).toBe('e02a7b89943384c33b0e84d815acc23566f3b232d5bdf6556c78490972dd8440');
});

it.each([
  { field: 'version', value: 2 },
  { field: 'backend', value: 'local' },
  { field: 'namespace', value: common.namespace.toUpperCase() },
  { field: 'namespace', value: common.namespace + '\n' },
  { field: 'success', value: true },
])('rejects malformed $field locally', ({ field, value }) => {
  expect(integrationCommandSchema.safeParse({ ...common, kind: 'snapshot', [field]: value }).success).toBe(false);
});

it.each(['review_id', 'attempt_id', 'user_id', 'tenant_id', 'repository_alias', 'base', 'head', 'profile_id', 'model'] as const)(
  'rejects trailing newline in mapping %s', (field) => {
    expect(integrationCommandSchema.safeParse({ ...common, kind: 'query', operation_id: randomUUID(),
      mapping: { ...mapping, [field]: mapping[field] + '\n' } }).success).toBe(false);
  },
);

it('rejects trailing newline in reply digests', () => {
  expect(integrationReplySchema.safeParse({ ...common, kind: 'query', requestDigest: 'a'.repeat(64) + '\n',
    resultDigest: 'b'.repeat(64), result: { status: 'not_found' } }).success).toBe(false);
});

it('round trips strict storage commands and historical receipts without completion authority', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'journal-protocol-'));
  const config = {
    python: '/usr/bin/python3',
    sourceRoot: path.resolve(__dirname, '../../../../../custom/coding-agent/orchestrator/src'),
    path: path.join(root, 'private/reviews.sqlite'),
  };
  let journal = await createIntegrationJournal(config, common.namespace);
  try {
    const snapshot = await journal.execute({ ...common, kind: 'snapshot' });
    expect(snapshot).toMatchObject({ status: 'snapshot', snapshot: { owner_epoch: 1, version: 0 } });
    const operation_id = randomUUID();
    const command = { ...common, kind: 'admit' as const, mapping, operation_id, owner_epoch: 1, expected_version: 0 };
    const accepted = await journal.execute(command);
    expect(accepted).toMatchObject({ status: 'recorded', receipt: { live_authority: false, stop_confirmed: false } });
    const [query, missing] = await Promise.all([
      journal.execute({ ...common, kind: 'query', mapping, operation_id }),
      journal.execute({ ...common, kind: 'query', mapping, operation_id: randomUUID() }),
    ]);
    expect(query).toMatchObject({ status: 'found', receipt: { operation_id, owner_epoch: 1, version: 1 } });
    expect(missing).toEqual({ status: 'not_found' });
    await expect(journal.execute({ ...common, kind: 'finish', mapping, owner_epoch: 1,
      expected_version: 1, verification_receipt_id: randomUUID() })).resolves.toEqual({ status: 'verification_unavailable' });
    const observation = { ...common, kind: 'observe' as const, mapping, operation_id: randomUUID(),
      owner_epoch: 1, expected_version: 1, evidence_id: randomUUID(), producer: 'guest' as const,
      producer_epoch: randomUUID(), sequence: 1, prior_binding_head: protocolDigest(mapping),
      data: Buffer.from('{"success":true,"stopped":true}').toString('base64') };
    const observed = await journal.execute(observation);
    expect(observed).toMatchObject({ status: 'recorded', receipt: {
      kind: 'unverified_observation_recorded', stop_confirmed: false, reservation_released: false } });
    await expect(journal.execute(observation)).resolves.toEqual(observed);
    await expect(journal.execute({ ...common, kind: 'query', mapping,
      operation_id: observation.operation_id })).resolves.toMatchObject({
      status: 'found', receipt: { operation_id: observation.operation_id, version: 2 },
    });
    await journal.close();
    expect(journal.signal.aborted).toBe(true);
    await expect(journal.execute(command)).rejects.toMatchObject({ code: 'configuration' });
    await expect(createReviewJournal(config)).rejects.toMatchObject({ code: 'configuration' });
    journal = await createIntegrationJournal(config, common.namespace);
    await expect(journal.execute({ ...common, kind: 'snapshot' })).resolves.toMatchObject({
      status: 'snapshot', snapshot: { owner_epoch: 2, version: 3, recovery: 1 },
    });
    await expect(journal.execute({ ...common, kind: 'query', mapping, operation_id })).resolves.toMatchObject({
      status: 'found', receipt: { owner_epoch: 1, version: 1 },
    });
    await expect(journal.execute({ ...common, kind: 'cancel', mapping, operation_id: randomUUID(),
      owner_epoch: 2, expected_version: 3 })).resolves.toMatchObject({
      status: 'recorded', receipt: { kind: 'cancellation_intent_only', stop_confirmed: false },
    });
  } finally {
    await journal.close();
    await rm(root, { recursive: true, force: true });
  }
});

it.each(['digest', 'namespace', 'kind', 'duplicate', 'authority', 'sequence', 'timeout'])(
  'fences all pending requests on a fabricated malformed %s reply', async (fault) => {
    const root = await mkdtemp(path.join(os.tmpdir(), 'journal-reply-'));
    const sourceRoot = path.join(root, 'source');
    await mkdir(path.join(sourceRoot, 'coding_orchestrator'), { recursive: true });
    // A deliberately malformed pipe peer, not a replacement for the round-trip test.
    const script = `import json,sys,hashlib
def encoded(value):
 return json.dumps(value,sort_keys=True,separators=(',',':'))
namespace=sys.argv[3]
print(encoded(dict(ready=True,version=1,backend='supervisor',namespace=namespace)),flush=True)
command=json.loads(sys.stdin.readline())
if ${JSON.stringify(fault)}=='timeout': sys.stdin.read(); sys.exit(0)
result=dict(status='not_found')
reply=dict(version=1,backend='supervisor',namespace=namespace,kind='query',requestDigest=command['payloadDigest'],resultDigest=hashlib.sha256(encoded(result).encode()).hexdigest(),result=result)
fault=${JSON.stringify(fault)}
if fault=='digest': reply['resultDigest']='0'*64
if fault=='namespace': reply['namespace']='550e8400-e29b-41d4-a716-446655440003'
if fault=='kind': reply['kind']='finish'
if fault=='authority': reply['result']['stop_confirmed']=True
wire=encoded(dict(sequence=99 if fault=='sequence' else command['sequence'],ok=True,integration=reply))
if fault=='duplicate': wire=wire.replace('"ok":true','"ok":true,"ok":true')
print(wire,flush=True)
sys.stdin.read()
`;
    await writeFile(path.join(sourceRoot, 'coding_orchestrator/review_journal.py'), script);
    const journal = await createIntegrationJournal({ python: '/usr/bin/python3', sourceRoot,
      path: path.join(root, 'unused.sqlite') }, common.namespace);
    try {
      const first = journal.execute({ ...common, kind: 'query', mapping, operation_id: randomUUID() });
      const second = journal.execute({ ...common, kind: 'query', mapping, operation_id: randomUUID() });
      const results = await Promise.allSettled([first, second]);
      expect(results.map((value) => value.status)).toEqual(['rejected', 'rejected']);
      expect(journal.signal.aborted).toBe(true);
      await expect(journal.execute({ ...common, kind: 'snapshot' })).rejects.toMatchObject({ code: 'configuration' });
    } finally {
      await journal.close();
      await rm(root, { recursive: true, force: true });
    }
  },
  20_000,
);
