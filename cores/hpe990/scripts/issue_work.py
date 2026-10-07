"""Local issue transitions and correlated PPFFP evidence; never writes to pk_system."""

import argparse
import json
import os
import re
from datetime import UTC, datetime

from cores.hpe990.common.paths import hpe990_folders


def transition(
    issue_id: str,
    stage: str,
    details: str,
    state: str | None = None,
    blocker: str | None = None,
    resume: str | None = None,
):
    root = hpe990_folders.D_HPE990_ISSUES
    matches = list(root.glob(f"*/**/{issue_id}.md"))
    if len(matches) != 1:
        raise ValueError(f"Expected one canonical issue: {issue_id}")
    source = matches[0]
    session = next(
        (
            os.environ[k]
            for k in ("CODEX_THREAD_ID", "CODEX_SESSION_ID", "CLAUDE_SESSION_ID")
            if os.environ.get(k)
        ),
        None,
    )
    if not session:
        raise RuntimeError("Executing agent session unavailable")
    text = source.read_text(encoding="utf-8")
    if state == "blocked":
        if not blocker or not resume:
            raise ValueError("Blocked transition requires concrete blocker and resume condition")
        details += f"\n차단: {blocker}\n재개 조건: {resume}"
    if stage == "Profile" and source.relative_to(root).parts[0] in ("backlog", "working"):
        text = re.sub(r"\nagent_session_id: [^\n]*", "", text)
        heading = text.index("# 담당자")
        text = text[:heading] + "# 담당자\nagent_session_id: " + session + "\n"
        source.write_text(text, encoding="utf-8")
        assert f"agent_session_id: {session}" in source.read_text(encoding="utf-8")
    evidence = hpe990_folders.D_HPE990_EVIDENCE / issue_id
    evidence.mkdir(parents=True, exist_ok=True)
    record = dict(
        timestamp_utc=datetime.now(UTC).isoformat(),
        issue_id=issue_id,
        agent_session_id=session,
        stage=stage,
        details=details,
    )
    with (evidence / "ppffp.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    if state:
        if state not in ("working", "closed", "blocked"):
            raise ValueError(state)
        if state != "working":
            start = text.index("# actual result") + len("# actual result")
            end = text.index("# expected result", start)
            text = text[:start] + "\n" + details + "\n\n" + text[end:]
            source.write_text(text, encoding="utf-8")
        destination = (
            root / state / source.relative_to(root).relative_to(source.relative_to(root).parts[0])
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination != source:
            source.replace(destination)
        if state != "working":
            priority = root / "priority.md"
            rows = priority.read_text(encoding="utf-8").splitlines()
            priority.write_text(
                "\n".join(r for r in rows if issue_id not in r) + "\n", encoding="utf-8"
            )
    print(json.dumps(record, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("issue")
    parser.add_argument("stage")
    parser.add_argument("details")
    parser.add_argument("--state")
    parser.add_argument("--blocker")
    parser.add_argument("--resume")
    args = parser.parse_args()
    transition(args.issue, args.stage, args.details, args.state, args.blocker, args.resume)
