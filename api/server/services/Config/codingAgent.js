const net = require('net');

let cachedStatus = null;
let lastCheckTime = 0;
const CACHE_TTL_MS = 15000;
const PROBE_TIMEOUT_MS = 2000;

async function probeExecutor(host, port) {
  if (!host || !port) {
    return { configured: false, status: 'unconfigured', version: null };
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), PROBE_TIMEOUT_MS);

  try {
    const response = await fetch(`http://${host}:${port}/health`, {
      signal: controller.signal,
    });

    if (!response.ok) {
      return { configured: true, status: `error_${response.status}`, version: null };
    }

    const data = await response.json().catch(() => ({}));
    return {
      configured: true,
      status: typeof data.status === 'string' ? data.status : 'ok',
      version: typeof data.version === 'string' ? data.version : null,
    };
  } catch {
    return { configured: true, status: 'unreachable', version: null };
  } finally {
    clearTimeout(timeoutId);
  }
}

function probeMaintenance(host, portRaw) {
  return new Promise((resolve) => {
    const validPort = /^[0-9]+$/.test(String(portRaw));
    const port = validPort ? Number(portRaw) : 0;

    if (!host || !validPort || port <= 0 || port > 65535) {
      resolve({ configured: false, status: 'unconfigured' });
      return;
    }

    const socket = net.createConnection({ host, port });
    let settled = false;

    const finish = (status) => {
      if (settled) {
        return;
      }
      settled = true;
      socket.destroy();
      resolve({ configured: true, status });
    };

    socket.setTimeout(PROBE_TIMEOUT_MS);
    socket.once('connect', () => finish('running'));
    socket.once('timeout', () => finish('unreachable'));
    socket.once('error', () => finish('unreachable'));
  });
}

async function getCodingAgentConfig(forceRefresh = false) {
  const executorHost = process.env.CODING_EXECUTOR_HOST || '';
  const maintenanceHost = process.env.CODING_MAINTENANCE_HOST || '';

  if (!executorHost && !maintenanceHost) {
    cachedStatus = null;
    lastCheckTime = 0;
    return undefined;
  }

  const now = Date.now();
  if (!forceRefresh && cachedStatus && now - lastCheckTime < CACHE_TTL_MS) {
    return cachedStatus;
  }

  const executorPort = process.env.CODING_EXECUTOR_PORT || '8765';
  const maintenancePort = process.env.CODING_MAINTENANCE_PORT || '8767';

  const [executor, maintenance] = await Promise.all([
    probeExecutor(executorHost, executorPort),
    probeMaintenance(maintenanceHost, maintenancePort),
  ]);

  cachedStatus = { executor, maintenance };
  lastCheckTime = now;
  return cachedStatus;
}

module.exports = {
  getCodingAgentConfig,
  probeExecutor,
  probeMaintenance,
};
