#!/usr/bin/env python3
"""Local preview with clean URLs and an actual 404 response."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import argparse

ROOT = Path(__file__).resolve().parents[1] / 'dist'
class Handler(SimpleHTTPRequestHandler):
    def send_error(self, code, message=None, explain=None):
        if code == 404 and (ROOT / '404.html').exists():
            body = (ROOT / '404.html').read_bytes()
            self.send_response(404); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(body))); self.end_headers()
            if self.command != 'HEAD': self.wfile.write(body)
        else: super().send_error(code, message, explain)

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--port', type=int, default=3000); p.add_argument('--host', default='127.0.0.1'); args = p.parse_args()
    if not (ROOT / 'index.html').exists(): p.error('Run python3 scripts/build.py first')
    print(f'Serving {ROOT} at http://{args.host}:{args.port}', flush=True)
    ThreadingHTTPServer((args.host,args.port),partial(Handler,directory=str(ROOT))).serve_forever()
