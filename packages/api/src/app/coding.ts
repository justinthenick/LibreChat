import net from 'net';
import type { TCodingAgentStatus } from 'librechat-data-provider';

type ExecutorStatus = NonNullable<TCodingAgentStatus['executor']>;
type MaintenanceStatus = NonNullable<TCodingAgentStatus['maintenance']>;

const CACHE_TTL_MS = 15000;
const PROBE_TIMEOUT_MS = 2000;

let cachedStatus: TCodingAgentStatus | null = null;
let cachedAt = 0;
let cachedKey: string | null = null;

function normalize(value: string | undefined): string | null {
  if (typeof value !== 'string') {
    return null;
  }

  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function parsePort(value: string | null): number | null {
  if (!value || !/^\d+$/.test(value)) {
    return null;
  }

  const port = Number(value);
  return port > 0 && port <= 65535 ? port : null;
}

function endpointConfigured(
  host: string | null,
  port: number | null,
  token: string | null,
): boolean {
  return Boolean(host && port && token);
}

function unconfiguredExecutor(): ExecutorStatus {
  return { configured: false, status: 'unconfigured', version: null };
}

function unconfiguredMaintenance(): MaintenanceStatus {
  return { configured: false, status: 'unconfigured' };
}

export async function probeExecutor(host: string, port: number): Promise<ExecutorStatus> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), PROBE_TIMEOUT_MS);

  try {
    const response = await fetch(`http://${host}:${port}/health`, {
      signal: controller.signal,
    });

    if (!response.ok) {
      return { configured: true, status: `error_${response.status}`, version: null };
    }

    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      return { configured: true, status: 'invalid_response', version: null };
    }

    if (
      typeof payload !== 'object' ||
      payload === null ||
      !('status' in payload) ||
      typeof payload.status !== 'string' ||
      payload.status.trim().length === 0
    ) {
      return { configured: true, status: 'invalid_response', version: null };
    }

    const version =
      'version' in payload && typeof payload.version === 'string' && payload.version.trim().length > 0
        ? payload.version
        : null;

    return {
      configured: true,
      status: payload.status,
      version,
    };
  } catch {
    return { configured: true, status: 'unreachable', version: null };
  } finally {
    clearTimeout(timeoutId);
  }
}

export function probeMaintenance(host: string, port: number): Promise<MaintenanceStatus> {
  return new Promise((resolve) => {
    const socket = net.createConnection({ host, port });
    let settled = false;

    const finish = (status: 'running' | 'unreachable') => {
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

export async function getCodingAgentConfig(
  forceRefresh = false,
): Promise<TCodingAgentStatus | undefined> {
  const executorHost = normalize(process.env.CODING_EXECUTOR_HOST);
  const executorPort = parsePort(normalize(process.env.CODING_EXECUTOR_PORT) ?? '8765');
  const executorToken = normalize(process.env.CODING_EXECUTOR_TOKEN);
  const maintenanceHost = normalize(process.env.CODING_MAINTENANCE_HOST);
  const maintenancePort = parsePort(normalize(process.env.CODING_MAINTENANCE_PORT) ?? '8767');
  const maintenanceToken = normalize(process.env.CODING_MAINTENANCE_TOKEN);

  const executorEnabled = endpointConfigured(executorHost, executorPort, executorToken);
  const maintenanceEnabled = endpointConfigured(maintenanceHost, maintenancePort, maintenanceToken);

  if (!executorEnabled && !maintenanceEnabled) {
    cachedStatus = null;
    cachedAt = 0;
    cachedKey = null;
    return undefined;
  }

  const cacheKey = [
    executorEnabled ? `executor:${executorHost}:${executorPort}` : 'executor:off',
    maintenanceEnabled ? `maintenance:${maintenanceHost}:${maintenancePort}` : 'maintenance:off',
  ].join('|');
  const now = Date.now();

  if (
    !forceRefresh &&
    cachedStatus &&
    cachedKey === cacheKey &&
    now - cachedAt < CACHE_TTL_MS
  ) {
    return cachedStatus;
  }

  const [executor, maintenance] = await Promise.all([
    executorEnabled && executorHost && executorPort
      ? probeExecutor(executorHost, executorPort)
      : Promise.resolve(unconfiguredExecutor()),
    maintenanceEnabled && maintenanceHost && maintenancePort
      ? probeMaintenance(maintenanceHost, maintenancePort)
      : Promise.resolve(unconfiguredMaintenance()),
  ]);

  cachedStatus = { executor, maintenance };
  cachedAt = now;
  cachedKey = cacheKey;
  return cachedStatus;
}

/** Test hook — resets the in-process status cache. Not exported from the package barrel. */
export function __resetCodingAgentCacheForTests(): void {
  cachedStatus = null;
  cachedAt = 0;
  cachedKey = null;
}
