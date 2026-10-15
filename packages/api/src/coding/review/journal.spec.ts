import os from 'node:os';
import path from 'node:path';
import { mkdtemp, rm } from 'node:fs/promises';
import type { CodeReviewResult } from 'librechat-data-provider';
import { createReviewJournal } from './journal';

it('normalizes concurrent pipe commands, completion, cancellation and restart', async () => {
  const root = await mkdtemp(path.join(os.tmpdir(), 'review-uuid-'));
  const config = {
    python: '/usr/bin/python3',
    sourceRoot: path.resolve(__dirname, '../../../../../custom/coding-agent/orchestrator/src'),
    path: path.join(root, 'private/reviews.sqlite'),
  };
  const id = '550e8400-e29b-41d4-a716-446655440000';
  const principal = { userId: 'alice', tenantId: 'tenant' };
  const request = { repository: 'fixture', base: 'a'.repeat(40), head: 'b'.repeat(40) };
  const model = 'fixture-model';
  const result: CodeReviewResult = {
    ...request,
    model,
    provider: 'chatgpt_subscription',
    status: 'human_review_required',
    findings: [],
  };
  let journal = await createReviewJournal(config);
  try {
    expect(
      await Promise.all([
        journal.admit(id.toUpperCase(), request, principal, model),
        journal.admit(id, request, principal, model),
      ]),
    ).toEqual([true, false]);
    await expect(journal.get(id.toUpperCase(), principal)).resolves.toMatchObject({
      id,
      state: 'running',
    });
    await expect(journal.finish(id.toUpperCase(), principal, result)).resolves.toBe(true);
    const cancelled = '550e8400-e29b-41d4-a716-446655440001';
    await journal.cancel(cancelled.toUpperCase(), principal);
    await journal.close();
    journal = await createReviewJournal(config);
    await expect(journal.admit(id.toUpperCase(), request, principal, model)).resolves.toBe(false);
    await expect(journal.get(id.toUpperCase(), principal)).resolves.toMatchObject({
      id,
      state: 'completed',
      result,
    });
    await expect(journal.admit(cancelled, request, principal, model)).rejects.toMatchObject({
      code: 'cancelled',
    });
    await expect(journal.get(id, { ...principal, tenantId: 'other' })).resolves.toBeNull();
  } finally {
    await journal.close();
    await rm(root, { recursive: true, force: true });
  }
});
