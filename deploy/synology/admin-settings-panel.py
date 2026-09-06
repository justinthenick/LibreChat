#!/usr/bin/env python3
"""Browser-facing Synology Admin Settings panel.

The panel has no .env mount and no Docker socket. Routine browser authentication
uses a password-derived verifier stored in the panel's private state volume and
an HttpOnly SameSite=Strict session cookie. The historical bearer token remains
available only as a host recovery/bootstrap credential.
"""

import base64
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import socket
import tempfile
import threading
import time
from http.cookies import SimpleCookie

PORT = int(os.environ.get("ADMIN_SETTINGS_PORT", "3210"))
RECOVERY_TOKEN = os.environ.get("ADMIN_SETTINGS_ACCESS_TOKEN", "")
SOCKET_PATH = Path(os.environ.get("ADMIN_SETTINGS_SOCKET", "/state/worker.sock"))
AUTH_PATH = Path(os.environ.get("ADMIN_SETTINGS_AUTH_FILE", "/state/auth.json"))
COOKIE_SECURE = os.environ.get("ADMIN_SETTINGS_COOKIE_SECURE", "false").lower() == "true"
COOKIE_NAME = "librechat_admin_settings"
SESSION_TTL = 8 * 60 * 60
MAX_BODY = 128 * 1024
PBKDF2_ITERATIONS = 310000
LOGIN_WINDOW = 300
LOGIN_MAX_FAILURES = 8
_LOGIN_FAILURES = {}
_LOGIN_LOCK = threading.Lock()


def b64e(data):
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def b64d(text):
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def hash_password(password):
    if not isinstance(password, str) or len(password) < 12:
        raise ValueError("Admin password must be at least 12 characters")
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(PBKDF2_ITERATIONS, b64e(salt), b64e(derived))


def verify_password(password, encoded):
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        rounds = int(iterations)
        if rounds < 100000 or rounds > 2000000:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), b64d(salt), rounds)
        return hmac.compare_digest(actual, b64d(expected))
    except Exception:
        return False


def load_auth_state():
    try:
        data = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}
        return data
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def write_auth_state(password):
    state = {
        "schema": 1,
        "password_hash": hash_password(password),
        "session_secret": secrets.token_urlsafe(48),
        "updated_at": int(time.time()),
    }
    AUTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="auth.json.tmp-", dir=str(AUTH_PATH.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_name, 0o600)
        os.replace(temp_name, str(AUTH_PATH))
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return state


def session_secret(state=None):
    state = state or load_auth_state()
    configured = state.get("session_secret")
    if isinstance(configured, str) and configured:
        return configured
    return RECOVERY_TOKEN


def make_session(secret):
    now = int(time.time())
    payload = {"iat": now, "exp": now + SESSION_TTL, "nonce": secrets.token_urlsafe(12)}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    body = b64e(raw)
    sig = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    return body + "." + b64e(sig)


def verify_session(token, secret):
    try:
        body, signature = token.split(".", 1)
        expected = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, b64d(signature)):
            return False
        payload = json.loads(b64d(body).decode("utf-8"))
        now = int(time.time())
        return int(payload.get("iat", 0)) <= now <= int(payload.get("exp", 0))
    except Exception:
        return False


def password_configured():
    value = load_auth_state().get("password_hash")
    return isinstance(value, str) and bool(value)


def record_login_failure(address):
    now = time.time()
    with _LOGIN_LOCK:
        recent = [stamp for stamp in _LOGIN_FAILURES.get(address, []) if now - stamp < LOGIN_WINDOW]
        recent.append(now)
        _LOGIN_FAILURES[address] = recent
        return len(recent)


def login_allowed(address):
    now = time.time()
    with _LOGIN_LOCK:
        recent = [stamp for stamp in _LOGIN_FAILURES.get(address, []) if now - stamp < LOGIN_WINDOW]
        _LOGIN_FAILURES[address] = recent
        return len(recent) < LOGIN_MAX_FAILURES


def clear_login_failures(address):
    with _LOGIN_LOCK:
        _LOGIN_FAILURES.pop(address, None)


HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Synology Admin Settings</title>
<style>
:root{font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color-scheme:light dark;--bg:#0f141b;--card:#171e28;--line:#2a3442;--text:#edf3fb;--muted:#9facbd;--accent:#6aa8ff;--danger:#ff7777;--ok:#70d79a;--warn:#f7c86a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text)}main{max-width:1100px;margin:0 auto;padding:28px 18px 60px}.top{display:flex;gap:12px;align-items:center;justify-content:space-between;margin-bottom:22px}.badge{font-size:12px;padding:4px 8px;border:1px solid var(--line);border-radius:999px;color:var(--muted)}h1{font-size:24px;margin:0}.sub{color:var(--muted);margin:6px 0 0}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;margin:14px 0}.group-title{font-size:16px;margin:0 0 14px}.row{display:grid;grid-template-columns:minmax(260px,1fr) minmax(280px,1fr);gap:14px;padding:13px 0;border-top:1px solid var(--line)}.row:first-of-type{border-top:0}.label{font-weight:600}.desc,.meta,.warning{font-size:12px;color:var(--muted);margin-top:5px;line-height:1.4}.warning{color:var(--warn)}input,select,textarea,button{font:inherit}input[type=text],input[type=number],input[type=password],select,textarea{width:100%;padding:9px 10px;border-radius:8px;border:1px solid var(--line);background:#101720;color:var(--text)}textarea{min-height:84px;resize:vertical}input[type=checkbox]{width:20px;height:20px}.switch{display:flex;align-items:center;gap:9px}.secret-state{font-size:12px;color:var(--muted);margin-bottom:7px}.actions{display:flex;gap:10px;flex-wrap:wrap;position:sticky;bottom:10px;background:rgba(15,20,27,.95);padding:12px;border:1px solid var(--line);border-radius:12px;backdrop-filter:blur(8px)}button{border:1px solid var(--line);background:#1d2734;color:var(--text);border-radius:8px;padding:9px 13px;cursor:pointer}button.primary{background:var(--accent);color:#07111d;border-color:transparent;font-weight:700}button:disabled{opacity:.45;cursor:not-allowed}.hidden{display:none!important}.status{padding:10px 12px;border-radius:8px;background:#101720;border:1px solid var(--line);font-size:13px;white-space:pre-wrap}.status.ok{border-color:#2c6c49;color:var(--ok)}.status.err{border-color:#7a3d3d;color:var(--danger)}.status.warn{border-color:#80662f;color:var(--warn)}.preview-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;padding:8px 0;border-top:1px solid var(--line);font-size:13px}.preview-row:first-child{border-top:0}.muted{color:var(--muted)}#login{max-width:520px;margin:70px auto}@media(max-width:700px){.row{grid-template-columns:1fr}.preview-row{grid-template-columns:1fr}.actions{position:static}}
</style></head>
<body><main>
<section id="login" class="card">
  <h1>Synology Admin Settings</h1><p class="sub">Administrator sign-in</p>
  <div style="margin-top:18px"><label id="credentialLabel" class="label" for="credential">Admin password</label><input id="credential" type="password" autocomplete="current-password"></div>
  <p id="loginNote" class="desc"></p><button id="loginBtn" class="primary">Open settings</button>
  <div id="loginStatus" class="status hidden" style="margin-top:12px"></div>
</section>
<section id="app" class="hidden">
  <div class="top"><div><h1>Synology Admin Settings</h1><p class="sub">Safe, allowlisted LibreChat deployment configuration</p></div><div><span id="workerBadge" class="badge">worker</span> <button id="logoutBtn">Log out</button></div></div>
  <div id="messages"></div>
  <section class="card"><h2 class="group-title">Admin panel password</h2><p id="passwordNote" class="desc"></p><div class="row"><div><div class="label">New admin password</div><div class="meta">At least 12 characters. Changing it invalidates every existing admin-panel session.</div></div><div><input id="newPassword" type="password" autocomplete="new-password" placeholder="New password"><input id="confirmPassword" type="password" autocomplete="new-password" placeholder="Confirm password" style="margin-top:8px"><button id="passwordBtn" style="margin-top:8px">Set / change password</button></div></div></section>
  <div id="settings"></div>
  <section id="previewCard" class="card hidden"><h2 class="group-title">Change preview</h2><div id="preview"></div><div id="previewWarnings"></div></section>
  <div class="actions"><button id="refreshBtn">Refresh</button><button id="previewBtn">Preview changes</button><button id="applyBtn" class="primary" disabled>Apply changes</button></div>
</section>
<script>
const $=s=>document.querySelector(s);let state=null,previewPayload=null,authInfo={password_configured:false};
function setMsg(text,kind=''){const box=document.createElement('div');box.className='status '+kind;box.textContent=text;$('#messages').replaceChildren(box)}
function clearMsg(){if($('#messages'))$('#messages').replaceChildren()}
async function api(path,method='GET',body=null){const opts={method,credentials:'same-origin',headers:{}};if(body!==null){opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(body)}const r=await fetch(path,opts);let data={};try{data=await r.json()}catch(e){}if(!r.ok||data.ok===false)throw new Error(data.error||('HTTP '+r.status));return data}
function control(item){const wrap=document.createElement('div');wrap.dataset.key=item.key;wrap.dataset.cls=item.class;if(item.class==='derived'){const x=document.createElement('input');x.type='text';x.disabled=true;x.value=item.value||'';wrap.appendChild(x);return wrap}if(item.class==='replace_only_secret'){const st=document.createElement('div');st.className='secret-state';st.textContent=item.configured?'Configured — leave blank to keep current value':'Not configured';wrap.appendChild(st);const x=document.createElement('input');x.type='password';x.autocomplete='new-password';x.placeholder='Replacement value (optional)';x.dataset.original='';wrap.appendChild(x);return wrap}if(item.control==='boolean'){const l=document.createElement('label');l.className='switch';const x=document.createElement('input');x.type='checkbox';x.checked=String(item.value).toLowerCase()==='true';x.dataset.original=x.checked?'true':'false';const t=document.createElement('span');t.textContent=x.checked?'Enabled':'Disabled';x.addEventListener('change',()=>t.textContent=x.checked?'Enabled':'Disabled');l.append(x,t);wrap.appendChild(l);return wrap}if(item.control==='select'){const x=document.createElement('select');for(const opt of item.options||[]){const o=document.createElement('option');o.value=opt;o.textContent=opt;o.selected=String(item.value)===String(opt);x.appendChild(o)}x.dataset.original=String(item.value||'');wrap.appendChild(x);return wrap}const x=document.createElement(item.control==='textarea'?'textarea':'input');if(x.tagName==='INPUT')x.type=item.control==='number'?'number':'text';x.value=item.value||'';x.dataset.original=String(item.value||'');wrap.appendChild(x);return wrap}
function render(s){state=s;$('#settings').replaceChildren();const byGroup={};for(const item of s.settings||[]){(byGroup[item.group]||(byGroup[item.group]=[])).push(item)}for(const g of s.groups||[]){const items=byGroup[g.id]||[];if(!items.length)continue;const card=document.createElement('section');card.className='card';const h=document.createElement('h2');h.className='group-title';h.textContent=g.label;card.appendChild(h);for(const item of items){const row=document.createElement('div');row.className='row';const left=document.createElement('div');const lab=document.createElement('div');lab.className='label';lab.textContent=item.label||item.key;left.appendChild(lab);const meta=document.createElement('div');meta.className='meta';meta.textContent=item.key+' · '+item.class+(item.restart==='recreate'?' · restart/recreate':'');left.appendChild(meta);if(item.description){const d=document.createElement('div');d.className='desc';d.textContent=item.description;left.appendChild(d)}if(item.warning){const w=document.createElement('div');w.className='warning';w.textContent=item.warning;left.appendChild(w)}row.append(left,control(item));card.appendChild(row)}$('#settings').appendChild(card)}$('#workerBadge').textContent='worker '+(s.worker_time||'ready');$('#previewCard').classList.add('hidden');$('#applyBtn').disabled=true;previewPayload=null;$('#passwordNote').textContent=authInfo.password_configured?'Password login is configured. The host recovery token remains available only for emergency access.':'Password login is not configured yet. Set one now; your current recovery-token session will be invalidated.'}
function collect(){const updates={},secrets={};for(const item of state.settings||[]){if(item.class==='derived')continue;const wrap=document.querySelector('[data-key="'+CSS.escape(item.key)+'"]');if(!wrap)continue;const el=wrap.querySelector('input,select,textarea');if(!el)continue;if(item.class==='replace_only_secret'){if(el.value)secrets[item.key]=el.value;continue}let value=item.control==='boolean'?(el.checked?'true':'false'):el.value;if(String(value)!==String(el.dataset.original??''))updates[item.key]=value}return {updates,secrets}}
function renderPreview(p){$('#preview').replaceChildren();for(const ch of p.changes||[]){const r=document.createElement('div');r.className='preview-row';for(const v of [ch.label||ch.key,ch.from,ch.to]){const d=document.createElement('div');d.textContent=v==null?'':String(v);r.appendChild(d)}$('#preview').appendChild(r)}if(!(p.changes||[]).length){const d=document.createElement('div');d.className='muted';d.textContent='No changes detected.';$('#preview').appendChild(d)}$('#previewWarnings').replaceChildren();if((p.services||[]).length){const d=document.createElement('p');d.className='meta';d.textContent='Services to recreate: '+p.services.join(', ');$('#previewWarnings').appendChild(d)}for(const w of p.warnings||[]){const d=document.createElement('div');d.className='warning';d.textContent=w;$('#previewWarnings').appendChild(d)}$('#previewCard').classList.remove('hidden');$('#applyBtn').disabled=!(p.changes||[]).length}
async function authState(){const d=await api('/api/auth-state');authInfo=d;$('#credentialLabel').textContent=d.password_configured?'Admin password':'Recovery access token';$('#loginNote').textContent=d.password_configured?'Use the admin-panel password. The long recovery token is no longer needed for normal browser access.':'One-time migration: sign in with the existing recovery token, then set a normal password from the first card.'}
async function load(){clearMsg();const d=await api('/api/state');render(d.state)}
$('#loginBtn').addEventListener('click',async()=>{const credential=$('#credential').value;if(!credential)return;try{const d=await api('/api/login','POST',{credential});authInfo.password_configured=!!d.password_configured;await load();$('#login').classList.add('hidden');$('#app').classList.remove('hidden');$('#credential').value=''}catch(e){$('#loginStatus').className='status err';$('#loginStatus').textContent=e.message}});
$('#logoutBtn').addEventListener('click',async()=>{try{await api('/api/logout','POST',{})}catch(e){}location.reload()});
$('#passwordBtn').addEventListener('click',async()=>{const p=$('#newPassword').value,c=$('#confirmPassword').value;if(p!==c){setMsg('Passwords do not match.','err');return}try{const d=await api('/api/password','POST',{password:p});$('#newPassword').value='';$('#confirmPassword').value='';alert(d.message||'Password changed. Sign in again.');location.reload()}catch(e){setMsg(e.message,'err')}});
$('#refreshBtn').addEventListener('click',()=>load().catch(e=>setMsg(e.message,'err')));
$('#previewBtn').addEventListener('click',async()=>{try{clearMsg();const payload=collect();const d=await api('/api/preview','POST',payload);previewPayload=payload;renderPreview(d.preview)}catch(e){setMsg(e.message,'err')}});
$('#applyBtn').addEventListener('click',async()=>{if(!previewPayload)return;if(!confirm('Apply these settings now? A local backup will be created and failed health checks will roll back the .env file.'))return;$('#applyBtn').disabled=true;try{setMsg('Applying settings and running health checks…','warn');const d=await api('/api/apply','POST',previewPayload);setMsg(d.message||'Settings applied','ok');render(d.state);for(const i of document.querySelectorAll('input[type=password]'))i.value=''}catch(e){setMsg(e.message,'err');try{await load()}catch(_){}}});
authState().catch(()=>{});load().then(()=>{$('#login').classList.add('hidden');$('#app').classList.remove('hidden')}).catch(()=>{});
</script></main></body></html>'''


def worker_call(payload):
    raw = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
    if len(raw) > MAX_BODY:
        raise RuntimeError("Request too large")
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sock.settimeout(180); sock.connect(str(SOCKET_PATH)); sock.sendall(raw)
        chunks=[]; total=0
        while True:
            data=sock.recv(65536)
            if not data: break
            chunks.append(data); total+=len(data)
            if total>1024*1024: raise RuntimeError("Worker response too large")
            if b"\n" in data: break
        response=json.loads(b"".join(chunks).split(b"\n",1)[0].decode("utf-8"))
        if not response.get("ok"): raise RuntimeError(response.get("error") or "Worker request failed")
        return response
    finally:
        sock.close()


class Handler(BaseHTTPRequestHandler):
    server_version = "SynologyAdminSettings/2.0"

    def log_message(self, fmt, *args):
        print("{} - {}".format(self.address_string(), fmt % args), flush=True)

    def security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")

    def send_json(self, code, payload, cookies=None):
        data=json.dumps(payload,ensure_ascii=False).encode("utf-8")
        self.send_response(code); self.security_headers()
        if cookies:
            for cookie in cookies: self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(data))); self.end_headers(); self.wfile.write(data)

    def cookie_value(self, name):
        try:
            cookie=SimpleCookie(); cookie.load(self.headers.get("Cookie", "")); item=cookie.get(name); return item.value if item else ""
        except Exception:
            return ""

    def authorized(self):
        state=load_auth_state(); secret=session_secret(state)
        cookie=self.cookie_value(COOKIE_NAME)
        if secret and cookie and verify_session(cookie, secret): return True
        # Emergency/automation fallback. Browser UI never stores this token.
        header=self.headers.get("Authorization", "")
        return bool(RECOVERY_TOKEN) and hmac.compare_digest(header, "Bearer "+RECOVERY_TOKEN)

    def require_auth(self):
        if self.authorized(): return True
        self.send_json(401,{"ok":False,"error":"Unauthorized"}); return False

    def read_json(self):
        try: length=int(self.headers.get("Content-Length","0"))
        except ValueError: raise RuntimeError("Invalid Content-Length")
        if length<0 or length>MAX_BODY: raise RuntimeError("Request body too large")
        raw=self.rfile.read(length)
        try: data=json.loads(raw.decode("utf-8")) if raw else {}
        except Exception as exc: raise RuntimeError("Invalid JSON body") from exc
        if not isinstance(data,dict): raise RuntimeError("JSON body must be an object")
        return data

    def session_cookie(self, token, clear=False):
        value="" if clear else token
        parts=["{}={}".format(COOKIE_NAME,value),"Path=/","HttpOnly","SameSite=Strict"]
        parts.append("Max-Age=0" if clear else "Max-Age={}".format(SESSION_TTL))
        if COOKIE_SECURE: parts.append("Secure")
        return "; ".join(parts)

    def do_GET(self):
        if self.path=="/health": self.send_json(200,{"ok":True,"worker_socket":SOCKET_PATH.exists(),"password_auth":password_configured()}); return
        if self.path=="/":
            data=HTML.encode("utf-8"); self.send_response(200); self.security_headers(); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(data))); self.end_headers(); self.wfile.write(data); return
        if self.path=="/api/auth-state": self.send_json(200,{"ok":True,"password_configured":password_configured()}); return
        if self.path=="/api/state":
            if not self.require_auth(): return
            try:
                result=worker_call({"action":"state"}); self.send_json(200,{"ok":True,"state":result["state"]})
            except Exception as exc: self.send_json(503,{"ok":False,"error":str(exc)})
            return
        self.send_json(404,{"ok":False,"error":"Not found"})

    def do_POST(self):
        if self.path=="/api/login":
            if not login_allowed(self.client_address[0]): self.send_json(429,{"ok":False,"error":"Too many failed login attempts; retry in a few minutes"}); return
            try: credential=str(self.read_json().get("credential") or "")
            except Exception as exc: self.send_json(400,{"ok":False,"error":str(exc)}); return
            state=load_auth_state(); encoded=state.get("password_hash")
            if isinstance(encoded,str) and encoded:
                valid=verify_password(credential,encoded); mode="password"
            else:
                valid=bool(RECOVERY_TOKEN) and hmac.compare_digest(credential,RECOVERY_TOKEN); mode="recovery_token"
            if not valid:
                record_login_failure(self.client_address[0]); self.send_json(401,{"ok":False,"error":"Invalid administrator credential"}); return
            clear_login_failures(self.client_address[0]); secret=session_secret(state)
            if not secret: self.send_json(503,{"ok":False,"error":"Admin authentication is not configured"}); return
            token=make_session(secret); self.send_json(200,{"ok":True,"mode":mode,"password_configured":bool(encoded)},[self.session_cookie(token)]); return
        if self.path=="/api/logout": self.send_json(200,{"ok":True},[self.session_cookie("",clear=True)]); return
        if self.path=="/api/password":
            if not self.require_auth(): return
            try:
                password=str(self.read_json().get("password") or ""); write_auth_state(password)
                self.send_json(200,{"ok":True,"message":"Admin password saved. All existing admin-panel sessions were invalidated; sign in again."},[self.session_cookie("",clear=True)])
            except Exception as exc: self.send_json(400,{"ok":False,"error":str(exc)})
            return
        if self.path not in ("/api/preview","/api/apply"): self.send_json(404,{"ok":False,"error":"Not found"}); return
        if not self.require_auth(): return
        try:
            body=self.read_json(); request={"action":"preview" if self.path.endswith("preview") else "apply","updates":body.get("updates") or {},"secrets":body.get("secrets") or {}}
            result=worker_call(request)
            if request["action"]=="preview": self.send_json(200,{"ok":True,"preview":result["preview"]})
            else: self.send_json(200,result)
        except Exception as exc: self.send_json(400,{"ok":False,"error":str(exc)})


def main():
    if not RECOVERY_TOKEN and not password_configured():
        raise SystemExit("Admin Settings has neither password state nor recovery token; refusing unauthenticated startup")
    server=ThreadingHTTPServer(("0.0.0.0",PORT),Handler)
    print("Synology Admin Settings listening on port {} (password auth: {})".format(PORT,"configured" if password_configured() else "migration required"),flush=True)
    server.serve_forever()


if __name__=="__main__": main()
