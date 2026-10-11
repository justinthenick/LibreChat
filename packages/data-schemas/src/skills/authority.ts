import { createHash } from 'node:crypto';
import type { Connection, mongo } from 'mongoose';
import type { CaptureIdentity } from './persistence';

export type CaptureOperation = 'source' | 'reserve' | 'complete' | 'fail' | 'recover' | 'edit';

export interface CaptureAuthorization extends CaptureIdentity {
  sourceId: string;
  epoch: number;
}

export interface SyntheticCaptureGrant extends CaptureAuthorization {
  operations: readonly CaptureOperation[];
}

export interface IsolatedCaptureAuthority {
  replace: (
    actor: CaptureIdentity,
    sourceId: string,
    expectedEpoch: number,
    operations: readonly CaptureOperation[],
  ) => Promise<SyntheticCaptureGrant>;
  read: (actor: CaptureIdentity, sourceId: string) => Promise<SyntheticCaptureGrant | null>;
  fence: (
    session: mongo.ClientSession,
    authorization: CaptureAuthorization,
    actor: CaptureIdentity,
    sourceId: string,
    operation: CaptureOperation,
  ) => Promise<void>;
}

interface AuthorityRecord extends SyntheticCaptureGrant {
  _id: string;
  uses: number;
}

function deny(): never {
  throw new Error('skill_capture_authorization_denied');
}

function scope(actor: CaptureIdentity, sourceId: string): CaptureIdentity & { sourceId: string } {
  if (
    typeof actor.ownerId !== 'string' ||
    !actor.ownerId ||
    actor.ownerId.length > 256 ||
    (actor.tenantId !== null &&
      (typeof actor.tenantId !== 'string' || !actor.tenantId || actor.tenantId.length > 256)) ||
    typeof sourceId !== 'string' ||
    !/^[a-f0-9]{24}$/.test(sourceId)
  )
    deny();
  return { ownerId: actor.ownerId, tenantId: actor.tenantId, sourceId };
}

function key(actor: CaptureIdentity & { sourceId: string }): string {
  return createHash('sha256')
    .update(JSON.stringify([actor.tenantId, actor.ownerId, actor.sourceId]))
    .digest('hex');
}

export function captureAuthorizationCopy(input: CaptureAuthorization): CaptureAuthorization {
  const who = scope(input, input.sourceId);
  if (!Number.isSafeInteger(input.epoch) || input.epoch < 1) deny();
  return Object.freeze({ ...who, epoch: input.epoch });
}

/** Isolated proof only: this grants synthetic actors, never application users or ACL entries. */
export async function createIsolatedCaptureAuthority(
  connection: Connection,
): Promise<IsolatedCaptureAuthority> {
  const db = connection.db;
  if (!db || !/^test_skill_capture_[a-z0-9_]+$/.test(db.databaseName))
    throw new Error('skill_capture_isolation_required');
  const hello = await db.admin().command({ hello: 1 });
  if (!hello.setName || hello.logicalSessionTimeoutMinutes == null)
    throw new Error('skill_capture_transactions_unavailable');
  const records = db.collection<AuthorityRecord>('capture_authority');
  await records.createIndex({ _id: 1 });

  async function replace(
    actor: CaptureIdentity,
    sourceId: string,
    expectedEpoch: number,
    inputOperations: readonly CaptureOperation[],
  ): Promise<SyntheticCaptureGrant> {
    const who = scope(actor, sourceId);
    const operations = [...inputOperations];
    if (
      !Number.isSafeInteger(expectedEpoch) ||
      expectedEpoch < 0 ||
      expectedEpoch >= Number.MAX_SAFE_INTEGER ||
      (expectedEpoch === Number.MAX_SAFE_INTEGER - 1 && operations.length > 0) ||
      operations.length > 6 ||
      new Set(operations).size !== operations.length ||
      operations.some(
        (op) => !['source', 'reserve', 'complete', 'fail', 'recover', 'edit'].includes(op),
      )
    )
      deny();
    const grant = { ...who, epoch: expectedEpoch + 1, operations };
    const options = { writeConcern: { w: 'majority' as const, j: true } };
    if (expectedEpoch === 0) {
      await records.insertOne({ _id: key(who), ...grant, uses: 0 }, options);
    } else {
      const result = await records.updateOne(
        { _id: key(who), ...who, epoch: expectedEpoch },
        { $set: grant },
        options,
      );
      if (result.modifiedCount !== 1) deny();
    }
    return Object.freeze({ ...grant, operations: Object.freeze(operations) });
  }

  async function read(
    actor: CaptureIdentity,
    sourceId: string,
  ): Promise<SyntheticCaptureGrant | null> {
    const who = scope(actor, sourceId);
    const grant = await records.findOne(
      { _id: key(who), ...who },
      { readPreference: 'primary', readConcern: { level: 'majority' } },
    );
    if (!grant) return null;
    return Object.freeze({
      ...captureAuthorizationCopy(grant),
      operations: Object.freeze([...grant.operations]),
    });
  }

  /** The caller must write capture state and receipt using this same active transaction. */
  async function fence(
    session: mongo.ClientSession,
    input: CaptureAuthorization,
    actor: CaptureIdentity,
    sourceId: string,
    operation: CaptureOperation,
  ): Promise<void> {
    const ticket = captureAuthorizationCopy(input);
    const who = scope(actor, sourceId);
    if (
      !session.inTransaction() ||
      ticket.epoch === Number.MAX_SAFE_INTEGER ||
      ticket.ownerId !== who.ownerId ||
      ticket.tenantId !== who.tenantId ||
      ticket.sourceId !== who.sourceId ||
      !['source', 'reserve', 'complete', 'fail', 'recover', 'edit'].includes(operation)
    )
      deny();
    const result = await records.updateOne(
      {
        _id: key(who),
        ...ticket,
        operations: operation,
        uses: { $gte: 0, $lt: Number.MAX_SAFE_INTEGER },
      },
      { $inc: { uses: 1 } },
      { session },
    );
    if (result.modifiedCount !== 1) deny();
  }

  return { replace, read, fence };
}
