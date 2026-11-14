"""Tiny demo shop API (AiVerdict video 008)."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

PRODUCTS = [
    {"id": 1, "name": "Mechanical keyboard", "price": 89.0},
    {"id": 2, "name": "USB-C hub", "price": 39.0},
]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/products":
            body = json.dumps(PRODUCTS).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "3000"))
    print(f"shop-api on http://localhost:{port}")
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
