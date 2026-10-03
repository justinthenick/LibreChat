import { normalizeCodingHostDiagnostics } from './diagnostics';

describe('normalizeCodingHostDiagnostics', () => {
  it('uses host diagnostics reported by the WSL maintenance broker', () => {
    expect(
      normalizeCodingHostDiagnostics({
        executor: {
          status: 'ok',
          version: '0.1.13',
        },
        maintenance: {
          status: 'running',
          host: {
            docker: 'available',
            wsl: 'available',
          },
        },
      }),
    ).toEqual({
      status: 'ok',
      docker: 'available',
      wsl: 'available',
    });
  });

  it('reports Docker failure from the host broker', () => {
    expect(
      normalizeCodingHostDiagnostics({
        executor: { status: 'ok' },
        maintenance: {
          status: 'running',
          host: {
            docker: 'unavailable',
            wsl: 'available',
          },
        },
      }),
    ).toEqual({
      status: 'docker_unavailable',
      docker: 'unavailable',
      wsl: 'available',
    });
  });

  it('reports an unreachable executor independently of host state', () => {
    expect(
      normalizeCodingHostDiagnostics({
        executor: { status: 'unreachable' },
        maintenance: {
          status: 'running',
          host: {
            docker: 'available',
            wsl: 'available',
          },
        },
      }),
    ).toEqual({
      status: 'executor_unreachable',
      docker: 'available',
      wsl: 'available',
    });
  });

  it('does not guess when an older maintenance service omits host diagnostics', () => {
    expect(
      normalizeCodingHostDiagnostics({
        executor: {
          status: 'ok',
          version: '0.1.13',
        },
        maintenance: {
          status: 'running',
        },
      }),
    ).toEqual({
      status: 'ok',
      docker: 'unknown',
      wsl: 'unknown',
    });
  });
});
