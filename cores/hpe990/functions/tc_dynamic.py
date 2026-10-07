"""Generate marked TC display expectations from collected UI identity definitions."""

import json
import os
import re
import sqlite3
import tempfile

from filelock import FileLock

from cores.hpe990.common.paths import hpe990_folders

START = "    # BEGIN collected General elements"
END = "    # END collected General elements"


def general_elements(database) -> list[dict]:
    """Use observed named definitions, never a manually maintained element list."""
    if not database.exists():
        return []
    elements = {}
    priorities = {"GROUP": 0, "WIDGET": 1, "COMBO": 2, "INPUT": 3, "STATIC_DATA": 4}
    with sqlite3.connect(database, timeout=30) as db:
        for number, selector in db.execute("SELECT number,selector FROM elements ORDER BY number"):
            selector = json.loads(selector)
            if selector[0] != "native":
                continue
            path = json.loads(selector[-1])
            name = path[-1][1]
            if not name.startswith("UI_GENERAL::"):
                continue
            _, kind, label = name.split("::", 2)
            if kind not in priorities or not label.strip():
                continue
            old = elements.get(label)
            if old is None or priorities[kind] > priorities[old["kind"]]:
                elements[label] = dict(name=label, kind=kind, ui_id=f"UI-{number:06d}")
    return sorted(elements.values(), key=lambda e: e["name"].casefold())


def _write_changed(path, content):
    if path.read_text(encoding="utf-8") == content:
        return False
    fd, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as output:
            output.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


def sync_general_expected(database=None, source=None) -> dict:
    """Refresh only the explicitly marked TC-001 block and its derived Markdown row."""
    database = database or hpe990_folders.F_HPE990_UI_REGISTRY
    source = source or hpe990_folders.D_HPE990 / "docs/bdd/preferences_general.feature"
    elements = general_elements(database)
    if not elements:
        return {"updated": False, "reason": "No observed named General elements"}
    with FileLock(str(source) + ".lock", timeout=5):
        content = source.read_text(encoding="utf-8")
        # Require author opt-in; do not rewrite arbitrary scenarios.
        if "@expected-collected-General" not in content or START not in content:
            return {"updated": False, "reason": "No marked dynamic expectation"}
        expected = ["스크롤 전후 해당 위치에서 다음 수집 요소가 각각 표시된다"]
        expected += [f"{element['name']} 항목이 표시된다" for element in elements]
        lines = [START, "    Then " + expected[0]]
        for element, text in zip(elements, expected[1:]):
            lines += [f"    # UI reference: {element['ui_id']}", "    And " + text]
        lines += [END]
        pattern = re.escape(START) + r".*?" + re.escape(END)
        content, count = re.subn(pattern, lambda _: "\n".join(lines), content, flags=re.S)
        if count != 1:
            raise ValueError("Expected exactly one marked General expectation block")
        updated = _write_changed(source, content)
        markdown = source.with_suffix(".md")
        if markdown.exists():
            document = markdown.read_text(encoding="utf-8")
            prefix, rest = document.split("### TC-001 ", 1)
            case, suffix = rest.split("\n### ", 1)
            row = "| 2 | 1. General 설정 영역을 위에서 아래까지 스크롤하며 입력요소 확인 | "
            row += "<br>".join(text.replace("|", "\\|") for text in expected) + " |"
            case, count = re.subn(r"^\| 2 \|.*$", lambda _: row, case, flags=re.M)
            if count != 1:
                raise ValueError("Expected one TC-001 Markdown step 2")
            _write_changed(markdown, prefix + "### TC-001 " + case + "\n### " + suffix)
    return {
        "updated": updated,
        "element_count": len(elements),
        "source": str(source),
        "ui_ids": [e["ui_id"] for e in elements],
        "executed": False,
    }
