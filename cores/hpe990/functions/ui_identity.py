"""Transactional UI identity SSOT; provider identities are observation aliases only."""

import json
import sqlite3
from collections import Counter

from cores.hpe990.common.paths import hpe990_folders


def assign_ui_ids(record: dict, database=None) -> dict:
    """Annotate every collected element without changing its provider evidence.

    Unique named native ancestry is reusable between sessions. Unnamed or duplicate
    ancestry and unlinked provider elements remain explicitly session scoped.
    """
    database = database or hpe990_folders.F_HPE990_UI_REGISTRY
    database.parent.mkdir(parents=True, exist_ok=True)
    nodes = record["nodes"]
    by_handle = {n["hwnd"]: n for n in nodes}
    paths = {}
    for node in nodes:
        chain, seen, current = [], set(), node
        while current["hwnd"] not in seen:
            seen.add(current["hwnd"])
            chain.append([current.get("class_name", ""), current.get("name", "")])
            if current.get("parent") not in by_handle:
                break
            current = by_handle[current["parent"]]
        paths[node["hwnd"]] = list(reversed(chain))
    signatures = {h: json.dumps(p, ensure_ascii=False) for h, p in paths.items()}
    counts = Counter(signatures.values())
    session = record["session_id"]
    evidence = record["evidence"]
    with sqlite3.connect(database, timeout=30) as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS elements (
                number INTEGER PRIMARY KEY AUTOINCREMENT,
                selector TEXT UNIQUE NOT NULL, scope TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS observations (
                number INTEGER NOT NULL REFERENCES elements(number),
                evidence TEXT NOT NULL, backend TEXT NOT NULL, alias TEXT NOT NULL,
                PRIMARY KEY(evidence, backend, alias));
        """)
        db.execute("BEGIN IMMEDIATE")

        def register(element, backend, alias, selector, scope, shared=None):
            previous = db.execute(
                "SELECT e.number,e.scope FROM observations o JOIN elements e USING(number) "
                "WHERE evidence=? AND backend=? AND alias=?",
                (evidence, backend, str(alias)),
            ).fetchone()
            if previous:
                number, scope = previous
                ui_id = f"UI-{number:06d}"
            elif shared is None:
                found = db.execute(
                    "SELECT number FROM elements WHERE selector=?", (selector,)
                ).fetchone()
                if found:
                    number = found[0]
                else:
                    number = db.execute(
                        "INSERT INTO elements(selector,scope) VALUES (?,?)", (selector, scope)
                    ).lastrowid
                ui_id = f"UI-{number:06d}"
            else:
                ui_id, scope = shared["ui_id"], shared["identity_scope"]
                number = int(ui_id[3:])
            element["ui_id"] = ui_id
            element["identity_scope"] = scope
            db.execute(
                "INSERT OR IGNORE INTO observations VALUES (?,?,?,?)",
                (number, evidence, backend, str(alias)),
            )

        for node in nodes:
            signature = signatures[node["hwnd"]]
            stable = all(part[1] for part in paths[node["hwnd"]]) and all(
                counts[json.dumps(paths[node["hwnd"]][:length], ensure_ascii=False)] == 1
                for length in range(1, len(paths[node["hwnd"]]) + 1)
            )
            scope = "semantic_path" if stable else "session_observation"
            selector = (
                ["native", signature]
                if stable
                else ["native", session, node["pid"], node["hwnd"], signature]
            )
            register(node, "native", node["hwnd"], json.dumps(selector), scope)
        for node in nodes:
            parent = by_handle.get(node.get("parent"))
            node["parent_ui_id"] = parent["ui_id"] if parent else None
        for root in record.get("roots", []):
            native = by_handle.get(root["hwnd"])
            if native:
                root.update(ui_id=native["ui_id"], identity_scope=native["identity_scope"])
        for capture in record.get("screenshots", []):
            root = by_handle.get(capture["hwnd"])
            capture["ui_id"] = root["ui_id"] if root else None
        for backend in ("accessibility", "visual"):
            for element in record.get(backend, {}).get("elements", []):
                native = by_handle.get(element.get("hwnd"))
                if backend == "visual":
                    matches = element.get("matching_native_nodes", [])
                    native = by_handle.get(matches[0]["hwnd"]) if len(matches) == 1 else None
                # Only link a provider handle within the observed root and process.
                if native:
                    current, seen = native, set()
                    while current["hwnd"] not in seen:
                        seen.add(current["hwnd"])
                        if current["hwnd"] == element.get("root_hwnd"):
                            break
                        if current.get("parent") not in by_handle:
                            current = None
                            break
                        current = by_handle[current["parent"]]
                    if (
                        not current
                        or current["hwnd"] != element.get("root_hwnd")
                        or native["pid"] != element.get("pid")
                    ):
                        native = None
                alias = element["id"]
                selector = json.dumps(
                    [
                        backend,
                        session,
                        element.get("pid"),
                        alias,
                        element.get("name"),
                        element.get("control_type"),
                    ]
                )
                register(element, backend, alias, selector, "session_observation", native)
                root = by_handle.get(element.get("root_hwnd"))
                element["root_ui_id"] = root["ui_id"] if root else None
        numbers = {int(e["ui_id"][3:]) for e in nodes}
        numbers.update(
            int(e["ui_id"][3:])
            for b in ("accessibility", "visual")
            for e in record.get(b, {}).get("elements", [])
        )
        elements = []
        for number in sorted(numbers):
            selector, scope = db.execute(
                "SELECT selector,scope FROM elements WHERE number=?", (number,)
            ).fetchone()
            elements.append(
                {
                    "ui_id": f"UI-{number:06d}",
                    "identity_scope": scope,
                    "selector": json.loads(selector),
                }
            )
    return {
        "database": str(database),
        "elements": elements,
        "unique_elements": len(elements),
        "unresolved_identity_count": sum(e["identity_scope"] != "semantic_path" for e in elements),
    }
