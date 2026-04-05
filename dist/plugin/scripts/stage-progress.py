#!/usr/bin/env python3
# AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY
"""
Stage progress tracker for WorkflowProgram runs.

This script maintains three runtime progress artifacts under RUN_ROOT:
- outputs/progress/current-progress.json
- outputs/progress/milestones.jsonl
- outputs/progress/user-progress.md
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


VALID_EVENTS = {"StageStarted", "StageCheckpoint", "StageCompleted"}
VALID_STATUS = {"running", "ok", "warn", "error", "blocked"}
VALID_STAGES = {"S0", "S1", "S2", "S3", "S4", "S5", "S6"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_last_milestones(path: Path, limit: int = 3) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    events: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events[-limit:]


def render_user_progress(
    run_root: Path,
    current: Dict[str, Any],
    latest: List[Dict[str, Any]],
) -> str:
    run_id = current.get("run_id", run_root.name)
    lines = [
        "# Workflow Progress",
        "",
        f"- run_id: `{run_id}`",
        f"- current_stage: `{current.get('current_stage', 'unknown')}`",
        f"- current_node: `{current.get('current_node', 'unknown')}`",
        f"- percent: `{current.get('percent', 0)}`",
        f"- last_status: `{current.get('last_status', 'unknown')}`",
        f"- last_verdict: `{current.get('last_verdict', 'unknown')}`",
        f"- updated_at: `{current.get('updated_at', '')}`",
        "",
        "## Recent Milestones",
    ]
    if not latest:
        lines.append("- No milestones yet")
    else:
        for item in latest:
            artifact_refs = item.get("artifact_refs", [])
            refs = ", ".join(artifact_refs) if artifact_refs else "-"
            lines.append(
                f"- [{item.get('stage','?')}/{item.get('node','?')}] "
                f"{item.get('event','?')} | {item.get('status','?')} | "
                f"{item.get('result','')} | refs: {refs}"
            )

    next_action = current.get("next_action")
    if next_action:
        lines.extend(["", "## Next Action", f"- {next_action}"])
    return "\n".join(lines) + "\n"


@dataclass
class ProgressPaths:
    current_json: Path
    milestones_jsonl: Path
    user_progress_md: Path


def progress_paths(run_root: Path) -> ProgressPaths:
    progress_root = run_root / "outputs" / "progress"
    return ProgressPaths(
        current_json=progress_root / "current-progress.json",
        milestones_jsonl=progress_root / "milestones.jsonl",
        user_progress_md=progress_root / "user-progress.md",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update WorkflowProgram stage progress artifacts")
    sub = parser.add_subparsers(dest="command", required=True)

    update = sub.add_parser("update", help="Update current progress and append one milestone event")
    update.add_argument("--run-root", required=True, help="Absolute path to RUN_ROOT")
    update.add_argument("--stage", required=True, choices=sorted(VALID_STAGES))
    update.add_argument("--node", required=True, help="Current node id")
    update.add_argument("--event", required=True, choices=sorted(VALID_EVENTS))
    update.add_argument("--status", required=True, choices=sorted(VALID_STATUS))
    update.add_argument("--result", default="", help="Short result summary")
    update.add_argument("--percent", type=int, default=None, help="Current completion percentage")
    update.add_argument("--next-action", default="", help="Suggested next action")
    update.add_argument("--artifact-ref", action="append", default=[], help="Artifact ref path")
    update.add_argument("--verdict", default="", help="Optional verdict such as PASS/WARN/FAIL")
    update.add_argument("--json", action="store_true", help="Print JSON result")
    return parser.parse_args()


def command_update(args: argparse.Namespace) -> int:
    run_root = Path(args.run_root).resolve()
    paths = progress_paths(run_root)
    now = utc_now()

    current = safe_read_json(paths.current_json)
    run_id = current.get("run_id", run_root.name)

    percent = args.percent if args.percent is not None else current.get("percent", 0)
    verdict = args.verdict or current.get("last_verdict", "unknown")

    current.update(
        {
            "run_id": run_id,
            "current_stage": args.stage,
            "current_node": args.node,
            "percent": percent,
            "last_status": args.status,
            "last_verdict": verdict,
            "next_action": args.next_action or current.get("next_action", ""),
            "updated_at": now,
        }
    )
    write_json(paths.current_json, current)

    milestone = {
        "ts": now,
        "stage": args.stage,
        "node": args.node,
        "event": args.event,
        "status": args.status,
        "result": args.result,
        "artifact_refs": args.artifact_ref,
    }
    append_jsonl(paths.milestones_jsonl, milestone)

    latest = read_last_milestones(paths.milestones_jsonl, limit=3)
    user_md = render_user_progress(run_root, current, latest)
    paths.user_progress_md.parent.mkdir(parents=True, exist_ok=True)
    paths.user_progress_md.write_text(user_md, encoding="utf-8")

    output = {
        "run_root": str(run_root),
        "current_progress": str(paths.current_json),
        "milestones": str(paths.milestones_jsonl),
        "user_progress": str(paths.user_progress_md),
        "event": milestone,
    }
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(
            f"[{args.stage}] {args.node} {args.event} -> {args.status}; "
            f"progress={percent}%"
        )
    return 0


def main() -> int:
    args = parse_args()
    if args.command == "update":
        return command_update(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

