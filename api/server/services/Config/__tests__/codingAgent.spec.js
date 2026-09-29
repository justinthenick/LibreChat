const { getCodingAgentConfig, probeExecutor, probeMaintenance } = require('../codingAgent');

describe('codingAgent config service', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  describe('probeExecutor', () => {
    it('returns unconfigured if host or port is missing', async () => {
      const res = await probeExecutor('', '8765');
      expect(res).toEqual({
        configured: false,
        status: 'unconfigured',
        version: null,
      });
    });

    it('returns status and version when health check responds with 200', async () => {
      const originalFetch = global.fetch;
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: 'ok', version: '0.1.13' }),
      });

      try {
        const res = await probeExecutor('127.0.0.1', '8765');
        expect(res).toEqual({
          configured: true,
          status: 'ok',
          version: '0.1.13',
        });
      } finally {
        global.fetch = originalFetch;
      }
    });

    it('returns error status if response is not ok', async () => {
      const originalFetch = global.fetch;
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 502,
      });

      try {
        const res = await probeExecutor('127.0.0.1', '8765');
        expect(res).toEqual({
          configured: true,
          status: 'error_502',
          version: null,
        });
      } finally {
        global.fetch = originalFetch;
      }
    });

    it('returns unreachable if fetch throws', async () => {
      const originalFetch = global.fetch;
      global.fetch = jest.fn().mockRejectedValue(new Error('Connection refused'));

      try {
        const res = await probeExecutor('127.0.0.1', '8765');
        expect(res).toEqual({
          configured: true,
          status: 'unreachable',
          version: null,
        });
      } finally {
        global.fetch = originalFetch;
      }
    });
  });

  describe('probeMaintenance', () => {
    it('returns unconfigured for invalid endpoint configuration', async () => {
      await expect(probeMaintenance('', '8767')).resolves.toEqual({
        configured: false,
        status: 'unconfigured',
      });
    });
  });

  describe('getCodingAgentConfig', () => {
    it('returns unconfigured when env vars are unset', async () => {
      delete process.env.CODING_EXECUTOR_HOST;
      delete process.env.CODING_MAINTENANCE_HOST;

      const config = await getCodingAgentConfig(true);
      expect(config.executor.configured).toBe(false);
      expect(config.maintenance.configured).toBe(false);
    });
  });
});
