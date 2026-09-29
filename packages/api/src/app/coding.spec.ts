import net from 'net';
import http from 'http';
import {
  getCodingAgentConfig,
  probeExecutor,
  probeMaintenance,
  __resetCodingAgentCacheForTests,
} from './coding';

type TestServer = ReturnType<typeof http.createServer> | ReturnType<typeof net.createServer>;

function listen(server: TestServer): Promise<number> {
  return new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const address = server.address();
      if (!address || typeof address === 'string') {
        reject(new Error('test server did not bind to a TCP port'));
        return;
      }
      resolve(address.port);
    });
  });
}

function close(server: TestServer): Promise<void> {
  return new Promise((resolve, reject) => {
    server.close((error) => {
      if (error) {
        reject(error);
        return;
      }
      resolve();
    });
  });
}

describe('coding agent status', () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    __resetCodingAgentCacheForTests();
    delete process.env.CODING_EXECUTOR_HOST;
    delete process.env.CODING_EXECUTOR_PORT;
    delete process.env.CODING_EXECUTOR_TOKEN;
    delete process.env.CODING_MAINTENANCE_HOST;
    delete process.env.CODING_MAINTENANCE_PORT;
    delete process.env.CODING_MAINTENANCE_TOKEN;
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  it('reads a valid executor health response', async () => {
    const server = http.createServer((_req, res) => {
      res.setHeader('content-type', 'application/json');
      res.end(JSON.stringify({ status: 'ok', version: '0.1.13' }));
    });
    const port = await listen(server);

    try {
      await expect(probeExecutor('127.0.0.1', port)).resolves.toEqual({
        configured: true,
        status: 'ok',
        version: '0.1.13',
      });
    } finally {
      await close(server);
    }
  });

  it('rejects malformed executor health JSON instead of reporting success', async () => {
    const server = http.createServer((_req, res) => {
      res.setHeader('content-type', 'text/html');
      res.end('<html>not health json</html>');
    });
    const port = await listen(server);

    try {
      await expect(probeExecutor('127.0.0.1', port)).resolves.toEqual({
        configured: true,
        status: 'invalid_response',
        version: null,
      });
    } finally {
      await close(server);
    }
  });

  it('rejects executor health JSON without a string status', async () => {
    const server = http.createServer((_req, res) => {
      res.setHeader('content-type', 'application/json');
      res.end(JSON.stringify({ version: '0.1.13' }));
    });
    const port = await listen(server);

    try {
      await expect(probeExecutor('127.0.0.1', port)).resolves.toEqual({
        configured: true,
        status: 'invalid_response',
        version: null,
      });
    } finally {
      await close(server);
    }
  });

  it('reports running when the maintenance listener accepts a connection', async () => {
    const server = net.createServer((socket) => socket.end());
    const port = await listen(server);

    try {
      await expect(probeMaintenance('127.0.0.1', port)).resolves.toEqual({
        configured: true,
        status: 'running',
      });
    } finally {
      await close(server);
    }
  });

  it('omits diagnostics when default hosts exist but credentials are absent', async () => {
    process.env.CODING_EXECUTOR_HOST = 'localhost';
    process.env.CODING_EXECUTOR_PORT = '8765';
    process.env.CODING_MAINTENANCE_HOST = 'localhost';
    process.env.CODING_MAINTENANCE_PORT = '8767';

    await expect(getCodingAgentConfig(true)).resolves.toBeUndefined();
  });

  it('supports an executor-only installation without probing maintenance', async () => {
    const server = http.createServer((_req, res) => {
      res.setHeader('content-type', 'application/json');
      res.end(JSON.stringify({ status: 'ok', version: '0.1.13' }));
    });
    const port = await listen(server);
    process.env.CODING_EXECUTOR_HOST = '127.0.0.1';
    process.env.CODING_EXECUTOR_PORT = String(port);
    process.env.CODING_EXECUTOR_TOKEN = 'configured-test-token';
    process.env.CODING_MAINTENANCE_HOST = 'localhost';
    process.env.CODING_MAINTENANCE_PORT = '8767';

    try {
      await expect(getCodingAgentConfig(true)).resolves.toEqual({
        executor: { configured: true, status: 'ok', version: '0.1.13' },
        maintenance: { configured: false, status: 'unconfigured' },
      });
    } finally {
      await close(server);
    }
  });
});
