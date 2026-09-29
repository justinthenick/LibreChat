const net = require('net');
const { EventEmitter } = require('events');
const {
  getCodingAgentConfig,
  probeExecutor,
  probeMaintenance,
} = require('../codingAgent');

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
      await expect(probeExecutor('', '8765')).resolves.toEqual({
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
        await expect(probeExecutor('127.0.0.1', '8765')).resolves.toEqual({
          configured: true,
          status: 'ok',
          version: '0.1.13',
        });
      } finally {
        global.fetch = originalFetch;
      }
    });

    it('returns an HTTP error status when the health endpoint is not ok', async () => {
      const originalFetch = global.fetch;
      global.fetch = jest.fn().mockResolvedValue({ ok: false, status: 502 });

      try {
        await expect(probeExecutor('127.0.0.1', '8765')).resolves.toEqual({
          configured: true,
          status: 'error_502',
          version: null,
        });
      } finally {
        global.fetch = originalFetch;
      }
    });

    it('returns unreachable if the health request fails', async () => {
      const originalFetch = global.fetch;
      global.fetch = jest.fn().mockRejectedValue(new Error('Connection refused'));

      try {
        await expect(probeExecutor('127.0.0.1', '8765')).resolves.toEqual({
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
    it('returns unconfigured for a missing endpoint', async () => {
      await expect(probeMaintenance('', '8767')).resolves.toEqual({
        configured: false,
        status: 'unconfigured',
      });
    });

    it('reports running when the maintenance listener accepts a connection', async () => {
      const socket = new EventEmitter();
      socket.setTimeout = jest.fn();
      socket.destroy = jest.fn();
      const createConnection = jest.spyOn(net, 'createConnection').mockReturnValue(socket);

      try {
        const result = probeMaintenance('127.0.0.1', '8767');
        process.nextTick(() => socket.emit('connect'));
        await expect(result).resolves.toEqual({ configured: true, status: 'running' });
        expect(createConnection).toHaveBeenCalledWith({ host: '127.0.0.1', port: 8767 });
      } finally {
        createConnection.mockRestore();
      }
    });
  });

  describe('getCodingAgentConfig', () => {
    it('omits coding-agent diagnostics when neither endpoint is configured', async () => {
      delete process.env.CODING_EXECUTOR_HOST;
      delete process.env.CODING_MAINTENANCE_HOST;

      await expect(getCodingAgentConfig(true)).resolves.toBeUndefined();
    });
  });
});
