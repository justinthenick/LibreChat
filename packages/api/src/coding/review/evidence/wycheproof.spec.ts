import path from 'node:path';
import { readFileSync } from 'node:fs';
import { createHash, createPublicKey, verify } from 'node:crypto';
import { verifyPublicFixture } from './verify';
import corpus from './fixtures/ed25519.json';

type Outcome = 'length_rejected' | 'verification_rejected' | 'verified';
type Classification = 'valid' | 'invalid' | 'acceptable';
type Observation = {
  tcId: number;
  flags: string[];
  expected: Classification;
  outcome: Outcome;
  apiAccepted: boolean;
};
const cases = corpus.testGroups.flatMap((group) =>
  group.tests.map((test) => ({ ...test, keyHex: group.publicKey.pk })),
);
const observations: Observation[] = [];

function decode(hex: string): Buffer {
  if (!/^(?:[0-9a-f]{2})*$/.test(hex)) throw new Error('Unexpected corpus hex encoding');
  return Buffer.from(hex, 'hex');
}

function direct(message: Buffer, keyBytes: Buffer, signature: Buffer): Outcome {
  if (keyBytes.length !== 32 || signature.length !== 64) return 'length_rejected';
  const key = createPublicKey({
    key: Buffer.concat([Buffer.from('302a300506032b6570032100', 'hex'), keyBytes]),
    format: 'der',
    type: 'spki',
  });
  return verify(null, message, key, signature) ? 'verified' : 'verification_rejected';
}

describe('independent public Wycheproof Ed25519 corpus, not signed S4 profile acceptance', () => {
  it('pins source bytes, complete case coverage and the measured runtime', () => {
    const bytes = readFileSync(path.join(__dirname, 'fixtures/ed25519.json'));
    expect(createHash('sha256').update(bytes).digest('hex')).toBe(
      'ea80ffebac085e21cb9d3e903e7fa2b448d96702da5b31f061d0b83b430b74b3',
    );
    expect(process.versions.node).toBe('24.16.0');
    expect(process.versions.openssl).toBe('3.5.6');
    expect(corpus.algorithm).toBe('EDDSA');
    expect(corpus.testGroups).toHaveLength(111);
    expect(corpus.testGroups.every((group) => group.type === 'EddsaVerify')).toBe(true);
    expect(corpus.testGroups.every((group) => group.publicKey.curve === 'edwards25519')).toBe(true);
    expect(cases).toHaveLength(210);
    expect(new Set(cases.map((test) => test.tcId)).size).toBe(210);
    expect(cases.filter((test) => test.result === 'valid')).toHaveLength(117);
    expect(cases.filter((test) => test.result === 'invalid')).toHaveLength(64);
    expect(cases.filter((test) => test.result === 'acceptable')).toHaveLength(29);
    console.info(
      `Wycheproof runtime Node=${process.versions.node} OpenSSL=${process.versions.openssl}`,
    );
  });

  it.each(cases)('tcId=$tcId expected=$result flags=$flags', (test) => {
    const message = decode(test.msg);
    const key = decode(test.keyHex);
    const signature = decode(test.sig);
    expect(message.length).toBeLessThanOrEqual(16384);
    if (!['valid', 'invalid', 'acceptable'].includes(test.result)) {
      throw new Error(`Unexpected classification for tcId=${test.tcId}`);
    }
    const outcome = direct(message, key, signature);
    const apiAccepted = verifyPublicFixture(message, key, signature);
    observations.push({
      tcId: test.tcId,
      flags: test.flags,
      expected: test.result as Classification,
      outcome,
      apiAccepted,
    });
    expect(apiAccepted).toBe(outcome === 'verified');
    if (test.result === 'valid') expect(outcome).toBe('verified');
    if (test.result === 'invalid') expect(outcome).not.toBe('verified');
  });

  it('accounts for every case and reports acceptable outcomes separately', () => {
    console.info(`Wycheproof observations ${JSON.stringify(observations)}`);
    expect(observations).toHaveLength(210);
    for (const expected of ['valid', 'invalid', 'acceptable']) {
      const results = observations.filter((item) => item.expected === expected);
      const rejected = results.filter((item) => item.outcome === 'verification_rejected');
      const summary = {
        total: results.length,
        verified: results.filter((item) => item.outcome === 'verified').length,
        lengthRejected: results.filter((item) => item.outcome === 'length_rejected').length,
        verificationRejected: rejected.length,
      };
      console.info(`Wycheproof ${expected} ${JSON.stringify(summary)}`);
    }
  });
});
