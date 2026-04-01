#!/usr/bin/env python3
"""
Workflow Session State Bus

Lightweight state management for workflow execution.
Enables checkpointing, debugging, and agent data sharing.

Usage:
    state-bus.py init [--session <name>]
    state-bus.py write <stage> <key> <value>
    state-bus.py read <stage> <key>
    state-bus.py checkpoint <stage> [--turn <n>]
    state-bus.py restore <checkpoint-id>
    state-bus.py status
    state-bus.py history
"""

import json
import uuid
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class StateBus:
    """Manages workflow session state."""

    def __init__(self, session_file: Path):
        self.session_file = session_file
        self.state = self._load_or_init()

    def _load_or_init(self) -> Dict[str, Any]:
        """Load existing state or initialize new session."""
        if self.session_file.exists():
            with open(self.session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self._init_state()

    def _init_state(self) -> Dict[str, Any]:
        """Initialize fresh session state."""
        return {
            "meta": {
                "session_id": str(uuid.uuid4()),
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status": "running",
                "command": None
            },
            "state": {
                "current_stage": None,
                "stage_history": [],
                "turn_count": 0,
                "max_turns": 100
            },
            "data_bus": {},
            "checkpoints": [],
            "debug": {
                "log_level": "info",
                "last_error": None,
                "performance": {
                    "tokens_input": 0,
                    "tokens_output": 0,
                    "api_calls": 0
                }
            }
        }

    def _save(self):
        """Persist state to disk."""
        self.state["meta"]["updated_at"] = datetime.now().isoformat()
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def init(self, command: Optional[str] = None, max_turns: int = 100):
        """Initialize new session."""
        self.state = self._init_state()
        if command:
            self.state["meta"]["command"] = command
        self.state["state"]["max_turns"] = max_turns
        self._save()
        print(f"Session initialized: {self.state['meta']['session_id']}")

    def write(self, stage: str, key: str, value: Any):
        """Write data to stage-specific bus."""
        if stage not in self.state["data_bus"]:
            self.state["data_bus"][stage] = {}
        self.state["data_bus"][stage][key] = value
        self._save()
        print(f"Written: {stage}.{key}")

    def read(self, stage: str, key: str) -> Optional[Any]:
        """Read data from stage-specific bus."""
        return self.state["data_bus"].get(stage, {}).get(key)

    def transition(self, stage: str):
        """Transition to new stage."""
        prev_stage = self.state["state"]["current_stage"]
        if prev_stage:
            self.state["state"]["stage_history"].append(prev_stage)
        self.state["state"]["current_stage"] = stage
        self.state["state"]["turn_count"] += 1
        self._save()
        print(f"Transitioned: {prev_stage or 'start'} -> {stage}")

    def checkpoint(self, stage: str, turn: Optional[int] = None):
        """Create checkpoint for debugging."""
        turn = turn or self.state["state"]["turn_count"]
        checkpoint_id = f"{stage}-{turn}-{datetime.now().strftime('%H%M%S')}"
        checkpoint_file = self.session_file.parent / "checkpoints" / f"{checkpoint_id}.json"
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

        # Save checkpoint
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

        # Add to checkpoint list
        self.state["checkpoints"].append({
            "id": checkpoint_id,
            "stage": stage,
            "turn": turn,
            "timestamp": datetime.now().isoformat(),
            "file": str(checkpoint_file)
        })
        self._save()
        print(f"Checkpoint created: {checkpoint_id}")
        return checkpoint_id

    def restore(self, checkpoint_id: str) -> bool:
        """Restore state from checkpoint."""
        for cp in self.state["checkpoints"]:
            if cp["id"] == checkpoint_id:
                with open(cp["file"], 'r', encoding='utf-8') as f:
                    self.state = json.load(f)
                self._save()
                print(f"Restored: {checkpoint_id}")
                return True
        print(f"Checkpoint not found: {checkpoint_id}")
        return False

    def status(self):
        """Print current session status."""
        meta = self.state["meta"]
        state = self.state["state"]

        print(f"\nSession: {meta['session_id']}")
        print(f"Command: {meta.get('command', 'N/A')}")
        print(f"Status: {meta['status']}")
        print(f"Current Stage: {state['current_stage'] or 'N/A'}")
        print(f"Stage History: {' -> '.join(state['stage_history'])}")
        print(f"Turn Count: {state['turn_count']}/{state['max_turns']}")
        print(f"Checkpoints: {len(self.state['checkpoints'])}")

    def history(self):
        """Print stage transition history."""
        print("\nStage Transition History:")
        print("-" * 40)
        history = self.state["state"]["stage_history"]
        current = self.state["state"]["current_stage"]

        for i, stage in enumerate(history):
            print(f"  Step {i+1}: {stage}")
        if current:
            print(f"  Current: {current}")

    def list_checkpoints(self):
        """List all checkpoints."""
        print("\nCheckpoints:")
        print("-" * 60)
        for cp in self.state["checkpoints"]:
            print(f"  {cp['id']}")
            print(f"    Stage: {cp['stage']}, Turn: {cp['turn']}")
            print(f"    Time: {cp['timestamp']}")
            print()


def main():
    parser = argparse.ArgumentParser(description="Workflow Session State Bus")
    parser.add_argument("action", choices=[
        "init", "write", "read", "transition", "checkpoint",
        "restore", "status", "history", "checkpoints"
    ])
    parser.add_argument("--session", default=".claude/session-state.json")
    parser.add_argument("--stage")
    parser.add_argument("--key")
    parser.add_argument("--value")
    parser.add_argument("--turn", type=int)
    parser.add_argument("--command")
    parser.add_argument("--max-turns", type=int, default=100)
    parser.add_argument("checkpoint_id", nargs="?")

    args = parser.parse_args()

    session_file = Path(args.session)
    bus = StateBus(session_file)

    if args.action == "init":
        bus.init(command=args.command, max_turns=args.max_turns)

    elif args.action == "write":
        if not args.stage or not args.key or not args.value:
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
