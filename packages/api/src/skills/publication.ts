import type { SkillBundleManifest, SkillBundleSnapshot } from './bundles';
import { SkillSelectionError } from './selection';
import { captureSkillBundle } from './bundles';

export interface SkillBundlePublisher {
  readonly userId: string;
  readonly tenantId: string | null;
}

export interface SkillBundlePublicationCandidate {
  /** One immutable committed draft generation, including definition and complete file manifest. */
  manifest: SkillBundleManifest;
  readFile: Parameters<typeof captureSkillBundle>[0]['readFile'];
  expectedPublishedRevision: string | null;
}

export interface SkillBundlePublicationCommit {
  readonly actor: Readonly<SkillBundlePublisher>;
  readonly skillId: string;
  readonly expectedSourceRevision: string;
  readonly expectedPublishedRevision: string | null;
  readonly snapshot: SkillBundleSnapshot;
}

export interface SkillBundlePublicationDeps {
  /** Authenticate/authorize and read one committed generation, never independent mutable rows. */
  loadCandidate: (
    skillId: string,
    actor: Readonly<SkillBundlePublisher>,
  ) => Promise<SkillBundlePublicationCandidate | null>;
  inspect: (snapshot: SkillBundleSnapshot, actor: Readonly<SkillBundlePublisher>) => Promise<void>;
  /**
   * One atomic transaction must reauthorize, check existence/tenant and BOTH expected revisions,
   * durably store the exact snapshot, then advance the publication pointer. Any failed check
   * makes no changes. Generation IDs must never be reused, including edit-and-revert cycles.
   * An uncertain acknowledgement must throw; it must not be guessed into success or retried.
   */
  compareAndPublish: (commit: Readonly<SkillBundlePublicationCommit>) => Promise<boolean>;
}

/** Dormant protocol coordinator. No live adapter, persistence, routes or automatic retries. */
export async function publishSkillBundle(
  deps: SkillBundlePublicationDeps,
  skillId: string,
  actor: SkillBundlePublisher,
): Promise<SkillBundleSnapshot> {
  try {
    if (
      typeof skillId !== 'string' ||
      !/^[a-f0-9]{24}$/.test(skillId) ||
      typeof actor.userId !== 'string' ||
      !actor.userId ||
      (actor.tenantId !== null && typeof actor.tenantId !== 'string')
    )
      throw new SkillSelectionError();
    const publisher = Object.freeze({ userId: actor.userId, tenantId: actor.tenantId });
    const candidate = await deps.loadCandidate(skillId, publisher);
    if (!candidate) throw new SkillSelectionError();
    if (
      candidate.manifest.skillId !== skillId ||
      candidate.manifest.tenantId !== publisher.tenantId
    ) {
      throw new SkillSelectionError();
    }
    const expectedPublishedRevision = candidate.expectedPublishedRevision;
    if (
      expectedPublishedRevision !== null &&
      (typeof expectedPublishedRevision !== 'string' ||
        !/^[a-f0-9]{64}$/.test(expectedPublishedRevision))
    ) {
      throw new SkillSelectionError();
    }
    const snapshot = await captureSkillBundle(candidate);
    const manifest = JSON.parse(snapshot.manifestJson) as SkillBundleManifest;
    if (manifest.skillId !== skillId || manifest.tenantId !== publisher.tenantId) {
      throw new SkillSelectionError();
    }
    await deps.inspect(snapshot, publisher);
    const committed = await deps.compareAndPublish(
      Object.freeze({
        actor: publisher,
        skillId,
        expectedSourceRevision: manifest.sourceRevision,
        expectedPublishedRevision,
        snapshot,
      }),
    );
    if (committed !== true) throw new SkillSelectionError();
    return snapshot;
  } catch {
    throw new SkillSelectionError();
  }
}
