const fs = require('fs');
const path = require('path');
const net = require('net');

let cachedStatus = null;
let lastCheckTime = 0;
const CACHE_TTL_MS = 15000;

async function probeExecutor(host, port) {
  if (!host || !port) {
    return { configured: false, status: 'unconfigured', version: null };
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 2000);

  try {
    const url = `http://${host}:${port}/health`;
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (!res.ok) {
      return { configured: true, status: `error_${res.status}`, version: null };
    }

    const data = await res.json().catch(() => ({}));
    const result = {
      configured: true,
      status: typeof data.status === 'string' ? data.status : 'ok',
      version: typeof data.version === 'string' ? data.version : null,
    };
    if (data.docker !== undefined) {
      result.docker = typeof data.docker === 'string' ? data.docker : (data.docker?.status ?? null);
    }
    if (data.wsl !== undefined) {
      result.wsl = typeof data.wsl === 'string' ? data.wsl : (data.wsl?.status ?? null);
    }
    if (data.host !== undefined) {
      result.host = data.host;
    }
    return result;
  } catch {
    clearTimeout(timeoutId);
    return { configured: true, status: 'unreachable', version: null };
  }
}

function probeMaintenance(host, portRaw) {
  return new Promise((resolve) => {
    const validPort = /^[0-9]+$/.test(String(portRaw));
    const port = validPort ? Number(portRaw) : 0;

    if (!host || !validPort || port <= 0 || port > 65535) {
      return resolve({ configured: false, status: 'unconfigured' });
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

    socket.setTimeout(2000);
    socket.once('connect', () => finish('running'));
    socket.once('timeout', () => finish('unreachable'));
    socket.once('error', () => finish('unreachable'));
  });
}

function probeHostIntegration({ executor, wslSocketPath, isWsl } = {}) {
  const socketPath =
    wslSocketPath ||
    process.env.CODING_AGENT_WSL_SOCKET_PATH ||
    '/mnt/wsl/docker-desktop/shared-sockets/host-services/backend.sock';

  let wslStatus = null;
  let dockerStatus = null;

  if (executor) {
    if (typeof executor.docker === 'string') {
      dockerStatus = executor.docker;
    } else if (executor.host && typeof executor.host.docker === 'string') {
      dockerStatus = executor.host.docker;
    }

    if (typeof executor.wsl === 'string') {
      wslStatus = executor.wsl;
    } else if (executor.host && typeof executor.host.wsl === 'string') {
      wslStatus = executor.host.wsl;
    }
  }

  let isWslEnvironment = typeof isWsl === 'boolean' ? isWsl : false;
  if (typeof isWsl !== 'boolean') {
    try {
      if (process.env.WSL_DISTRO_NAME || process.env.WSL_INTEROP) {
        isWslEnvironment = true;
      } else if (
        fs.existsSync('/mnt/wsl') ||
        fs.existsSync('/proc/sys/fs/binfmt_misc/WSLInterop')
      ) {
        isWslEnvironment = true;
      }
    } catch {
      isWslEnvironment = false;
    }
  }

  if (isWslEnvironment && !wslStatus) {
    try {
      if (fs.existsSync(socketPath)) {
        wslStatus = 'available';
      } else {
        wslStatus = 'unavailable';
      }
    } catch {
      wslStatus = 'unavailable';
    }
  }

  if (!dockerStatus) {
    if (executor?.status === 'unreachable') {
      dockerStatus = 'unknown';
    } else if (executor?.status === 'ok') {
      if (wslStatus === 'unavailable') {
        dockerStatus = 'unavailable';
      } else {
        dockerStatus = 'available';
      }
    } else {
      dockerStatus = 'unknown';
    }
  }

  if (!wslStatus) {
    wslStatus = isWslEnvironment ? 'unavailable' : 'not_detected';
  }

  let overallStatus = 'ok';
  if (executor?.status === 'unreachable') {
    overallStatus = 'executor_unreachable';
  } else if (wslStatus === 'unavailable') {
    overallStatus = 'wsl_unavailable';
  } else if (dockerStatus === 'unavailable') {
    overallStatus = 'docker_unavailable';
  }

  return {
    status: overallStatus,
    docker: dockerStatus,
    wsl: wslStatus,
  };
}

function getPilotIdentity(manifestDir) {
  try {
    const dir = manifestDir || process.env.CODING_AGENT_MANIFEST_DIR;
    if (!dir) {
      return {
        configured: false,
        status: 'unconfigured',
        version: null,
        provider: null,
        model: null,
      };
    }

    const manifestPath = path.join(dir, 'software-engineering-pilot.json');
    if (!fs.existsSync(manifestPath)) {
      return {
        configured: false,
        status: 'unconfigured',
        version: null,
        provider: null,
        model: null,
      };
    }

    const stat = fs.statSync(manifestPath);
    if (!stat.isFile()) {
      return {
        configured: false,
        status: 'unconfigured',
        version: null,
        provider: null,
        model: null,
      };
    }

    const raw = fs.readFileSync(manifestPath, 'utf8');
    const parsed = JSON.parse(raw);

    const version = typeof parsed.version === 'string' ? parsed.version : null;
    const provider = typeof parsed.provider === 'string' ? parsed.provider : null;
    let model = null;
    if (typeof parsed.preferred_model === 'string') {
      model = parsed.preferred_model;
    } else if (typeof parsed.model === 'string') {
      model = parsed.model;
    }

    const configured = Boolean(version && provider && model);
    return {
      configured,
      status: configured ? 'ok' : 'incomplete',
      version,
      provider,
      model,
    };
  } catch {
    return {
      configured: false,
      status: 'unconfigured',
      version: null,
      provider: null,
      model: null,
    };
  }
}

async function getCodingAgentConfig(forceRefresh = false) {
  const now = Date.now();
  if (!forceRefresh && cachedStatus && now - lastCheckTime < CACHE_TTL_MS) {
    return cachedStatus;
  }

  const executorHost = process.env.CODING_EXECUTOR_HOST || '';
  const executorPort = process.env.CODING_EXECUTOR_PORT || '8765';
  const maintenanceHost = process.env.CODING_MAINTENANCE_HOST || '';
  const maintenancePort = process.env.CODING_MAINTENANCE_PORT || '8767';

  const [executor, maintenance] = await Promise.all([
    probeExecutor(executorHost, executorPort),
    probeMaintenance(maintenanceHost, maintenancePort),
  ]);
  const pilot = getPilotIdentity();
  const host = probeHostIntegration({ executor });

  cachedStatus = {
    executor,
    maintenance,
    pilot,
    host,
  };
  lastCheckTime = now;
  return cachedStatus;
}

module.exports = {
  getCodingAgentConfig,
  probeExecutor,
  probeMaintenance,
  getPilotIdentity,
  probeHostIntegration,
};
