jest.mock('../connect', () => jest.fn());

const mongoose = require('mongoose');
const {
  disconnectMongoose,
  validateManifestSkillPolicy,
  resolveSkillAllowlist,
} = require('../seed-coding-agent-pilot');

function validSkillManifest() {
  return {
    id: 'agent_software_engineering_pilot_v01',
    skills_enabled: true,
    skills: [
      {
        name: 'codebase-design',
        source: 'github',
        source_id: 'coding-agent-skills',
        owner: 'justinthenick',
        repo: 'LibreChat',
        ref: 'server/synology',
        path: '.agents/skills/codebase-design',
      },
    ],
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
  it('accepts only the validated codebase-design manifest identity', () => {
    expect(() => validateManifestSkillPolicy(validSkillManifest())).not.toThrow();

    const widened = validSkillManifest();
    widened.skills.push({ ...widened.skills[0], name: 'another-skill' });
    expect(() => validateManifestSkillPolicy(widened)).toThrow(/exactly one validated skill/);
  });

  it('resolves the mirrored GitHub skill by stable upstream identity', async () => {
    const db = {
      findSkillBySourceIdentity: jest.fn().mockResolvedValue({
        _id: { toString: () => '64b000000000000000000001' },
        name: 'codebase-design',
        disableModelInvocation: false,
        sourceMetadata: {
          sourceId: 'coding-agent-skills',
          owner: 'justinthenick',
          repo: 'LibreChat',
          ref: 'server/synology',
          skillPath: '.agents/skills/codebase-design',
          syncStatus: 'synced',
        },
      }),
    };

    await expect(resolveSkillAllowlist(db, validSkillManifest())).resolves.toEqual([
      {
        id: '64b000000000000000000001',
        name: 'codebase-design',
        upstreamId: 'coding-agent-skills:.agents/skills/codebase-design',
      },
    ]);
    expect(db.findSkillBySourceIdentity).toHaveBeenCalledWith({
      source: 'github',
      upstreamId: 'coding-agent-skills:.agents/skills/codebase-design',
    });
  });

  it('fails closed when the mirrored skill is unavailable', async () => {
    const db = {
      findSkillBySourceIdentity: jest.fn().mockResolvedValue(null),
    };

    await expect(resolveSkillAllowlist(db, validSkillManifest())).rejects.toThrow(
      /refusing to widen the allowlist/,
    );
  });
});
