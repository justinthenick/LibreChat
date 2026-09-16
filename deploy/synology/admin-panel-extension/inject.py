#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path('/src')


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected exactly one injection anchor, found {count}')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')


sidebar = ROOT / 'src/components/Sidebar.tsx'
replace_once(
    sidebar,
    """  {\n    labelKey: 'com_nav_configuration',\n    path: '/configuration',\n    icon: 'settings',\n    capability: SystemCapabilities.READ_CONFIGS,\n  },\n""",
    """  {\n    labelKey: 'com_nav_configuration',\n    path: '/configuration',\n    icon: 'settings',\n    capability: SystemCapabilities.READ_CONFIGS,\n  },\n  {\n    labelKey: 'com_nav_deployment',\n    path: '/deployment',\n    icon: 'settings',\n  },\n""",
)

app = ROOT / 'src/routes/_app.tsx'
replace_once(
    app,
    "  '/configuration': 'com_config_title',\n",
    "  '/configuration': 'com_config_title',\n  '/deployment': 'com_nav_deployment',\n",
)

translations = ROOT / 'src/locales/en/translation.json'
data = json.loads(translations.read_text(encoding='utf-8'))
if 'com_nav_deployment' in data:
    raise SystemExit('translation already contains com_nav_deployment; upstream layout changed')
data['com_nav_deployment'] = 'Deployment'
translations.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

server = ROOT / 'server.ts'
replace_once(
    server,
    "const BASE_PATH = (env.VITE_BASE_PATH || '').replace(/\\/$/, '');\n",
    "const BASE_PATH = (env.VITE_BASE_PATH || '').replace(/\\/$/, '');\nconst DEPLOYMENT_GATEWAY_URL = env.DEPLOYMENT_GATEWAY_URL || 'http://deployment-frame-gateway:3211';\n",
)

bridge = r'''const DEPLOYMENT_PREFIX = '/deployment-control';

async function proxyDeploymentControl(req: Request): Promise<Response> {
  const incoming = new URL(req.url);
  const suffix = incoming.pathname.slice(DEPLOYMENT_PREFIX.length) || '/';
  const target = new URL(`${suffix}${incoming.search}`, DEPLOYMENT_GATEWAY_URL);
  const method = req.method.toUpperCase();
  const headers = new Headers(req.headers);
  headers.delete('host');
  headers.delete('content-length');

  const init: RequestInit = { method, headers, redirect: 'manual' };
  if (method !== 'GET' && method !== 'HEAD') {
    init.body = await req.arrayBuffer();
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

'''
replace_once(server, 'const server = Bun.serve({\n', bridge + 'const server = Bun.serve({\n')
replace_once(
    server,
    "    ...(await buildStaticRoutes()),\n    '/metrics': (req) => metricsResponse(req),\n",
    "    ...(await buildStaticRoutes()),\n    '/deployment-control': () => Response.redirect('/deployment-control/', 302),\n    '/deployment-control/*': (req) => proxyDeploymentControl(req),\n    '/metrics': (req) => metricsResponse(req),\n",
)
