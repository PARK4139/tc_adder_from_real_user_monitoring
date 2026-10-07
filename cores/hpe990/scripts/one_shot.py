"""Fail-fast build, verification, versioned publication, runtime replacement."""

import argparse
import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tomllib
import uuid
from datetime import UTC, datetime
from pathlib import Path

from filelock import FileLock

from cores.common.functions.run_family_bdd import run_family_bdd
from cores.common.paths import D_ROOT
from cores.hpe990.common.paths import (
    F_AUTO_EMULATOR_RUNTIME,
    F_HPE990_RELEASES,
    hpe990_folders,
)
from cores.hpe990.functions.lifecycle import _target
from cores.hpe990.scripts.verify_mcp import verify


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def run(uv: str, verify_existing: bool = False, allow_desktop_input: bool = False) -> dict:
    uv = shutil.which(uv) or uv
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    evidence = hpe990_folders.D_HPE990_EVIDENCE / "5488b646" / run_id
    build = hpe990_folders.D_HPE990_BUILD / run_id
    evidence.mkdir(parents=True)
    build.mkdir(parents=True)
    report = {"run_id": run_id, "stages": [], "verdict": "RUNNING"}
    record = None
    state = None
    published = None
    backup = build / "previous-runtime.exe"
    replaced = False
    created_publication = False

    def command(stage: str, arguments: list[str], timeout=180, environment=None):
        report["stage"] = stage
        print(f"[{stage}] {' '.join(arguments)}", flush=True)
        result = subprocess.run(
            arguments,
            cwd=D_ROOT,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=timeout,
            env=environment,
        )
        (evidence / f"{stage}.stdout.log").write_bytes(result.stdout)
        (evidence / f"{stage}.stderr.log").write_bytes(result.stderr)
        sys.stdout.buffer.write(result.stdout)
        sys.stderr.buffer.write(result.stderr)
        report["stages"].append(
            {"name": stage, "command": arguments, "returncode": result.returncode}
        )
        if result.returncode:
            raise RuntimeError(f"{stage} exited {result.returncode}; evidence={evidence}")
        return result

    lock = hpe990_folders.D_HPE990_RUNTIME / "one-shot.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    with FileLock(str(lock), timeout=1):
        try:
            report["stage"] = "preflight"
            report["target"] = _target()
            if not allow_desktop_input:
                raise PermissionError("Required real BDD needs --allow-desktop-input")
            crate = hpe990_folders.D_HPE990 / "rust/ram/Cargo.toml"
            rust_environment = dict(
                os.environ, CARGO_TARGET_DIR=str(hpe990_folders.D_HPE990_BUILD / "rust")
            )
            command("rust-format", ["cargo", "fmt", "--check", "--manifest-path", str(crate)])
            command(
                "rust-build",
                ["cargo", "build", "--release", "--locked", "--manifest-path", str(crate)],
                environment=rust_environment,
            )
            command(
                "rule-registry",
                [uv, "run", "--locked", "python", "-m", "cores.common.rules.registry"],
            )
            command("lint", [uv, "run", "--locked", "ruff", "check", "cores"])
            command("format", [uv, "run", "--locked", "ruff", "format", "--check", "cores"])
            command(
                "pytest",
                [
                    uv,
                    "run",
                    "--locked",
                    "python",
                    "-m",
                    "pytest",
                    "-q",
                    "--ignore=cores/hpe990/tests/bdd",
                    "--basetemp",
                    str(build / "pytest-temp"),
                    "-o",
                    f"cache_dir={build / 'pytest-cache'}",
                    "--junitxml",
                    str(evidence / "junit.xml"),
                ],
            )
            # No zero-test, skip or xfail test gate can be declared successful.
            from xml.etree import ElementTree

            suites = list(ElementTree.parse(evidence / "junit.xml").iter("testsuite"))
            if (
                not suites
                or sum(int(s.get("tests", 0)) for s in suites) == 0
                or any(
                    int(s.get(key, 0)) for s in suites for key in ("skipped", "failures", "errors")
                )
            ):
                raise RuntimeError("Incomplete ordinary test gate")
            report["bdd"] = run_family_bdd("hpe990", allow_desktop_input, evidence / "source-bdd")
            state = json.loads(F_HPE990_RELEASES.read_text(encoding="utf-8"))
            if verify_existing:
                release = next(
                    item for item in reversed(state["attempts"]) if item["status"] == "released"
                )
                deployment = (
                    hpe990_folders.D_AUTO_EMULATOR_OUTPUT
                    / f"auto_emulator_{release['version']}.exe"
                )
                for role, executable in (
                    ("published", deployment),
                    ("runtime", F_AUTO_EMULATOR_RUNTIME),
                ):
                    if _hash(executable) != release["sha256"]:
                        raise RuntimeError(f"{role} does not match the recorded release")
                    report["stage"] = f"{role}-mcp"
                    report[f"{role}_mcp"] = asyncio.run(
                        verify(str(executable), ["--mcp"], evidence / role)
                    )
                    report[f"{role}_bdd"] = run_family_bdd(
                        "hpe990", allow_desktop_input, evidence / f"{role}-bdd", str(executable)
                    )
                report.update(verdict="PASS", release=release, mode="verify-existing")
                return report
            version = f"{state['next_major']}.{state['next_minor']}"
            published = hpe990_folders.D_AUTO_EMULATOR_OUTPUT / f"auto_emulator_{version}.exe"
            if published.exists():
                raise FileExistsError(f"Refusing to overwrite versioned release: {published}")
            record = {
                "version": version,
                "run_id": run_id,
                "status": "reserved",
                "internal_version": tomllib.loads((D_ROOT / "pyproject.toml").read_text())[
                    "project"
                ]["version"],
                "source_commit": None,
                "source_commit_reason": "project has no Git metadata",
            }
            state["next_minor"] += 1
            state["attempts"].append(record)
            _write(F_HPE990_RELEASES, state)
            version_file = hpe990_folders.D_HPE990 / "common" / "version.py"
            version_file.write_text(
                '"""Deployment version, maintained by the one-shot release allocator."""\n\n'
                f'DEPLOYMENT_VERSION = "{version}"\n',
                encoding="utf-8",
            )
            bdd_assets = build / "bdd-assets"
            source_bdd = hpe990_folders.D_HPE990 / "tests/bdd"
            for pattern in ("**/*.py", "**/*.feature"):
                for source in source_bdd.glob(pattern):
                    destination = bdd_assets / source.relative_to(source_bdd)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
            command(
                "build",
                [
                    uv,
                    "run",
                    "--locked",
                    "pyinstaller",
                    "--onefile",
                    "--noupx",
                    "--name",
                    f"auto_emulator_{version}",
                    "--paths",
                    str(D_ROOT),
                    "--workpath",
                    str(build / "work"),
                    "--specpath",
                    str(build / "spec"),
                    "--distpath",
                    str(build / "dist"),
                    "--copy-metadata",
                    "mcp",
                    "--collect-all",
                    "pytest_bdd",
                    "--collect-all",
                    "gherkin",
                    "--collect-submodules",
                    "_pytest",
                    "--add-binary",
                    f"{hpe990_folders.D_HPE990_BUILD / 'rust/release/hpe990-ram.exe'};.",
                    "--add-data",
                    f"{hpe990_folders.D_HPE990 / 'configs/one_shot_bdd.json'};cores/hpe990/configs",
                    "--add-data",
                    f"{bdd_assets};cores/hpe990/tests/bdd",
                    "--add-data",
                    f"{hpe990_folders.D_HPE990 / 'tests/conftest.py'};cores/hpe990/tests",
                    "--hidden-import",
                    "win32timezone",
                    "--hide-console",
                    "hide-early",
                    "cores/hpe990/wrapper/emulator.py",
                ],
                timeout=600,
            )
            candidate = build / "dist" / published.name
            command("candidate-version", [str(candidate), "--version"])
            report["stage"] = "candidate-mcp"
            report["candidate_mcp"] = asyncio.run(
                verify(str(candidate), ["--mcp"], evidence / "candidate")
            )
            report["candidate_bdd"] = run_family_bdd(
                "hpe990", allow_desktop_input, evidence / "candidate-bdd", str(candidate)
            )
            expected_hash = _hash(candidate)
            if F_AUTO_EMULATOR_RUNTIME.exists():
                shutil.copy2(F_AUTO_EMULATOR_RUNTIME, backup)
            shutil.copy2(candidate, published)
            created_publication = True
            staging = F_AUTO_EMULATOR_RUNTIME.with_suffix(".pending")
            shutil.copy2(candidate, staging)
            os.replace(staging, F_AUTO_EMULATOR_RUNTIME)
            replaced = True
            if _hash(published) != expected_hash or _hash(F_AUTO_EMULATOR_RUNTIME) != expected_hash:
                raise RuntimeError("Published/runtime hash mismatch")
            command("published-version", [str(published), "--version"])
            report["stage"] = "published-mcp"
            report["published_mcp"] = asyncio.run(
                verify(str(published), ["--mcp"], evidence / "published")
            )
            report["published_bdd"] = run_family_bdd(
                "hpe990", allow_desktop_input, evidence / "published-bdd", str(published)
            )
            report["stage"] = "runtime-mcp"
            report["runtime_mcp"] = asyncio.run(
                verify(str(F_AUTO_EMULATOR_RUNTIME), ["--mcp"], evidence / "runtime")
            )
            report["runtime_bdd"] = run_family_bdd(
                "hpe990",
                allow_desktop_input,
                evidence / "runtime-bdd",
                str(F_AUTO_EMULATOR_RUNTIME),
            )
            record.update(
                status="released",
                deployment_path=str(published),
                runtime_path=str(F_AUTO_EMULATOR_RUNTIME),
                sha256=expected_hash,
                size_bytes=published.stat().st_size,
                evidence=str(evidence),
            )
            _write(F_HPE990_RELEASES, state)
            report.update(verdict="PASS", release=record)
            return report
        except BaseException as error:
            if replaced:
                if backup.exists():
                    os.replace(backup, F_AUTO_EMULATOR_RUNTIME)
                    report["rollback"] = "restored previous runtime"
                else:
                    F_AUTO_EMULATOR_RUNTIME.unlink(missing_ok=True)
                    report["rollback"] = "removed unverified first runtime"
            if created_publication and published.exists() and record["status"] != "released":
                published.unlink()
            if record:
                record.update(status="failed", error=f"{type(error).__name__}: {error}")
                _write(F_HPE990_RELEASES, state)
            report.update(verdict="FAIL", error=f"{type(error).__name__}: {error}")
            raise
        finally:
            _write(evidence / "pipeline-report.json", report)
            print(f"{report['verdict']}: {evidence}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uv", default="uv")
    parser.add_argument("--allow-desktop-input", action="store_true")
    parser.add_argument(
        "--verify-existing",
        action="store_true",
        help="verify latest release without reserving/building a new version",
    )
    args = parser.parse_args()
    run(args.uv, args.verify_existing, args.allow_desktop_input)


if __name__ == "__main__":
    main()
