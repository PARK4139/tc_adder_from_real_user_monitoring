"""Load individually authored TC files into one in-memory review document."""

import json
import re
from pathlib import Path

from gherkin.parser import Parser

from cores.hpe990.common.paths import hpe990_folders


def review_stamp(directory=None, order_file=None):
    """Include additions, deletions, renames and changes in the watcher inventory."""
    directory = directory or hpe990_folders.D_HPE990_TC_CASES
    order_file = order_file or hpe990_folders.F_HPE990_TC_REVIEW
    files = sorted(directory.rglob("*.feature")) + [order_file]
    return tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in files)


def load_review_source(directory=None, order_file=None) -> str:
    """One standalone Feature/Scenario per file; inherit tags without storing a copy."""
    directory = directory or hpe990_folders.D_HPE990_TC_CASES
    order_file = order_file or hpe990_folders.F_HPE990_TC_REVIEW
    order = json.loads(order_file.read_text(encoding="utf-8"))["order"]
    if len(order) != len(set(order)):
        raise ValueError("Duplicate TC identity in review order")
    cases = {}
    for path in sorted(directory.rglob("*.feature")):
        source = path.read_text(encoding="utf-8")
        feature = Parser().parse(source)["feature"]
        children = feature["children"]
        if len(children) != 1 or "scenario" not in children[0]:
            raise ValueError(f"Expected one Scenario without Background/Rule: {path}")
        scenario = children[0]["scenario"]
        if scenario.get("examples"):
            raise ValueError(f"Review TC must not be a Scenario Outline: {path}")
        tags = [t["name"] for t in scenario["tags"]]
        identities = [t[1:] for t in tags if t.startswith("@TC-")]
        if len(identities) != 1 or not re.fullmatch(r"TC-[0-9]{3,}", identities[0]):
            raise ValueError(f"Expected one numeric TC identity: {path}")
        identity = identities[0]
        if path.stem != identity or identity in cases:
            raise ValueError(f"Duplicate TC identity or filename mismatch: {path}")
        # Keep the original scenario text (including dynamic-generation markers).
        lines = source.splitlines()
        body = "\n".join(lines[scenario["location"]["line"] - 1 :]).rstrip()
        inherited = [t["name"] for t in feature["tags"]]
        if any(t.startswith("@path-") for t in tags):
            inherited = [t for t in inherited if not t.startswith("@path-")]
        combined = list(dict.fromkeys(inherited + tags))
        cases[identity] = "  " + " ".join(combined) + "\n" + body + "\n"
    if not cases:
        raise ValueError("No review TC files found")
    # Explicit UI order survives insertions; new files are discovered automatically.
    ordered = [identity for identity in order if identity in cases]
    ordered += sorted(set(cases) - set(ordered), key=lambda identity: int(identity[3:]))
    return "Feature: TC review\n\n" + "\n".join(cases[i] for i in ordered)


def case_file(identity: str) -> Path:
    matches = list(hpe990_folders.D_HPE990_TC_CASES.rglob(identity + ".feature"))
    if len(matches) != 1:
        raise ValueError(f"Expected one file for {identity}")
    return matches[0]
