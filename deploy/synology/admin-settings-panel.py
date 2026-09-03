#!/usr/bin/env python3
"""Browser-facing Synology Admin Settings panel.

This service has no access to the private .env file and no Docker socket. It
requires an independent bearer token, serves a small same-origin UI, and sends
validated-looking requests to the privileged host worker over a Unix socket.
The worker remains authoritative for validation and apply safety.
"""

import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket


PORT = int(os.environ.get("ADMIN_SETTINGS_PORT", "3210"))
TOKEN = os.environ.get("ADMIN_SETTINGS_ACCESS_TOKEN", "")
SOCKET_PATH = Path(os.environ.get("ADMIN_SETTINGS_SOCKET", "/state/worker.sock"))
MAX_BODY = 128 * 1024

HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Synology Admin Settings</title>
<style>
:root{font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color-scheme:light dark;--bg:#0f141b;--card:#171e28;--line:#2a3442;--text:#edf3fb;--muted:#9facbd;--accent:#6aa8ff;--danger:#ff7777;--ok:#70d79a;--warn:#f7c86a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text)}main{max-width:980px;margin:0 auto;padding:28px 18px 60px}.top{display:flex;gap:12px;align-items:center;justify-content:space-between;margin-bottom:22px}.badge{font-size:12px;padding:4px 8px;border:1px solid var(--line);border-radius:999px;color:var(--muted)}h1{font-size:24px;margin:0}.sub{color:var(--muted);margin:6px 0 0}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;margin:14px 0}.group-title{font-size:16px;margin:0 0 14px}.row{display:grid;grid-template-columns:minmax(220px,1fr) minmax(220px,1fr);gap:14px;padding:13px 0;border-top:1px solid var(--line)}.row:first-of-type{border-top:0}.label{font-weight:600}.desc,.meta,.warning{font-size:12px;color:var(--muted);margin-top:5px;line-height:1.4}.warning{color:var(--warn)}input,select,button{font:inherit}input[type=text],input[type=number],input[type=password],select{width:100%;padding:9px 10px;border-radius:8px;border:1px solid var(--line);background:#101720;color:var(--text)}input[type=checkbox]{width:20px;height:20px}.switch{display:flex;align-items:center;gap:9px}.secret-state{font-size:12px;color:var(--muted);margin-bottom:7px}.actions{display:flex;gap:10px;flex-wrap:wrap;position:sticky;bottom:10px;background:rgba(15,20,27,.95);padding:12px;border:1px solid var(--line);border-radius:12px;backdrop-filter:blur(8px)}button{border:1px solid var(--line);background:#1d2734;color:var(--text);border-radius:8px;padding:9px 13px;cursor:pointer}button.primary{background:var(--accent);color:#07111d;border-color:transparent;font-weight:700}button.danger{border-color:#8a4545}button:disabled{opacity:.45;cursor:not-allowed}.hidden{display:none!important}.status{padding:10px 12px;border-radius:8px;background:#101720;border:1px solid var(--line);font-size:13px;white-space:pre-wrap}.status.ok{border-color:#2c6c49;color:var(--ok)}.status.err{border-color:#7a3d3d;color:var(--danger)}.status.warn{border-color:#80662f;color:var(--warn)}.preview-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;padding:8px 0;border-top:1px solid var(--line);font-size:13px}.preview-row:first-child{border-top:0}.muted{color:var(--muted)}#login{max-width:520px;margin:70px auto}.token-note{font-size:12px;color:var(--muted);line-height:1.45}@media(max-width:700px){.row{grid-template-columns:1fr}.preview-row{grid-template-columns:1fr}.actions{position:static}}
</style>
</head>
<body>
<main>
<section id="login" class="card">
  <h1>Synology Admin Settings</h1>
  <p class="sub">Independent administrator authentication</p>
  <div style="margin-top:18px"><label class="label" for="token">Access token</label><input id="token" type="password" autocomplete="off" placeholder="Paste the local admin settings token"></div>
  <p class="token-note">The token is kept only in this browser tab's session storage and sent as a Bearer token to this panel. It is not stored in the page or returned by the settings API.</p>
  <button id="loginBtn" class="primary">Open settings</button>
  <div id="loginStatus" class="status hidden" style="margin-top:12px"></div>
</section>

<section id="app" class="hidden">
  <div class="top"><div><h1>Synology Admin Settings</h1><p class="sub">Safe, allowlisted LibreChat deployment configuration</p></div><div><span id="workerBadge" class="badge">worker</span> <button id="logoutBtn">Log out</button></div></div>
  <div id="messages"></div>
  <div id="settings"></div>
  <section id="previewCard" class="card hidden"><h2 class="group-title">Change preview</h2><div id="preview"></div><div id="previewWarnings"></div></section>
  <div class="actions"><button id="refreshBtn">Refresh</button><button id="previewBtn">Preview changes</button><button id="applyBtn" class="primary" disabled>Apply changes</button></div>
</section>
</main>
<script>
const $=s=>document.querySelector(s);
let state=null, previewPayload=null;
const tokenKey='synologyAdminSettingsToken';
function token(){return sessionStorage.getItem(tokenKey)||''}
function setMsg(text,kind=''){const box=document.createElement('div');box.className='status '+kind;box.textContent=text;$('#messages').replaceChildren(box)}
function clearMsg(){if($('#messages'))$('#messages').replaceChildren()}
async function api(path,method='GET',body=null){const opts={method,headers:{'Authorization':'Bearer '+token()}};if(body!==null){opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(body)}const r=await fetch(path,opts);let data={};try{data=await r.json()}catch(e){}if(!r.ok||data.ok===false)throw new Error(data.error||('HTTP '+r.status));return data}
function escapeText(v){return v==null?'':String(v)}
function control(item){const wrap=document.createElement('div');wrap.dataset.key=item.key;wrap.dataset.cls=item.class;
 if(item.class==='derived'){const x=document.createElement('input');x.type='text';x.disabled=true;x.value=item.value||'';wrap.appendChild(x);return wrap}
 if(item.class==='replace_only_secret'){const st=document.createElement('div');st.className='secret-state';st.textContent=item.configured?'Configured — leave blank to keep current value':'Not configured';wrap.appendChild(st);const x=document.createElement('input');x.type='password';x.autocomplete='new-password';x.placeholder='Replacement value (optional)';x.dataset.original='';wrap.appendChild(x);return wrap}
 if(item.control==='boolean'){const l=document.createElement('label');l.className='switch';const x=document.createElement('input');x.type='checkbox';x.checked=String(item.value).toLowerCase()==='true';x.dataset.original=x.checked?'true':'false';const t=document.createElement('span');t.textContent=x.checked?'Enabled':'Disabled';x.addEventListener('change',()=>t.textContent=x.checked?'Enabled':'Disabled');l.append(x,t);wrap.appendChild(l);return wrap}
 if(item.control==='select'){const x=document.createElement('select');for(const opt of item.options||[]){const o=document.createElement('option');o.value=opt;o.textContent=opt;o.selected=String(item.value)===String(opt);x.appendChild(o)}x.dataset.original=String(item.value||'');wrap.appendChild(x);return wrap}
 const x=document.createElement('input');x.type=item.control==='number'?'number':'text';x.value=item.value||'';x.dataset.original=String(item.value||'');wrap.appendChild(x);return wrap}
function render(s){state=s;$('#settings').replaceChildren();const byGroup={};for(const item of s.settings||[]){(byGroup[item.group]||(byGroup[item.group]=[])).push(item)}for(const g of s.groups||[]){const items=byGroup[g.id]||[];if(!items.length)continue;const card=document.createElement('section');card.className='card';const h=document.createElement('h2');h.className='group-title';h.textContent=g.label;card.appendChild(h);for(const item of items){const row=document.createElement('div');row.className='row';const left=document.createElement('div');const lab=document.createElement('div');lab.className='label';lab.textContent=item.label||item.key;left.appendChild(lab);const meta=document.createElement('div');meta.className='meta';meta.textContent=item.key+' · '+item.class+(item.restart==='recreate'?' · restart/recreate':'');left.appendChild(meta);if(item.description){const d=document.createElement('div');d.className='desc';d.textContent=item.description;left.appendChild(d)}if(item.warning){const w=document.createElement('div');w.className='warning';w.textContent=item.warning;left.appendChild(w)}row.append(left,control(item));card.appendChild(row)}$('#settings').appendChild(card)}$('#workerBadge').textContent='worker '+(s.worker_time||'ready');$('#previewCard').classList.add('hidden');$('#applyBtn').disabled=true;previewPayload=null}
function collect(){const updates={},secrets={};for(const item of state.settings||[]){if(item.class==='derived')continue;const wrap=document.querySelector('[data-key="'+CSS.escape(item.key)+'"]');if(!wrap)continue;const el=wrap.querySelector('input,select');if(!el)continue;if(item.class==='replace_only_secret'){if(el.value)secrets[item.key]=el.value;continue}let value;if(item.control==='boolean')value=el.checked?'true':'false';else value=el.value;if(String(value)!==String(el.dataset.original??''))updates[item.key]=value}return {updates,secrets}}
function renderPreview(p){$('#preview').replaceChildren();for(const ch of p.changes||[]){const r=document.createElement('div');r.className='preview-row';for(const v of [ch.label||ch.key,ch.from,ch.to]){const d=document.createElement('div');d.textContent=escapeText(v);r.appendChild(d)}$('#preview').appendChild(r)}if(!(p.changes||[]).length){const d=document.createElement('div');d.className='muted';d.textContent='No changes detected.';$('#preview').appendChild(d)}$('#previewWarnings').replaceChildren();if((p.services||[]).length){const d=document.createElement('p');d.className='meta';d.textContent='Services to recreate: '+p.services.join(', ');$('#previewWarnings').appendChild(d)}for(const w of p.warnings||[]){const d=document.createElement('div');d.className='warning';d.textContent=w;$('#previewWarnings').appendChild(d)}$('#previewCard').classList.remove('hidden');$('#applyBtn').disabled=!(p.changes||[]).length}
async function load(){clearMsg();const d=await api('/api/state');render(d.state)}
$('#loginBtn').addEventListener('click',async()=>{const v=$('#token').value.trim();if(!v)return;sessionStorage.setItem(tokenKey,v);try{await load();$('#login').classList.add('hidden');$('#app').classList.remove('hidden');$('#token').value=''}catch(e){sessionStorage.removeItem(tokenKey);$('#loginStatus').className='status err';$('#loginStatus').textContent=e.message}});
$('#logoutBtn').addEventListener('click',()=>{sessionStorage.removeItem(tokenKey);location.reload()});
$('#refreshBtn').addEventListener('click',()=>load().catch(e=>setMsg(e.message,'err')));
$('#previewBtn').addEventListener('click',async()=>{try{clearMsg();const payload=collect();const d=await api('/api/preview','POST',payload);previewPayload=payload;renderPreview(d.preview)}catch(e){setMsg(e.message,'err')}});
$('#applyBtn').addEventListener('click',async()=>{if(!previewPayload)return;if(!confirm('Apply these settings now? A local backup will be created and failed health checks will roll back the .env file.'))return;$('#applyBtn').disabled=true;try{setMsg('Applying settings and running health checks…','warn');const d=await api('/api/apply','POST',previewPayload);setMsg(d.message||'Settings applied','ok');render(d.state);for(const i of document.querySelectorAll('input[type=password]'))i.value=''}catch(e){setMsg(e.message,'err');try{await load()}catch(_){}}});
if(token()){load().then(()=>{$('#login').classList.add('hidden');$('#app').classList.remove('hidden')}).catch(()=>sessionStorage.removeItem(tokenKey))}
</script>
</body></html>'''


def worker_call(payload):
    raw = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
    if len(raw) > MAX_BODY:
        raise RuntimeError("Request too large")
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.settimeout(180)
        sock.connect(str(SOCKET_PATH))
        sock.sendall(raw)
        chunks = []
        total = 0
        while True:
            data = sock.recv(65536)
            if not data:
                break
            chunks.append(data)
            total += len(data)
            if total > 1024 * 1024:
                raise RuntimeError("Worker response too large")
            if b"\n" in data:
                break
        response = json.loads(b"".join(chunks).split(b"\n", 1)[0].decode("utf-8"))
        if not response.get("ok"):
            raise RuntimeError(response.get("error") or "Worker request failed")
        return response
    finally:
        sock.close()


class Handler(BaseHTTPRequestHandler):
    server_version = "SynologyAdminSettings/1.0"

    def log_message(self, fmt, *args):
        # Never log Authorization headers or bodies. Standard request line only.
        print("{} - {}".format(self.address_string(), fmt % args), flush=True)

    def security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")

    def send_json(self, code, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.security_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def authorized(self):
        if not TOKEN:
            return False
        header = self.headers.get("Authorization", "")
        expected = "Bearer " + TOKEN
        return hmac.compare_digest(header, expected)

    def require_auth(self):
        if self.authorized():
            return True
        self.send_json(401, {"ok": False, "error": "Unauthorized"})
        return False

    def read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise RuntimeError("Invalid Content-Length")
        if length < 0 or length > MAX_BODY:
            raise RuntimeError("Request body too large")
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception as exc:
            raise RuntimeError("Invalid JSON body") from exc
        if not isinstance(data, dict):
            raise RuntimeError("JSON body must be an object")
        return data

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {"ok": True, "worker_socket": SOCKET_PATH.exists()})
            return
        if self.path == "/":
            data = HTML.encode("utf-8")
            self.send_response(200)
            self.security_headers()
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path == "/api/state":
            if not self.require_auth():
                return
            try:
                result = worker_call({"action": "state"})
                self.send_json(200, {"ok": True, "state": result["state"]})
            except Exception as exc:
                self.send_json(503, {"ok": False, "error": str(exc)})
            return
        self.send_json(404, {"ok": False, "error": "Not found"})

    def do_POST(self):
        if self.path not in ("/api/preview", "/api/apply"):
            self.send_json(404, {"ok": False, "error": "Not found"})
            return
        if not self.require_auth():
            return
        try:
            body = self.read_json()
            request = {"action": "preview" if self.path.endswith("preview") else "apply"}
            request["updates"] = body.get("updates") or {}
            request["secrets"] = body.get("secrets") or {}
            result = worker_call(request)
            if request["action"] == "preview":
                self.send_json(200, {"ok": True, "preview": result["preview"]})
            else:
                self.send_json(200, result)
        except Exception as exc:
            self.send_json(400, {"ok": False, "error": str(exc)})


def main():
    if not TOKEN:
        raise SystemExit("ADMIN_SETTINGS_ACCESS_TOKEN is not configured; refusing to start an unauthenticated admin panel")
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("Synology Admin Settings listening on port {}".format(PORT), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
