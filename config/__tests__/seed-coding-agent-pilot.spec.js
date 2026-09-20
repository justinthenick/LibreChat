jest.mock('../connect', () => jest.fn());

const mongoose = require('mongoose');
const { disconnectMongoose } = require('../seed-coding-agent-pilot');

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
