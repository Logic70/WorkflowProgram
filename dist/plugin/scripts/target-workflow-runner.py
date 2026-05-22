#!/usr/bin/env python3
# AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY
"""Execute a generated target workflow graph under managed-runtime control."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lib.io_utils import write_json
from lib.yaml_utils import load_yaml_mapping


TERMINALS = {"abort", "end", "done", "complete", "stop", "finish", "success", "failure"}
DETERMINISTIC_PROVIDERS = {"fixture_host", "command_adapter"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a generated target workflow graph")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run target workflow graph")
    run.add_argument("--spec", required=True)
    run.add_argument("--run-root", required=True)
    run.add_argument("--target-root", required=True)
    run.add_argument("--plugin-root", default="")
    run.add_argument("--request", default="")
    run.add_argument("--intent", default="develop")
    run.add_argument("--entry-skill", required=True)
    run.add_argument("--runtime-provider", default="")
    run.add_argument("--provider-command", default="")
    run.add_argument("--claude-bin", default="claude")
    run.add_argument("--auto-approve", action="store_true")
    run.add_argument("--approval-status", default="")
    run.add_argument("--json", action="store_true")

    status = sub.add_parser("status", help="Read target workflow status")
    status.add_argument("--run-root", required=True)
    status.add_argument("--json", action="store_true")
    return parser.parse_args()


def append_event(run_root: Path, event_type: str, **fields: Any) -> None:
    path = run_root / "target-events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"ts": utc_now(), "event": event_type, **fields}
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_rel(path_text: str) -> str:
    cleaned = path_text.strip().replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned


def is_logical_ref(ref: str) -> bool:
    text = ref.strip()
    if not text or text.startswith("$"):
        return True
    if "/" not in text and not text.startswith("."):
        return True
    return False


def existing_file_snapshot(target_root: Path, patterns: List[str]) -> Dict[str, str]:
    snapshot: Dict[str, str] = {}
    if not patterns or not target_root.exists():
        return snapshot
    for path in target_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(target_root).as_posix()
        if any(fnmatch.fnmatch(rel, pattern) for pattern in patterns):
            snapshot[rel] = sha256_file(path)
    return snapshot


def immutable_changes(before: Dict[str, str], after: Dict[str, str]) -> List[str]:
    changes: List[str] = []
    for rel, digest in sorted(before.items()):
        if rel not in after:
            changes.append(f"deleted:{rel}")
        elif after[rel] != digest:
            changes.append(f"modified:{rel}")
    for rel in sorted(set(after) - set(before)):
        changes.append(f"created:{rel}")
    return changes


def collect_registry(spec: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    registry = spec.get("registry", {})
    result: Dict[str, Dict[str, str]] = {}
    if not isinstance(registry, dict):
        return result
    for section, kind in (("commands", "command"), ("skills", "skill"), ("agents", "agent"), ("runtime_assets", "runtime_asset")):
        items = registry.get(section, [])
        if not isinstance(items, list):
            continue
        for raw in items:
            if not isinstance(raw, dict):
                continue
            name = str(raw.get("name", "")).strip()
            file_path = str(raw.get("file", "")).strip()
            if name:
                result[name] = {"kind": kind, "file": file_path}
    return result


def resolve_owner(owner: str, registry: Dict[str, Dict[str, str]], target_root: Path) -> Tuple[bool, Dict[str, str]]:
    owner = owner.strip()
    if owner.startswith("script:"):
        rel = safe_rel(owner[len("script:"):])
        path = target_root / rel
        return path.exists(), {"kind": "script", "file": rel, "name": owner}
    if owner in registry:
        record = dict(registry[owner])
        rel = safe_rel(record.get("file", ""))
        if rel:
            return (target_root / rel).exists(), {"name": owner, **record}
        return True, {"name": owner, **record}
    fallback_paths = [
        (f".claude/skills/{owner}/SKILL.md", "skill"),
        (f".claude/agents/{owner}.md", "agent"),
        (f".claude/commands/{owner}.md", "command"),
    ]
    for rel, kind in fallback_paths:
        if (target_root / rel).exists():
            return True, {"name": owner, "kind": kind, "file": rel}
    return False, {"name": owner, "kind": "unknown", "file": ""}


def materialize_output(target_root: Path, run_root: Path, node: Dict[str, Any], output_ref: str, owner: Dict[str, str], attempt: int) -> Dict[str, Any]:
    rel = safe_rel(output_ref)
    path = target_root / rel
    if output_ref.endswith("/"):
        path.mkdir(parents=True, exist_ok=True)
        marker = path / ".workflowprogram-output"
        marker.write_text(f"node={node['id']}\nowner={owner.get('name', '')}\n", encoding="utf-8", newline="\n")
        digest: Optional[str] = sha256_file(marker)
        kind = "dir"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith(".json"):
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "node_id": node["id"],
                        "owner": owner.get("name", ""),
                        "generated_at": utc_now(),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
        elif rel.endswith((".yaml", ".yml")):
            path.write_text(f"schema_version: 1\nnode_id: {node['id']}\nowner: {owner.get('name', '')}\n", encoding="utf-8", newline="\n")
        elif rel.endswith(".md"):
            path.write_text(f"# {node['id']}\n\nGenerated by `{owner.get('name', '')}`.\n", encoding="utf-8", newline="\n")
        else:
            path.write_text(f"node={node['id']}\nowner={owner.get('name', '')}\n", encoding="utf-8", newline="\n")
        digest = sha256_file(path)
        kind = "file"
    return {
        "path": rel,
        "kind": kind,
        "node_id": node["id"],
        "owner": owner.get("name", ""),
        "owner_kind": owner.get("kind", ""),
        "attempt": attempt,
        "sha256": digest,
        "generated_at": utc_now(),
        "producer": "target-workflow-runner.py",
    }


def execute_script_owner(target_root: Path, owner: Dict[str, str], node: Dict[str, Any], request: str) -> Tuple[bool, str]:
    rel = safe_rel(owner.get("file", ""))
    path = target_root / rel
    completed = subprocess.run(
        [sys.executable, str(path), "--node-id", str(node["id"]), "--request", request],
        cwd=target_root,
        capture_output=True,
        text=True,
        check=False,
    )
    text = completed.stdout.strip() or completed.stderr.strip()
    return completed.returncode == 0, text


def execute_claude_owner(args: argparse.Namespace, target_root: Path, owner: Dict[str, str], node: Dict[str, Any]) -> Tuple[bool, str]:
    prompt = "\n".join(
        [
            "Execute one WorkflowProgram managed-runtime target node.",
            f"Node id: {node['id']}",
            f"Owner: {owner.get('name', '')}",
            f"Owner kind: {owner.get('kind', '')}",
            f"Required outputs: {', '.join(str(item) for item in node.get('output_refs', []))}",
            "Write only the declared outputs. Do not modify runtime/design/config scripts.",
        ]
    )
    completed = subprocess.run(
        [args.claude_bin, "-p", prompt],
        cwd=target_root,
        capture_output=True,
        text=True,
        check=False,
    )
    text = completed.stdout.strip() or completed.stderr.strip()
    return completed.returncode == 0, text


def check_inputs(target_root: Path, node: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    for raw_ref in node.get("input_refs", []):
        ref = str(raw_ref).strip()
        if is_logical_ref(ref):
            continue
        if not (target_root / safe_rel(ref)).exists():
            missing.append(ref)
    return missing


def check_outputs(target_root: Path, node: Dict[str, Any]) -> List[str]:
    missing: List[str] = []
    for raw_ref in node.get("output_refs", []):
        ref = str(raw_ref).strip()
        if is_logical_ref(ref):
            continue
        if not (target_root / safe_rel(ref)).exists():
            missing.append(ref)
    return missing


def transition_map(graph: Dict[str, Any]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    transitions = graph.get("transitions", [])
    if not isinstance(transitions, list):
        return result
    for raw in transitions:
        if not isinstance(raw, dict):
            continue
        source = str(raw.get("from", "")).strip()
        target = str(raw.get("to", "")).strip()
        if source and target and source not in result:
            result[source] = target
    return result


def ordered_nodes(graph: Dict[str, Any], entry_skill: str) -> List[Dict[str, Any]]:
    nodes = [node for node in graph.get("nodes", []) if isinstance(node, dict)]
    node_map = {str(node.get("id", "")).strip(): node for node in nodes}
    entrypoints = graph.get("entrypoints", [])
    entry_node = ""
    if isinstance(entrypoints, list):
        for raw in entrypoints:
            if not isinstance(raw, dict):
                continue
            if str(raw.get("name", "")).strip() == entry_skill:
                entry_node = str(raw.get("node", "")).strip()
                break
        if not entry_node and entrypoints and isinstance(entrypoints[0], dict):
            entry_node = str(entrypoints[0].get("node", "")).strip()
    if not entry_node and nodes:
        entry_node = str(nodes[0].get("id", "")).strip()
    transitions = transition_map(graph)
    if not transitions:
        if entry_node in node_map:
            start_index = next((idx for idx, node in enumerate(nodes) if str(node.get("id", "")).strip() == entry_node), 0)
            return nodes[start_index:]
        return nodes
    result: List[Dict[str, Any]] = []
    current = entry_node
    seen: set[str] = set()
    while current and current not in TERMINALS and current not in seen:
        seen.add(current)
        node = node_map.get(current)
        if node is None:
            break
        result.append(node)
        current = transitions.get(current, "")
    return result


def run_graph(args: argparse.Namespace) -> Dict[str, Any]:
    spec_path = Path(args.spec).resolve()
    run_root = Path(args.run_root).resolve()
    target_root = Path(args.target_root).resolve()
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "outputs" / "stages").mkdir(parents=True, exist_ok=True)

    spec = load_yaml_mapping(spec_path)
    graph = spec.get("workflow_graph", {})
    if not isinstance(graph, dict) or not graph.get("nodes"):
        raise RuntimeError("workflow_graph.nodes is required for target managed runtime")
    policy = spec.get("target_runtime_policy", {})
    if not isinstance(policy, dict):
        policy = {}
    max_retries = policy.get("max_retries_per_node", 0)
    if not isinstance(max_retries, int) or max_retries < 0:
        max_retries = 0
    immutable_patterns = [safe_rel(str(item)) for item in policy.get("immutable_during_run", []) if str(item).strip()] if isinstance(policy.get("immutable_during_run", []), list) else []
    provider = str(args.runtime_provider or "claude_cli").strip()

    registry = collect_registry(spec)
    node_results: List[Dict[str, Any]] = []
    provenance: List[Dict[str, Any]] = []
    status = "PASS"
    failure_kind = "none"
    failure_reason = ""

    append_event(run_root, "TargetRuntimeStarted", status="running", entry_skill=args.entry_skill, provider=provider)
    for node in ordered_nodes(graph, args.entry_skill):
        node_id = str(node.get("id", "")).strip()
        owner_name = str(node.get("owner", "")).strip()
        attempts: List[Dict[str, Any]] = []
        node_status = "FAIL"
        for attempt in range(1, max_retries + 2):
            append_event(run_root, "NodeStarted", node_id=node_id, owner=owner_name, attempt=attempt)
            missing_inputs = check_inputs(target_root, node)
            if missing_inputs:
                attempts.append({"attempt": attempt, "status": "FAIL", "reason": "missing_inputs", "missing_inputs": missing_inputs})
                failure_reason = f"node {node_id} missing inputs: {missing_inputs}"
                break

            owner_ok, owner = resolve_owner(owner_name, registry, target_root)
            if not owner_ok:
                append_event(run_root, "OwnerFailed", node_id=node_id, owner=owner_name, attempt=attempt, reason="owner_not_found")
                attempts.append({"attempt": attempt, "status": "FAIL", "reason": "owner_not_found"})
                failure_reason = f"node {node_id} owner not found: {owner_name}"
                break
            append_event(run_root, "OwnerResolved", node_id=node_id, owner=owner_name, owner_kind=owner.get("kind", ""), attempt=attempt)

            before = existing_file_snapshot(target_root, immutable_patterns)
            if owner.get("kind") == "script":
                owner_success, owner_message = execute_script_owner(target_root, owner, node, args.request)
            elif provider in DETERMINISTIC_PROVIDERS:
                owner_success, owner_message = True, "deterministic provider materialized declared outputs"
                for output_ref in node.get("output_refs", []):
                    ref = str(output_ref).strip()
                    if not is_logical_ref(ref):
                        provenance.append(materialize_output(target_root, run_root, node, ref, owner, attempt))
            else:
                owner_success, owner_message = execute_claude_owner(args, target_root, owner, node)
            after = existing_file_snapshot(target_root, immutable_patterns)
            changes = immutable_changes(before, after)
            missing_outputs = check_outputs(target_root, node)
            if not owner_success:
                attempts.append({"attempt": attempt, "status": "FAIL", "reason": "owner_failed", "message": owner_message})
            elif changes:
                attempts.append({"attempt": attempt, "status": "FAIL", "reason": "immutable_changed", "changes": changes})
            elif missing_outputs:
                attempts.append({"attempt": attempt, "status": "FAIL", "reason": "missing_outputs", "missing_outputs": missing_outputs})
            else:
                node_status = "PASS"
                attempts.append({"attempt": attempt, "status": "PASS", "message": owner_message})
                append_event(run_root, "OwnerCompleted", node_id=node_id, owner=owner_name, attempt=attempt, status="PASS")
                append_event(run_root, "NodeGatePassed", node_id=node_id, gate=str(node.get("gate", "none")).strip() or "none")
                break
            if attempt <= max_retries:
                append_event(run_root, "NodeRetried", node_id=node_id, owner=owner_name, attempt=attempt)

        node_result = {
            "node_id": node_id,
            "owner": owner_name,
            "status": node_status,
            "attempts": attempts,
            "outputs": [safe_rel(str(item)) for item in node.get("output_refs", []) if str(item).strip()],
        }
        node_results.append(node_result)
        if node_status != "PASS":
            status = "FAIL"
            failure_kind = "implementation"
            if not failure_reason and attempts:
                failure_reason = str(attempts[-1].get("reason", "node_failed"))
            append_event(run_root, "NodeGateFailed", node_id=node_id, owner=owner_name, reason=failure_reason or "node_failed")
            break

    append_event(run_root, "TargetRuntimeCompleted", status=status, failure_kind=failure_kind, reason=failure_reason)
    state = {
        "schema_version": 1,
        "schema_name": "target-workflow-runtime-state",
        "run_id": run_root.name,
        "status": status,
        "failure_kind": failure_kind,
        "failure_reason": failure_reason,
        "target_root": str(target_root),
        "spec": str(spec_path),
        "entry_skill": args.entry_skill,
        "provider": provider,
        "node_results_path": "node-results.json",
        "events_path": "target-events.jsonl",
        "artifact_provenance_path": "artifact-provenance.json",
        "updated_at": utc_now(),
    }
    write_json(run_root / "node-results.json", {"schema_version": 1, "nodes": node_results})
    write_json(run_root / "artifact-provenance.json", {"schema_version": 1, "artifacts": provenance})
    write_json(run_root / "target-state.json", state)
    summary = {
        "schema_version": 1,
        "status": status,
        "failure_kind": failure_kind,
        "failure_reason": failure_reason,
        "run_root": str(run_root),
        "target_root": str(target_root),
        "node_count": len(node_results),
        "artifact_count": len(provenance),
    }
    write_json(run_root / "outputs" / "stages" / "target-runtime-summary.json", summary)
    return summary


def write_failure_evidence(args: argparse.Namespace, error: str) -> Dict[str, Any]:
    """Persist a target-runtime failure with the same evidence shape as normal runs."""

    run_root = Path(getattr(args, "run_root", ".")).resolve()
    target_root = Path(getattr(args, "target_root", ".")).resolve()
    spec_path = Path(getattr(args, "spec", "") or ".").resolve()
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "outputs" / "stages").mkdir(parents=True, exist_ok=True)
    if not (run_root / "target-events.jsonl").exists():
        append_event(
            run_root,
            "TargetRuntimeStarted",
            status="failed",
            entry_skill=str(getattr(args, "entry_skill", "")),
            provider=str(getattr(args, "runtime_provider", "") or "unknown"),
        )
    append_event(run_root, "TargetRuntimeCompleted", status="FAIL", failure_kind="implementation", reason=error)
    write_json(run_root / "node-results.json", {"schema_version": 1, "nodes": []})
    write_json(run_root / "artifact-provenance.json", {"schema_version": 1, "artifacts": []})
    state = {
        "schema_version": 1,
        "schema_name": "target-workflow-runtime-state",
        "run_id": run_root.name,
        "status": "FAIL",
        "failure_kind": "implementation",
        "failure_reason": error,
        "target_root": str(target_root),
        "spec": str(spec_path),
        "entry_skill": str(getattr(args, "entry_skill", "")),
        "provider": str(getattr(args, "runtime_provider", "") or "unknown"),
        "node_results_path": "node-results.json",
        "events_path": "target-events.jsonl",
        "artifact_provenance_path": "artifact-provenance.json",
        "updated_at": utc_now(),
    }
    write_json(run_root / "target-state.json", state)
    summary = {
        "schema_version": 1,
        "status": "FAIL",
        "failure_kind": "implementation",
        "failure_reason": error,
        "run_root": str(run_root),
        "target_root": str(target_root),
        "node_count": 0,
        "artifact_count": 0,
    }
    write_json(run_root / "outputs" / "stages" / "target-runtime-summary.json", summary)
    return summary


def command_status(args: argparse.Namespace) -> int:
    run_root = Path(args.run_root).resolve()
    state_path = run_root / "target-state.json"
    if not state_path.exists():
        print(json.dumps({"status": "FAIL", "error": f"target-state.json not found: {state_path}"}, ensure_ascii=False, indent=2))
        return 1
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"[{payload.get('status', 'UNKNOWN')}] {state_path}")
    return 0 if payload.get("status") == "PASS" else 1


def main() -> int:
    args = parse_args()
    if args.command == "status":
        return command_status(args)
    try:
        summary = run_graph(args)
    except Exception as exc:
        payload = write_failure_evidence(args, str(exc))
        payload["error"] = str(exc)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"[{summary['status']}] target runtime run_root={summary['run_root']}")
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
