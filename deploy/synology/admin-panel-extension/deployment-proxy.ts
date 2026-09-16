import { verifyAdminTokenFn } from '@/server/auth';

const DEPLOYMENT_PREFIX = '/deployment-control';
const DEPLOYMENT_GATEWAY_URL =
  process.env.DEPLOYMENT_GATEWAY_URL || 'http://deployment-frame-gateway:3211';

function deploymentCookies(rawCookie: string | null): string {
  if (!rawCookie) return '';
  return rawCookie
    .split(';')
    .map((part) => part.trim())
    .filter(Boolean)
    .filter((part) => {
      const eq = part.indexOf('=');
      const name = eq >= 0 ? part.slice(0, eq) : part;
      return name !== 'admin-session' && !name.startsWith('admin-session.');
    })
    .join('; ');
}

function unauthorized(): Response {
  return Response.json(
    { ok: false, error: 'A valid LibreChat administrator session is required.' },
    {
      status: 401,
      headers: {
        'Cache-Control': 'no-store',
        'X-Content-Type-Options': 'nosniff',
      },
    },
  );
}

export async function handleDeploymentControl(request: Request): Promise<Response> {
  const verified = await verifyAdminTokenFn();
  if (!verified.valid) return unauthorized();

  const incoming = new URL(request.url);
  const suffix = incoming.pathname.slice(DEPLOYMENT_PREFIX.length) || '/';
  const target = new URL(`${suffix}${incoming.search}`, DEPLOYMENT_GATEWAY_URL);
  const method = request.method.toUpperCase();

  // Deliberately forward only what the Deployment Settings service needs.
  // In particular, never expose the official Admin Panel session or browser
  // Authorization headers to the lower-trust deployment gateway.
  const headers = new Headers();
  for (const name of ['accept', 'content-type']) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  const cookies = deploymentCookies(request.headers.get('cookie'));
  if (cookies) headers.set('cookie', cookies);

  const init: RequestInit = { method, headers, redirect: 'manual' };
  if (method !== 'GET' && method !== 'HEAD') {
    init.body = await request.arrayBuffer();
  }

  const upstream = await fetch(target, init);
  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.delete('content-length');
  let body: BodyInit | null = upstream.body;
  const contentType = responseHeaders.get('content-type') ?? '';

  if (contentType.toLowerCase().startsWith('text/html')) {
    let html = await upstream.text();
    html = html
      .replaceAll("'/api/", "'/deployment-control/api/")
      .replaceAll('"/api/', '"/deployment-control/api/');
    body = html;
  }

  const setCookie = responseHeaders.get('set-cookie');
  if (setCookie) {
    responseHeaders.set(
      'set-cookie',
      setCookie.replace(/Path=\/(?:;|$)/i, 'Path=/deployment-control/;'),
    );
  }
  responseHeaders.set('cache-control', 'no-store');

  return new Response(method === 'HEAD' ? null : body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  });
}
