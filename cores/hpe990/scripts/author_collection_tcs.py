"""Author UI-route validation drafts from retained public MCP collection evidence."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import quote

from filelock import FileLock

from cores.hpe990.common.paths import hpe990_folders


def author(reports: list[Path]) -> dict:
    routes = {}
    for source in reports:
        for route in json.loads(source.read_text(encoding="utf-8"))["routes"]:
            if route.get("returned_to_setup") or route.get("returned_to_parent"):
                routes[(route.get("parent", "Setup"), route["actual"])] = (route, source)
    ledger_path = hpe990_folders.F_HPE990_TC_IDS
    root = hpe990_folders.D_HPE990_TC_CASES
    written = []
    with FileLock(str(hpe990_folders.D_HPE990_RUNTIME / "tc-authoring.lock"), timeout=30):
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        files = list(root.rglob("*.feature"))
        for (parent, screen), (route, report) in routes.items():
            snapshot = json.loads(Path(route["snapshots"][-1]).read_text(encoding="utf-8"))
            labels = {e.get("name") for e in snapshot.get("visual", {}).get("elements", [])}
            return_label = route.get("return_label") or next(
                (label for label in ("Cancel", "Close", "Back") if label in labels), None
            )
            if return_label is None:
                return_label = "복귀"
            title = f"{screen} 화면 진입·표시 및 {parent} 복귀"
            marker = (
                f"# collection-route: {screen}"
                if parent == "Setup"
                else f"# collection-route: {parent}/{screen}"
            )
            matches = [p for p in files if marker in p.read_text(encoding="utf-8")]
            if len(matches) > 1:
                raise ValueError(f"Duplicate route TC: {screen}")
            if matches:
                path = matches[0]
                identity = path.stem
            else:
                identity = f"TC-{ledger['next_number']}"
                if identity in ledger["issued_ids"] or any(p.stem == identity for p in files):
                    raise ValueError("TC allocator collision")
                ledger["issued_ids"].append(identity)
                ledger["next_number"] = (ledger["next_number"] // 10 + 1) * 10
                slug = re.sub(r"[^a-z0-9]+", "_", screen.lower()).strip("_")
                parent_slug = {
                    "Job Editor": "job_editor",
                    "HoleEditor": "hole_editor",
                    "Digital Pattern": "digital_pattern",
                }.get(parent, re.sub(r"[^a-z0-9]+", "_", parent.lower()).strip("_"))
                directory = "setup" if parent == "Setup" else f"edger/{parent_slug}"
                path = root / "to_review" / directory / slug / f"{identity}.feature"
                path.parent.mkdir(parents=True, exist_ok=True)
                pending = ledger_path.with_suffix(".pending")
                pending.write_text(
                    json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
                pending.replace(ledger_path)
            content = (
                f"@draft @ISSUE-50c688e3 @AC-route-ui-validation @path-Edger/{quote(parent, safe='')}/{quote(screen, safe='')}\n"
                f"Feature: {screen} 화면 이동 검수\n\n"
                f"{marker}\n# MCP 진입·복귀 수집 증거: {report}\n"
                "# 수집 경로의 관찰 증거이며 제품 TC 실행 PASS를 의미하지 않는다.\n"
                f"  @{identity} @type-navigation\n  Scenario: {identity} {title}\n"
                f"    Given {'시험 작업을 불러온 ' if parent != 'Setup' else ''}{parent} 화면이 열려 있어야 합니다.\n"
                "    # Step 1\n"
                f"    When {parent}에서 {route['requested']} 화면을 선택\n"
                f"    Then {screen} 화면이 보여야 합니다.\n"
                "    And 화면에 표시된 버튼·탭·입력란이 수집 화면과 대응해야 합니다.\n"
                "    # Step 2\n"
                f"    When {'입력값을 변경하지 않고 ' if return_label == '↵' else ''}해당 화면의 {return_label} 버튼 선택\n"
                f"    Then {parent} 화면으로 복귀해야 합니다.\n"
            )
            if (
                path.relative_to(root).parts[0] == "reviewed"
                and path.read_text(encoding="utf-8") != content
            ):
                destination = root / "to_review" / Path(*path.relative_to(root).parts[1:])
                if destination.exists():
                    raise ValueError("Duplicate review destination")
                destination.parent.mkdir(parents=True, exist_ok=True)
                path.replace(destination)
                path = destination
            path.write_text(content, encoding="utf-8")
            written.append(
                {"id": identity, "screen": screen, "file": str(path), "execution_status": "NOT_RUN"}
            )
    return {"cases": written, "count": len(written)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("reports", nargs="+", type=Path)
    args = parser.parse_args()
    print(json.dumps(author(args.reports), ensure_ascii=True))
