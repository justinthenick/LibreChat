"""Pinned Bun server + real deployment proxy; auth/SSR/metrics use local fixtures."""
import concurrent.futures
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent / "admin-panel-extension"
BUN = shutil.which("bun")
DELAY_SECONDS = int(os.environ.get("LIBRECHAT_TEST_DELAY_SECONDS", "16"))


class Gateway(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_POST(self):
        mode = self.rfile.read(int(self.headers.get("Content-Length", "0"))).decode()
        if mode == "headers": time.sleep(DELAY_SECONDS)
        payload = b'{"ok":true}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if mode == "body":
            self.wfile.write(payload[:1])
            self.wfile.flush()
            time.sleep(DELAY_SECONDS)
            payload = payload[1:]
        try: self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError): pass


@unittest.skipUnless(BUN, "Bun 1.3.11 is required; covered by extension CI")
class BunDeadlineTests(unittest.TestCase):
    def test_delayed_apply_survives_header_and_body_inactivity_through_pinned_server(self):
        self.assertEqual(subprocess.check_output([BUN, "--version"], text=True).strip(), "1.3.11")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for path in ("dist/client", "dist/server", "src/server", "src/components", "src/routes", "src/locales/en"):
                (root / path).mkdir(parents=True, exist_ok=True)
            with urllib.request.urlopen("https://raw.githubusercontent.com/LibreChat-AI/admin-panel/522e8cd404abba30cfa01b2c0e9353e546c8ff2a/server.ts", timeout=20) as upstream:
                pinned = upstream.read(65537)
            self.assertEqual(hashlib.sha256(pinned).hexdigest(), "7d290a68fcba1dd7e8e9e3360124275d77490db85d6abc3a9b64a348e3ffa06c")
            (root / "server.ts").write_bytes(pinned)
            (root / "src/server/deploymentProxy.ts").write_bytes((HERE / "deployment-proxy.ts").read_bytes())
            if (HERE / "deployment-deadline.ts").exists():
                (root / "src/server/deploymentDeadline.ts").write_bytes((HERE / "deployment-deadline.ts").read_bytes())
            (root / "tsconfig.json").write_text('{"compilerOptions":{"baseUrl":".","paths":{"@/*":["./src/*"]}}}')
            (root / "src/server/metrics.ts").write_text('export const normalizeMetricsPath=(p)=>p; export const httpRequestDurationSeconds={startTimer:()=>()=>{}}; export const httpRequestsTotal={inc:()=>{}}; export const metricsResponse=()=>new Response("ok");')
            (root / "src/server/auth.ts").write_text('import {AsyncLocalStorage} from "node:async_hooks"; export const context=new AsyncLocalStorage(); export async function verifyAdminTokenFn(){return {valid:context.getStore()?.headers.get("Authorization")==="Bearer fixture-admin"}}')
            (root / "dist/server/server.js").write_text('import {context} from "../../src/server/auth.ts"; import {handleDeploymentControl} from "../../src/server/deploymentProxy.ts"; export default {fetch(req){return context.run(req,()=>handleDeploymentControl(req))}}')
            (root / "src/components/Sidebar.tsx").write_text("  {\n    labelKey: 'com_nav_configuration',\n    path: '/configuration',\n    icon: 'settings',\n    capability: SystemCapabilities.READ_CONFIGS,\n  },\n")
            (root / "src/routes/_app.tsx").write_text("  '/configuration': 'com_config_title',\n")
            (root / "src/locales/en/translation.json").write_text('{}')
            # Execute the production injector against the fixture directory.
            source = (HERE / "inject.py").read_text().replace("ROOT = Path('/src')", "ROOT = Path(" + repr(str(root)) + ")")
            exec(compile(source, str(HERE / "inject.py"), "exec"), {})
            gateway = ThreadingHTTPServer(("127.0.0.1", 0), Gateway)
            thread = threading.Thread(target=gateway.serve_forever, daemon=True)
            thread.start()
            env = dict(os.environ, PORT="0", SESSION_SECRET="fixture-secret-" * 4,
                       DEPLOYMENT_GATEWAY_URL="http://127.0.0.1:" + str(gateway.server_port))
            proc = subprocess.Popen([BUN, "server.ts"], cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                line = proc.stdout.readline()
                self.assertIn("listening on", line, line)
                base = line.strip().split("http://", 1)[1].rstrip("/")
                url = "http://" + base + "/deployment-control/api/apply"
                def request(mode):
                    req = urllib.request.Request(url, data=mode.encode(), headers={"Authorization":"Bearer fixture-admin"})
                    with urllib.request.urlopen(req, timeout=DELAY_SECONDS + 25) as response:
                        return response.status, response.read()
                print("Pinned Bun header/body requests starting; delay={}s".format(DELAY_SECONDS), flush=True)
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                    results = list(pool.map(request, ["headers", "body"]))
                self.assertEqual(results, [(200, b'{"ok":true}'), (200, b'{"ok":true}')])
                with self.assertRaises(urllib.error.HTTPError) as denied:
                    urllib.request.urlopen(urllib.request.Request(url, data=b"headers"), timeout=3)
                self.assertEqual(denied.exception.code, 401)
            finally:
                proc.terminate()
                proc.communicate(timeout=5)
                gateway.shutdown()
                gateway.server_close()
                thread.join(2)


if __name__ == "__main__":
    unittest.main()
