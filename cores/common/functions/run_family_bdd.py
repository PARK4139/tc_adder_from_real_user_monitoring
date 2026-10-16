"""Strict family-owned BDD registry and execution gate, including frozen worker support."""

import ast
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from xml.etree import ElementTree

from cores.common.paths import D_ROOT, D_TEMP


def bdd_registry(family: str) -> dict:
    if not re.fullmatch(r"[a-z][a-z0-9_]*", family):
        raise ValueError("Invalid family")
    root = D_ROOT / "cores" / family
    config = json.loads((root / "configs/one_shot_bdd.json").read_text(encoding="utf-8"))
    if config["status"] != "REQUIRED":
        raise RuntimeError("Family has no required registered acceptance suite")
    for key, pattern in (
        ("features", "tests/bdd/**/*.feature"),
        ("bindings", "tests/bdd/**/test_*.py"),
    ):
        declared = config[key]
        if len(declared) != len(set(declared)) or not declared:
            raise RuntimeError(f"Missing or duplicate {key}")
        actual = {p.relative_to(root).as_posix() for p in root.glob(pattern)}
        if set(declared) != actual:
            raise RuntimeError(f"Unregistered/missing {key}: declared={declared}, actual={actual}")
    from gherkin.parser import Parser

    scenarios = []
    for relative in config["features"]:
        content = (root / relative).read_text(encoding="utf-8")
        feature = Parser().parse(content)["feature"]
        tags = [tag["name"] for tag in feature.get("tags", [])]
        if not any(re.fullmatch(r"@ISSUE-[0-9a-f]{8}", t) for t in tags) or not any(
            t.startswith("@AC-") for t in tags
        ):
            raise RuntimeError(f"Missing issue/acceptance tags: {relative}")
        for child in feature["children"]:
            if "scenario" in child:
                item = child["scenario"]
                scenarios.append(
                    {
                        "feature": relative,
                        "name": item["name"],
                        "tags": tags,
                        "steps": [s["text"] for s in item["steps"]],
                        "gherkin": content,
                    }
                )
    bindings = []
    for relative in config["bindings"]:
        module = ast.parse((root / relative).read_text(encoding="utf-8"))
        for node in ast.walk(module):
            if not isinstance(node, ast.FunctionDef):
                continue
            for decorator in node.decorator_list:
                if (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Name)
                    and decorator.func.id == "scenario"
                ):
                    feature, title = [ast.literal_eval(a) for a in decorator.args[:2]]
                    feature_path = (Path(relative).parent / feature).as_posix()
                    bindings.append(
                        {
                            "feature": feature_path,
                            "name": title,
                            "binding": relative,
                            "test": node.name,
                        }
                    )
    for scenario in scenarios:
        matches = [
            b
            for b in bindings
            if b["feature"] == scenario["feature"] and b["name"] == scenario["name"]
        ]
        if len(matches) != 1:
            raise RuntimeError(f"Expected exactly one binding: {scenario['name']}")
        scenario.update(matches[0])
    if len(bindings) != len(scenarios) or len(scenarios) != config["expected_tests"]:
        raise RuntimeError("Binding/scenario count mismatch")
    return {
        "family": family,
        "scenarios": scenarios,
        "expected_tests": len(scenarios),
        "config": str(root / "configs/one_shot_bdd.json"),
    }


def run_family_bdd(
    family: str,
    allow_desktop_input: bool = False,
    evidence: Path | None = None,
    executable: str | None = None,
) -> dict:
    registry = bdd_registry(family)
    if not allow_desktop_input:
        raise PermissionError("Required BDD gate needs explicit --allow-desktop-input")
    evidence = evidence or D_TEMP / family / "evidence/5488b646" / uuid.uuid4().hex
    evidence = evidence.resolve()
    evidence.relative_to(D_TEMP.resolve())
    evidence.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, HPE990_BDD_EVIDENCE=str(evidence))
    if executable:
        environment["HPE990_BDD_EXECUTABLE"] = executable
    else:
        environment.pop("HPE990_BDD_EXECUTABLE", None)
    if getattr(sys, "frozen", False):
        arguments = [sys.executable, "--bdd-worker", str(evidence)]
        environment["HPE990_BDD_EXECUTABLE"] = sys.executable
    else:
        arguments = [
            sys.executable,
            "-m",
            "pytest",
            str(D_ROOT / "cores" / family / "tests/bdd"),
            "--allow-desktop-input",
            "-q",
            "--junitxml",
            str(evidence / "bdd-results.xml"),
            "-o",
            f"cache_dir={evidence / 'pytest-cache'}",
        ]
    result = subprocess.run(
        arguments,
        cwd=D_ROOT,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=300,
    )
    (evidence / "bdd-stdout.log").write_bytes(result.stdout)
    (evidence / "bdd-stderr.log").write_bytes(result.stderr)
    xml = evidence / "bdd-results.xml"
    suites = list(ElementTree.parse(xml).iter("testsuite")) if xml.exists() else []
    counts = {
        key: sum(int(s.get(key, 0)) for s in suites)
        for key in ("tests", "skipped", "failures", "errors")
    }
    verdict = (
        "PASS"
        if (
            result.returncode == 0
            and counts["tests"] == registry["expected_tests"]
            and not any(counts[k] for k in ("skipped", "failures", "errors"))
        )
        else "FAIL"
    )
    report = {
        "family": family,
        "registry": registry,
        "command": arguments,
        "counts": counts,
        "returncode": result.returncode,
        "verdict": verdict,
        "evidence": str(evidence),
    }
    (evidence / "bdd-gate-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    contracts = []
    observed_tools = set()
    for source in evidence.glob("test_*/mcp-contract-report.json"):
        contract = json.loads(source.read_text(encoding="utf-8"))
        state = contract["state"]
        monitor = state.get("ram_report", {})
        controls = []
        for call in contract["calls"]:
            if not call["result"]["isError"]:
                observed_tools.add(call["name"])
                if call["name"] in ("hpe990_ui_control", "hpe990_window_geometry"):
                    data = call["result"].get("structuredContent") or json.loads(
                        call["result"]["content"][0]["text"]
                    )
                    controls.append(
                        {"action_id": data["action_id"], "ram_active": data["ram_active"]}
                    )
        contracts.append(
            {
                "scenario": source.parent.name,
                "session_id": state.get("session_id"),
                "verdict": state.get("verdict", "FAIL"),
                "controls": controls,
                "monitor_stop_reason": monitor.get("stop_reason"),
                "runtime_log": state.get("launch", {}).get("runtime_log"),
                "mcp_contract": str(source),
            }
        )
    missing = sum(not c["ram_active"] for item in contracts for c in item["controls"])
    concurrent = {
        "verdict": verdict,
        "scenarios": contracts,
        "successful_public_tools": sorted(observed_tools),
        "missing_control_ram_associations": missing,
        "all_monitors_finalized": all(
            c["monitor_stop_reason"] == "process_exited" for c in contracts
        ),
        "expected_scenarios": registry["expected_tests"],
    }
    if (
        len(contracts) != registry["expected_tests"]
        or missing
        or not concurrent["all_monitors_finalized"]
        or any(c["verdict"] != "PASS" for c in contracts)
    ):
        concurrent["verdict"] = "FAIL"
        report["verdict"] = verdict = "FAIL"
    report["concurrent"] = concurrent
    (evidence / "concurrent-ram-report.json").write_text(
        json.dumps(concurrent, indent=2), encoding="utf-8"
    )
    (evidence / "bdd-gate-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if verdict != "PASS":
        raise RuntimeError(f"Incomplete BDD gate: {counts}; evidence={evidence}")
    return report


def frozen_bdd_worker(evidence: Path) -> int:
    """Internal fixed suite; packaged pytest plugins and source bindings are required."""
    import pytest
    import pytest_bdd.plugin

    registry = bdd_registry("auto_emulator")
    evidence = evidence.resolve()
    evidence.relative_to(D_TEMP.resolve())
    evidence.mkdir(parents=True, exist_ok=True)
    os.environ["HPE990_BDD_EXECUTABLE"] = sys.executable
    os.environ["HPE990_BDD_EVIDENCE"] = str(evidence)
    os.environ["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    arguments = [
        str(D_ROOT / "cores/auto_emulator/tests/bdd"),
        "--allow-desktop-input",
        "-q",
        "--junitxml",
        str(evidence / "bdd-results.xml"),
        "-o",
        f"cache_dir={evidence / 'pytest-cache'}",
        "-o",
        "markers=integration: interactive Windows desktop",
    ]
    result = pytest.main(arguments, plugins=[pytest_bdd.plugin])
    if registry["expected_tests"] == 0:
        return 1
    return result
