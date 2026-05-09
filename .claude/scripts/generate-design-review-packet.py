#!/usr/bin/env python3
"""Generate the S3 design-review packet consumed before S4 implementation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

from lib.io_utils import utc_now, write_json
from lib.reporting import with_report_fields


REQUIRED_ARTIFACTS = {
    "requirements": "outputs/stages/s1-requirements.yaml",
    "context_findings": "outputs/stages/s2-context-findings.yaml",
    "design_highlevel": "outputs/stages/s3-design-highlevel.md",
    "design_lowlevel": "outputs/stages/s3-design-lowlevel.md",
    "acceptance_tests": "outputs/stages/acceptance-tests.yaml",
    "traceability_matrix": "outputs/stages/traceability-matrix.json",
    "implementation_plan": "outputs/stages/s3-implementation-plan.md",
    "workflow_spec": "workflow-spec.yaml",
}

OPTIONAL_ARTIFACTS = {
    "route_intent": "outputs/stages/route-intent.json",
    "change_context": "outputs/stages/change-context.json",
    "existing_workflow_readback": "outputs/stages/existing-workflow-readback.json",
    "change_policy": "outputs/stages/change-policy.json",
    "impact_analysis": "outputs/stages/impact-analysis.json",
    "clarification_handoff": "outputs/stages/clarification-handoff.json",
    "question_backlog": "outputs/stages/question-backlog.json",
    "requirement_logic_map": "outputs/stages/requirement-logic-map.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate WorkflowProgram design-review packet")
    parser.add_argument("--run-root", required=True, help="RUN_ROOT for this develop run")
    parser.add_argument("--target-root", default="", help="Target project root")
    parser.add_argument("--request", default="", help="Original user request")
    parser.add_argument("--out", default="", help="Optional packet output path")
    parser.add_argument("--json", action="store_true", help="Print JSON result")
    return parser.parse_args()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(run_root: Path, rel_path: str, *, required: bool) -> Dict[str, Any]:
    path = run_root / rel_path
    exists = path.exists() and path.is_file()
    return {
        "path": rel_path,
        "required": required,
        "exists": exists,
        "sha256": sha256_file(path),
        "size": path.stat().st_size if exists else None,
    }


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def node_design_records(run_root: Path) -> List[Dict[str, Any]]:
    root = run_root / "outputs" / "stages" / "node-designs"
    if not root.exists():
        return []
    records: List[Dict[str, Any]] = []
    for path in sorted(root.rglob("*.md")):
        rel_path = str(path.relative_to(run_root)).replace("\\", "/")
        records.append(file_record(run_root, rel_path, required=False))
    return records


def build_packet(run_root: Path, target_root: Path | None, request: str) -> Dict[str, Any]:
    required = {name: file_record(run_root, rel, required=True) for name, rel in REQUIRED_ARTIFACTS.items()}
    optional = {name: file_record(run_root, rel, required=False) for name, rel in OPTIONAL_ARTIFACTS.items()}
    node_designs = node_design_records(run_root)
    missing_required = [name for name, item in required.items() if not item["exists"]]
    artifact_fingerprints: Dict[str, str] = {}
    for item in [*required.values(), *optional.values(), *node_designs]:
        if item.get("exists") and item.get("sha256"):
            artifact_fingerprints[str(item["path"])] = str(item["sha256"])

    change_context = load_json(run_root / OPTIONAL_ARTIFACTS["change_context"])
    packet = {
        "schema_version": 1,
        "schema_name": "design-review-packet",
        "generated_at": utc_now(),
        "run_root": str(run_root),
        "target_root": str(target_root) if target_root else "",
        "request": request,
        "required_artifacts": required,
        "optional_artifacts": optional,
        "node_designs": node_designs,
        "artifact_fingerprints": artifact_fingerprints,
        "missing_required": missing_required,
        "change_policy_required": bool(change_context.get("change_policy_required", False)) if change_context else False,
        "review_lenses": [
            "goal_fidelity",
            "requirement_coverage",
            "flow_closure",
            "spec_projection",
            "evidence_quality",
            "change_impact",
            "runtime_compatibility",
            "complexity_control",
            "context_propagation",
        ],
        "status": "PASS" if not missing_required else "FAIL",
    }
    return with_report_fields(
        packet,
        schema_name="design-review-packet",
        error_code=None if not missing_required else "DESIGN_REVIEW_PACKET_INCOMPLETE",
        failure_kind="none" if not missing_required else "design",
        remediation=[
            {
                "code": "COMPLETE_S3_DESIGN_SOURCES",
                "summary": "Regenerate S1/S2/S3 design artifacts before design review.",
            }
        ]
        if missing_required
        else [],
    )


def main() -> int:
    args = parse_args()
    run_root = Path(args.run_root).resolve()
    target_root = Path(args.target_root).resolve() if args.target_root.strip() else None
    out_path = Path(args.out).resolve() if args.out.strip() else run_root / "outputs" / "stages" / "design-review" / "design-review-packet.json"
    packet = build_packet(run_root, target_root, args.request)
    write_json(out_path, packet)
    if args.json:
        print(json.dumps(packet, ensure_ascii=False, indent=2))
    else:
        print(f"{packet['status']} design-review packet: {out_path}")
    return 0 if packet["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
