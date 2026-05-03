#!/usr/bin/env python3
"""校验人类可读的 WorkflowProgram S1 草案规格及其结构化澄清包。

该校验器覆盖的核心段落包括：
- User Intent
- Clarification Summary
- Trigger Model
- Open Questions
- Readback Confirmation
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

from lib.clarification_utils import (
    CONFIRMED_STATUS_RE,
    PLACEHOLDER_RE,
    REQUIRED_SECTIONS,
    draft_data_from_text,
    extract_sections,
    load_json,
    load_text,
    readiness_report_from_data,
    section_value,
    split_items,
)


def validate_draft(path: Path, run_root: Path | None = None) -> Dict[str, object]:
    """按强制质量门禁校验人工编写的 S1 草案。"""
    errors: List[str] = []
    warnings: List[str] = []
    if not path.exists():
        return {
            "status": "FAIL",
            "errors": [f"workflow draft not found: {path}"],
            "warnings": warnings,
            "spec": str(path),
        }

    text = load_text(path)
    # 先做全文占位符扫描；即使章节结构完整，残留 TBD/待补 也必须拦住。
    if PLACEHOLDER_RE.search(text):
        errors.append("workflow-spec.md contains unresolved placeholders (TBD/待补)")

    sections = extract_sections(text)
    for section_name, labels in REQUIRED_SECTIONS.items():
        block = sections.get(section_name, "")
        if not block:
            errors.append(f"missing required section: {section_name}")
            continue
        for label in labels:
            value = section_value(block, label)
            if not value:
                errors.append(f"section '{section_name}' is missing a non-empty value for '{label}'")
                continue
            if PLACEHOLDER_RE.search(value):
                errors.append(f"section '{section_name}' field '{label}' contains unresolved placeholders")

    data = draft_data_from_text(text)
    clarification_block = sections.get("Clarification Summary", "")
    if clarification_block:
        rounds = data.get("clarification_rounds")
        if rounds is None:
            errors.append("section 'Clarification Summary' field '澄清轮次' must be an integer")
        elif int(rounds) < 2:
            errors.append("section 'Clarification Summary' field '澄清轮次' must be >= 2")

    edge_cases = data.get("edge_cases", [])
    if len(edge_cases) < 3:
        errors.append("section 'Assumptions and Boundaries' field '关键边界场景' must list at least 3 edge cases or boundaries")

    readback_status = str(data.get("readback_confirmation_status", "")).strip()
    if not CONFIRMED_STATUS_RE.match(readback_status):
        errors.append("section 'Readback Confirmation' field '用户确认状态' must be a confirmed status")

    blocking_questions = data.get("blocking_questions", [])
    if blocking_questions:
        errors.append("section 'Open Questions' field '阻塞未决问题' must be empty before S1 can be treated as complete")

    deferred_questions = data.get("deferred_questions", [])
    resolution_strategy = str(data.get("question_resolution_strategy", "")).strip()
    if deferred_questions and not resolution_strategy:
        errors.append("section 'Open Questions' field '问题处理策略' must explain how deferred questions are handled")

    readiness_expected = readiness_report_from_data(data)

    if run_root is not None:
        stages_root = run_root / "outputs" / "stages"
        clarification_record_path = stages_root / "clarification-record.json"
        open_questions_path = stages_root / "open-questions.json"
        assumption_log_path = stages_root / "assumption-log.md"
        readiness_report_path = stages_root / "design-readiness-report.json"
        challenge_report_path = stages_root / "clarification-challenge-report.json"
        handoff_path = stages_root / "clarification-handoff.json"
        evidence_path = stages_root / "clarification-evidence.json"

        if not clarification_record_path.exists():
            errors.append(f"clarification record not found: {clarification_record_path}")
        if not open_questions_path.exists():
            errors.append(f"open questions file not found: {open_questions_path}")
        if not assumption_log_path.exists():
            errors.append(f"assumption log not found: {assumption_log_path}")
        if not readiness_report_path.exists():
            errors.append(f"design readiness report not found: {readiness_report_path}")
        if not challenge_report_path.exists():
            errors.append(f"clarification challenge report not found: {challenge_report_path}")
        if not handoff_path.exists():
            errors.append(f"clarification handoff not found: {handoff_path}")
        if not evidence_path.exists():
            errors.append(f"clarification evidence not found: {evidence_path}")

        record = load_json(clarification_record_path)
        if clarification_record_path.exists():
            for key in (
                "user_goal",
                "business_purpose",
                "success_criteria",
                "trigger_mode",
                "primary_inputs",
                "primary_outputs",
                "blocking_conditions",
                "external_dependencies",
                "edge_cases",
                "non_goals",
                "readback_summary",
                "readback_confirmation_status",
            ):
                if key not in record:
                    errors.append(f"clarification-record.json is missing key '{key}'")
            if record and str(record.get("user_goal", "")).strip() != str(data.get("user_goal", "")).strip():
                errors.append("clarification-record.json user_goal does not match workflow-spec.md")

        open_questions = load_json(open_questions_path)
        if open_questions_path.exists():
            if not isinstance(open_questions.get("blocking_questions", None), list):
                errors.append("open-questions.json must contain a blocking_questions list")
            if not isinstance(open_questions.get("deferred_questions", None), list):
                errors.append("open-questions.json must contain a deferred_questions list")
            if int(open_questions.get("blocking_count", 0) or 0) != len(open_questions.get("blocking_questions", [])):
                errors.append("open-questions.json blocking_count must match blocking_questions length")
            if int(open_questions.get("deferred_count", 0) or 0) != len(open_questions.get("deferred_questions", [])):
                errors.append("open-questions.json deferred_count must match deferred_questions length")
            if open_questions.get("blocking_questions"):
                errors.append("open-questions.json must not contain blocking questions for a completed S1 package")

        assumption_log = load_text(assumption_log_path)
        if assumption_log_path.exists():
            for heading in ("# Assumption Log", "## Current Assumptions", "## External Dependencies", "## Edge Cases", "## Non-Goals"):
                if heading not in assumption_log:
                    errors.append(f"assumption-log.md is missing heading '{heading}'")

        readiness_report = load_json(readiness_report_path)
        if readiness_report_path.exists():
            if readiness_report.get("status") != "READY" or readiness_report.get("ready") is not True:
                errors.append("design-readiness-report.json must mark the request as READY before S1 is considered complete")
            expected_checks = readiness_expected.get("blocking_checks", {})
            actual_checks = readiness_report.get("blocking_checks", {})
            if expected_checks and actual_checks != expected_checks:
                errors.append("design-readiness-report.json blocking_checks do not match workflow-spec.md derived readiness state")

        challenge_report = load_json(challenge_report_path)
        if challenge_report_path.exists():
            if challenge_report.get("lead_role") != "requirement-clarification-lead":
                errors.append("clarification-challenge-report.json must set lead_role=requirement-clarification-lead")
            review_roles = challenge_report.get("review_roles", [])
            if not isinstance(review_roles, list) or len(review_roles) < 3:
                errors.append("clarification-challenge-report.json must contain at least 3 review roles")
            else:
                for role in review_roles:
                    if not isinstance(role, dict):
                        errors.append("clarification-challenge-report.json review_roles entries must be mapping objects")
                        continue
                    if role.get("direct_user_contact") is not False:
                        errors.append("clarification-challenge-report.json review roles must not speak to the user directly")
            if challenge_report.get("ready_for_handoff") is not True:
                errors.append("clarification-challenge-report.json must mark ready_for_handoff=true for a completed S1 package")

        handoff = load_json(handoff_path)
        if handoff_path.exists():
            if handoff.get("ready") is not True:
                errors.append("clarification-handoff.json must mark ready=true before S2/S3 consume it")
            source_files = handoff.get("source_files", {})
            if not isinstance(source_files, dict) or "draft" not in source_files or "clarification_record" not in source_files:
                errors.append("clarification-handoff.json must include deterministic source_files references")
            if not isinstance(handoff.get("s2_inputs", None), dict) or not handoff.get("s2_inputs"):
                errors.append("clarification-handoff.json must contain non-empty s2_inputs")
            if not isinstance(handoff.get("s3_inputs", None), dict) or not handoff.get("s3_inputs"):
                errors.append("clarification-handoff.json must contain non-empty s3_inputs")

        evidence = load_json(evidence_path)
        if evidence_path.exists():
            if evidence.get("clarification_rounds") != data.get("clarification_rounds"):
                errors.append("clarification-evidence.json clarification_rounds must match workflow-spec.md")
            if int(evidence.get("challenge_rounds", 0) or 0) < 1:
                errors.append("clarification-evidence.json challenge_rounds must be >= 1")
            if evidence.get("readback_confirmed") is not True:
                errors.append("clarification-evidence.json must record readback_confirmed=true")
            challenge_roles = evidence.get("challenge_roles_executed", [])
            if not isinstance(challenge_roles, list) or len(challenge_roles) < 3:
                errors.append("clarification-evidence.json must record at least 3 executed challenge roles")
            checks = evidence.get("evidence_checks", {})
            if not isinstance(checks, dict):
                errors.append("clarification-evidence.json must contain evidence_checks")
            else:
                for key in (
                    "clarification_rounds_sufficient",
                    "challenge_roles_executed",
                    "readback_confirmed",
                    "blocking_questions_cleared",
                    "s2_handoff_ready",
                    "s3_handoff_ready",
                ):
                    if checks.get(key) is not True:
                        errors.append(f"clarification-evidence.json evidence_checks.{key} must be true")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "spec": str(path),
        "run_root": str(run_root) if run_root else None,
    }


def parse_args() -> argparse.Namespace:
    """解析草案校验所需的命令行参数。"""
    parser = argparse.ArgumentParser(description="Validate WorkflowProgram workflow-spec.md draft quality gates")
    parser.add_argument("--spec", required=True, help="Path to workflow-spec.md")
    parser.add_argument("--run-root", help="Optional RUN_ROOT path for validating the structured clarification package")
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    return parser.parse_args()


def main() -> int:
    """执行校验并输出结构化或可读诊断结果。"""
    args = parse_args()
    payload = validate_draft(
        Path(args.spec).resolve(),
        Path(args.run_root).resolve() if args.run_root else None,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"[{payload['status']}] {payload['spec']}")
        for item in payload["errors"]:
            print(f"- ERROR: {item}")
        for item in payload["warnings"]:
            print(f"- WARN: {item}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
