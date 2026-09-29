import { createConnection } from 'net';
import type { TCodingAgentStatus } from 'librechat-data-provider';

type ExecutorStatus = NonNullable<TCodingAgentStatus['executor']>;
type MaintenanceStatus = NonNullable<TCodingAgentStatus['maintenance']>;

const CACHE_TTL_MS = 15_000;
const PROBE_TIMEOUT_MS = 2_000;

let cachedStatus: TCodingAgentStatus | null = null;
let lastCheckTime = 0;

export async function probeExecutor(
  host: string,
  port: string,
  timeoutMs = PROBE_TIMEOUT_MS,
): Promise<ExecutorStatus> {
  if (!host || !port) {
    return { configured: false, status: 'unconfigured', version: null };
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`http://${host}:${port}/health`, {
      signal: controller.signal,
    });
    if (!response.ok) {
      return { configured: true, status: `error_${response.status}`, version: null };
    }

    const data = (await response.json().catch(() => ({}))) as Record<string, unknown>;
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

export function probeMaintenance(
  host: string,
  portRaw: string,
  timeoutMs = PROBE_TIMEOUT_MS,
): Promise<MaintenanceStatus> {
  return new Promise((resolve) => {
    const validPort = /^[0-9]+$/.test(portRaw);
    const port = validPort ? Number(portRaw) : 0;
    if (!host || !validPort || port <= 0 || port > 65535) {
      resolve({ configured: false, status: 'unconfigured' });
      return;
    }

    const socket = createConnection({ host, port });
    let settled = false;

    const finish = (status: string) => {
      if (settled) {
        return;
      }
      settled = true;
      socket.destroy();
      resolve({ configured: true, status });
    };

    socket.setTimeout(timeoutMs);
    socket.once('connect', () => finish('running'));
    socket.once('timeout', () => finish('unreachable'));
    socket.once('error', () => finish('unreachable'));
  });
}

export async function getCodingAgentConfig(forceRefresh = false): Promise<TCodingAgentStatus> {
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

  cachedStatus = { executor, maintenance };
  lastCheckTime = now;
  return cachedStatus;
}

/** Test hook — resets the in-process status cache. Not exported from the package barrel. */
export function __resetCodingAgentConfigCacheForTests(): void {
  cachedStatus = null;
  lastCheckTime = 0;
}
