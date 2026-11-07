# -*- coding: utf-8 -*-
# I am pro human editor - local relay
# Lets the website (https://ayushbropro.github.io) talk to FreeLLMAPI on this PC.
# It listens on 127.0.0.1:31416, forwards everything to FreeLLMAPI on 31415,
# and adds the browser-permission headers (CORS / Private Network Access).
# Nothing leaves your PC except the answers FreeLLMAPI already gives.
import http.server, socketserver, urllib.request, urllib.error, sys

RELAY_VERSION = "1.1"
TARGET = "http://127.0.0.1:31415"
LISTEN = 31416

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "authorization, content-type, x-requested-with",
    "Access-Control-Allow-Private-Network": "true",
}

class Relay(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def _cors(self):
        for k, v in CORS.items():
            self.send_header(k, v)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _proxy(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        body = self.rfile.read(length) if length else None
        url = TARGET + self.path
        headers = {}
        for k, v in self.headers.items():
            if k.lower() in ("host", "content-length", "connection", "accept-encoding"):
                continue
            headers[k] = v
        req = urllib.request.Request(url, data=body, headers=headers, method=self.command)
        print("relay: %s %s%s" % (self.command, self.path, ("  body: " + body[:300].decode("utf-8", "replace")) if body and self.command == "POST" else ""), flush=True)
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                data = resp.read()
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() in ("transfer-encoding", "connection", "content-length", "content-encoding"):
                        continue
                    self.send_header(k, v)
                self._cors()
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            data = e.read()
            # Show the real reason in this window, and pass it through to the browser.
            print("relay: FreeLLMAPI answered HTTP %d: %s" % (e.code, data[:600].decode("utf-8", "replace")), flush=True)
            self.send_response(e.code)
            self._cors()
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            print("relay: could not reach FreeLLMAPI at %s: %s" % (TARGET, e), flush=True)
            msg = ("relay v%s could not reach FreeLLMAPI at %s: %s" % (RELAY_VERSION, TARGET, e)).encode()
            self.send_response(502)
            self._cors()
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    do_GET = _proxy
    do_POST = _proxy
    do_PUT = _proxy
    do_DELETE = _proxy

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

if __name__ == "__main__":
    print("=" * 56)
    print("  I am pro human editor - local relay  v%s" % RELAY_VERSION)
    print("  (this version prints what FreeLLMAPI answers below)")
    print("  Listening on  http://127.0.0.1:%d" % LISTEN)
    print("  Forwarding to FreeLLMAPI at %s" % TARGET)
    print()
    print("  In the editor's Settings, set the API base URL to:")
    print("      http://127.0.0.1:%d/v1" % LISTEN)
    print()
    print("  Keep this window open while you use the editor.")
    print("  Close it to stop.")
    print("=" * 56)
    try:
        with Server(("127.0.0.1", LISTEN), Relay) as httpd:
            httpd.serve_forever()
    except OSError as e:
        print()
        print("Could not start: %s" % e)
        print("Is the relay already running in another window?")
        input("Press Enter to close...")
    except KeyboardInterrupt:
        pass
