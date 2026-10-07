"""Serve only the exported TC review HTML on one explicitly selected LAN address."""

import argparse
import hashlib
import ipaddress
import json
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import psutil
from filelock import FileLock

from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.scripts.render_tc_review import render_review

LIVE_SCRIPT = """
if(location.protocol!=='file:'){
 const saved=sessionStorage.getItem('tc-review-position');
 if(saved){const p=JSON.parse(saved);document.getElementById('search').value=p.search;filter();window.scrollTo(0,p.y);sessionStorage.removeItem('tc-review-position')}
 const live=new EventSource(location.pathname+'events');
 live.onmessage=e=>{if(e.data!==document.documentElement.dataset.revision){sessionStorage.setItem('tc-review-position',JSON.stringify({search:document.getElementById('search').value,y:window.scrollY}));location.reload()}};
}
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind")
    parser.add_argument("--port", type=int, default=9999)
    parser.add_argument("--stop", action="store_true")
    parser.add_argument(
        "--token",
        default="tc-up-validation",
        help="Optional additional share path; /tc-up-validation/ is always available",
    )
    args = parser.parse_args()
    runtime = hpe990_folders.D_HPE990_RUNTIME
    runtime.mkdir(parents=True, exist_ok=True)
    manifest = runtime / "tc-review-share.json"
    stop = runtime / "tc-review-share.stop"
    if args.stop:
        stop.write_text("stop", encoding="utf-8")
        return
    address = ipaddress.ip_address(args.bind or "")
    if not address.is_private or address.is_loopback or address.is_unspecified:
        raise ValueError("Specify one concrete private LAN address")
    source = hpe990_folders.D_HPE990 / "docs/bdd/preferences_general.feature"
    export = hpe990_folders.D_HPE990_EVIDENCE / "093ca349/preferences-general-tc-review.html"
    token = args.token
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?", token):
        raise ValueError(
            "Expected a 1-64 character share path using lowercase letters, digits, hyphens"
        )
    route = "/tc-up-validation/"
    routes = {route, "/" + token + "/"}
    changed = threading.Condition()
    cache = {}

    def update():
        contents = source.read_text(encoding="utf-8")
        revision = hashlib.sha256(contents.encode()).hexdigest()
        with changed:
            if revision == cache.get("revision"):
                return
        document, summary = render_review(contents)
        document = document.replace(
            '<html lang="ko">', f'<html lang="ko" data-revision="{revision}">'
        )
        document = document.replace("</script>", LIVE_SCRIPT + "</script>")
        with changed:
            cache.update(revision=revision, body=document.encode(), summary=summary)
            changed.notify_all()
        export.write_text(document, encoding="utf-8")

    update()

    def watch():
        stamp = None
        while not stop.exists():
            try:
                current = (source.stat().st_mtime_ns, source.stat().st_size)
                if current != stamp:
                    update()
                    stamp = current
            except Exception:
                # Retry during a partial edit; keep the last readable draft visible.
                pass
            threading.Event().wait(0.1)

    def events(handler):
        handler.send_response(200)
        handler.send_header("Content-Type", "text/event-stream")
        handler.send_header("Cache-Control", "no-store")
        handler.end_headers()
        previous = None
        try:
            while not stop.exists():
                with changed:
                    if previous == cache["revision"]:
                        changed.wait(timeout=10)
                    revision = cache["revision"]
                if previous != revision:
                    handler.wfile.write(f"data: {revision}\n\n".encode())
                    previous = revision
                else:
                    handler.wfile.write(b": heartbeat\n\n")
                handler.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.headers.get("Host") != f"{address}:{args.port}":
                self.send_error(404)
                return
            if self.path in {path + "events" for path in routes}:
                events(self)
                return
            if self.path not in routes:
                self.send_error(404)
                return
            with changed:
                body = cache["body"]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    with FileLock(str(runtime / "tc-review-share.lock"), timeout=0):
        stop.unlink(missing_ok=True)
        threading.Thread(target=watch, daemon=True).start()
        with ThreadingHTTPServer((str(address), args.port), Handler) as server:
            server.timeout = 0.5
            server.daemon_threads = True
            process = psutil.Process()
            record = {
                "url": f"http://{address}:{args.port}{route}",
                "pid": os.getpid(),
                "create_time": process.create_time(),
                "program": process.exe(),
                "html": str(export),
                "source": str(source),
                "watch_interval_ms": 100,
                "live_transport": "server-sent events",
            }
            manifest.write_text(json.dumps(record, indent=2), encoding="utf-8")
            while not stop.exists():
                server.handle_request()
            manifest.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
