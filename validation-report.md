# Validation Report

## 2026-03-20 Baseline

- status: PASS
- scope: repository bootstrap completeness
- command: `powershell -ExecutionPolicy Bypass -File .claude/scripts/validate-workflow.ps1`
- result: 70 checks passed, 0 failed
- notes: initial structure validation before contract refactor

## 2026-03-23 Contract Refactor

- status: PASS
- scope: contracts, command metadata, semantic validation, smoke testing
- command: `powershell -ExecutionPolicy Bypass -File .claude/scripts/validate-workflow.ps1`
- result: 186 checks passed, 0 failed
- notes: contract layer, internal core skills, and command metadata validation are active

## 2026-03-23 Smoke Test

- status: PASS
- scope: dependency resolution and write target sanity for registered commands
- command: `powershell -ExecutionPolicy Bypass -File .claude/scripts/smoke-test-workflow.ps1`
- result: 6 commands checked, pass
- notes: all registered commands resolve known skills and valid write targets

## 2026-03-23 Local Claude Hardening

- status: PASS
- scope: extracted-workflow conventions and workspace-boundary rules
- command: manual repository hardening after local Claude design session
- result: constraints, develop command, spec template, and lessons updated
- notes: fixes the specific drift that produced command JSON files and external write permission denials during C audit workflow extraction

## 2026-03-23 Audit-C-Workflow-Pro Generation

- status: PASS
- scope: end-to-end /develop flow producing Audit-C-Workflow-Pro standalone repository
- command: manual /develop execution + `powershell -ExecutionPolicy Bypass -File .claude/scripts/validate-workflow.ps1`
- result: 187 checks passed (WorkflowProgram-CN), 63 checks passed (Audit-C-Workflow-Pro), local Claude test produced 36 findings on kernel_liteos_m
- notes: all prior constraints (Markdown commands, object-map settings) correctly enforced. JSON command file detection added to validate-workflow.ps1. spec-template.md extended with Toolchain Dependencies and Security Scope sections. Gate pre-approval needed for -p mode — new constraint extracted.

## 2026-03-23 Five-Issue Fix (Audit-C-Workflow-Pro Hardening)

- status: PASS
- scope: toolchain validation, L2 methodology, lessons mechanism, code path, hooks configuration
- command: manual issue analysis + fixes + `powershell -ExecutionPolicy Bypass -File .claude/scripts/validate-workflow.ps1`
- result: 63 checks passed (Audit-C-Workflow-Pro), 187 checks passed (WorkflowProgram-CN), 0 failures
- notes:
  - Problem 1: Added L1 toolchain availability checks (WARN level, 6 warnings expected)
  - Problem 2: Added step-by-step methodology to all 4 L2 agents with evidence requirements and depth boundaries
  - Problem 3: Redesigned lessons.md as append-only log, created session-findings.md as session buffer
  - Problem 4: Changed Stage 1 to clone target into ./target-code/ within workspace
  - Problem 5: Configured PostToolUseFailure and Stop hooks for auto error logging and progress tracking
  - 5 new constraints extracted to WorkflowProgram-CN

## 2026-03-28 Claude Code Cleanup

- status: PASS
- scope: remove Codex mirror layer and contract-only assets, keep Claude Code compatible structure
- command: `powershell -ExecutionPolicy Bypass -File .claude/scripts/validate-workflow.ps1`
- result: 70 checks passed, 0 failed
- notes: removed `.agents/`, `.claude/contracts/`, `smoke-test-workflow.ps1`, `core-*` skills, and downstream transcript artifacts

## 2026-03-30 Plugin Packaging

- status: PASS
- scope: package WorkflowProgram-CN as a Claude Code plugin with root-level commands, skills, agents, rules, and scripts
- command: `scripts/verify-plugin-load.sh`
- result: 11 slash entrypoints discovered via `claude --plugin-dir /mnt/d/Code/WorkflowProgram-CN`, 0 discovery failures
- notes: WSL Claude is currently not logged in, so runtime checks stop at `/login`; discovery and plugin loading are confirmed.

## 2026-04-03 Runtime Smoke (empty-project)

- status: ENVIRONMENT-SKIP
- scope: Phase 3 runtime smoke against copied empty-project fixture
- command: `python3 tools/runtime_smoke.py --fixture empty-project --json`
- result: run_id `20260403T031024Z-empty-project`, category `CLAUDE_NOT_LOGGED_IN`
- notes: `RUN_ROOT` created successfully under `tests/transcripts/20260403T031024Z-empty-project/target/.workflowprogram/runs/20260403T031024Z-empty-project`; `context.json`, `state.json`, `events.jsonl`, `transcript.md`, and `validation-runtime-report.md` were all written; `EnvironmentSkip` event recorded; target `.claude/` output not generated because Claude CLI is not logged in.

## 2026-04-03 Runtime Smoke Expansion

- status: ENVIRONMENT-SKIP
- scope: existing-workflow and broken-workflow fixture coverage; state-bus RUN_ROOT alignment
- command: `python3 tools/runtime_smoke.py --fixture existing-workflow --json` and `python3 tools/runtime_smoke.py --fixture broken-workflow --json`
- result: run_id `20260403T032546Z-existing-workflow` and `20260403T032546Z-broken-workflow`, both classified as `CLAUDE_NOT_LOGGED_IN`
- notes: both fixtures produced complete `RUN_ROOT` evidence bundles under `tests/transcripts/*`; `.claude/scripts/state-bus.py` now defaults to `.workflowprogram/session-state.json`, supports `--run-root`, and appends state events to `events.jsonl` when a run root is provided.

## 2026-04-03 Phase 4 Finalization

- status: PASS
- scope: remove root compatibility layer, retire legacy sync script, archive obsolete migration docs
- command: `python3 tools/build_plugin.py`, `python3 .claude/scripts/validate-workflow.py`, `powershell.exe -ExecutionPolicy Bypass -File .claude/scripts/validate-workflow.ps1`, `python3 tools/runtime_smoke.py --fixture empty-project --json`
- result: build succeeded; Python validator `PASS: 117 / FAIL: 0`; PowerShell validator `PASS: 116 / FAIL: 0`; runtime smoke returned `ENVIRONMENT-SKIP` with run_id `20260403T033137Z-empty-project` and category `CLAUDE_NOT_LOGGED_IN`
- notes: root-level `commands/`, `skills/`, `agents/`, `rules/`, `scripts/` and `tools/sync_plugin_assets.py` are removed; `review_report.md`, `实施方案V3.md`, and `实施计划-Plugin架构迁移.md` were moved to `docs/archive/`; active entry docs now describe only `.claude/` source assets and `dist/plugin/` build output.

## 2026-04-05 Phase 5 Lifecycle Closure

- status: PASS
- scope: implement managed asset ownership guard and build trace manifest; update validators and runtime evidence
- command: `python3 tools/build_plugin.py`, `python3 .claude/scripts/validate-workflow.py`, `powershell.exe -ExecutionPolicy Bypass -File .claude/scripts/validate-workflow.ps1`, `python3 .claude/scripts/managed-assets.py plan/apply-staged ...`, `python3 tools/runtime_smoke.py --fixture empty-project --json`
- result: build succeeded with `dist/plugin/build-manifest.json`; Python validator `PASS: 183 / FAIL: 0`; PowerShell validator `PASS: 183 / FAIL: 0`; managed-assets smoke produced `plan_exit=0` and `apply_exit=2` with one expected unmanaged-file conflict and one managed-file update; runtime smoke returned `ENVIRONMENT-SKIP` with run_id `20260405T105730Z-empty-project` and category `CLAUDE_NOT_LOGGED_IN`
- notes:
  - added `.claude/scripts/managed-assets.py` to enforce staged candidate -> apply flow and maintain `TARGET_ROOT/.workflowprogram/managed-files.json`
  - `workflowprogram-develop` and `/develop` now require candidate generation under `RUN_ROOT/outputs/candidate/.claude/` before apply
  - `build_plugin.py` now packages the full script set and emits `dist/plugin/build-manifest.json` with plugin version, source commit, dirty flag, and per-file sha256
  - `tools/runtime_smoke.py` now captures `outputs/plugin-build-manifest.json` inside `RUN_ROOT`
  - the managed-assets smoke confirmed that unmanaged target files are not overwritten; candidate conflicts are copied to `RUN_ROOT/outputs/conflicts/`

## 2026-04-05 Natural-Language Routing Optimization

- status: PASS
- scope: keep natural-language auto-trigger on `workflowprogram-orchestrate` only; keep leaf skills explicit
- command: `python3 tools/build_plugin.py`, `python3 .claude/scripts/validate-workflow.py`
- result: build succeeded; Python validator `PASS: 183 / FAIL: 0`; regenerated plugin artifact confirms `dist/plugin/skills/workflowprogram-orchestrate/SKILL.md` no longer contains `disable-model-invocation`
- notes:
  - `workflowprogram-orchestrate` description is now bilingual and includes current-project workflow design / audit / iterate / validate cues
  - `.claude/settings.json` and `.claude/rules/constraints.md` now explicitly state that only `workflowprogram-orchestrate` should accept natural-language auto-trigger
  - leaf skills `workflowprogram-develop/audit/iterate/validate` remain slash-first to avoid multi-skill competition

## 2026-04-06 Phase 6 Stage Progress Instrumentation

- status: PASS
- scope: add stage progress instrumentation, stage-node encapsulation plan, and validator enforcement
- command: `python3 .claude/scripts/stage-progress.py update --run-root /tmp/wf-run ... --json`, `python3 tools/build_plugin.py`, `python3 .claude/scripts/validate-workflow.py`, `powershell.exe -ExecutionPolicy Bypass -File .claude/scripts/validate-workflow.ps1`
- result: stage-progress smoke generated `current-progress.json` / `milestones.jsonl` / `user-progress.md`; build succeeded; Python validator `PASS: 187 / FAIL: 0`; PowerShell validator `PASS: 187 / FAIL: 0`
- notes:
  - added `.claude/scripts/stage-progress.py` for `StageStarted/StageCheckpoint/StageCompleted` event logging
  - `/develop` and `workflowprogram-develop` now include explicit progress hook requirements
  - validators now require both source and build outputs to include `stage-progress.py`
  - added `docs/phase-06-implementation-plan.md` and expanded lowlevel design to provide stage-level node encapsulation and runtime progress contracts
