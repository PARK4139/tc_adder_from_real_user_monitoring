# title
RAM UI ID 기록과 정본 백업의 SQLite 잠금 경합 제거

# pre-condition
- Owner: hpe990/activity_monitoring. uv-managed Python, Windows interactive session.
- Parent: ui_collection/complete-ui-inventory/50c688e3.
- Incident: activity_monitoring/registry-backup-delay/d5f1cd12.
- Existing registry uses DELETE journal; a scoped backup held a long read transaction.
- Preserve Emulator, native RAM, activity log, UI IDs, aliases and existing evidence.

# steps
근거: 사용자 수집 지연 원인 분석 후 do issue. Actual max observation start gap 241031.917ms during scoped registry backup.
1. Confirm the conflicting read/write path through code, correlated incident evidence and isolated before/after reproduction.
2. Isolate identity writes from readers and expose a bounded canonical identity backup through auto_emulator MCP. Preserve stable IDs/counters/mappings; explicitly exclude observation history from this backup scope.
3. Test cancellation/failure safety and concurrent writer behavior; validate actual MCP backup and collection with RAM active.

# actual result
PASS. Isolated DELETE reader blocked writer commit; WAL reader/writer isolation passed 3 trials. Explicit connection closure, WAL access for UI identities/mappings and bounded public MCP canonical backup implemented. 47 focused tests and Ruff PASS; timeout/interruption cleanup verified; populated version mapping test also PASS. Actual MCP discovery includes hpe990_ui_registry_backup. Three actual concurrent backup/UI-collection trials passed with no lock errors. Backups: 58,144 canonical identities, 1 version target, 1 confirmed binding, preserved allocator counter 58,144. All three exports matched the source definitions/counters/mappings exactly; integrity_check=ok, foreign_key_check empty. Historical observations/aliases/logs retained in source; export scope explicitly excludes history. Duration 595.159-1037.891ms; observed timestamp gap upper bound 2440ms and maximum observation age 1720ms during the backup verification window. Native/semantic RAM and activity logger stayed active. Cause supported by incident correlation/code/reproduction, not a blocked-thread stack. Evidence: D_TEMP/hpe990/evidence/ffba3c51/live-verification.json, canonical-content-verification.json, tools.json and public MCP receipts. Prior cause/reproduction: D_TEMP/hpe990/evidence/50c688e3/edger-remaining/collection-delay-cause.json, sqlite-lock-reproduction.json. Scope/limitations: cores/hpe990/docs/ram_registry_isolation.md. Source MCP validated; one-shot EXE not rebuilt. Full UI inventory remains separate.

# expected result
- One AC PASS only if cause is evidenced, isolated DELETE conflict is reproduced, corrected reader/writer concurrency passes at least 3 trials, and actual public MCP backup plus at least 3 concurrent UI collections preserve IDs with no lock errors.
- Backup integrity_check=ok and foreign_key_check empty; allocator counters and all canonical definitions/mappings match the backup snapshot. Existing observation history remains in the original registry/logs.
- Interrupted/expired backup is never published as complete. Deadline failure releases its read connection. Live backup verification has semantic observation start gaps <=10000ms while native RAM/activity log remain active; record actual maximum and do not infer uninterrupted capture from worker liveness.
- Evidence: D_TEMP/hpe990/evidence/ffba3c51/. No full-app collection/BDD completion claim.

# label
SQA_sk_0_0_0

# environment
OS: Windows
hostname: Huvitz workstation

# 담당자
agent_session_id: 01a1104b-a9f2-7771-8ea6-39705d165cf5
