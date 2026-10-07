"""Data-driven local viewer for saved UI evidence, including historical sessions."""

import hashlib
import json
import os
import re
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import psutil
from filelock import FileLock

from cores.common.functions.run_family_bdd import bdd_registry
from cores.hpe990.common.paths import hpe990_folders


def evidence_root(session_id: str | None = None) -> Path:
    root = hpe990_folders.D_HPE990_EVIDENCE / "ui"
    if session_id is not None:
        if not re.fullmatch(r"[0-9a-f]{32}", session_id):
            raise ValueError("Expected a saved UI session ID")
        root = root / session_id
    if not root.is_dir():
        raise FileNotFoundError("No saved UI collection found")
    return root


def viewer_data(session_id: str | None = None) -> dict:
    """Discover observations from data; never assume a fixed list of screens or controls."""
    root = evidence_root(session_id)
    ui_root = evidence_root().resolve()
    windows, controls, sessions, failures, fingerprints = {}, {}, set(), [], []
    observations = 0
    image_hashes = {}
    catalog_actions = {}
    catalogs = root.glob("ui-inventory.json") if session_id else root.glob("*/ui-inventory.json")
    for path in catalogs:
        try:
            catalog = json.loads(path.read_text(encoding="utf-8-sig"))
            fingerprints.append((str(path), path.stat().st_mtime_ns))
            for item in catalog.get("controls", []):
                catalog_actions[(catalog["session_id"], item["identity"]["hwnd"])] = len(
                    item.get("actions", [])
                )
        except (OSError, ValueError, KeyError, TypeError) as error:
            failures.append({"file": str(path), "error": type(error).__name__})
    pattern = "*/inventory.json" if session_id else "*/*/inventory.json"
    for path in root.glob(pattern):
        try:
            path.resolve().relative_to(ui_root)
            record = json.loads(path.read_text(encoding="utf-8-sig"))
            sid = record["session_id"]
            observed = record["observed_unix_ms"]
            nodes = record["nodes"]
            shots = {s["hwnd"]: s for s in record.get("screenshots", [])}
            sessions.add(sid)
            observations += 1
            fingerprints.append((str(path), path.stat().st_mtime_ns))
            by_handle = {n["hwnd"]: n for n in nodes}
            for node in nodes:
                identity = (sid, node["hwnd"])
                previous = controls.get(identity)
                observations_count = previous["observations"] + 1 if previous else 1
                if previous and previous["observed_unix_ms"] > observed:
                    previous["observations"] = observations_count
                    continue
                current, seen, ancestry = node, set(), []
                while current["hwnd"] not in seen:
                    seen.add(current["hwnd"])
                    ancestry.append(current["name"] or current["class_name"])
                    if current["parent"] not in by_handle:
                        break
                    current = by_handle[current["parent"]]
                controls[identity] = {
                    **node,
                    "session_id": sid,
                    "window_name": current["name"] or current["class_name"],
                    "path": list(reversed(ancestry)),
                    "observations": observations_count,
                    "observed_unix_ms": observed,
                    "action_count": catalog_actions.get(identity),
                    "evidence": str(path),
                }
            children = {}
            for node in nodes:
                children.setdefault(node["parent"], []).append(node)
            for window in record["roots"]:
                # Hidden native support windows still appear in the hierarchy of their root.
                if not window["visible"]:
                    continue
                descendants, pending, seen = [], [window], set()
                while pending:
                    node = pending.pop()
                    if node["hwnd"] in seen:
                        continue
                    seen.add(node["hwnd"])
                    item = dict(node)
                    item["action_count"] = catalog_actions.get((sid, node["hwnd"]))
                    descendants.append(item)
                    pending.extend(reversed(children.get(node["hwnd"], [])))
                shot = shots.get(window["hwnd"])
                image = None
                image_digest = None
                if shot:
                    image_path = Path(shot["path"]).resolve()
                    image_path.relative_to(ui_root)
                    if image_path.is_file() and image_path.suffix.lower() == ".png":
                        image = image_path.relative_to(ui_root).as_posix()
                        image_digest = shot.get("sha256")
                        if not isinstance(image_digest, str) or not re.fullmatch(
                            r"[0-9a-f]{64}", image_digest
                        ):
                            if image not in image_hashes:
                                with image_path.open("rb") as stream:
                                    image_hashes[image] = hashlib.file_digest(
                                        stream, "sha256"
                                    ).hexdigest()
                            image_digest = image_hashes[image]
                if image_digest is None:
                    # Without a screenshot, preserve distinct observed native states.
                    native_state = sorted(
                        (n["name"], n["class_name"], n["visible"], n["enabled"], n["rect"])
                        for n in descendants
                    )
                    image_digest = (
                        "native-" + hashlib.sha256(json.dumps(native_state).encode()).hexdigest()
                    )
                key = f"{sid}:{window['name']}:{window['class_name']}:{image_digest}"
                occurrence = {
                    "evidence": str(path),
                    "observed_unix_ms": observed,
                    "hwnd": window["hwnd"],
                }
                previous = windows.get(key)
                occurrences = previous["occurrences"] + [occurrence] if previous else [occurrence]
                if previous and previous["observed_unix_ms"] > observed:
                    previous["occurrences"] = occurrences
                    previous["collection_count"] = len(occurrences)
                    continue
                windows[key] = {
                    "key": key,
                    "session_id": sid,
                    "root": window,
                    "observed_unix_ms": observed,
                    "image": image,
                    "image_file_uri": image_path.as_uri() if image else None,
                    "nodes": descendants,
                    "evidence": str(path),
                    "image_digest": image_digest,
                    "collection_count": len(occurrences),
                    "occurrences": occurrences,
                }
        except (OSError, ValueError, KeyError, TypeError) as error:
            failures.append({"file": str(path), "error": type(error).__name__})
    if not observations:
        raise FileNotFoundError("No readable UI observations found")
    try:
        bdd = bdd_registry("hpe990")
        bdd_error = None
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        bdd = {"scenarios": [], "expected_tests": 0}
        bdd_error = str(error)
    return {
        "schema_version": 1,
        "revision": hashlib.sha256(
            json.dumps([sorted(fingerprints), bdd, bdd_error]).encode()
        ).hexdigest(),
        "bdd": bdd,
        "bdd_error": bdd_error,
        "summary": {
            "sessions": len(sessions),
            "observations": observations,
            "windows": len(windows),
            "native_controls": len(controls),
            "duplicate_screens": sum(w["collection_count"] - 1 for w in windows.values()),
        },
        "windows": sorted(windows.values(), key=lambda w: (w["root"]["name"], w["session_id"])),
        "all_controls": list(controls.values()),
        "whole_application_complete": False,
        "read_errors": failures,
        "limits": [
            "관찰한 화면만 표시합니다. 미탐색 경로를 포함한 전체 UI 수집은 미완료입니다.",
            "Qt 내부에서 그린 항목은 native HWND가 없을 수 있습니다. 이미지를 함께 확인하세요.",
            "탐색 횟수는 마지막 catalog 집계 기준이며, 클릭 성공이 기능 검증 완료를 뜻하지 않습니다.",
        ],
    }


def bdd_viewer_data() -> dict:
    """Read the validated registry without requiring collected UI or a running Emulator."""
    try:
        catalog, error = bdd_registry("hpe990"), None
    except Exception as failure:
        # Registration/parser errors must be visible, never rendered as a passing catalog.
        catalog, error = {"scenarios": [], "expected_tests": 0}, str(failure)
    return {
        "bdd": catalog,
        "bdd_error": error,
        "revision": hashlib.sha256(json.dumps([catalog, error]).encode()).hexdigest(),
        "summary": {"scenarios": catalog["expected_tests"]},
    }


HTML = r"""<!doctype html>
<html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HPE990 · BDD 시나리오</title>
<style>
:root{font-family:Segoe UI,Malgun Gothic,sans-serif;color:#183047;background:#f3f6fa}*{box-sizing:border-box}body{margin:0}header{background:#152b43;color:white;padding:26px 32px}h1{margin:0 0 8px;font-size:25px}header p{margin:0;color:#c1d4e8;font-size:13px}main{max-width:1500px;margin:auto;padding:24px}.toolbar{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:18px}input,button{font:inherit;padding:10px;border:1px solid #c8d5e3;border-radius:7px;background:white}input[type=search]{flex:1;min-width:220px}button{cursor:pointer;color:#1d5c99}label,#status,#count{font-size:13px;color:#516d87}.layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(320px,.8fr);gap:20px}.panel{background:white;border:1px solid #dce5ee;border-radius:12px;padding:18px;min-width:0}h2{font-size:18px;margin:0 0 14px}.table-wrap{overflow:auto;max-height:72vh}table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:12px;border-bottom:1px solid #e4ebf2;vertical-align:top;overflow-wrap:anywhere}th{background:#edf3fa}td button{text-align:left;border:0;padding:0;font-weight:600}tr.selected{background:#e8f2ff}small{display:block;margin-top:6px;color:#658099}pre{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.8;font-size:13px;background:#f4f7fb;padding:16px;border-radius:8px}.meta{font-size:12px;overflow-wrap:anywhere;color:#567089}#error{color:#a63325;margin-bottom:15px}#empty{color:#658099}footer{font-size:12px;color:#61768b;margin-top:18px}@media(max-width:900px){.layout{grid-template-columns:1fr}main{padding:14px}}
</style>
<header><h1>BDD 시나리오</h1><p>HPE990 · 등록 시나리오 목록과 Given / When / Then 상세</p></header>
<main><div class="toolbar"><input id="search" type="search" aria-label="시나리오 검색" placeholder="시나리오 이름·이슈·단계 검색"><label><input id="auto" type="checkbox" checked> 3초 자동 갱신</label><button id="refresh">새로고침</button><span id="status" role="status"></span></div><div id="error" role="alert"></div><div class="layout"><section class="panel"><h2>BDD 시나리오 목록 <span id="count"></span></h2><div class="table-wrap"><table><thead><tr><th>시나리오</th><th>이슈 / 검증 기준</th><th>단계</th></tr></thead><tbody id="list"></tbody></table></div><p id="empty" hidden>검색 결과가 없습니다.</p></section><section class="panel" id="detail" aria-live="polite"></section></div><footer>등록 여부는 테스트 실행 결과를 의미하지 않습니다. 시나리오와 바인딩 등록이 검증되면 목록에 반영됩니다.</footer></main>
<script>
'use strict';
let data=__INITIAL_DATA__,selected=null,busy=false;
const base=__API_BASE__, $=id=>document.getElementById(id);
function el(tag,text){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n}
function key(s){return s.feature+':'+s.name}
function render(){
 const q=$('search').value.trim().toLowerCase(),items=data.bdd.scenarios.filter(s=>!q||[s.name,s.feature,s.test,...s.tags,...s.steps].join(' ').toLowerCase().includes(q));
 if(!items.some(s=>key(s)===selected))selected=items.length?key(items[0]):null;
 $('count').textContent=`· ${items.length} / ${data.bdd.expected_tests}개`;$('error').textContent=data.bdd_error?'등록 검증 실패: '+data.bdd_error:'';$('empty').hidden=items.length>0;
 $('list').replaceChildren();items.forEach(s=>{const row=el('tr'),cell=el('td'),button=el('button',s.name);row.classList.toggle('selected',key(s)===selected);button.onclick=()=>{selected=key(s);render()};cell.append(button,el('small',s.feature));row.append(cell,el('td',s.tags.join(' ')),el('td',s.steps.length+'개'));$('list').append(row)});
 $('detail').replaceChildren();const s=items.find(s=>key(s)===selected);if(!s){$('detail').append(el('h2','시나리오 상세'),el('p','조회할 시나리오가 없습니다.'));return}
 const meta=el('p',s.tags.join(' ')),binding=el('p',s.binding+' · '+s.test);meta.className=binding.className='meta';$('detail').append(el('h2',s.name),meta,binding,el('pre',s.gherkin));
}
async function refresh(){if(busy)return;busy=true;try{const r=await fetch(base+'data',{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const next=await r.json();if(next.revision!==data.revision){data=next;render()}$('status').textContent='갱신 '+new Date().toLocaleTimeString()}catch(e){$('status').textContent='갱신 실패: '+e.message}finally{busy=false}}
$('search').oninput=render;$('refresh').onclick=refresh;render();if(location.protocol==='file:'){$('auto').checked=false;$('auto').disabled=true;$('refresh').disabled=true;$('status').textContent='저장된 목록 · 자동 갱신은 MCP 반환 URL에서 제공'}else{setInterval(()=>{if($('auto').checked)refresh()},3000);refresh()}
</script></html>"""


def render_html(data: dict, base: str) -> str:
    def safe_json(value):
        return (
            json.dumps(value, ensure_ascii=False)
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026")
        )

    return HTML.replace("__INITIAL_DATA__", safe_json(data)).replace(
        "__API_BASE__", safe_json(base)
    )


def serve_viewer(token: str, session_id: str | None, response: Path) -> None:
    data = bdd_viewer_data()
    directory = hpe990_folders.D_HPE990_EVIDENCE / "ui-viewer" / token
    directory.mkdir(parents=True)
    stop = directory / "stop.request"
    cache = {"data": data, "time": time.monotonic()}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            parsed = urlsplit(self.path)
            if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
                self.send_error(403)
                return
            prefix = f"/{token}/"
            if not parsed.path.startswith(prefix):
                self.send_error(404)
                return
            route = parsed.path[len(prefix) :]
            try:
                if route == "data":
                    if time.monotonic() - cache["time"] >= 1:
                        cache["data"] = bdd_viewer_data()
                        cache["time"] = time.monotonic()
                    body = json.dumps(cache["data"], ensure_ascii=False).encode("utf-8")
                    content_type = "application/json; charset=utf-8"
                elif route == "":
                    body = html.read_bytes()
                    content_type = "text/html; charset=utf-8"
                else:
                    self.send_error(404)
                    return
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (OSError, ValueError, KeyError, IndexError):
                self.send_error(404)

    with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
        server.timeout = 0.5
        server.daemon_threads = True
        url = f"http://127.0.0.1:{server.server_port}/{token}/"
        html = hpe990_folders.D_HPE990_EVIDENCE / "inspection" / "ui-gallery.html"
        html.parent.mkdir(parents=True, exist_ok=True)
        html.write_text(render_html(data, url), encoding="utf-8")
        result = {
            "screen_kind": "bdd-scenarios",
            "url": url,
            "html": str(html),
            "session_id": session_id,
            "pid": os.getpid(),
            "create_time": psutil.Process().create_time(),
            "stop_file": str(stop),
            "summary": data["summary"],
            "refresh_seconds": 3,
        }
        temporary = response.with_suffix(".pending")
        temporary.write_text(json.dumps(result), encoding="utf-8")
        temporary.replace(response)
        while not stop.exists():
            server.handle_request()


def visualize_ui(session_id: str | None = None, open_browser: bool = True) -> dict:
    from cores.hpe990.functions.backend import request_backend

    bdd_viewer_data()  # The scenario screen is independent of collected UI sessions.
    runtime = hpe990_folders.D_HPE990_RUNTIME
    runtime.mkdir(parents=True, exist_ok=True)
    manifest = runtime / "ui-viewer.json"
    with FileLock(str(runtime / "ui-viewer.lock")):
        old = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else None
        if (
            old
            and _viewer_alive(old)
            and old["session_id"] == session_id
            and old.get("screen_kind") == "bdd-scenarios"
        ):
            result = old
        else:
            if old and _viewer_alive(old):
                _stop_viewer(old)
            result = request_backend("ui_viewer", {"session_id": session_id})
            manifest.write_text(json.dumps(result), encoding="utf-8")
    if open_browser:
        webbrowser.open(result["url"])
    return {**result, "opened": open_browser, "whole_application_complete": False}


def _viewer_alive(record: dict) -> bool:
    try:
        return psutil.Process(record["pid"]).create_time() == record["create_time"]
    except psutil.Error:
        return False


def _stop_viewer(record: dict) -> None:
    path = Path(record["stop_file"]).resolve()
    path.relative_to((hpe990_folders.D_HPE990_EVIDENCE / "ui-viewer").resolve())
    path.write_text("stop", encoding="utf-8")
    deadline = time.monotonic() + 10
    while _viewer_alive(record) and time.monotonic() < deadline:
        time.sleep(0.1)
    if _viewer_alive(record):
        raise TimeoutError("UI viewer has not stopped")


def stop_ui_viewer() -> dict:
    manifest = hpe990_folders.D_HPE990_RUNTIME / "ui-viewer.json"
    with FileLock(str(manifest.with_suffix(".lock"))):
        record = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else None
        if record and _viewer_alive(record):
            _stop_viewer(record)
        manifest.unlink(missing_ok=True)
    return {"stopped": True}
