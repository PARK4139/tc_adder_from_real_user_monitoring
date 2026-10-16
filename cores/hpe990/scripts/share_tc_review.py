"""Serve only the exported TC review HTML on one explicitly selected LAN address."""

import argparse
import hashlib
import ipaddress
import json
import os
import re
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

import psutil
from filelock import FileLock

from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.functions.tc_repository import load_review_source, review_stamp
from cores.hpe990.functions.ui_viewer import monitoring_viewer_data, render_html as render_dashboard_html
from cores.hpe990.scripts.render_tc_review import load_basic_scenarios, render_review

LIVE_SCRIPT = """
if(location.protocol!=='file:'){
 const saved=sessionStorage.getItem('tc-review-position');
 if(saved){const p=JSON.parse(saved);document.getElementById('search').value=p.search;filter();window.scrollTo(0,p.y);sessionStorage.removeItem('tc-review-position')}
 const live=new EventSource(location.pathname+'events');
 live.onmessage=e=>{if(e.data!==document.documentElement.dataset.revision){sessionStorage.setItem('tc-review-position',JSON.stringify({search:document.getElementById('search').value,y:window.scrollY}));location.reload()}};
}
"""


def stop_previous(record, stop, timeout=10):
    """Ask the recorded process to exit; never terminate an unrelated reused PID."""
    if not record:
        return
    try:
        process = psutil.Process(record["pid"])
        if process.create_time() != record["create_time"]:
            return
        if os.path.normcase(process.exe()) != os.path.normcase(record["program"]):
            return
    except psutil.NoSuchProcess:
        return
    stop.write_text("stop", encoding="utf-8")
    try:
        process.wait(timeout=timeout)
    except psutil.TimeoutExpired as error:
        raise RuntimeError("Previous TC review server did not stop within 10 seconds") from error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bind")
    parser.add_argument("--port", type=int)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--stop", action="store_true")
    action.add_argument("--restart", action="store_true", default=True, help="Restart (default)")
    parser.add_argument("--open-browser", action="store_true")
    parser.add_argument(
        "--token",
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
    previous = {}
    if args.restart and manifest.exists():
        previous = json.loads(manifest.read_text(encoding="utf-8"))
    previous_url = urlsplit(previous.get("url", ""))
    address = ipaddress.ip_address(args.bind or previous_url.hostname or "172.20.13.185")
    args.port = args.port if args.port is not None else previous_url.port or 9999
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    if not address.is_private or address.is_loopback or address.is_unspecified:
        raise ValueError("Specify one concrete private LAN address")
    source = hpe990_folders.D_HPE990_TC_CASES
    export = hpe990_folders.D_HPE990_EVIDENCE / "093ca349/preferences-general-tc-review.html"
    token = args.token if args.token is not None else previous.get("token", "tc-up-validation")
    if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?", token):
        raise ValueError(
            "Expected a 1-64 character share path using lowercase letters, digits, hyphens"
        )
    route = "/tc-up-validation/"
    url = f"http://{address}:{args.port}{route}"
    dashboard_route = "/activity/"
    dashboard_url = f"http://{address}:{args.port}{dashboard_route}"
    if args.restart:
        stop_previous(previous, stop)
    review_routes = {route, "/" + token + "/"}
    routes = review_routes | {dashboard_route}
    changed = threading.Condition()
    cache = {}
    dashboard_root = hpe990_folders.D_HPE990_EVIDENCE / "ui"
    dashboard_lock = threading.Lock()
    dashboard_data = {
        "session_id": None,
        "summary": {},
        "ui": {"windows": [], "summary": {}},
        "ui_error": "화면 자료를 불러오는 중입니다.",
        "bdd": {"bdd": {"scenarios": [], "expected_tests": 0}},
    }
    dashboard_page = render_dashboard_html(dashboard_data, dashboard_url).encode("utf-8")

    def update():
        contents = load_review_source()
        scenarios = load_basic_scenarios()
        revision_source = contents + json.dumps(scenarios, ensure_ascii=False, sort_keys=True)
        revision = hashlib.sha256(revision_source.encode()).hexdigest()
        with changed:
            if revision == cache.get("revision"):
                return
        document, summary = render_review(
            contents, scenarios, functions_root=True
        )
        document = document.replace(
            '<html lang="ko">', f'<html lang="ko" data-revision="{revision}">'
        )
        document = document.replace("</script>", LIVE_SCRIPT + "</script>")
        with changed:
            cache.update(revision=revision, body=document.encode(), summary=summary)
            changed.notify_all()
        export.parent.mkdir(parents=True, exist_ok=True)
        export.write_text(document, encoding="utf-8")

    update()

    def watch():
        stamp = None
        while not stop.exists():
            try:
                current = review_stamp()
                if current != stamp:
                    update()
                    stamp = current
            except Exception:
                # Retry during a partial edit; keep the last readable draft visible.
                pass
            threading.Event().wait(0.1)

    def watch_dashboard():
        while not stop.exists():
            try:
                latest = monitoring_viewer_data()
                with dashboard_lock:
                    dashboard_data.clear()
                    dashboard_data.update(latest)
            except Exception:
                pass
            stop.wait(5)

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
            request_path = urlsplit(self.path).path
            if request_path in {path + "events" for path in review_routes}:
                events(self)
                return
            if request_path == dashboard_route:
                body = dashboard_page
                content_type = "text/html; charset=utf-8"
            elif request_path == dashboard_route + "data":
                with dashboard_lock:
                    body = json.dumps(dashboard_data, ensure_ascii=False).encode("utf-8")
                content_type = "application/json; charset=utf-8"
            elif request_path.startswith(dashboard_route + "image/"):
                try:
                    relative = Path(unquote(request_path[len(dashboard_route + "image/") :]))
                    if relative.is_absolute() or relative.suffix.lower() != ".png":
                        self.send_error(404)
                        return
                    image_path = (dashboard_root / relative).resolve()
                    image_path.relative_to(dashboard_root.resolve())
                    if not image_path.is_file():
                        self.send_error(404)
                        return
                    body = image_path.read_bytes()
                except (OSError, ValueError):
                    self.send_error(404)
                    return
                content_type = "image/png"
            elif request_path in review_routes:
                with changed:
                    body = cache["body"]
                content_type = "text/html; charset=utf-8"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type)
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
        threading.Thread(target=watch_dashboard, daemon=True).start()
        with ThreadingHTTPServer((str(address), args.port), Handler) as server:
            server.timeout = 0.5
            server.daemon_threads = True
            process = psutil.Process()
            record = {
                "url": url,
                "activity_url": dashboard_url,
                "token": token,
                "pid": os.getpid(),
                "create_time": process.create_time(),
                "program": process.exe(),
                "html": str(export),
                "source": str(source),
                "watch_interval_ms": 100,
                "live_transport": "server-sent events",
            }
            manifest.write_text(json.dumps(record, indent=2), encoding="utf-8")
            print(f"TC review ready: {url}", flush=True)
            print("Keep this console open. Use tc-review.cmd --stop to stop.", flush=True)
            if args.open_browser:
                threading.Thread(target=webbrowser.open, args=(url,), daemon=True).start()
            while not stop.exists():
                server.handle_request()
            # Retain the last settings so --restart also works after a normal stop.


if __name__ == "__main__":
    main()
