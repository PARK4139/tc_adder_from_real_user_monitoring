"""Data-driven local viewer for saved UI evidence, including historical sessions."""

import hashlib
import json
import os
import re
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

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
                # A dashboard card represents a screen in a session, not every capture.
                # Keep the newest image and expose repeated captures as its count.
                key = f"{sid}:{window['name']}:{window['class_name']}"
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
        bdd = bdd_registry("auto_emulator")
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
        catalog, error = bdd_registry("auto_emulator"), None
    except Exception as failure:
        # Registration/parser errors must be visible, never rendered as a passing catalog.
        catalog, error = {"scenarios": [], "expected_tests": 0}, str(failure)
    return {
        "bdd": catalog,
        "bdd_error": error,
        "revision": hashlib.sha256(json.dumps([catalog, error]).encode()).hexdigest(),
        "summary": {"scenarios": catalog["expected_tests"]},
    }


def _tail_jsonl(path: Path, limit: int = 100) -> list[dict]:
    """Read only the newest complete JSONL records for a live dashboard."""
    if not path.is_file():
        return []
    with path.open("rb") as stream:
        stream.seek(0, os.SEEK_END)
        end = stream.tell()
        chunk_size = 64 * 1024
        data = b""
        position = end
        while position > 0 and data.count(b"\n") <= limit:
            size = min(chunk_size, position)
            position -= size
            stream.seek(position)
            data = stream.read(size) + data
    lines = data.splitlines()[-limit:]
    records = []
    for line in lines:
        try:
            records.append(json.loads(line))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
    return records


def _tail_text_lines(path: Path, limit: int = 100) -> list[str]:
    if not path.is_file():
        return []
    with path.open("rb") as stream:
        stream.seek(0, os.SEEK_END)
        position = stream.tell()
        data = b""
        while position > 0 and data.count(b"\n") <= limit:
            size = min(64 * 1024, position)
            position -= size
            stream.seek(position)
            data = stream.read(size) + data
    return data.decode("utf-8", errors="replace").splitlines()[-limit:]


def monitoring_viewer_data(session_id: str | None = None) -> dict:
    """Combine saved UI, BDD and current-session activity evidence for the dashboard."""
    from cores.hpe990.functions.lifecycle import _read_session

    session = _read_session()
    active_id = session_id or (session or {}).get("session_id")
    try:
        ui = viewer_data(active_id)
        # The archive may contain many historical screens; the live dashboard
        # needs only a small recent gallery and a bounded payload.
        ui["windows"] = sorted(
            ui["windows"], key=lambda w: w["observed_unix_ms"], reverse=True
        )[:12]
        for window in ui["windows"]:
            window["nodes"] = window["nodes"][:120]
            window.pop("occurrences", None)
        ui.pop("all_controls", None)
        ui.pop("read_errors", None)
        ui_error = None
    except (OSError, ValueError) as error:
        ui, ui_error = {"summary": {}, "windows": [], "read_errors": []}, str(error)
    bdd = bdd_viewer_data()
    ram, ram_events, semantic, semantic_events, activity = None, [], None, [], []
    ram_error = semantic_error = activity_error = None
    if active_id:
        try:
            from cores.hpe990.functions.monitoring import ram_status

            ram = ram_status(active_id)
            if ram.get("directory"):
                ram_events = _tail_jsonl(Path(ram["directory"]) / "events.jsonl")
        except (OSError, ValueError, RuntimeError) as error:
            ram_error = str(error)
        try:
            from cores.hpe990.functions.semantic_ram import semantic_status

            semantic = semantic_status(active_id)
            if semantic.get("directory"):
                semantic_events = _tail_jsonl(
                    Path(semantic["directory"]) / "events.jsonl"
                )
        except (OSError, ValueError, RuntimeError) as error:
            semantic_error = str(error)
        try:
            from cores.hpe990.functions.activity_log import activity_status

            activity_status_data = activity_status(active_id)
            log_path = Path(activity_status_data["log"])
            if log_path.is_file():
                for line in _tail_text_lines(log_path, 100):
                    try:
                        activity.append(json.loads(line.split(" INFO ", 1)[1]))
                    except (IndexError, json.JSONDecodeError):
                        continue
            activity = {"status": activity_status_data, "events": activity}
        except (OSError, ValueError, KeyError) as error:
            activity_error = str(error)
    return {
        "session_id": active_id,
        "summary": {
            **ui.get("summary", {}),
            "native_events": len(ram_events),
            "semantic_events": len(semantic_events),
            "activity_events": len(activity.get("events", [])) if isinstance(activity, dict) else 0,
            "bdd_scenarios": bdd.get("summary", {}).get("scenarios", 0),
        },
        "ui": ui,
        "ui_error": ui_error,
        "bdd": bdd,
        "ram": ram,
        "ram_events": ram_events,
        "ram_error": ram_error,
        "semantic": semantic,
        "semantic_events": semantic_events,
        "semantic_error": semantic_error,
        "activity": activity,
        "activity_error": activity_error,
        "revision": hashlib.sha256(
            json.dumps(
                [ui.get("revision"), bdd.get("revision"), ram, len(ram_events), semantic, len(semantic_events), len(activity.get("events", [])) if isinstance(activity, dict) else 0],
                ensure_ascii=False,
                default=str,
            ).encode()
        ).hexdigest(),
    }


HTML = r"""<!doctype html>
<html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>auto_emulator · 도구 검증 BDD</title>
<style>
:root{color-scheme:light;font-family:Segoe UI,Malgun Gothic,sans-serif;color:#183047;background:#f3f6fa}*{box-sizing:border-box}body{margin:0}header{background:#152b43;color:white;padding:26px 32px}h1{margin:0 0 8px;font-size:25px}header p{margin:0;color:#c1d4e8;font-size:13px}main{max-width:1500px;margin:auto;padding:24px}.toolbar{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:18px}input,button{font:inherit;padding:10px;border:1px solid #c8d5e3;border-radius:7px;background:white}input[type=search]{flex:1;min-width:220px}button{cursor:pointer;color:#1d5c99}label,#status,#count{font-size:13px;color:#516d87}.layout{display:grid;grid-template-columns:minmax(0,1fr) minmax(320px,.8fr);gap:20px}.panel{background:white;border:1px solid #dce5ee;border-radius:12px;padding:18px;min-width:0}h2{font-size:18px;margin:0 0 14px}.table-wrap{overflow:auto;max-height:72vh}table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:12px;border-bottom:1px solid #e4ebf2;vertical-align:top;overflow-wrap:anywhere}th{background:#edf3fa}td button{text-align:left;border:0;padding:0;font-weight:600}tr.selected{background:#e8f2ff}small{display:block;margin-top:6px;color:#658099}pre{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.8;font-size:13px;background:#f4f7fb;padding:16px;border-radius:8px}.meta{font-size:12px;overflow-wrap:anywhere;color:#567089}#error{color:#a63325;margin-bottom:15px}#empty{color:#658099}footer{font-size:12px;color:#61768b;margin-top:18px}body.dark{color-scheme:dark;color:#e3edf7;background:#111923}body.dark header{background:#090f17}body.dark input,body.dark button{background:#202c3a;color:#e3edf7;border-color:#40536a}body.dark label,body.dark #status,body.dark #count,body.dark small,body.dark .meta,body.dark footer{color:#a9bfd6}body.dark .panel{background:#192431;border-color:#344457}body.dark th{background:#263547}body.dark th,body.dark td{border-color:#344457}body.dark tr.selected{background:#253b55}body.dark pre{background:#202c3a}body.dark #empty{color:#a9bfd6}@media(max-width:900px){.layout{grid-template-columns:1fr}main{padding:14px}}
</style>
<header><h1>BDD 시나리오</h1><p>auto_emulator 도구 검증 · 실행 대상 HPE990 · Given / When / Then 상세</p></header>
<main><div class="toolbar"><input id="search" type="search" aria-label="시나리오 검색" placeholder="시나리오 이름·이슈·단계 검색"><button id="theme-toggle" type="button" aria-pressed="false">Dark mode</button><label><input id="auto" type="checkbox" checked> 3초 자동 갱신</label><button id="refresh">새로고침</button><span id="status" role="status"></span></div><div id="error" role="alert"></div><div class="layout"><section class="panel"><h2>BDD 시나리오 목록 <span id="count"></span></h2><div class="table-wrap"><table><thead><tr><th>시나리오</th><th>이슈 / 검증 기준</th><th>단계</th></tr></thead><tbody id="list"></tbody></table></div><p id="empty" hidden>검색 결과가 없습니다.</p></section><section class="panel" id="detail" aria-live="polite"></section></div><footer>등록 여부는 테스트 실행 결과를 의미하지 않습니다. 시나리오와 바인딩 등록이 검증되면 목록에 반영됩니다.</footer></main>
<script>
'use strict';
let data=__INITIAL_DATA__,selected=null,busy=false;
const base=__API_BASE__, $=id=>document.getElementById(id);
const themeKey='auto-emulator-dark-mode';
function setTheme(dark){document.body.classList.toggle('dark',dark);$('theme-toggle').setAttribute('aria-pressed',String(dark));$('theme-toggle').textContent=dark?'Light mode':'Dark mode';try{localStorage.setItem(themeKey,dark?'dark':'light')}catch{}}
let savedTheme=null;try{savedTheme=localStorage.getItem(themeKey)}catch{}setTheme(savedTheme==='dark');$('theme-toggle').onclick=()=>setTheme(!document.body.classList.contains('dark'));
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

    return DASHBOARD_HTML.replace("__INITIAL_DATA__", safe_json(data)).replace(
        "__API_BASE__", safe_json(base)
    )


DASHBOARD_HTML = r'''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>auto_emulator 사용자 활동 모니터링</title><style>
:root{font-family:Segoe UI,Malgun Gothic,sans-serif;color:#183047;background:#f2f5f9;color-scheme:light}*{box-sizing:border-box}body{margin:0}header{background:#132b43;color:#fff;padding:22px 28px}h1{font-size:23px;margin:0 0 6px}header p{margin:0;color:#bdd0e2;font-size:13px}main{max-width:1600px;margin:auto;padding:20px}.toolbar,.tabs{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin-bottom:14px}button,input{font:inherit;border:1px solid #cbd7e3;border-radius:7px;background:#fff;color:#26445f;padding:9px 12px}button{cursor:pointer}button.active{background:#1b5d91;color:white;border-color:#1b5d91}.tabs button{font-weight:600}.toolbar .spacer{flex:1}#status{font-size:13px;color:#55738e}.pane{display:none}.pane.active{display:block}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}.card,.panel{background:#fff;border:1px solid #dbe4ed;border-radius:11px;padding:15px;min-width:0}.card strong{font-size:23px;display:block;margin-top:5px}.muted,small{color:#688098;font-size:12px}.panel{margin-bottom:13px}h2{font-size:18px;margin:0 0 12px}h3{font-size:15px;margin:0 0 8px}.gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:12px}.gallery img{width:100%;height:auto;border:1px solid #d8e1e9;border-radius:7px}.scroll{max-height:68vh;overflow:auto}table{border-collapse:collapse;width:100%;font-size:13px}td,th{text-align:left;padding:9px;border-bottom:1px solid #e4ebf1;vertical-align:top;overflow-wrap:anywhere}th{position:sticky;top:0;background:#edf3f8}.event{border-left:3px solid #3980b8;padding:8px 12px;margin:8px 0;background:#f7f9fb;border-radius:3px}.event time{font-size:12px;color:#637d95}.event strong{margin:0 8px}.empty{padding:24px;text-align:center;color:#688098}.error{color:#a63c32}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f7fa;padding:12px;border-radius:7px;font-size:12px}body.dark{color-scheme:dark;color:#e4edf6;background:#111923}body.dark header{background:#090f17}body.dark button,body.dark input{background:#202c3a;color:#e4edf6;border-color:#40536a}body.dark .card,body.dark .panel{background:#192431;border-color:#344457}body.dark td,body.dark th{border-color:#344457}body.dark th{background:#263547}body.dark .event{background:#202c3a}body.dark pre{background:#202c3a}body.dark .muted,body.dark small,body.dark #status{color:#a9bfd6}@media(max-width:720px){main{padding:12px}header{padding:18px}.gallery{grid-template-columns:1fr}}
</style>
<style>
/* Match the TC review's pale blue inspection surface and quiet information hierarchy. */
:root{font-family:'Segoe UI','Malgun Gothic',sans-serif;color:#20334a;background:#f3f6fa;color-scheme:light}
body{line-height:1.65}header{background:#eaf1f8;color:#20334a;padding:26px 32px;border-bottom:1px solid #cbd9e7}
h1{font-size:24px;line-height:1.35;letter-spacing:-.02em}header p{color:#526a82;font-size:14px;line-height:1.65}
main{max-width:1600px;padding:0 30px 32px}.toolbar{position:sticky;top:0;z-index:3;background:#f3f6fa;padding:12px 0;margin:0;gap:12px}
button,input,select{font-family:inherit;font-size:14px;min-height:40px;border-color:#c5d3e2;border-radius:7px;color:#31516e}
button{font-weight:600}button:hover{background:#f0f5fa}button:focus-visible,input:focus-visible,select:focus-visible,summary:focus-visible{outline:2px solid #3074bd;outline-offset:2px}
#status,.muted,small{color:#66788a}.tabs{position:sticky;top:64px;z-index:2;background:#f3f6fa;border-bottom:1px solid #ccd9e6;padding:0;margin:0 0 18px;gap:4px}
.tabs button{border:0;border-bottom:3px solid transparent;border-radius:0;background:transparent;padding:11px 15px;color:#315b82;font-size:14px}
.tabs button:hover{background:#edf3f8}.tabs button.active{background:#eaf3ff;border-bottom-color:#3074bd;color:#20334a}
.pane.active{padding-top:2px}.panel,.card{background:#fff;border:1px solid #dae4ee;border-radius:10px;box-shadow:none}
.panel{padding:22px;margin-bottom:18px}.grid{gap:0}.grid#summary{grid-template-columns:repeat(4,minmax(0,1fr));background:#fff;border:1px solid #dae4ee;border-radius:10px;margin-bottom:18px;overflow:hidden}
.grid#summary .card{border:0;border-right:1px solid #dae4ee;border-radius:0;padding:14px 18px}.grid#summary .card:last-child{border-right:0}
.card strong{font-size:23px;line-height:1.35;color:#20334a}.card .muted,small{font-size:13px;line-height:1.6}.panel h2{font-size:18px;line-height:1.5;padding-bottom:10px;border-bottom:1px solid #dae4ee}
.panel h3{font-size:16px;line-height:1.5}.toolbar label{font-size:14px;color:#526a82}.toolbar input[type=search]{flex:1;min-width:240px}
.toolbar:has(#stream){position:static;padding:0 0 12px;margin:0;align-items:center}.toolbar:has(#stream) select{min-width:190px}
.scroll{max-height:68vh;overflow:auto}.event{display:grid;grid-template-columns:minmax(160px,190px) 140px minmax(180px,1fr) 110px;align-items:center;gap:14px;padding:10px 12px;margin:0;background:#fff;border:0;border-bottom:1px solid #e1e9f2;border-radius:0;border-left:3px solid transparent;font-size:14px;line-height:1.55}
.event:hover{background:#f7faff;border-left-color:#8fb3d8}.event time{font-size:13px;color:#526a82;font-variant-numeric:tabular-nums}.event strong{font-size:13px;font-weight:600;color:#315b82;margin:0}.event-info b{display:block;font-size:14px;font-weight:600}.event .muted{font-size:13px;overflow-wrap:anywhere}.event details{font-size:13px}.event details summary{cursor:pointer;color:#315b82}
.event pre,pre{font-family:Consolas,'Malgun Gothic',monospace;font-size:13px;line-height:1.7;white-space:pre-wrap;overflow-wrap:anywhere;background:#f7faff;border:1px solid #dae4ee;border-radius:6px;padding:14px;margin:10px 0}
.gallery{grid-template-columns:repeat(auto-fill,minmax(min(100%,390px),1fr));gap:14px}.gallery .card{padding:18px}.gallery img{border-color:#ccd9e6;border-radius:6px;margin:10px 0}.gallery details summary{cursor:pointer;color:#315b82;font-size:14px}
table{font-size:14px;line-height:1.65}td,th{padding:12px 14px;text-align:left;border-bottom:1px solid #dae4ee;vertical-align:top;overflow-wrap:anywhere}th{position:sticky;top:0;background:#eaf1f8;color:#31516e;font-weight:600}tr:hover td{background:#f7faff}
#bdd-search{margin:0 0 12px;min-width:min(100%,320px)}#bdd-list button{border:0;background:transparent;padding:2px 0;text-align:left;color:#315b82;font-size:14px}#bdd-list small{display:block;margin-top:3px}
.empty{padding:24px;text-align:center;color:#66788a;font-size:14px}.error{color:#a12626}
body.dark{color-scheme:dark;color:#e3edf7;background:#111923}body.dark header{background:#090f17;color:#e3edf7;border-color:#ffffff33}body.dark header p{color:#a9bfd6}
body.dark .toolbar,body.dark .tabs{background:#111923}body.dark button,body.dark input,body.dark select{background:#202c3a;color:#e3edf7;border-color:#40536a}body.dark .tabs button{background:transparent;color:#bdd4ec}body.dark .tabs button.active{background:#253b55;border-bottom-color:#7cb2e8}
body.dark .panel,body.dark .card,body.dark .grid#summary{background:#192431;border-color:#344457}body.dark .grid#summary .card{border-color:#344457}body.dark .card strong{color:#e3edf7}body.dark .muted,body.dark small,body.dark #status,body.dark .event time{color:#a9bfd6}
body.dark .panel h2{border-color:#344457}body.dark .event{background:#192431;border-color:#344457;border-left-color:transparent}body.dark .event:hover{background:#202c3a;border-left-color:#7cb2e8}body.dark .event strong,body.dark .event details summary,body.dark .gallery details summary{color:#bdd4ec}
body.dark td,body.dark th{border-color:#40536a}body.dark th{background:#263547;color:#d0dfef}body.dark tr:hover td{background:#202c3a}body.dark pre,body.dark .event pre{background:#202c3a;border-color:#40536a}body.dark .empty{color:#a9bfd6}
@media(max-width:900px){header{padding:20px 16px}main{padding:0 14px 22px}.toolbar{flex-wrap:wrap}.tabs{top:62px;overflow-x:auto;flex-wrap:nowrap}.tabs button{white-space:nowrap;padding:10px}.grid#summary{grid-template-columns:repeat(2,minmax(0,1fr))}.grid#summary .card:nth-child(2){border-right:0}.grid#summary .card:nth-child(-n+2){border-bottom:1px solid #dae4ee}.event{grid-template-columns:minmax(0,1fr) auto;gap:4px 12px}.event time{grid-column:1}.event strong{grid-column:2;grid-row:1}.event .muted{grid-column:1}.event details{grid-column:2;grid-row:2}}
@media(max-width:520px){.toolbar:has(#stream){align-items:stretch}.toolbar:has(#stream) select,.toolbar:has(#stream) input{width:100%;min-width:0}.panel{padding:15px}.grid#summary .card{padding:12px}.grid#summary .card strong{font-size:20px}.event{padding:10px 8px}.gallery{grid-template-columns:1fr}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;animation-duration:.01ms!important;transition-duration:.01ms!important}}
</style><header><h1>사용자 활동 모니터링</h1><p>화면 수집, Native·Semantic 활동 이벤트와 BDD를 한 화면에서 확인합니다.</p></header>
<main><div class="toolbar"><span id="session" class="muted"></span><span class="spacer"></span><label><input id="auto" type="checkbox" checked> 3초마다 갱신</label><button id="refresh">새로고침</button><button id="theme">다크 모드</button><span id="status" role="status"></span></div>
<nav class="tabs" role="tablist" aria-label="시각화 기능"><button id="tab-activity" role="tab" aria-selected="true" aria-controls="activity" data-tab="activity" class="active">활동 타임라인</button><button id="tab-screens" role="tab" aria-selected="false" aria-controls="screens" data-tab="screens">화면 갤러리</button><button id="tab-status" role="tab" aria-selected="false" aria-controls="statusTab" data-tab="statusTab">모니터링 상태</button><button id="tab-bdd" role="tab" aria-selected="false" aria-controls="bdd" data-tab="bdd">BDD 시나리오</button></nav>
<section id="activity" class="pane active" role="tabpanel" aria-labelledby="tab-activity"><div class="grid" id="summary"></div><div class="panel"><h2>통합 활동 이벤트 <span id="event-count" class="muted"></span></h2><div class="toolbar"><select id="stream" aria-label="이벤트 종류"><option value="all">전체 스트림</option><option value="native_ram">Native RAM</option><option value="semantic_ram">Semantic RAM</option><option value="activity_log">활동 기록</option></select><input id="filter" type="search" aria-label="이벤트 검색" placeholder="이벤트 검색"></div><div id="timeline" class="scroll"></div></div></section>
<section id="screens" class="pane" role="tabpanel" aria-labelledby="tab-screens"><div class="panel"><h2>수집 화면</h2><div id="gallery" class="gallery"></div></div></section>
<section id="statusTab" class="pane" role="tabpanel" aria-labelledby="tab-status"><div class="grid" id="health"></div><div class="panel"><h2>최근 관찰 스냅샷</h2><div id="snapshot"></div></div></section>
<section id="bdd" class="pane" role="tabpanel" aria-labelledby="tab-bdd"><div class="panel"><h2>BDD 시나리오 <span id="bdd-count" class="muted"></span></h2><input id="bdd-search" type="search" aria-label="BDD 시나리오 검색" placeholder="시나리오 검색"><div class="scroll"><table><thead><tr><th>시나리오</th><th>태그</th><th>단계</th></tr></thead><tbody id="bdd-list"></tbody></table></div><div id="bdd-detail"></div></div></section></main>
<script>'use strict';let data=__INITIAL_DATA__,busy=false;const base=__API_BASE__, $=id=>document.getElementById(id);const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
document.querySelectorAll('[data-tab]').forEach(b=>b.onclick=()=>{document.querySelectorAll('[data-tab]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-selected',String(x===b))});document.querySelectorAll('.pane').forEach(x=>x.classList.toggle('active',x.id===b.dataset.tab))});$('theme').onclick=()=>document.body.classList.toggle('dark');
function card(label,value,detail=''){return `<div class="card"><span class="muted">${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(detail)}</small></div>`}
function allEvents(){const out=[];for(const e of data.ram_events||[])out.push({...e,source:'native_ram'});for(const e of data.semantic_events||[])out.push({...e,source:'semantic_ram'});for(const r of data.activity?.events||[])out.push({...r.event,source:'activity_log',observed_at:r.observed_at,recorded_at:r.recorded_at});return out.sort((a,b)=>(b.observed_unix_ms||0)-(a.observed_unix_ms||0))}
function render(){
 $('session').textContent=data.session_id?`세션 ${data.session_id}`:'활성 세션 없음';
 const events=allEvents();
 $('summary').innerHTML=[card('관찰 화면',data.ui?.summary?.windows||0,`${data.ui?.summary?.observations||0}회 수집`),card('Native 이벤트',data.ram_events?.length||0,data.ram?.active?'모니터링 중':'중지'),card('Semantic 이벤트',data.semantic_events?.length||0,data.semantic?.observation_health?.state||'미실행'),card('활동 기록',data.activity?.events?.length||0,data.activity?.status?.active?'기록 중':'중지')].join('');
 const q=$('filter').value.toLowerCase(),src=$('stream').value;
 const filtered=events.filter(e=>(src==='all'||e.source===src)&&(!q||JSON.stringify(e).toLowerCase().includes(q)));
 $('event-count').textContent=`${filtered.length}개`;
 const sourceName={native_ram:'Native RAM',semantic_ram:'Semantic RAM',activity_log:'활동 기록'};
 $('timeline').innerHTML=filtered.length?filtered.map(e=>`<article class="event"><time>${esc(e.observed_at||new Date(e.observed_unix_ms||Date.now()).toLocaleString())}</time><strong>${esc(sourceName[e.source]||e.source)}</strong><div class="event-info"><b>${esc(e.kind||'이벤트')}</b><div class="muted">${esc(e.ui_id||e.window_name||e.run_id||'')} ${esc(e.name||e.title||'')}</div></div><details><summary>세부 정보</summary><pre>${esc(JSON.stringify(e,null,2))}</pre></details></article>`).join(''):'<div class="empty">표시할 이벤트가 없습니다. 모니터링을 시작하거나 필터를 바꿔주세요.</div>';
const windows=data.ui?.windows||[];$('gallery').innerHTML=windows.length?windows.map(w=>`<article class="card"><h3>${esc(w.root?.name||w.root?.class_name||'화면')}</h3><small>${esc(new Date(w.observed_unix_ms).toLocaleString())} · ${w.collection_count||1}회 수집 · ${w.nodes?.length||0}개 요소</small>${w.image?`<img loading="lazy" src="${esc(base+'image/'+encodeURIComponent(w.image))}" alt="수집 화면">`:''}<details><summary>요소 목록</summary><div class="scroll"><table><thead><tr><th>이름</th><th>유형</th><th>상태</th></tr></thead><tbody>${(w.nodes||[]).map(n=>`<tr><td>${esc(n.name)}</td><td>${esc(n.class_name)}</td><td>${n.visible?'표시':'숨김'} · ${n.enabled?'활성':'비활성'}</td></tr>`).join('')}</tbody></table></div></details></article>`).join(''):`<div class="empty">${esc(data.ui_error||'화면 수집 자료가 없습니다.')}</div>`;document.querySelectorAll('#gallery img').forEach(img=>img.addEventListener('error',()=>{img.alt='이미지를 불러오지 못했습니다';img.insertAdjacentText('afterend',' 이미지를 불러오지 못했습니다.')}));
const states=[['Real Activity Monitoring',data.ram],['Semantic Activity Monitoring',data.semantic],['Activity Log',data.activity?.status]];$('health').innerHTML=states.map(([n,s])=>card(n,s?.active?'활성':'중지',s?.observation_health?.state||s?.writer?.records&&`${s.writer.records} records`||s?.error||'현재 세션에서 상태를 확인할 수 없음')).join('');$('snapshot').innerHTML=`<pre>${esc(JSON.stringify({native:data.ram?.snapshot,semantic:data.semantic?.observation,ui_summary:data.ui?.summary,errors:[data.ram_error,data.semantic_error,data.activity_error].filter(Boolean)},null,2))}</pre>`;
const scenarios=data.bdd?.bdd?.scenarios||[],bq=$('bdd-search').value.toLowerCase(),bs=scenarios.filter(s=>!bq||JSON.stringify(s).toLowerCase().includes(bq));$('bdd-count').textContent=`${bs.length}/${data.bdd?.bdd?.expected_tests||0}`;$('bdd-list').innerHTML=bs.map((s,i)=>`<tr><td><button data-bdd="${i}">${esc(s.name)}</button><small>${esc(s.feature)}</small></td><td>${esc((s.tags||[]).join(' '))}</td><td>${s.steps?.length||0}</td></tr>`).join('');document.querySelectorAll('[data-bdd]').forEach(b=>b.onclick=()=>{$('bdd-detail').innerHTML=`<h3>${esc(bs[+b.dataset.bdd].name)}</h3><pre>${esc(bs[+b.dataset.bdd].gherkin)}</pre>`});if(data.bdd?.bdd_error)$('bdd-detail').innerHTML=`<p class="error">BDD 등록 오류: ${esc(data.bdd.bdd_error)}</p>`}
async function refresh(){if(busy)return;busy=true;try{const r=await fetch(base+'data',{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);data=await r.json();render();$('status').textContent='갱신 '+new Date().toLocaleTimeString()}catch(e){$('status').textContent='갱신 실패: '+e.message}finally{busy=false}}$('refresh').onclick=refresh;$('filter').oninput=render;$('stream').onchange=render;$('bdd-search').oninput=render;render();setInterval(()=>{if($('auto').checked)refresh()},3000);
</script></html>'''


def serve_viewer(token: str, session_id: str | None, response: Path) -> None:
    data = monitoring_viewer_data(session_id)
    directory = hpe990_folders.D_HPE990_EVIDENCE / "ui-viewer" / token
    directory.mkdir(parents=True)
    stop = directory / "stop.request"
    cache = {"data": data, "time": time.monotonic(), "refreshing": False}
    cache_lock = threading.Lock()

    def refresh_data():
        try:
            updated = monitoring_viewer_data(session_id)
        except Exception:
            with cache_lock:
                cache["refreshing"] = False
            return
        with cache_lock:
            cache.update(data=updated, time=time.monotonic(), refreshing=False)

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
                    with cache_lock:
                        if time.monotonic() - cache["time"] >= 5 and not cache["refreshing"]:
                            cache["refreshing"] = True
                            threading.Thread(target=refresh_data, daemon=True).start()
                        snapshot = cache["data"]
                    body = json.dumps(snapshot, ensure_ascii=False).encode("utf-8")
                    content_type = "application/json; charset=utf-8"
                elif route == "":
                    body = html.read_bytes()
                    content_type = "text/html; charset=utf-8"
                elif route.startswith("image/"):
                    relative = Path(unquote(route[len("image/") :]))
                    if relative.is_absolute() or relative.suffix.lower() != ".png":
                        self.send_error(404)
                        return
                    image_path = (hpe990_folders.D_HPE990_EVIDENCE / "ui" / relative).resolve()
                    image_path.relative_to((hpe990_folders.D_HPE990_EVIDENCE / "ui").resolve())
                    if not image_path.is_file():
                        self.send_error(404)
                        return
                    body = image_path.read_bytes()
                    content_type = "image/png"
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
            "screen_kind": "monitoring-dashboard",
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
            and old.get("screen_kind") == "monitoring-dashboard"
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
