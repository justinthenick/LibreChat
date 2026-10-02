const fs = require('fs');
const path = require('path');
const os = require('os');
const {
  getCodingAgentConfig,
  probeExecutor,
  probeMaintenance,
  getPilotIdentity,
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
    it('returns unconfigured for an invalid endpoint', async () => {
      await expect(probeMaintenance('', '8767')).resolves.toEqual({
        configured: false,
        status: 'unconfigured',
      });
    });

    it('returns host diagnostics reported by the WSL maintenance broker', async () => {
      const originalFetch = global.fetch;
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          status: 'ok',
          host: {
            docker: 'available',
            wsl: 'available',
          },
        }),
      });

      try {
        await expect(probeMaintenance('127.0.0.1', '8767')).resolves.toEqual({
          configured: true,
          status: 'running',
          host: {
            docker: 'available',
            wsl: 'available',
          },
        });
      } finally {
        global.fetch = originalFetch;
      }
    });

    it('keeps older reachable maintenance services compatible', async () => {
      const originalFetch = global.fetch;
      global.fetch = jest.fn().mockResolvedValue({
        ok: false,
        status: 404,
      });

      try {
        await expect(probeMaintenance('127.0.0.1', '8767')).resolves.toEqual({
          configured: true,
          status: 'running',
        });
      } finally {
        global.fetch = originalFetch;
      }
    });
  });

  describe('getPilotIdentity', () => {
    let tmpDir;

    beforeEach(() => {
      tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), 'pilot-manifest-test-'));
    });

    afterEach(() => {
      if (tmpDir && fs.existsSync(tmpDir)) {
        fs.rmSync(tmpDir, { recursive: true, force: true });
      }
    });

    it('returns unconfigured when manifest does not exist in specified dir', () => {
      const identity = getPilotIdentity(path.join(tmpDir, 'nonexistent'));
      expect(identity.configured).toBe(false);
      expect(identity.status).toBe('unconfigured');
      expect(identity.version).toBeNull();
      expect(identity.provider).toBeNull();
      expect(identity.model).toBeNull();
    });

    it('extracts pilot identity from valid manifest', () => {
      const manifest = {
        name: 'Software Engineering Pilot',
        version: '0.1.16',
        provider: 'google',
        preferred_model: 'gemini-3.8-flash',
      };
      fs.writeFileSync(
        path.join(tmpDir, 'software-engineering-pilot.json'),
        JSON.stringify(manifest),
      );

      const identity = getPilotIdentity(tmpDir);
      expect(identity).toEqual({
        configured: true,
        status: 'ok',
        version: '0.1.16',
        provider: 'google',
        model: 'gemini-3.8-flash',
      });
    });

    it('handles malformed json gracefully', () => {
      fs.writeFileSync(path.join(tmpDir, 'software-engineering-pilot.json'), 'INVALID JSON');
      const identity = getPilotIdentity(tmpDir);
      expect(identity.configured).toBe(false);
      expect(identity.status).toBe('unconfigured');
    });

    it('returns unconfigured when manifestDir and CODING_AGENT_MANIFEST_DIR are absent', () => {
      const prev = process.env.CODING_AGENT_MANIFEST_DIR;
      delete process.env.CODING_AGENT_MANIFEST_DIR;
      try {
        const identity = getPilotIdentity();
        expect(identity.configured).toBe(false);
        expect(identity.status).toBe('unconfigured');
      } finally {
        if (prev !== undefined) {
          process.env.CODING_AGENT_MANIFEST_DIR = prev;
        }
      }
    });

    it('reads manifest from process.env.CODING_AGENT_MANIFEST_DIR when manifestDir argument is omitted', () => {
      const prev = process.env.CODING_AGENT_MANIFEST_DIR;
      process.env.CODING_AGENT_MANIFEST_DIR = tmpDir;
      try {
        const manifest = {
          name: 'Software Engineering Pilot',
          version: '0.1.16',
          provider: 'google',
          preferred_model: 'gemini-3.8-flash',
        };
        fs.writeFileSync(
          path.join(tmpDir, 'software-engineering-pilot.json'),
          JSON.stringify(manifest),
        );
        const identity = getPilotIdentity();
        expect(identity.configured).toBe(true);
        expect(identity.status).toBe('ok');
        expect(identity.version).toBe('0.1.16');
      } finally {
        if (prev !== undefined) {
          process.env.CODING_AGENT_MANIFEST_DIR = prev;
        } else {
          delete process.env.CODING_AGENT_MANIFEST_DIR;
        }
      }
    });

    it('returns incomplete when required fields are missing', () => {
      const manifest = {
        name: 'Software Engineering Pilot',
        version: '0.1.16',
      };
      fs.writeFileSync(
        path.join(tmpDir, 'software-engineering-pilot.json'),
        JSON.stringify(manifest),
      );
      const identity = getPilotIdentity(tmpDir);
      expect(identity.configured).toBe(false);
      expect(identity.status).toBe('incomplete');
      expect(identity.version).toBe('0.1.16');
      expect(identity.provider).toBeNull();
      expect(identity.model).toBeNull();
    });
  });

  describe('getCodingAgentConfig', () => {
    it('returns executor, maintenance, and pilot config', async () => {
      delete process.env.CODING_EXECUTOR_HOST;
      delete process.env.CODING_MAINTENANCE_HOST;

      const config = await getCodingAgentConfig(true);
      expect(config.executor.configured).toBe(false);
      expect(config.maintenance.configured).toBe(false);
      expect(config).toHaveProperty('pilot');
      expect(typeof config.pilot.configured).toBe('boolean');
      expect(config).toHaveProperty('host');
      expect(typeof config.host.status).toBe('string');
    });
  });
});
