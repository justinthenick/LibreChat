#!/usr/bin/env python3
"""Narrow reverse proxy for embedding Synology Deployment Settings in the Admin Panel."""

from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from urllib.parse import urlsplit

PORT = int(os.environ.get("DEPLOYMENT_GATEWAY_PORT", "3211"))
UPSTREAM = os.environ.get("DEPLOYMENT_GATEWAY_UPSTREAM", "http://admin-settings:3210")
FRAME_ANCESTOR = os.environ.get("DEPLOYMENT_GATEWAY_FRAME_ANCESTOR", "")
MAX_BODY = 128 * 1024

upstream = urlsplit(UPSTREAM)
if upstream.scheme != "http" or not upstream.hostname or not upstream.port:
    raise SystemExit("DEPLOYMENT_GATEWAY_UPSTREAM must be an http://host:port URL")
if not FRAME_ANCESTOR.startswith(("http://", "https://")):
    raise SystemExit("DEPLOYMENT_GATEWAY_FRAME_ANCESTOR must be an http(s) origin")


class Handler(BaseHTTPRequestHandler):
    server_version = "LibreChatDeploymentGateway/1.0"

    def log_message(self, fmt, *args):
        print("{} - {}".format(self.address_string(), fmt % args), flush=True)

    def _proxy(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_error(400, "Invalid Content-Length")
            return
        if length < 0 or length > MAX_BODY:
            self.send_error(413, "Request body too large")
            return

        body = self.rfile.read(length) if length else None
        headers = {}
        for name in ("Content-Type", "Cookie", "Authorization", "Accept"):
            value = self.headers.get(name)
            if value:
                headers[name] = value
        headers["Host"] = upstream.netloc

        connection = HTTPConnection(upstream.hostname, upstream.port, timeout=30)
        try:
            connection.request(self.command, self.path, body=body, headers=headers)
            response = connection.getresponse()
            payload = response.read()
        except Exception as exc:
            self.send_response(502)
            self._security_headers()
            data = ("Deployment gateway upstream failure: {}".format(exc)).encode("utf-8")
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        finally:
            connection.close()

        self.send_response(response.status)
        self._security_headers()
        passthrough = {"content-type", "set-cookie", "location"}
        for name, value in response.getheaders():
            if name.lower() in passthrough:
                self.send_header(name, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def _security_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
            "connect-src 'self'; frame-ancestors {}; base-uri 'none'; form-action 'self'".format(
                FRAME_ANCESTOR
            ),
        )

    def do_GET(self):
        self._proxy()

    def do_HEAD(self):
        self._proxy()

    def do_POST(self):
        self._proxy()


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("Deployment frame gateway listening on {} for ancestor {}".format(PORT, FRAME_ANCESTOR), flush=True)
    server.serve_forever()
