#!/usr/bin/env python3
"""Runtime smoke harness for WorkflowProgram-CN.

This script runs a minimal end-to-end plugin invocation against a copied fixture
workspace and writes runtime evidence into RUN_ROOT under the copied target.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


FIXTURE_PRESETS: Dict[str, Dict[str, str]] = {
    "empty-project": {
        "entry_skill": "workflowprogram-develop",
        "request": "为当前项目设计一个最小 Claude Code workflow，至少包含 settings、一个 skill 和一个 rule 文件",
    },
    "existing-workflow": {
        "entry_skill": "workflowprogram-audit",
        "request": "审计当前项目中的 workflow 结构，并输出结构问题、模式偏离和下一步建议",
    },
    "broken-workflow": {
        "entry_skill": "workflowprogram-validate",
        "request": "验证当前项目中的 workflow 资产，并输出失败项、影响范围和修复优先级",
    },
}


@dataclass
class RunVerdict:
    result: str
    category: Optional[str]
    message: str
    is_error: bool
    subagent_evidence: bool


class RuntimeSmokeError(Exception):
    pass


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso_now() -> str:
    return now_utc().isoformat().replace("+00:00", "Z")


def make_run_id(fixture: str) -> str:
    return f"{now_utc().strftime('%Y%m%dT%H%M%SZ')}-{fixture}"


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def append_event(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_json_from_output(stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
    candidates = []
    for stream in (stdout, stderr):
        for line in stream.splitlines():
            stripped = line.strip()
            if stripped.startswith("{") and stripped.endswith("}"):
                candidates.append(stripped)
    for raw in reversed(candidates):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            continue
    return None


def detect_subagent_evidence(text: str) -> bool:
    lowered = text.lower()
    tokens = [
        "subagentstart",
        "subagentstop",
        "subagent",
        "taskcreated",
        "taskcompleted",
    ]
    return any(token in lowered for token in tokens)


def snapshot_tree(root: Path) -> list[str]:
    if not root.exists():
        return []
    return sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())


def update_state(state_path: Path, **changes: Any) -> Dict[str, Any]:
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
    else:
        state = {}
    state.update(changes)
    state["updated_at"] = iso_now()
    write_json(state_path, state)
    return state


def prepare_workspace(repo_root: Path, fixture: str, run_id: str) -> tuple[Path, Path]:
    fixture_root = repo_root / "tests" / "fixtures" / fixture
    if not fixture_root.exists():
        raise RuntimeSmokeError(f"Fixture not found: {fixture_root}")

    workspace_root = repo_root / "tests" / "transcripts" / run_id
    target_root = workspace_root / "target"

    if workspace_root.exists():
        shutil.rmtree(workspace_root)
    workspace_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(fixture_root, target_root)
    return workspace_root, target_root


def classify_result(stdout: str, stderr: str, parsed: Optional[Dict[str, Any]], returncode: int) -> RunVerdict:
    combined = "\n".join(part for part in [stdout.strip(), stderr.strip()] if part)
    subagent_evidence = detect_subagent_evidence(combined + "\n" + json.dumps(parsed or {}, ensure_ascii=False))

    if "Not logged in · Please run /login" in combined:
        return RunVerdict(
            result="ENVIRONMENT-SKIP",
            category="CLAUDE_NOT_LOGGED_IN",
            message="Claude CLI is installed but not logged in.",
            is_error=False,
            subagent_evidence=subagent_evidence,
        )

    if "Unknown skill:" in combined or "Unknown command" in combined:
        return RunVerdict(
            result="FAIL",
            category="STRUCTURE_FAILURE",
            message="Plugin entry was not discovered by Claude CLI.",
            is_error=True,
            subagent_evidence=subagent_evidence,
        )

    if parsed is not None:
        result_text = str(parsed.get("result", ""))
        is_error = bool(parsed.get("is_error", False))
        if is_error:
            return RunVerdict(
                result="FAIL",
                category="RUNTIME_FAILURE",
                message=result_text or "Claude CLI returned an error result.",
                is_error=True,
                subagent_evidence=subagent_evidence,
            )
        return RunVerdict(
            result="PASS",
            category=None,
            message=result_text or "Claude CLI completed successfully.",
            is_error=False,
            subagent_evidence=subagent_evidence,
        )

    if returncode != 0:
        return RunVerdict(
            result="FAIL",
            category="RUNTIME_FAILURE",
            message="Claude CLI exited with non-zero status without structured JSON output.",
            is_error=True,
            subagent_evidence=subagent_evidence,
        )

    return RunVerdict(
        result="FAIL",
        category="EVIDENCE_FAILURE",
        message="No structured Claude CLI JSON output was captured.",
        is_error=True,
        subagent_evidence=subagent_evidence,
    )


def build_command(claude_bin: str, plugin_root: Path, entry_skill: str, request: str) -> list[str]:
    invocation = f"/{entry_skill} {request}".strip()
    return [
        claude_bin,
        "-p",
        "--plugin-dir",
        str(plugin_root),
        "--output-format",
        "json",
        invocation,
    ]


def write_report(report_path: Path, context: Dict[str, Any], verdict: RunVerdict, state: Dict[str, Any], target_claude_files: list[str]) -> None:
    lines = [
        "# Runtime Validation Report",
        "",
        f"- Run ID: `{context['run_id']}`",
        f"- Fixture: `{context['fixture']}`",
        f"- Entry skill: `{context['entry_skill']}`",
        f"- Result: `{verdict.result}`",
    ]
    if verdict.category:
        lines.append(f"- Category: `{verdict.category}`")
    lines.extend([
        f"- Target root: `{context['target_root']}`",
        f"- Plugin root: `{context['plugin_root']}`",
        f"- Plugin build manifest: `{context.get('plugin_build_manifest', 'not-captured')}`",
        f"- Subagent evidence: `{str(state['subagent_evidence']).lower()}`",
        "",
        "## Message",
        "",
        verdict.message,
        "",
        "## Output Snapshot",
        "",
    ])
    if target_claude_files:
        lines.extend(f"- `{item}`" for item in target_claude_files)
    else:
        lines.append("- No `.claude/` output files were detected in target workspace.")
    write_text(report_path, "\n".join(lines) + "\n")


def write_transcript(transcript_path: Path, command: list[str], stdout: str, stderr: str, verdict: RunVerdict, context: Dict[str, Any]) -> None:
    lines = [
        "# Runtime Smoke Transcript",
        "",
        f"- Run ID: `{context['run_id']}`",
        f"- Fixture: `{context['fixture']}`",
        f"- Entry skill: `{context['entry_skill']}`",
        f"- Result: `{verdict.result}`",
        "",
        "## Command",
        "",
        "```bash",
        " ".join(command),
        "```",
        "",
        "## Stdout",
        "",
        "```text",
        stdout.strip() or "<empty>",
        "```",
        "",
        "## Stderr",
        "",
        "```text",
        stderr.strip() or "<empty>",
        "```",
    ]
    write_text(transcript_path, "\n".join(lines) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run runtime smoke validation for WorkflowProgram-CN")
    parser.add_argument("--fixture", default="empty-project", choices=sorted(FIXTURE_PRESETS.keys()))
    parser.add_argument("--entry-skill", help="Override fixture default entry skill")
    parser.add_argument("--request", help="Override fixture default request text")
    parser.add_argument("--claude-bin", default="claude")
    parser.add_argument("--plugin-root", help="Override plugin root, defaults to dist/plugin")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--json", action="store_true", help="Print final summary as JSON")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    plugin_root = Path(args.plugin_root).resolve() if args.plugin_root else (repo_root / "dist" / "plugin").resolve()
    plugin_build_manifest = plugin_root / "build-manifest.json"
    fixture_meta = FIXTURE_PRESETS[args.fixture]
    entry_skill = args.entry_skill or fixture_meta["entry_skill"]
    request = args.request or fixture_meta["request"]
    run_id = make_run_id(args.fixture)

    workspace_root = repo_root / "tests" / "transcripts" / run_id
    target_root = workspace_root / "target"
    run_root = target_root / ".workflowprogram" / "runs" / run_id
    outputs_root = run_root / "outputs"

    context = {
        "run_id": run_id,
        "started_at": iso_now(),
        "plugin_root": str(plugin_root),
        "target_root": str(target_root),
        "fixture": args.fixture,
        "entry_skill": entry_skill,
        "request": request,
        "claude_bin": args.claude_bin,
        "mode": "runtime-smoke",
        "plugin_build_manifest": str(plugin_build_manifest) if plugin_build_manifest.exists() else None,
    }

    def emit(event_type: str, stage: str, status: str, message: str) -> None:
        append_event(
            run_root / "events.jsonl",
            {
                "ts": iso_now(),
                "type": event_type,
                "stage": stage,
                "source": "runtime_smoke",
                "status": status,
                "message": message,
            },
        )
        current = 0
        state_path = run_root / "state.json"
        if state_path.exists():
            current = json.loads(state_path.read_text(encoding="utf-8")).get("events_written", 0)
        update_state(state_path, events_written=current + 1)

    try:
        if not plugin_root.exists():
            raise RuntimeSmokeError(f"Plugin root not found: {plugin_root}")

        workspace_root, target_root = prepare_workspace(repo_root, args.fixture, run_id)
        run_root = target_root / ".workflowprogram" / "runs" / run_id
        outputs_root = run_root / "outputs"
        outputs_root.mkdir(parents=True, exist_ok=True)
        context["target_root"] = str(target_root)
        write_json(run_root / "context.json", context)
        update_state(
            run_root / "state.json",
            run_id=run_id,
            status="initializing",
            stage="prepare",
            result=None,
            category=None,
            subagent_evidence=False,
            events_written=0,
            started_at=context["started_at"],
        )
        emit("RunStarted", "prepare", "ok", f"Preparing fixture {args.fixture}")

        claude_path = shutil.which(args.claude_bin)
        if claude_path is None:
            verdict = RunVerdict(
                result="ENVIRONMENT-SKIP",
                category="CLAUDE_NOT_FOUND",
                message=f"Claude binary not found: {args.claude_bin}",
                is_error=False,
                subagent_evidence=False,
            )
            emit("EnvironmentSkip", "prepare", "warn", verdict.message)
            stdout = ""
            stderr = ""
            command = [args.claude_bin]
            write_text(outputs_root / "stdout.log", stdout)
            write_text(outputs_root / "stderr.log", stderr)
        else:
            update_state(
                run_root / "state.json",
                status="running",
                stage="invoke",
                result=None,
                category=None,
                subagent_evidence=False,
            )
            emit("TaskCreated", "invoke", "ok", f"Invoking /{entry_skill} against copied fixture")
            command = build_command(args.claude_bin, plugin_root, entry_skill, request)

            try:
                completed = subprocess.run(
                    command,
                    cwd=target_root,
                    capture_output=True,
                    text=True,
                    timeout=args.timeout,
                    check=False,
                )
                stdout = completed.stdout
                stderr = completed.stderr
                parsed = read_json_from_output(stdout, stderr)
                verdict = classify_result(stdout, stderr, parsed, completed.returncode)
                if verdict.result == "ENVIRONMENT-SKIP":
                    emit("EnvironmentSkip", "invoke", "warn", verdict.message)
            except subprocess.TimeoutExpired as exc:
                stdout = exc.stdout or ""
                stderr = exc.stderr or ""
                verdict = RunVerdict(
                    result="FAIL",
                    category="RUNTIME_FAILURE",
                    message=f"Claude CLI timed out after {args.timeout}s.",
                    is_error=True,
                    subagent_evidence=False,
                )
                emit("RuntimeError", "invoke", "error", verdict.message)
                command = build_command(args.claude_bin, plugin_root, entry_skill, request)

            emit("TaskCompleted", "invoke", "ok" if not verdict.is_error else "error", verdict.message)

            target_claude_files = snapshot_tree(target_root / ".claude")
            write_json(outputs_root / "target-claude-files.json", {"files": target_claude_files})
            write_json(outputs_root / "target-root-files.json", {"files": snapshot_tree(target_root)})
            if plugin_build_manifest.exists():
                shutil.copy2(plugin_build_manifest, outputs_root / "plugin-build-manifest.json")
                emit("OutputWritten", "invoke", "ok", "Captured plugin build manifest into RUN_ROOT outputs")
            write_text(outputs_root / "stdout.log", stdout)
            write_text(outputs_root / "stderr.log", stderr)
            update_state(
                run_root / "state.json",
                status="completed" if verdict.result != "ENVIRONMENT-SKIP" else "skipped",
                stage="finished",
                result=verdict.result,
                category=verdict.category,
                subagent_evidence=verdict.subagent_evidence,
            )
            write_transcript(run_root / "transcript.md", command, stdout, stderr, verdict, context)
            write_report(run_root / "validation-runtime-report.md", context, verdict, json.loads((run_root / "state.json").read_text(encoding="utf-8")), target_claude_files)
            emit("RunFinished", "finished", "ok" if verdict.result == "PASS" else "warn", f"Run finished with result {verdict.result}")

            summary = {
                "run_id": run_id,
                "fixture": args.fixture,
                "entry_skill": entry_skill,
                "result": verdict.result,
                "category": verdict.category,
                "run_root": str(run_root),
                "target_root": str(target_root),
            }
            if args.json:
                print(json.dumps(summary, ensure_ascii=False, indent=2))
            else:
                print(f"Result: {verdict.result}")
                if verdict.category:
                    print(f"Category: {verdict.category}")
                print(f"Run root: {run_root}")
            return 0 if verdict.result in {"PASS", "ENVIRONMENT-SKIP"} else 1

        # Environment skip path before workspace copy.
        write_text(run_root / "transcript.md", "# Runtime Smoke Transcript\n\nClaude binary was not found.\n")
        update_state(
            run_root / "state.json",
            status="skipped",
            stage="finished",
            result=verdict.result,
            category=verdict.category,
            subagent_evidence=False,
        )
        write_report(run_root / "validation-runtime-report.md", context, verdict, json.loads((run_root / "state.json").read_text(encoding="utf-8")), [])
        emit("RunFinished", "finished", "warn", f"Run finished with result {verdict.result}")
        summary = {
            "run_id": run_id,
            "fixture": args.fixture,
            "entry_skill": entry_skill,
            "result": verdict.result,
            "category": verdict.category,
            "run_root": str(run_root),
            "target_root": str(target_root),
        }
        if args.json:
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        else:
            print(f"Result: {verdict.result}")
            if verdict.category:
                print(f"Category: {verdict.category}")
            print(f"Run root: {run_root}")
        return 0

    except RuntimeSmokeError as exc:
        emit("RuntimeError", "prepare", "error", str(exc))
        update_state(
            run_root / "state.json",
            status="completed",
            stage="finished",
            result="FAIL",
            category="STRUCTURE_FAILURE",
            subagent_evidence=False,
        )
        verdict = RunVerdict(
            result="FAIL",
            category="STRUCTURE_FAILURE",
            message=str(exc),
            is_error=True,
            subagent_evidence=False,
        )
        write_text(run_root / "transcript.md", f"# Runtime Smoke Transcript\n\n{exc}\n")
        write_report(run_root / "validation-runtime-report.md", context, verdict, json.loads((run_root / "state.json").read_text(encoding="utf-8")), [])
        emit("RunFinished", "finished", "error", f"Run finished with result {verdict.result}")
        print(f"Result: {verdict.result}")
        print(f"Category: {verdict.category}")
        print(f"Run root: {run_root}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
