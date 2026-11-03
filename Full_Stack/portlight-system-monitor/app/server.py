"""Read-only local dashboard server; Python standard library, no remote execution."""
import argparse
from collections import deque
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import hmac
import os
from pathlib import Path
import threading
from urllib.parse import urlparse, parse_qs

from .analysis import analyze, validate_snapshot
from .demo import demo_snapshot

STATIC = Path(__file__).with_name('static')
MAX_SNAPSHOT_BYTES = 16 * 1024 * 1024


class SnapshotStore:
    def __init__(self, data_dir):
        self.path = Path(data_dir) / 'latest.json'
        self.lock = threading.Lock()
        self.history = deque(maxlen=120)
        self.first_seen = {}
        self.last_stamp = None
        self.latest = None

    def ingest(self, raw):
        validate_snapshot(raw)
        with self.lock:
            self.latest = raw

    def read(self, demo=False):
        if demo:
            result = analyze(demo_snapshot(), demo=True)
            result['history'] = []
            return result
        with self.lock:
            if self.latest is None and not self.path.exists():
                raise FileNotFoundError('No Windows snapshot yet. Run scripts/Collect-Windows.ps1 in Windows PowerShell.')
            if self.latest is None and self.path.stat().st_size > MAX_SNAPSHOT_BYTES:
                raise ValueError('Snapshot exceeds the 16 MiB size limit.')
            raw = self.latest if self.latest is not None else json.loads(self.path.read_text(encoding='utf-8-sig'))
            result = analyze(raw, first_seen=self.first_seen)
            if raw['collected_at'] != self.last_stamp:
                for row in result['connections']:
                    key = f"{row.get('process_name')}|{row.get('remote_address')}|{row.get('remote_port')}"
                    self.first_seen.setdefault(key, raw['collected_at'])
                # Bound memory; oldest first-seen entries are evicted after 5,000 destinations.
                while len(self.first_seen) > 5000:
                    del self.first_seen[next(iter(self.first_seen))]
                self.history.append(dict(at=raw['collected_at'], **result['summary']))
                self.last_stamp = raw['collected_at']
            result['history'] = list(self.history)
            return result


def make_handler(store, ingest_token=None):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            # Do not put telemetry or query strings into access logs.
            pass

        def respond(self, status, body, content_type='application/json; charset=utf-8'):
            if not isinstance(body, bytes):
                body = json.dumps(body, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('X-Frame-Options', 'DENY')
            self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
            self.end_headers()
            self.wfile.write(body)

        def local_host(self):
            try:
                host = urlparse('http://' + self.headers.get('Host', '')).hostname
            except ValueError:
                host = None
            return host in ('localhost', '127.0.0.1', '::1')

        def do_POST(self):
            if not self.local_host():
                self.respond(403, {'error': 'Local Host header required.'})
                return
            if urlparse(self.path).path != '/api/ingest' or not ingest_token:
                self.respond(404, {'error': 'Not found.'})
                return
            # Browser origins never need to upload; this endpoint is collector-only.
            auth = self.headers.get('Authorization', '')
            if self.headers.get('Origin') or not hmac.compare_digest(auth.encode(), ('Bearer ' + ingest_token).encode()):
                self.respond(403, {'error': 'Collector authentication required.'})
                return
            if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json':
                self.respond(415, {'error': 'application/json required.'})
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                length = 0
            if not 0 < length <= MAX_SNAPSHOT_BYTES:
                self.respond(413, {'error': 'Snapshot body must be between 1 byte and 16 MiB.'})
                return
            self.connection.settimeout(10)
            try:
                raw = json.loads(self.rfile.read(length).decode('utf-8-sig'))
                store.ingest(raw)
            except (ValueError, TypeError, KeyError, OSError):
                self.respond(400, {'error': 'Invalid snapshot.'})
                return
            self.respond(200, {'status': 'accepted', 'collected_at': raw['collected_at']})

        def do_GET(self):
            if not self.local_host():
                self.respond(403, {'error': 'Local Host header required.'})
                return
            parsed = urlparse(self.path)
            if parsed.path == '/api/health':
                self.respond(200, {'status': 'ok', 'service': 'portlight', 'telemetry': 'Check /api/snapshot for collector freshness.'})
            elif parsed.path == '/api/snapshot':
                try:
                    mode = parse_qs(parsed.query).get('mode', ['live'])[0]
                    if mode not in ('live', 'demo'):
                        raise ValueError('mode must be live or demo.')
                    self.respond(200, store.read(demo=mode == 'demo'))
                except FileNotFoundError as exc:
                    self.respond(503, {'error': str(exc), 'mode': 'live', 'status': 'waiting'})
                except (ValueError, TypeError, KeyError, OSError):
                    self.respond(503, {'error': 'Snapshot unreadable or invalid. Check the collector terminal; the last file may be inaccessible or incompatible.', 'mode': 'live', 'status': 'error'})
            else:
                files = {'/': ('index.html', 'text/html; charset=utf-8'),
                    '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
                    '/styles.css': ('styles.css', 'text/css; charset=utf-8'),
                    '/favicon.svg': ('favicon.svg', 'image/svg+xml')}
                if parsed.path not in files:
                    self.respond(404, {'error': 'Not found.'})
                    return
                name, mime = files[parsed.path]
                self.respond(200, (STATIC / name).read_bytes(), mime)
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bind', default=os.environ.get('PORTLIGHT_BIND', '127.0.0.1'))
    parser.add_argument('--port', type=int, default=9090)
    parser.add_argument('--data-dir', default=os.environ.get('PORTLIGHT_DATA_DIR', 'data'))
    args = parser.parse_args()
    token = os.environ.get('PORTLIGHT_INGEST_TOKEN')
    server = ThreadingHTTPServer((args.bind, args.port), make_handler(SnapshotStore(args.data_dir), token))
    print(f'Portlight listening on http://{args.bind}:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
