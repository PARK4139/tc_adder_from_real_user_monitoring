"""Persistent, bounded image/text/value observation beside the Rust WinEvent RAM stream."""

import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

from filelock import FileLock

from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.functions.backend import request_backend
from cores.hpe990.functions.monitoring import _worker_alive, session_guard, start_ram

SCOPE = (
    "Zero RGB threshold on successfully captured visible top-level windows. "
    "Native text and readable accessibility values are compared; OCR is unverified evidence. "
    "Sampling can miss transient changes, occluded/minimized content and unreadable values. "
    "Separate sequenced local stream; no remote transmission."
)


def _write(path: Path, data: dict) -> None:
    pending = path.with_suffix(".pending")
    pending.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    deadline = time.monotonic() + 1
    while True:
        try:
            pending.replace(path)
            break
        except PermissionError:
            # Windows readers can briefly prevent atomic replacement. Preserve the
            # previous complete JSON while waiting; do not suppress permanent errors.
            if time.monotonic() >= deadline:
                raise
            time.sleep(0.01)


def _manifest(session_id: str) -> Path:
    session_guard(session_id, False)
    return hpe990_folders.D_HPE990_SEMANTIC_RAM / session_id / "manifest.json"


def semantic_status(session_id: str) -> dict:
    path = _manifest(session_id)
    if not path.exists():
        result = {"session_id": session_id, "active": False, "scope": SCOPE}
        return {**result, **observation_health(result)}
    result = json.loads(path.read_text(encoding="utf-8"))
    result["active"] = _worker_alive(result["worker"])
    status = Path(result["directory"]) / "status.json"
    if status.exists():
        result["observation"] = json.loads(status.read_text(encoding="utf-8"))
    result.update(observation_health(result))
    return result


def observation_health(status: dict, now_ms: int | None = None) -> dict:
    """Worker ownership is distinct from fresh, successful sampling."""
    now_ms = time.time_ns() // 1000000 if now_ms is None else now_ms
    sample = status.get("observation", {})
    timestamp = sample.get("observed_unix_ms")
    age = max(0, now_ms - timestamp) if timestamp is not None else None
    threshold = max(10000, 4 * status.get("interval_ms", 250))
    if not status.get("active"):
        state = "stopped"
    elif timestamp is None:
        state = "starting"
    elif sample.get("error"):
        state = "error"
    elif age > threshold:
        state = "stale"
    else:
        state = "observing"
    return {
        "sampling_healthy": state == "observing",
        "observation_health": {
            "state": state,
            "observed_age_ms": age,
            "stale_after_ms": threshold,
            "scope": "Last observation freshness; not full temporal/UI coverage.",
        },
    }


def semantic_start(
    session_id: str, interval_ms: int = 250, accessibility_backend: str = "msaa"
) -> dict:
    if isinstance(interval_ms, bool) or not 100 <= interval_ms <= 10000:
        raise ValueError("interval_ms must be 100..10000")
    if accessibility_backend not in ("msaa", "uia", "none"):
        raise ValueError("accessibility_backend must be msaa, uia or none")
    session = session_guard(session_id)
    if len(session["processes"]) != 1:
        raise ValueError("Semantic RAM requires one target process")
    if not hpe990_folders.F_HPE990_VISUAL.is_file():
        raise FileNotFoundError("Build the Rust visual worker first")
    path = _manifest(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(path) + ".lock", timeout=30):
        existing = semantic_status(session_id)
        if existing["active"]:
            from cores.hpe990.functions.activity_log import ensure_activity_log

            existing["activity_log"] = ensure_activity_log(session_id)
            return existing
        ram = start_ram(session_id)
        directory = path.parent / uuid.uuid4().hex
        directory.mkdir()
        config = {
            "session_id": session_id,
            "directory": str(directory),
            "interval_ms": interval_ms,
            "accessibility_backend": accessibility_backend,
            "target": session["processes"][0],
            "native_ram_directory": ram["directory"],
            "scope": SCOPE,
        }
        _write(directory / "config.json", config)
        worker = request_backend("semantic_ram", {**session["processes"][0], **config})
        _write(path, {**config, "worker": worker})
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            result = semantic_status(session_id)
            if result.get("observation"):
                return result
            if not result["active"]:
                raise RuntimeError(f"Worker exited: {directory / 'worker-stderr.log'}")
            time.sleep(0.1)
        raise TimeoutError("First semantic observation missing; inspect semantic_status")


def semantic_stop(session_id: str) -> dict:
    result = semantic_status(session_id)
    if result["active"]:
        (Path(result["directory"]) / "stop.request").touch()
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            result = semantic_status(session_id)
            if not result["active"]:
                return result
            time.sleep(0.1)
        raise TimeoutError("Semantic observer stop pending")
    return result


def semantic_read(session_id: str, after_sequence: int = 0, limit: int = 200) -> dict:
    if after_sequence < 0 or not 1 <= limit <= 10000:
        raise ValueError("Invalid cursor or limit")
    result = semantic_status(session_id)
    if "directory" not in result:
        raise ValueError("Start semantic RAM first")
    source = Path(result["directory"]) / "events.jsonl"
    events = []
    if source.exists():
        with source.open(encoding="utf-8") as stream:
            for line in stream:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    break
                if record["sequence"] > after_sequence:
                    events.append(record)
                    if len(events) == limit:
                        break
    return {
        "session_id": session_id,
        "run_id": Path(result["directory"]).name,
        "stream": "semantic_ram",
        "events": events,
        "active": result["active"],
        "next_sequence": events[-1]["sequence"] if events else after_sequence,
        "source": str(source),
        "sampling_healthy": result["sampling_healthy"],
        "observation_health": result["observation_health"],
    }


def semantic_changes(before: dict, after: dict) -> list[dict]:
    """Use HWND for native observations, UI IDs for linked values, geometry for OCR evidence."""
    changes = []
    old = {n["hwnd"]: n for n in before["nodes"]}
    for node in after["nodes"]:
        previous = old.get(node["hwnd"])
        if previous and previous["class_name"] == node["class_name"]:
            for field in ("name", "enabled", "visible", "rect"):
                if previous.get(field) != node.get(field):
                    changes.append(
                        {
                            "kind": "native_text_changed"
                            if field == "name"
                            else "native_state_changed",
                            "ui_id": node["ui_id"],
                            "before_ui_id": previous["ui_id"],
                            "hwnd": node["hwnd"],
                            "field": field,
                            "before": previous.get(field),
                            "after": node.get(field),
                            "source": "native_hwnd",
                            "semantic_state_verified": field != "name",
                        }
                    )
    for backend in ("accessibility", "visual"):
        if before[backend].get("errors") or after[backend].get("errors"):
            continue  # Do not fabricate changes across provider failure gaps.

        def key(element):
            if backend == "accessibility":
                return (element.get("root_hwnd"), element["ui_id"])
            if element.get("control_type") == "text":
                # Text width changes with its contents; match only its starting position.
                return (
                    element.get("root_hwnd"),
                    "text",
                    tuple(round(v / 4) for v in element.get("rect", [])[:2]),
                )
            return (
                element.get("root_hwnd"),
                element.get("control_type"),
                tuple(round(v / 4) for v in element.get("rect", [])),
            )

        previous = {}
        for element in before[backend]["elements"]:
            previous.setdefault(key(element), []).append(element)
        current_keys = {key(element) for element in after[backend]["elements"]}
        for element in after[backend]["elements"]:
            matches = previous.get(key(element), [])
            if not matches and backend == "visual":
                changes.append(
                    {
                        "kind": "ocr_element_observed",
                        "ui_id": element["ui_id"],
                        "source": "visual",
                        "after": element.get("observed_text", element.get("name")),
                        "rect": element.get("rect"),
                        "root_hwnd": element.get("root_hwnd"),
                        "semantic_state_verified": False,
                    }
                )
            if len(matches) != 1:
                continue
            for field in (
                ("name", "value") if backend == "accessibility" else ("name", "observed_text")
            ):
                a, b = matches[0].get(field), element.get(field)
                if a is not None and b is not None and a != b:
                    changes.append(
                        {
                            "kind": "value_changed"
                            if field == "value"
                            else "ocr_input_changed"
                            if field == "observed_text"
                            else "text_changed",
                            "ui_id": element["ui_id"],
                            "before_ui_id": matches[0]["ui_id"],
                            "field": field,
                            "before": a,
                            "after": b,
                            "source": backend,
                            "rect": element.get("rect"),
                            "root_hwnd": element.get("root_hwnd"),
                            "semantic_state_verified": backend == "accessibility",
                        }
                    )
        if backend == "visual":
            for element in before[backend]["elements"]:
                if key(element) not in current_keys:
                    changes.append(
                        {
                            "kind": "ocr_element_no_longer_observed",
                            "ui_id": element["ui_id"],
                            "source": "visual",
                            "before": element.get("observed_text", element.get("name")),
                            "rect": element.get("rect"),
                            "root_hwnd": element.get("root_hwnd"),
                            "semantic_state_verified": False,
                        }
                    )
    return changes


def _native_signature(record: dict) -> dict:
    fields = ("pid", "name", "class_name", "parent", "owner", "visible", "enabled", "rect")
    return {node["hwnd"]: [node.get(field) for field in fields] for node in record["nodes"]}


def affected_elements(record: dict, hwnd: int, regions: list[dict]) -> list[dict]:
    """Geometry overlap candidates, never a claim that every overlapping control changed."""
    by_handle = {node["hwnd"]: node for node in record["nodes"]}
    root = by_handle[hwnd]
    result = []
    for node in record["nodes"]:
        if not node["visible"] or node["hwnd"] == hwnd:
            continue
        current, seen = node, set()
        while current["hwnd"] not in seen and current["hwnd"] != hwnd:
            seen.add(current["hwnd"])
            current = by_handle.get(current["parent"])
            if current is None:
                break
        if current is None or current["hwnd"] != hwnd:
            continue
        rect = [
            node["rect"][0] - root["rect"][0],
            node["rect"][1] - root["rect"][1],
            node["rect"][2] - root["rect"][0],
            node["rect"][3] - root["rect"][1],
        ]
        if any(
            rect[0] < r["rect"][2]
            and rect[2] > r["rect"][0]
            and rect[1] < r["rect"][3]
            and rect[3] > r["rect"][1]
            for r in regions
        ):
            result.append(
                {
                    "ui_id": node["ui_id"],
                    "hwnd": node["hwnd"],
                    "name": node["name"],
                    "rect": rect,
                    "association": "geometry_overlap_candidate",
                }
            )
    return result


def observe(directory: Path) -> None:
    from cores.hpe990.functions.accessibility import collect_accessibility
    from cores.hpe990.functions.ui import _capture, _native_tree

    config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
    session = session_guard(config["session_id"])
    if config["target"] not in session["processes"]:
        raise ValueError("Target identity changed")
    nodes = _native_tree(session)
    roots = [node for node in nodes if not node["parent"] and node["visible"]]
    captures, errors = [], []
    for root in roots:
        try:
            captures.append(_capture(root["hwnd"], directory / f"{root['hwnd']}.png"))
        except Exception as error:
            errors.append({"hwnd": root["hwnd"], "error": str(error)})
    record = {
        "session_id": config["session_id"],
        "nodes": nodes,
        "roots": roots,
        "screenshots": captures,
        "capture_errors": errors,
        "accessibility": {"elements": [], "errors": [], "backend": "not_due"},
        "visual": {"elements": [], "errors": []},
        "observed_unix_ms": time.time_ns() // 1000000,
    }
    if config.get("read_accessibility"):
        record["accessibility"] = collect_accessibility(
            roots, timeout_seconds=1, backend=config["accessibility_backend"]
        )
    _write(directory / "raw.json", record)


def run_worker(directory: Path) -> None:
    from cores.hpe990.functions.ui import _associate_visual_nodes
    from cores.hpe990.functions.ui_identity import assign_ui_ids
    from cores.hpe990.functions.visual_elements import collect_visual_elements

    config = json.loads((directory / "config.json").read_text(encoding="utf-8"))
    sequence, cycles, max_gap_ms = 0, 0, 0
    baseline = None
    last_started = None
    accessibility_due = 0
    last_accessibility = None
    emit_time = time.time_ns() // 1000000

    def emit(kind, **details):
        nonlocal sequence
        sequence += 1
        record = {
            "schema_version": 1,
            "stream": "semantic_ram",
            "sequence": sequence,
            "session_id": config["session_id"],
            "run_id": directory.name,
            "observed_unix_ms": emit_time,
            "kind": kind,
            **details,
        }
        with (directory / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")

    emit("observer_started", scope=SCOPE, native_ram_directory=config["native_ram_directory"])
    while not (directory / "stop.request").exists():
        started = time.monotonic()
        gap_ms = 0 if last_started is None else (started - last_started) * 1000
        max_gap_ms = max(max_gap_ms, gap_ms)
        last_started = started
        cycles += 1
        current = directory / f"observation-{cycles:08d}"
        current.mkdir()
        due = started >= accessibility_due
        _write(current / "config.json", {**config, "read_accessibility": due})
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cores.hpe990.functions.semantic_ram",
                    "--observe",
                    str(current),
                ],
                check=True,
                timeout=8,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            record = json.loads((current / "raw.json").read_text(encoding="utf-8"))
            emit_time = record["observed_unix_ms"]
            pixel_changes = []
            previous_captures = {c["hwnd"]: c for c in baseline["screenshots"]} if baseline else {}
            changed_captures = []
            for capture in record["screenshots"]:
                previous = previous_captures.get(capture["hwnd"])
                if previous and previous["sha256"] == capture["sha256"]:
                    Path(capture["path"]).unlink()
                    capture.update(previous)
                    if baseline["visual"].get("errors"):
                        changed_captures.append(capture)
                else:
                    changed_captures.append(capture)
                    if previous:
                        result = subprocess.run(
                            [
                                str(hpe990_folders.F_HPE990_VISUAL),
                                "--diff",
                                previous["path"],
                                capture["path"],
                            ],
                            check=True,
                            capture_output=True,
                            timeout=5,
                            stdin=subprocess.DEVNULL,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                        )
                        diff = json.loads(result.stdout)
                        if diff["changed"]:
                            pixel_changes.append(
                                {
                                    "hwnd": capture["hwnd"],
                                    "before": previous,
                                    "after": capture,
                                    "diff": diff,
                                }
                            )
            visual = collect_visual_elements(
                changed_captures, record["roots"], include_disabled=True
            )
            _associate_visual_nodes(visual, record["nodes"], record["roots"])
            unchanged = {c["hwnd"] for c in record["screenshots"]} - {
                c["hwnd"] for c in changed_captures
            }
            if baseline:
                visual["elements"].extend(
                    e for e in baseline["visual"]["elements"] if e["root_hwnd"] in unchanged
                )
            record["visual"] = visual
            observation_errors = (
                record["capture_errors"]
                + visual.get("errors", [])
                + record["accessibility"].get("errors", [])
            )
            reuse = bool(
                baseline
                and not due
                and not changed_captures
                and not record["capture_errors"]
                and not visual.get("errors")
                and _native_signature(record) == _native_signature(baseline)
            )
            if reuse:
                record = baseline
            else:
                record["evidence"] = str(current / "snapshot.json")
                assign_ui_ids(record)
            if due:
                accessibility_due = time.monotonic() + 5
                if last_accessibility is not None:
                    before = {
                        **record,
                        "nodes": [],
                        "visual": {"elements": [], "errors": []},
                        "accessibility": last_accessibility,
                    }
                    after = {**before, "accessibility": record["accessibility"]}
                    for change in semantic_changes(before, after):
                        emit(
                            change.pop("kind"),
                            **change,
                            before_evidence=last_accessibility.get("evidence"),
                            after_evidence=record["evidence"],
                        )
                last_accessibility = {**record["accessibility"], "evidence": record["evidence"]}
            for change in pixel_changes:
                root = next(n for n in record["nodes"] if n["hwnd"] == change["hwnd"])
                emit(
                    "pixel_color_changed",
                    **change,
                    ui_id=root["ui_id"],
                    affected_elements=affected_elements(
                        record, change["hwnd"], change["diff"]["regions"]
                    ),
                    semantic_state_verified=False,
                )
            for capture in changed_captures:
                if capture["hwnd"] not in previous_captures:
                    emit("screen_observed", screenshot=capture)
            current_handles = {c["hwnd"] for c in record["screenshots"]}
            failed_handles = {e["hwnd"] for e in record["capture_errors"]}
            for hwnd, capture in previous_captures.items():
                if hwnd not in current_handles and hwnd not in failed_handles:
                    emit("screen_no_longer_visible", screenshot=capture)
            if baseline:
                comparison = {**record, "accessibility": {"elements": [], "errors": []}}
                before = {**baseline, "accessibility": {"elements": [], "errors": []}}
                for change in semantic_changes(before, comparison):
                    emit(
                        change.pop("kind"),
                        **change,
                        before_evidence=baseline["evidence"],
                        after_evidence=record["evidence"],
                    )
            for error in observation_errors:
                emit("observation_gap", error=error, evidence=record["evidence"])
            if not baseline:
                emit("baseline", evidence=record["evidence"], roots=len(record["screenshots"]))
            if reuse:
                # This scratch directory contains only the two files created by this cycle.
                (current / "config.json").unlink()
                (current / "raw.json").unlink()
                current.rmdir()
            else:
                _write(current / "snapshot.json", record)
            baseline = record
            error = None
        except Exception as failure:
            error = f"{type(failure).__name__}: {failure}"
            emit_time = time.time_ns() // 1000000
            emit("observation_gap", error=error, evidence=str(current))
            baseline = None  # Never compare across failed samples as an uninterrupted observation.
            last_accessibility = None
        elapsed_ms = (time.monotonic() - started) * 1000
        _write(
            directory / "status.json",
            {
                "cycles": cycles,
                "sequence": sequence,
                "observed_unix_ms": emit_time,
                "last_cycle_ms": elapsed_ms,
                "last_start_gap_ms": gap_ms,
                "max_start_gap_ms": max_gap_ms,
                "requested_interval_ms": config["interval_ms"],
                "error": error,
                "latest_evidence": baseline["evidence"] if baseline else None,
                "scope": SCOPE,
            },
        )
        if error:
            try:
                session_guard(config["session_id"])
            except ValueError:
                break
        deadline = started + config["interval_ms"] / 1000
        while time.monotonic() < deadline and not (directory / "stop.request").exists():
            time.sleep(min(0.05, max(0, deadline - time.monotonic())))
    emit_time = time.time_ns() // 1000000
    emit("observer_stopped", cycles=cycles)


if __name__ == "__main__":
    if sys.argv[1] == "--observe":
        observe(Path(sys.argv[2]))
    else:
        run_worker(Path(sys.argv[1]))
