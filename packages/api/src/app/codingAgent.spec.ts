import {
  getCodingAgentConfig,
  probeExecutor,
  probeMaintenance,
  __resetCodingAgentConfigCacheForTests,
} from './codingAgent';

describe('coding-agent runtime status', () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    __resetCodingAgentConfigCacheForTests();
    delete process.env.CODING_EXECUTOR_HOST;
    delete process.env.CODING_EXECUTOR_PORT;
    delete process.env.CODING_MAINTENANCE_HOST;
    delete process.env.CODING_MAINTENANCE_PORT;
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  describe('probeExecutor', () => {
    it('returns unconfigured if host or port is missing', async () => {
      await expect(probeExecutor('', '8765')).resolves.toEqual({
        configured: false,
        status: 'unconfigured',
        version: null,
      });
    });

    it('returns status and version when health check responds successfully', async () => {
      const fetchSpy = jest.spyOn(globalThis, 'fetch').mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ status: 'ok', version: '0.1.13' }),
      } as Response);

      await expect(probeExecutor('127.0.0.1', '8765')).resolves.toEqual({
        configured: true,
        status: 'ok',
        version: '0.1.13',
      });

      fetchSpy.mockRestore();
    });

    it('returns the HTTP error status for a non-success response', async () => {
      const fetchSpy = jest.spyOn(globalThis, 'fetch').mockResolvedValue({
        ok: false,
        status: 502,
      } as Response);

      await expect(probeExecutor('127.0.0.1', '8765')).resolves.toEqual({
        configured: true,
        status: 'error_502',
        version: null,
      });

      fetchSpy.mockRestore();
    });

    it('keeps the timeout active while parsing the response body', async () => {
      const fetchSpy = jest.spyOn(globalThis, 'fetch').mockImplementation(async (_input, init) => {
        return {
          ok: true,
          status: 200,
          json: () =>
            new Promise((_resolve, reject) => {
              init?.signal?.addEventListener(
                'abort',
                () => reject(new Error('aborted while reading body')),
                { once: true },
              );
            }),
        } as Response;
      });

      await expect(probeExecutor('127.0.0.1', '8765', 5)).resolves.toEqual({
        configured: true,
        status: 'unreachable',
        version: null,
      });

      fetchSpy.mockRestore();
    });

    it('returns unreachable if fetch throws', async () => {
      const fetchSpy = jest
        .spyOn(globalThis, 'fetch')
        .mockRejectedValue(new Error('Connection refused'));

      await expect(probeExecutor('127.0.0.1', '8765')).resolves.toEqual({
        configured: true,
        status: 'unreachable',
        version: null,
      });

      fetchSpy.mockRestore();
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
      const config = await getCodingAgentConfig(true);

      expect(config.executor?.configured).toBe(false);
      expect(config.maintenance?.configured).toBe(false);
    });
  });
});
