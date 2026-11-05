import os from 'node:os';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { mkdtempSync, rmSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fixtureArchiveRequest, parseFixtureReceipt } from './archive';
import { integrationReplySchema, protocolJson } from '../protocol';

const source = path.resolve(__dirname, '../../../../../../custom/coding-agent/orchestrator/src');
const child = `
import sys, json
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from coding_orchestrator.job_store import JobStore
from coding_orchestrator.fixture_archive import canonical, catalog_bundles
request = json.loads(sys.argv[3])
with JobStore(Path(sys.argv[2]), fixture_namespace=request['namespace']) as store:
    state = store.fixtures.state()
    result = store.fixtures.dispatch(canonical(request))
    query = dict(version=1,kind='fixture_operation_query',namespace=request['namespace'],
                 operation_id=request['operation_id'])
    print(json.dumps(dict(state=state, result=result, query=store.fixtures.dispatch(canonical(query)),
                          digest=catalog_bundles()[request['bundle_index']][0])))
`;

it.each([0, 1])('verifies and atomically archives fixed bundle %i across TS/Python', (index) => {
  const root = mkdtempSync(path.join(os.tmpdir(), 's6-fixture-'));
  try {
    const namespace = randomUUID();
    const request = fixtureArchiveRequest(namespace, randomUUID(), 1, 0, index);
    const run = spawnSync(
      '/usr/bin/python3',
      ['-I', '-B', '-c', child, source, path.join(root, 'private/archive.sqlite'), request],
      { encoding: 'utf8', timeout: 20000 },
    );
    expect(run.error).toBeUndefined();
    expect(run.status).toBe(0);
    expect(run.stderr).toBe('');
    const response = JSON.parse(run.stdout);
    expect(response.state).toMatchObject({ owner_epoch: 1, version: 0, integrity: true });
    expect(response.digest).toBe(JSON.parse(request).bundle_digest);
    const receipt = parseFixtureReceipt(protocolJson(response.result.receipt), request);
    expect(receipt).toMatchObject({
      committed_version: 1,
      accepted_owner_epoch: 1,
      synthetic_only: true,
      live_authority: false,
      stop_confirmed: false,
      reservation_released: false,
      quarantine_clearance: false,
      result_publication_authority: false,
    });
    expect(response.query.receipt).toEqual(receipt);
    expect(response.query.state.version).toBe(1);
    expect(
      integrationReplySchema.safeParse({
        version: 1,
        backend: 'supervisor',
        namespace,
        kind: 'query',
        requestDigest: 'a'.repeat(64),
        resultDigest: 'b'.repeat(64),
        result: { status: 'found', receipt },
      }).success,
    ).toBe(false);
    for (const field of [
      'live_authority',
      'stop_confirmed',
      'reservation_released',
      'quarantine_clearance',
      'result_publication_authority',
    ]) {
      expect(() =>
        parseFixtureReceipt(protocolJson({ ...receipt, [field]: true }), request),
      ).toThrow();
    }
    expect(() =>
      parseFixtureReceipt(protocolJson({ ...receipt, class: 'runtime' }), request),
    ).toThrow();
    expect(() =>
      parseFixtureReceipt(protocolJson({ ...receipt, verdict: true }), request),
    ).toThrow();
    expect(() => parseFixtureReceipt(protocolJson(receipt) + '\n', request)).toThrow();
    expect(() => parseFixtureReceipt(protocolJson(receipt), request + '\n')).toThrow();
    expect(() =>
      parseFixtureReceipt(
        protocolJson(receipt),
        protocolJson({ ...JSON.parse(request), verdict: true }),
      ),
    ).toThrow();
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

it.each([-1, 2, 0.5, NaN, Infinity])('rejects unsupported fixed bundle index %s', (index) => {
  expect(() => fixtureArchiveRequest(randomUUID(), randomUUID(), 1, 0, index)).toThrow();
});

it.each([0, -1, 0.5, Number.MAX_SAFE_INTEGER + 1])('rejects invalid owner %s', (epoch) => {
  expect(() => fixtureArchiveRequest(randomUUID(), randomUUID(), epoch, 0, 0)).toThrow();
});

it('rejects noncanonical identity and negative version before verification', () => {
  expect(() => fixtureArchiveRequest(randomUUID() + '\n', randomUUID(), 1, 0, 0)).toThrow();
  expect(() => fixtureArchiveRequest(randomUUID(), randomUUID(), 1, -1, 0)).toThrow();
});
