# Repository Guidelines

## Response Language

사용자에게 전달하는 설명, 진행 상황, 최종 답변은 항상 한국어로 작성한다. 코드, 명령어, 경로, 식별자는 원문을 유지한다.

## Project Structure & Module Organization

Follow `../pk_system/cores/common/rules/path/family_skeleton.py` and `family_local_ssot.py`. Use `cores/{family}/`. New families require:

- `common/paths.py`: family-local path constants.
- `rules/families.md`: established function families.
- `issues/priority.md`: issue priorities.

Add `functions/`, `wrapper/`, `tests/`, `configs/`, `docs/`, and `scripts/` only as needed. Shared functions and paths belong in `cores/common/functions/` and `cores/common/paths.py`. Keep family infrastructure in `common/`.

## Build, Test, and Development Commands

Manage Python and dependencies with uv. Maintain `pyproject.toml`, `uv.lock`, and `.python-version`; commit metadata and lockfile together. Exclude `.venv/` and caches.

After initialization:

- `uv sync --locked`: reproduce the environment.
- `uv add <package>` / `uv add --dev <package>`: manage dependencies.
- `uv run python cores/{family}/wrapper/{entry}.py`: execute a wrapper.

Document initialization in `README.md`.

## Performance & Rust

Implement performance-critical computation and latency-sensitive processing in Rust. Keep Python orchestration managed by uv. Place crates under `cores/{family}/rust/`, with `Cargo.toml` and crate-local `src/`. Use `cargo build --release`, `cargo test`, and `cargo fmt --check` inside crates; measure representative workloads.

## Coding Style & Naming Conventions

Use consistent indentation and configure formatters. In family `common/paths.py`, define `D_*` directories before `F_*` files, including `D_{FAMILY}`. Use `{Family}Folders` and `{family}_folders`. Avoid competing path modules and compatibility aliases; update consumers atomically.

## Family Rule System

Follow pk_system's `cores/common/rules/registry.generated.json` and its canonical atomic rule files. Store local domain rules in `cores/{family}/rules/` and shared rules in `cores/common/rules/`. Each canonical file has one unique `RULE_ID` and one independent body. Avoid duplicate IDs/bodies, date suffixes, and repeated parent namespaces in basenames.

Apply explicit user instructions, specific domain rules, common rules, then governance. Resolve identity conflicts before proceeding. Update canonical files first; regenerate and validate the registry through its established tooling. Keep indexes and this guide as references, not competing rule bodies.

## Family Issue System

Follow `../pk_system/cores/i18n/rules/issue.md` for registration, templates, execution, and closure.

Store issues at `cores/{family}/issues/{state}/{function_family}/{sub_family}/{uuid8}.md`. States are `backlog`, `working`, `blocked`, and `closed`; do not duplicate status in the body. Declare function families in `rules/families.md` using snake_case; use kebab-case subfamilies. Reserve IDs through pk_system's `get_issue_id()`; never assign IDs manually.

Check all states for duplicates. Each issue must have one measurable PASS/FAIL result and the canonical template. Move individual files while preserving UUIDs. Synchronize `priority.md` Active/Blocked tables using only `우선순위 | UUID | 근거`, ordered Critical → High → Normal → Low, then dependencies and family order. Close after evidenced PASS; update actual results and remove priority rows.

## Testing & Pull Requests

Keep tests family-owned. Use imperative commits. PRs need purpose, issues, validation, and UI screenshots. Never commit credentials.

## Repository Boundary

Create project families, issues, rules, and implementation only inside auto_emulator. Treat ../pk_system as a reference; do not create project files there. Use already reserved IDs for this registration; do not mutate the external registry again without explicit authorization.

## Emulator MCP Interface

Expose every Emulator function through MCP; follow cores/hpe990/rules/mcp_function_coverage.py. Keep the adapter at cores/hpe990/mcp/server.py and tool groups under mcp/tools/. BDD must use public MCP tools while Real Activity Monitoring remains active. Validate complete function-to-tool coverage through actual MCP calls.

## One Shot Output

Follow pk_system common one-shot rules with the explicit local destination override in cores/hpe990/rules/one_shot_output.py: 3rd_party/auto_emulator_X.Y.exe, with the fixed runtime at 3rd_party/auto_emulator.exe. Use the thin one-shot-pipeline.cmd launcher, automatic version allocation, external build intermediates, and verified publication.
