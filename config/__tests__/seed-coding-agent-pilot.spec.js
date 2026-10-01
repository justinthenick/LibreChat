jest.mock('../connect', () => jest.fn());

const mongoose = require('mongoose');
const {
  disconnectMongoose,
  validateManifestSkillPolicy,
  resolveSkillAllowlist,
} = require('../seed-coding-agent-pilot');

function validatedSkills() {
  return [
    {
      name: 'codebase-design',
      source: 'github',
      source_id: 'coding-agent-skills',
      owner: 'justinthenick',
      repo: 'LibreChat',
      ref: 'server/synology',
      path: '.agents/skills/codebase-design',
    },
    {
      name: 'systematic-debugging',
      source: 'github',
      source_id: 'managed-skills',
      owner: 'justinthenick',
      repo: 'LibreChat',
      ref: 'server/synology',
      path: 'managed-skills/skills/systematic-debugging',
    },
    {
      name: 'test-driven-development',
      source: 'github',
      source_id: 'managed-skills',
      owner: 'justinthenick',
      repo: 'LibreChat',
      ref: 'server/synology',
      path: 'managed-skills/skills/test-driven-development',
    },
    {
      name: 'verification-before-completion',
      source: 'github',
      source_id: 'managed-skills',
      owner: 'justinthenick',
      repo: 'LibreChat',
      ref: 'server/synology',
      path: 'managed-skills/skills/verification-before-completion',
    },
  ];
}

function validSkillManifest() {
  return {
    id: 'agent_software_engineering_pilot_v01',
    skills_enabled: true,
    skills: validatedSkills(),
  };
}

describe('disconnectMongoose', () => {
  const originalModels = mongoose.models;

  afterEach(() => {
    mongoose.models = originalModels;
    jest.restoreAllMocks();
  });

  it('waits for all registered model initializations before disconnecting', async () => {
    const order = [];

    mongoose.models = {
      ModelA: {
        init: jest.fn(async () => {
          order.push('modelA.init');
        }),
      },
      ModelB: {
        init: jest.fn(async () => {
          order.push('modelB.init');
        }),
      },
    };

    jest.spyOn(mongoose, 'disconnect').mockImplementation(async () => {
      order.push('disconnect');
    });

    await disconnectMongoose();

    expect(order).toEqual(['modelA.init', 'modelB.init', 'disconnect']);
  });

  it('disconnects cleanly but surfaces genuine model initialization failures', async () => {
    const order = [];

    mongoose.models = {
      BrokenModel: {
        init: jest.fn(async () => {
          order.push('broken.init');
          throw new Error('real index initialization failure');
        }),
      },
      HealthyModel: {
        init: jest.fn(async () => {
          order.push('healthy.init');
        }),
      },
    };

    const disconnectSpy = jest.spyOn(mongoose, 'disconnect').mockImplementation(async () => {
      order.push('disconnect');
    });

    await expect(disconnectMongoose()).rejects.toThrow(
      /1 Mongoose model initialization\(s\) failed before disconnect/,
    );

    expect(disconnectSpy).toHaveBeenCalledTimes(1);
    expect(order).toEqual(['broken.init', 'healthy.init', 'disconnect']);
  });

  it('can suppress initialization failures when cleaning up an already-failed seed', async () => {
    mongoose.models = {
      BrokenModel: {
        init: jest.fn(async () => {
          throw new Error('existing seed failure cleanup');
        }),
      },
    };

    const disconnectSpy = jest.spyOn(mongoose, 'disconnect').mockResolvedValue();

    await expect(disconnectMongoose({ throwOnInitFailure: false })).resolves.toBeUndefined();

    expect(disconnectSpy).toHaveBeenCalledTimes(1);
  });
});


describe('coding-agent skill allowlist', () => {
  it('accepts only the validated four-skill manifest identity', () => {
    expect(() => validateManifestSkillPolicy(validSkillManifest())).not.toThrow();

    const missing = validSkillManifest();
    missing.skills.pop();
    expect(() => validateManifestSkillPolicy(missing)).toThrow(/exactly 4 validated skills/);

    const widened = validSkillManifest();
    widened.skills.push({ ...widened.skills[0], name: 'another-skill' });
    expect(() => validateManifestSkillPolicy(widened)).toThrow(/exactly 4 validated skills/);

    const replaced = validSkillManifest();
    replaced.skills[1] = { ...replaced.skills[1], name: 'wrong-skill' };
    expect(() => validateManifestSkillPolicy(replaced)).toThrow(/systematic-debugging identity/);
  });

  it('resolves every mirrored GitHub skill by stable upstream identity', async () => {
    const ids = {
      'coding-agent-skills:.agents/skills/codebase-design': '64b000000000000000000001',
      'managed-skills:managed-skills/skills/systematic-debugging': '64b000000000000000000002',
      'managed-skills:managed-skills/skills/test-driven-development': '64b000000000000000000003',
      'managed-skills:managed-skills/skills/verification-before-completion': '64b000000000000000000004',
    };
    const db = {
      findSkillBySourceIdentity: jest.fn().mockImplementation(async ({ upstreamId }) => {
        const declared = validatedSkills().find(
          (skill) => `${skill.source_id}:${skill.path}` === upstreamId,
        );
        if (!declared) return null;
        return {
          _id: { toString: () => ids[upstreamId] },
          name: declared.name,
          disableModelInvocation: false,
          sourceMetadata: {
            sourceId: declared.source_id,
            owner: declared.owner,
            repo: declared.repo,
            ref: declared.ref,
            skillPath: declared.path,
            syncStatus: 'synced',
          },
        };
      }),
    };

    await expect(resolveSkillAllowlist(db, validSkillManifest())).resolves.toEqual([
      {
        id: '64b000000000000000000001',
        name: 'codebase-design',
        upstreamId: 'coding-agent-skills:.agents/skills/codebase-design',
      },
      {
        id: '64b000000000000000000002',
        name: 'systematic-debugging',
        upstreamId: 'managed-skills:managed-skills/skills/systematic-debugging',
      },
      {
        id: '64b000000000000000000003',
        name: 'test-driven-development',
        upstreamId: 'managed-skills:managed-skills/skills/test-driven-development',
      },
      {
        id: '64b000000000000000000004',
        name: 'verification-before-completion',
        upstreamId: 'managed-skills:managed-skills/skills/verification-before-completion',
      },
    ]);
    expect(db.findSkillBySourceIdentity).toHaveBeenCalledTimes(4);
  });

  it('fails closed when any mirrored skill is unavailable', async () => {
    const db = {
      findSkillBySourceIdentity: jest.fn().mockImplementation(async ({ upstreamId }) => {
        if (upstreamId.endsWith('/test-driven-development')) return null;
        const declared = validatedSkills().find(
          (skill) => `${skill.source_id}:${skill.path}` === upstreamId,
        );
        return {
          _id: { toString: () => '64b000000000000000000001' },
          name: declared.name,
          disableModelInvocation: false,
          sourceMetadata: {
            sourceId: declared.source_id,
            owner: declared.owner,
            repo: declared.repo,
            ref: declared.ref,
            skillPath: declared.path,
            syncStatus: 'synced',
          },
        };
      }),
    };

    await expect(resolveSkillAllowlist(db, validSkillManifest())).rejects.toThrow(
      /refusing to widen the allowlist/,
    );
  });
});
