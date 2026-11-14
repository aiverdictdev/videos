"""The "attacker server" for the video 008 demo: logs every request it receives.
Usage: python3 listener.py <your Mac LAN address> [logfile]   (listens on port 8765)"""
import datetime
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

LOG = sys.argv[2] if len(sys.argv) > 2 else "listener.log"


class H(BaseHTTPRequestHandler):
    def _log(self, body=b""):
        with open(LOG, "a") as f:
            f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')} {self.client_address[0]} "
                    f"{self.command} {self.path}\n")
            if body:
                f.write(body.decode(errors="replace") + "\n")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok\n")

    def do_GET(self):
        self._log()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        self._log(self.rfile.read(n))

    def log_message(self, *a):
        pass


HTTPServer((sys.argv[1], 8765), H).serve_forever()
