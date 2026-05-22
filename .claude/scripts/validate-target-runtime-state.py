#!/usr/bin/env python3
"""Validate generated target workflow managed-runtime state and evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


REQUIRED_EVENTS = {"TargetRuntimeStarted", "TargetRuntimeCompleted"}
VALID_STATUS = {"PASS", "WARN", "FAIL", "BLOCKED", "ENVIRONMENT-SKIP"}
VALID_FAILURE_KIND = {"none", "design", "implementation", "environment", "conflict"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate target managed runtime state")
    parser.add_argument("--state", required=True, help="Path to target-state.json")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def load_json(path: Path, errors: List[str]) -> Dict[str, Any]:
    if not path.exists():
        errors.append(f"missing file: {path}")
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"cannot parse JSON {path}: {exc}")
        return {}
    if not isinstance(payload, dict):
        errors.append(f"JSON root must be object: {path}")
        return {}
    return payload


def load_events(path: Path, errors: List[str]) -> List[Dict[str, Any]]:
    if not path.exists():
        errors.append(f"missing file: {path}")
        return []
    events: List[Dict[str, Any]] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSONL event at line {idx}: {exc}")
            continue
        if not isinstance(payload, dict):
            errors.append(f"event line {idx} must be object")
            continue
        events.append(payload)
    return events


def validate_state(state_path: Path) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    state = load_json(state_path, errors)
    run_root = state_path.parent
    status = str(state.get("status", "")).strip()
    failure_kind = str(state.get("failure_kind", "")).strip()
    if state.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if state.get("schema_name") != "target-workflow-runtime-state":
        errors.append("schema_name must be target-workflow-runtime-state")
    if status not in VALID_STATUS:
        errors.append(f"status must be one of {sorted(VALID_STATUS)}")
    if failure_kind not in VALID_FAILURE_KIND:
        errors.append(f"failure_kind must be one of {sorted(VALID_FAILURE_KIND)}")

    node_payload = load_json(run_root / str(state.get("node_results_path", "node-results.json")), errors)
    provenance_payload = load_json(run_root / str(state.get("artifact_provenance_path", "artifact-provenance.json")), errors)
    events = load_events(run_root / str(state.get("events_path", "target-events.jsonl")), errors)
    event_types = {str(item.get("event", "")).strip() for item in events}
    missing_events = sorted(REQUIRED_EVENTS - event_types)
    for event in missing_events:
        errors.append(f"missing lifecycle event: {event}")

    nodes = node_payload.get("nodes", [])
    if not isinstance(nodes, list) or not nodes:
        errors.append("node-results.json.nodes must be a non-empty list")
        nodes = []
    artifacts = provenance_payload.get("artifacts", [])
    if not isinstance(artifacts, list):
        errors.append("artifact-provenance.json.artifacts must be a list")
        artifacts = []
    provenance_paths = {str(item.get("path", "")).strip() for item in artifacts if isinstance(item, dict)}
    for idx, raw_node in enumerate(nodes):
        if not isinstance(raw_node, dict):
            errors.append(f"nodes[{idx}] must be object")
            continue
        node_id = str(raw_node.get("node_id", "")).strip()
        node_status = str(raw_node.get("status", "")).strip()
        if not node_id:
            errors.append(f"nodes[{idx}].node_id is required")
        if node_status not in {"PASS", "FAIL"}:
            errors.append(f"nodes[{idx}].status must be PASS or FAIL")
        if status == "PASS" and node_status != "PASS":
            errors.append(f"PASS target state cannot contain failed node: {node_id}")
        outputs = raw_node.get("outputs", [])
        if not isinstance(outputs, list):
            errors.append(f"nodes[{idx}].outputs must be a list")
            outputs = []
        if status == "PASS":
            for output in outputs:
                rel = str(output).strip()
                if rel and not rel.startswith("$") and "/" in rel and rel not in provenance_paths:
                    errors.append(f"missing artifact provenance for output: {rel}")

    if status == "PASS" and failure_kind != "none":
        errors.append("PASS target state must use failure_kind=none")
    if status != "PASS" and failure_kind == "none":
        warnings.append("non-PASS target state should usually provide a non-none failure_kind")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "state": str(state_path),
    }


def main() -> int:
    args = parse_args()
    payload = validate_state(Path(args.state).resolve())
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"[{payload['status']}] {payload['state']}")
        for error in payload["errors"]:
            print(f"[ERROR] {error}")
        for warning in payload["warnings"]:
            print(f"[WARN] {warning}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
