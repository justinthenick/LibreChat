export type CodingIntegrationStatus = 'available' | 'unavailable' | 'not_detected' | 'unknown';

export type CodingHostStatus =
  | 'ok'
  | 'executor_unreachable'
  | 'wsl_unavailable'
  | 'docker_unavailable';

export interface CodingReportedHostDiagnostics {
  docker?: string | null;
  wsl?: string | null;
}

export interface CodingExecutorHealth {
  configured?: boolean;
  status?: string | null;
  version?: string | null;
  docker?: string | null;
  wsl?: string | null;
  host?: CodingReportedHostDiagnostics | null;
}

export interface CodingMaintenanceHealth {
  configured?: boolean;
  status?: string | null;
  host?: CodingReportedHostDiagnostics | null;
}

export interface CodingHostDiagnostics {
  status: CodingHostStatus;
  docker: CodingIntegrationStatus;
  wsl: CodingIntegrationStatus;
}

export interface CodingHostDiagnosticSources {
  executor?: CodingExecutorHealth | null;
  maintenance?: CodingMaintenanceHealth | null;
}

function normalizeIntegrationStatus(value: string | null | undefined): CodingIntegrationStatus {
  switch (value) {
    case 'available':
    case 'unavailable':
    case 'not_detected':
    case 'unknown':
      return value;
    default:
      return 'unknown';
  }
}

export function normalizeCodingHostDiagnostics({
  executor,
  maintenance,
}: CodingHostDiagnosticSources = {}): CodingHostDiagnostics {
  /*
   * The WSL host-maintenance broker is authoritative because it runs outside
   * the isolated executor container. Executor-reported values remain accepted
   * for forward/backward compatibility, but NAS-local state is never inferred.
   */
  const reportedHost = maintenance?.host ?? executor?.host;

  const docker = normalizeIntegrationStatus(reportedHost?.docker ?? executor?.docker);
  const wsl = normalizeIntegrationStatus(reportedHost?.wsl ?? executor?.wsl);

  let status: CodingHostStatus = 'ok';
  if (executor?.status === 'unreachable') {
    status = 'executor_unreachable';
  } else if (wsl === 'unavailable') {
    status = 'wsl_unavailable';
  } else if (docker === 'unavailable') {
    status = 'docker_unavailable';
  }

  return {
    status,
    docker,
    wsl,
  };
}
