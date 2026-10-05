import { test, expect, mock, spyOn } from 'bun:test';

mock.module('@/server/auth', () => ({ verifyAdminTokenFn: async () => ({valid: true}) }));
const { handleDeploymentControl } = await import('./deployment-proxy');

test('only apply disables Bun fetch socket timeout and retains cancellation', async () => {
  for (const [method, path, expected] of [
    ['POST', '/deployment-control/api/apply', false],
    ['POST', '/deployment-control/api/preview', undefined],
    ['GET', '/deployment-control/api/apply', undefined],
  ] as const) {
    const request = new Request('http://admin.test' + path, {method});
    let captured: RequestInit & {timeout?: false};
    const fetch = spyOn(globalThis, 'fetch').mockImplementation(async (_, init) => {
      captured = init;
      return Response.json({ok: true});
    });
    try {
      expect((await handleDeploymentControl(request)).status).toBe(200);
      expect(captured!.timeout).toBe(expected);
      expect(captured!.signal).toBe(request.signal);
    } finally { fetch.mockRestore(); }
  }
});
