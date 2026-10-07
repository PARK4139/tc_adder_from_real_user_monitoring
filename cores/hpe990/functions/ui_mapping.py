"""Version-scoped, explicitly confirmed semantic mappings in the UI identity SSOT."""

import hashlib
import json
import sqlite3
import time
from functools import lru_cache
from pathlib import Path

import win32api

from cores.hpe990.common.paths import hpe990_folders
from cores.hpe990.functions.monitoring import session_guard


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


@lru_cache(maxsize=16)
def _fingerprint(path, size, modified, created):
    executable = Path(path)
    digest = hashlib.sha256()
    with executable.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    stat = executable.stat()
    if (stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns) != (size, modified, created):
        raise ValueError("Executable changed while fingerprinting")
    versions = {}
    try:
        info = win32api.GetFileVersionInfo(path, "\\")
        for field in ("FileVersion", "ProductVersion"):
            ms, ls = info[field + "MS"], info[field + "LS"]
            versions[field] = ".".join(str(n) for n in (ms >> 16, ms & 65535, ls >> 16, ls & 65535))
    except win32api.error:
        versions = {"FileVersion": None, "ProductVersion": None}
    return {"model": "HPE990", "sha256": digest.hexdigest(), "executable": path, **versions}


def target_identity(session):
    paths = {str(Path(p["exe"]).resolve()) for p in session["processes"]}
    if len(paths) != 1:
        raise ValueError("Version mapping requires one executable identity")
    path = paths.pop()
    stat = Path(path).stat()
    target = dict(_fingerprint(path, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns))
    target["target_id"] = target["model"] + ":" + target["sha256"]
    return target


def definitions(target=None):
    document = json.loads(hpe990_folders.F_HPE990_UI_SEMANTICS.read_text(encoding="utf-8"))
    result = {}
    for definition in document["definitions"]:
        definition = dict(definition)
        variants = definition.pop("variants", {})
        override = variants.get(target["target_id"], {}) if target else {}
        if set(override) - {"internal_name", "root_names", "ancestor_names", "class_name"}:
            raise ValueError("Variant can override native selectors only")
        definition.update(override)
        identity = definition["semantic_id"]
        if not identity.startswith("HPE990.") or identity in result:
            raise ValueError("Invalid or duplicate semantic identity")
        result[identity] = definition
    return result


def ancestry(node, nodes):
    chain, seen = [], set()
    while node["hwnd"] not in seen:
        seen.add(node["hwnd"])
        chain.append(node)
        if not node["parent"]:
            return list(reversed(chain))
        if node["parent"] not in nodes:
            raise ValueError("Incomplete native ancestry")
        node = nodes[node["parent"]]
    raise ValueError("Cyclic native ancestry")


def selector(node, nodes, definition):
    chain = ancestry(node, nodes)
    root = chain[0]
    if root["name"] not in definition["root_names"] or root["class_name"] != "QWidget":
        return None
    if node["class_name"] != definition["class_name"]:
        return None
    name = definition["internal_name"]
    if (name is None and len(chain) != 1) or (name is not None and node["name"] != name):
        return None
    names = [n["name"] for n in chain[1:-1]]
    position = 0
    for required in definition["ancestor_names"]:
        try:
            position = names.index(required, position) + 1
        except ValueError:
            return None
    # Compare the complete native chain, including unnamed nodes. Only the reviewed
    # root display aliases are normalized; do not guess Qt objectName or control type.
    return [
        [n["class_name"], "<reviewed-root>" if i == 0 else n["name"]] for i, n in enumerate(chain)
    ]


def interactable(node, nodes):
    chain = ancestry(node, nodes)
    if not all(n["visible"] and n["enabled"] for n in chain):
        return False
    # Native visible flags alone do not establish that a scrolled-off control is usable.
    left, top, right, bottom = node["rect"]
    for parent in chain:
        rect = parent["rect"]
        left, top = max(left, rect[0]), max(top, rect[1])
        right, bottom = min(right, rect[2]), min(bottom, rect[3])
    return right > left and bottom > top


def connect(database):
    database.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(database, timeout=30)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS ui_map_targets (
            target_id TEXT PRIMARY KEY, metadata TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS ui_map_observations (
            target_id TEXT NOT NULL, session_id TEXT NOT NULL, evidence TEXT NOT NULL,
            ui_id TEXT NOT NULL, data TEXT NOT NULL,
            PRIMARY KEY(target_id,session_id,evidence,ui_id));
        CREATE TABLE IF NOT EXISTS ui_map_bindings (
            target_id TEXT NOT NULL, semantic_id TEXT NOT NULL, definition TEXT NOT NULL,
            selector TEXT NOT NULL, evidence TEXT NOT NULL, ui_id TEXT NOT NULL,
            verified_unix_ms INTEGER NOT NULL, PRIMARY KEY(target_id,semantic_id));
    """)
    return db


def inspect_record(record, target, database=None, semantic_definitions=None):
    database = database or hpe990_folders.F_HPE990_UI_REGISTRY
    semantic_definitions = semantic_definitions or definitions(target)
    nodes = {n["hwnd"]: n for n in record["nodes"]}
    matches = {identity: [] for identity in semantic_definitions}
    rows = []
    for node in record["nodes"]:
        path = [[n["class_name"], n["name"]] for n in ancestry(node, nodes)]
        candidates = []
        for identity, definition in semantic_definitions.items():
            if selector(node, nodes, definition) is not None:
                matches[identity].append(node)
                candidates.append(identity)
        rows.append(
            (
                target["target_id"],
                record["session_id"],
                record["evidence"],
                node["ui_id"],
                encoded(
                    {
                        "internal_name": node["name"],
                        "class_name": node["class_name"],
                        "native_path": path,
                        "hwnd": node["hwnd"],
                        "pid": node["pid"],
                        "parent_ui_id": node.get("parent_ui_id"),
                        "candidate_semantic_ids": candidates,
                        "observed_unix_ms": record["observed_unix_ms"],
                    }
                ),
            )
        )
    db = connect(database)
    try:
        with db:
            db.execute(
                "INSERT OR REPLACE INTO ui_map_targets VALUES (?,?)",
                (target["target_id"], encoded(target)),
            )
            db.executemany("INSERT OR IGNORE INTO ui_map_observations VALUES (?,?,?,?,?)", rows)
        bindings = {
            row[0]: row[1:]
            for row in db.execute(
                "SELECT semantic_id,definition,selector,evidence,ui_id,verified_unix_ms FROM ui_map_bindings WHERE target_id=?",
                (target["target_id"],),
            )
        }
        results = []
        for identity, definition in semantic_definitions.items():
            found = matches[identity]
            binding = bindings.get(identity)
            usable = len(found) == 1 and interactable(found[0], nodes)
            confirmed = (
                usable
                and binding
                and binding[0] == encoded(definition)
                and binding[1] == encoded(selector(found[0], nodes, definition))
            )
            results.append(
                {
                    "semantic_id": identity,
                    "kind": definition["kind"],
                    "status": "confirmed"
                    if confirmed
                    else "ambiguous"
                    if len(found) > 1
                    else "candidate"
                    if found
                    else "unobserved",
                    "currently_interactable": bool(usable),
                    "candidates": [
                        {
                            "ui_id": n["ui_id"],
                            "hwnd": n["hwnd"],
                            "internal_name": n["name"],
                            "root_hwnd": ancestry(n, nodes)[0]["hwnd"],
                        }
                        for n in found
                    ],
                    "verification": {
                        "evidence": binding[2],
                        "ui_id": binding[3],
                        "verified_unix_ms": binding[4],
                    }
                    if binding
                    else None,
                }
            )
        return {
            "target": target,
            "session_id": record["session_id"],
            "evidence": record["evidence"],
            "observed_native_count": len(rows),
            "unmapped_native_count": sum(
                not json.loads(row[4])["candidate_semantic_ids"] for row in rows
            ),
            "mappings": results,
            "database": str(database),
            "scope": "Observed native controls; meanings are reviewed definitions, not inferred app completeness or verified Qt objectName",
        }
    finally:
        db.close()


def verify_record(record, target, semantic_id, ui_id, database=None, semantic_definitions=None):
    database = database or hpe990_folders.F_HPE990_UI_REGISTRY
    semantic_definitions = semantic_definitions or definitions(target)
    report = inspect_record(record, target, database, semantic_definitions)
    item = next((m for m in report["mappings"] if m["semantic_id"] == semantic_id), None)
    if (
        not item
        or len(item["candidates"]) != 1
        or not item["currently_interactable"]
        or item["candidates"][0]["ui_id"] != ui_id
    ):
        raise ValueError(
            "Verification requires one current visible enabled candidate and its exact UI ID"
        )
    nodes = {n["hwnd"]: n for n in record["nodes"]}
    node = next(n for n in record["nodes"] if n["ui_id"] == ui_id)
    definition = semantic_definitions[semantic_id]
    db = connect(database)
    try:
        with db:
            db.execute(
                "INSERT OR REPLACE INTO ui_map_bindings VALUES (?,?,?,?,?,?,?)",
                (
                    target["target_id"],
                    semantic_id,
                    encoded(definition),
                    encoded(selector(node, nodes, definition)),
                    record["evidence"],
                    ui_id,
                    time.time_ns() // 1_000_000,
                ),
            )
    finally:
        db.close()
    return inspect_record(record, target, database, semantic_definitions)


def resolve_record(record, target, semantic_id, database=None, semantic_definitions=None):
    report = inspect_record(record, target, database, semantic_definitions)
    item = next((m for m in report["mappings"] if m["semantic_id"] == semantic_id), None)
    if not item or item["status"] != "confirmed":
        raise ValueError(
            "No confirmed unique interactable mapping for this version and current selector"
        )
    node = next(n for n in record["nodes"] if n["ui_id"] == item["candidates"][0]["ui_id"])
    native_path = [
        [n["class_name"], n["name"]]
        for n in ancestry(node, {n["hwnd"]: n for n in record["nodes"]})
    ]
    return {
        **item["candidates"][0],
        "semantic_id": semantic_id,
        "target": target,
        "evidence": record["evidence"],
        "native_path": native_path,
    }


def current_observation(session_id):
    from cores.hpe990.functions.ui import collect_ui

    session = session_guard(session_id)
    target = target_identity(session)
    record = collect_ui(session_id, screenshots=False, accessibility_backend="none")
    if target_identity(session_guard(session_id)) != target:
        raise ValueError("Target version changed during observation")
    return record, target


def mapping(session_id, action="observe", semantic_id=None, ui_id=None, include_observations=False):
    if action not in ("observe", "verify", "catalog", "revoke"):
        raise ValueError("Unsupported mapping action")
    if action == "catalog":
        session_guard(session_id)
        db = connect(hpe990_folders.F_HPE990_UI_REGISTRY)
        try:
            result = {
                "targets": [
                    json.loads(r[0])
                    for r in db.execute("SELECT metadata FROM ui_map_targets ORDER BY target_id")
                ],
                "bindings": [
                    {
                        "target_id": r[0],
                        "semantic_id": r[1],
                        "definition": json.loads(r[2]),
                        "selector": json.loads(r[3]),
                        "evidence": r[4],
                        "ui_id": r[5],
                        "verified_unix_ms": r[6],
                    }
                    for r in db.execute(
                        "SELECT * FROM ui_map_bindings ORDER BY target_id,semantic_id"
                    )
                ],
                "observation_count": db.execute(
                    "SELECT COUNT(*) FROM ui_map_observations"
                ).fetchone()[0],
            }
            if include_observations:
                result["native_observations"] = []
                for target in result["targets"]:
                    latest = db.execute(
                        "SELECT session_id,evidence FROM ui_map_observations WHERE target_id=? ORDER BY json_extract(data,'$.observed_unix_ms') DESC LIMIT 1",
                        (target["target_id"],),
                    ).fetchone()
                    if latest:
                        for ui_id, data in db.execute(
                            "SELECT ui_id,data FROM ui_map_observations WHERE target_id=? AND session_id=? AND evidence=? ORDER BY ui_id",
                            (target["target_id"], *latest),
                        ):
                            result["native_observations"].append(
                                {
                                    "target_id": target["target_id"],
                                    "session_id": latest[0],
                                    "evidence": latest[1],
                                    "ui_id": ui_id,
                                    **json.loads(data),
                                }
                            )
            return result
        finally:
            db.close()
    record, target = current_observation(session_id)
    if action == "verify":
        return verify_record(record, target, semantic_id, ui_id)
    if action == "revoke":
        if semantic_id not in definitions(target):
            raise ValueError("Unknown semantic_id")
        db = connect(hpe990_folders.F_HPE990_UI_REGISTRY)
        try:
            with db:
                db.execute(
                    "DELETE FROM ui_map_bindings WHERE target_id=? AND semantic_id=?",
                    (target["target_id"], semantic_id),
                )
        finally:
            db.close()
    return inspect_record(record, target)


def resolve_current(session_id, semantic_id):
    record, target = current_observation(session_id)
    return resolve_record(record, target, semantic_id)


def control_semantic(session_id, semantic_id, action="click", text=None, point_fraction=None):
    from cores.hpe990.functions.ui import control_ui

    resolved = resolve_current(session_id, semantic_id)
    # Pass the current exact HWND and root through existing process/session/RAM guards.
    result = control_ui(
        session_id,
        resolved["internal_name"],
        action,
        resolved["root_hwnd"],
        text,
        resolved["hwnd"],
        point_fraction,
        expected_native_path=resolved["native_path"],
    )
    return {
        **result,
        "semantic_id": semantic_id,
        "mapping_target": resolved["target"],
        "mapping_evidence": resolved["evidence"],
        "application_result_verified": False,
    }
