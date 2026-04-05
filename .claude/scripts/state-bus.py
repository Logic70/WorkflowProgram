#!/usr/bin/env python3
"""
Workflow Session State Bus

Lightweight state management for workflow execution.
Supports session persistence, stage transitions, checkpoints, and optional
RUN_ROOT-aligned event emission.

Usage:
    state-bus.py init [--session <path>] [--run-root <path>] [--command <name>]
    state-bus.py write --stage <stage> --key <key> --value <value> [--session <path>] [--run-root <path>]
    state-bus.py read --stage <stage> --key <key> [--session <path>] [--run-root <path>]
    state-bus.py transition --stage <stage> [--session <path>] [--run-root <path>]
    state-bus.py checkpoint --stage <stage> [--turn <n>] [--session <path>] [--run-root <path>]
    state-bus.py restore <checkpoint-id> [--session <path>] [--run-root <path>]
    state-bus.py status [--session <path>] [--run-root <path>]
    state-bus.py history [--session <path>] [--run-root <path>]
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class StateBus:
    """Manages workflow session state and optional event emission."""

    def __init__(self, session_file: Path, event_file: Optional[Path] = None):
        self.session_file = session_file
        self.event_file = event_file
        self.state = self._load_or_init()

    def _load_or_init(self) -> Dict[str, Any]:
        if self.session_file.exists():
            with self.session_file.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        return self._init_state()

    def _run_root(self) -> Optional[Path]:
        if not self.event_file:
            return None
        return self.event_file.parent

    def _init_state(self) -> Dict[str, Any]:
        return {
            "meta": {
                "session_id": str(uuid.uuid4()),
                "version": "1.1",
                "created_at": iso_now(),
                "updated_at": iso_now(),
                "status": "running",
                "command": None,
            },
            "state": {
                "current_stage": None,
                "stage_history": [],
                "turn_count": 0,
                "max_turns": 100,
                "run_root": str(self._run_root()) if self._run_root() else None,
            },
            "data_bus": {},
            "checkpoints": [],
            "debug": {
                "log_level": "info",
                "last_error": None,
                "performance": {
                    "tokens_input": 0,
                    "tokens_output": 0,
                    "api_calls": 0,
                },
            },
        }

    def _save(self) -> None:
        self.state["meta"]["updated_at"] = iso_now()
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        with self.session_file.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(self.state, handle, indent=2, ensure_ascii=False)
            handle.write("\n")

    def _emit_event(
        self,
        event_type: str,
        stage: Optional[str],
        status: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self.event_file:
            return
        payload: Dict[str, Any] = {
            "ts": iso_now(),
            "type": event_type,
            "stage": stage or self.state.get("state", {}).get("current_stage") or "N/A",
            "source": "state-bus",
            "status": status,
            "message": message,
        }
        if extra:
            payload.update(extra)
        self.event_file.parent.mkdir(parents=True, exist_ok=True)
        with self.event_file.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def init(self, command: Optional[str] = None, max_turns: int = 100) -> None:
        self.state = self._init_state()
        if command:
            self.state["meta"]["command"] = command
        self.state["state"]["max_turns"] = max_turns
        self._save()
        self._emit_event(
            "StateBusInit",
            None,
            "ok",
            "Initialized state bus session",
            {
                "command": command,
                "max_turns": max_turns,
                "session_file": str(self.session_file),
            },
        )
        print(f"Session initialized: {self.state['meta']['session_id']}")

    def write(self, stage: str, key: str, value: Any) -> None:
        if stage not in self.state["data_bus"]:
            self.state["data_bus"][stage] = {}
        self.state["data_bus"][stage][key] = value
        self._save()
        self._emit_event(
            "StateBusWrite",
            stage,
            "ok",
            f"Wrote {stage}.{key}",
            {"key": key, "value": value},
        )
        print(f"Written: {stage}.{key}")

    def read(self, stage: str, key: str) -> Optional[Any]:
        return self.state["data_bus"].get(stage, {}).get(key)

    def transition(self, stage: str) -> None:
        previous = self.state["state"]["current_stage"]
        if previous:
            self.state["state"]["stage_history"].append(previous)
        self.state["state"]["current_stage"] = stage
        self.state["state"]["turn_count"] += 1
        self._save()
        self._emit_event(
            "StateBusTransition",
            stage,
            "ok",
            f"Transitioned from {previous or 'start'} to {stage}",
            {
                "previous_stage": previous,
                "turn_count": self.state["state"]["turn_count"],
            },
        )
        print(f"Transitioned: {previous or 'start'} -> {stage}")

    def checkpoint(self, stage: str, turn: Optional[int] = None) -> str:
        turn = turn or self.state["state"]["turn_count"]
        checkpoint_id = f"{stage}-{turn}-{datetime.now().strftime('%H%M%S')}"
        checkpoint_file = self.session_file.parent / "checkpoints" / f"{checkpoint_id}.json"
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        with checkpoint_file.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(self.state, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        self.state["checkpoints"].append(
            {
                "id": checkpoint_id,
                "stage": stage,
                "turn": turn,
                "timestamp": iso_now(),
                "file": str(checkpoint_file),
            }
        )
        self._save()
        self._emit_event(
            "StateBusCheckpoint",
            stage,
            "ok",
            f"Created checkpoint {checkpoint_id}",
            {
                "checkpoint_id": checkpoint_id,
                "checkpoint_file": str(checkpoint_file),
            },
        )
        print(f"Checkpoint created: {checkpoint_id}")
        return checkpoint_id

    def restore(self, checkpoint_id: str) -> bool:
        for checkpoint in self.state["checkpoints"]:
            if checkpoint["id"] == checkpoint_id:
                with Path(checkpoint["file"]).open("r", encoding="utf-8") as handle:
                    self.state = json.load(handle)
                self._save()
                self._emit_event(
                    "StateBusRestore",
                    checkpoint.get("stage"),
                    "ok",
                    f"Restored checkpoint {checkpoint_id}",
                    {"checkpoint_id": checkpoint_id},
                )
                print(f"Restored: {checkpoint_id}")
                return True
        self.state["debug"]["last_error"] = f"Checkpoint not found: {checkpoint_id}"
        self._save()
        self._emit_event(
            "StateBusRestore",
            None,
            "error",
            f"Checkpoint not found: {checkpoint_id}",
            {"checkpoint_id": checkpoint_id},
        )
        print(f"Checkpoint not found: {checkpoint_id}")
        return False

    def status(self) -> None:
        meta = self.state["meta"]
        state = self.state["state"]
        print(f"\nSession: {meta['session_id']}")
        print(f"Command: {meta.get('command', 'N/A')}")
        print(f"Status: {meta['status']}")
        print(f"Current Stage: {state['current_stage'] or 'N/A'}")
        print(f"Stage History: {' -> '.join(state['stage_history'])}")
        print(f"Turn Count: {state['turn_count']}/{state['max_turns']}")
        print(f"Checkpoints: {len(self.state['checkpoints'])}")
        print(f"Session File: {self.session_file}")
        if self.event_file:
            print(f"Event File: {self.event_file}")

    def history(self) -> None:
        print("\nStage Transition History:")
        print("-" * 40)
        for index, stage in enumerate(self.state["state"]["stage_history"], start=1):
            print(f"  Step {index}: {stage}")
        current = self.state["state"]["current_stage"]
        if current:
            print(f"  Current: {current}")

    def list_checkpoints(self) -> None:
        print("\nCheckpoints:")
        print("-" * 60)
        for checkpoint in self.state["checkpoints"]:
            print(f"  {checkpoint['id']}")
            print(f"    Stage: {checkpoint['stage']}, Turn: {checkpoint['turn']}")
            print(f"    Time: {checkpoint['timestamp']}")
            print()


def resolve_paths(args: argparse.Namespace) -> tuple[Path, Optional[Path]]:
    env_session = os.environ.get("WORKFLOWPROGRAM_SESSION_FILE")
    env_run_root = os.environ.get("WORKFLOWPROGRAM_RUN_ROOT")
    run_root_raw = args.run_root or env_run_root
    run_root = Path(run_root_raw).resolve() if run_root_raw else None

    if args.session:
        session_file = Path(args.session).resolve()
    elif env_session:
        session_file = Path(env_session).resolve()
    elif run_root:
        session_file = (run_root / "state-bus" / "session-state.json").resolve()
    else:
        session_file = Path(".workflowprogram/session-state.json").resolve()

    event_file = (run_root / "events.jsonl").resolve() if run_root else None
    return session_file, event_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Workflow Session State Bus")
    parser.add_argument(
        "action",
        choices=["init", "write", "read", "transition", "checkpoint", "restore", "status", "history", "checkpoints"],
    )
    parser.add_argument("checkpoint_id", nargs="?")
    parser.add_argument("--session")
    parser.add_argument("--run-root")
    parser.add_argument("--stage")
    parser.add_argument("--key")
    parser.add_argument("--value")
    parser.add_argument("--turn", type=int)
    parser.add_argument("--command")
    parser.add_argument("--max-turns", type=int, default=100)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    session_file, event_file = resolve_paths(args)
    bus = StateBus(session_file=session_file, event_file=event_file)

    if args.action == "init":
        bus.init(command=args.command, max_turns=args.max_turns)
    elif args.action == "write":
        if not args.stage or not args.key or args.value is None:
            print("Error: write requires --stage, --key, --value")
            return 1
        bus.write(args.stage, args.key, args.value)
    elif args.action == "read":
        if not args.stage or not args.key:
            print("Error: read requires --stage, --key")
            return 1
        value = bus.read(args.stage, args.key)
        print(json.dumps(value, indent=2, ensure_ascii=False))
    elif args.action == "transition":
        if not args.stage:
            print("Error: transition requires --stage")
            return 1
        bus.transition(args.stage)
    elif args.action == "checkpoint":
        if not args.stage:
            print("Error: checkpoint requires --stage")
            return 1
        bus.checkpoint(args.stage, args.turn)
    elif args.action == "restore":
        if not args.checkpoint_id:
            print("Error: restore requires checkpoint_id")
            return 1
        bus.restore(args.checkpoint_id)
    elif args.action == "status":
        bus.status()
    elif args.action == "history":
        bus.history()
    elif args.action == "checkpoints":
        bus.list_checkpoints()
    return 0


if __name__ == "__main__":
    sys.exit(main())
