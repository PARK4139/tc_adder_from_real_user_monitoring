"""Generate a validated metadata index of local canonical atomic rules."""

import ast
import hashlib
import json
from pathlib import Path

from cores.common.paths import D_ROOT


def generate() -> dict:
    entries = []
    ids = set()
    bodies = set()
    for path in sorted((D_ROOT / "cores").glob("*/rules/**/*.py")):
        if path == Path(__file__).resolve():
            continue
        module = ast.parse(path.read_text(encoding="utf-8"))
        values = {}
        for statement in module.body:
            if isinstance(statement, ast.Assign) and len(statement.targets) == 1:
                target = statement.targets[0]
                if isinstance(target, ast.Name) and target.id in {
                    "RULE_ID",
                    "TITLE",
                    "BODY",
                    "SOURCE",
                    "STATUS",
                }:
                    values[target.id] = ast.literal_eval(statement.value)
        if not values:
            continue
        if not {"RULE_ID", "TITLE", "BODY", "SOURCE", "STATUS"} <= values.keys():
            raise ValueError(f"Missing atomic rule metadata: {path}")
        source = path.relative_to(D_ROOT).as_posix()
        digest = hashlib.sha256(values["BODY"].strip().encode()).hexdigest()
        if values["SOURCE"] != source or values["RULE_ID"] in ids or digest in bodies:
            raise ValueError(f"Duplicate rule identity/body or broken source pointer: {source}")
        ids.add(values["RULE_ID"])
        bodies.add(digest)
        entries.append(
            {key: values[key] for key in ("RULE_ID", "TITLE", "SOURCE", "STATUS")}
            | {"body_sha256": digest}
        )
    registry = {"summary": {"rule_count": len(entries), "verdict": "PASS"}, "rules": entries}
    destination = Path(__file__).with_name("registry.generated.json")
    destination.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return registry


if __name__ == "__main__":
    print(json.dumps(generate()["summary"]))
