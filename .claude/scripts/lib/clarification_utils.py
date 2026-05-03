from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List


PLACEHOLDER_RE = re.compile(r"\bTBD\b|待补", re.IGNORECASE)
NO_VALUE_RE = re.compile(r"^(无|none|n/?a|not applicable|已清空|无阻塞|无阻塞问题|无新增|无修正)$", re.IGNORECASE)
CONFIRMED_STATUS_RE = re.compile(r"^(confirmed|corrected-confirmed|已确认|修正后确认)$", re.IGNORECASE)

REQUIRED_SECTIONS: Dict[str, List[str]] = {
    "User Intent": ["用户诉求", "最终目的", "成功标准"],
    "Clarification Summary": ["澄清轮次", "已确认事项", "已消解歧义"],
    "Trigger Model": ["调用方式", "触发细节"],
    "Inputs": ["必需输入", "可选输入", "所需外部上下文"],
    "Outputs": ["主交付物", "次级产物", "输出格式"],
    "Quality Gates": ["阻塞条件", "必需验证", "完成定义"],
    "Open Questions": ["阻塞未决问题", "可延后问题", "问题处理策略"],
    "Assumptions and Boundaries": ["当前假设", "外部依赖", "关键边界场景", "明确不做"],
    "Target Workflow Graph Readback": ["目标 workflow_graph 节点", "目标 workflow_graph 入口与转移", "目标输出是否已映射到 `registry` 或 `test_contract.artifacts`"],
    "File Plan": ["需要创建的文件", "需要修改的文件"],
    "Readback Confirmation": ["回读摘要", "用户确认状态", "最近修正"],
}

CHALLENGE_ROLE_SPECS: List[Dict[str, str]] = [
    {
        "id": "scenario-extractor",
        "focus": "Identify missing scenarios, edge cases, and workflow output expectations.",
    },
    {
        "id": "assumption-auditor",
        "focus": "Challenge hidden assumptions, dependency gaps, and unclear non-goals.",
    },
    {
        "id": "constraint-reviewer",
        "focus": "Challenge quality gates, stop conditions, and definition-of-done gaps.",
    },
]


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def extract_sections(text: str) -> Dict[str, str]:
    sections: Dict[str, str] = {}
    current = ""
    buffer: List[str] = []
    for line in text.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            if current:
                sections[current] = "\n".join(buffer).strip()
            current = match.group(1).strip()
            buffer = []
            continue
        if current:
            buffer.append(line)
    if current:
        sections[current] = "\n".join(buffer).strip()
    return sections


def section_value(section_text: str, label: str) -> str:
    pattern = re.compile(rf"^- {re.escape(label)}[：:]\s*(.*)$", re.MULTILINE)
    match = pattern.search(section_text)
    if not match:
        return ""
    return match.group(1).strip()


def is_no_value(value: str) -> bool:
    return not value.strip() or bool(NO_VALUE_RE.match(value.strip()))


def split_items(value: str) -> List[str]:
    stripped = value.strip()
    if is_no_value(stripped):
        return []

    items: List[str] = []
    for line in stripped.splitlines():
        line = re.sub(r"^\s*-\s*", "", line).strip()
        if not line:
            continue
        for part in re.split(r"[；;]+", line):
            candidate = part.strip()
            if candidate and not is_no_value(candidate):
                items.append(candidate)
    if not items and stripped:
        items.append(stripped)
    return items


def parse_rounds(value: str) -> int | None:
    try:
        return int(value.strip())
    except Exception:
        return None


def draft_data_from_text(text: str) -> Dict[str, Any]:
    sections = extract_sections(text)

    def field(section: str, label: str) -> str:
        return section_value(sections.get(section, ""), label)

    rounds = parse_rounds(field("Clarification Summary", "澄清轮次"))
    blocking_questions = split_items(field("Open Questions", "阻塞未决问题"))
    deferred_questions = split_items(field("Open Questions", "可延后问题"))
    edge_cases = split_items(field("Assumptions and Boundaries", "关键边界场景"))
    assumptions = split_items(field("Assumptions and Boundaries", "当前假设"))
    external_dependencies = split_items(field("Assumptions and Boundaries", "外部依赖"))
    non_goals = split_items(field("Assumptions and Boundaries", "明确不做"))

    return {
        "sections": sections,
        "workflow_name": field("Workflow Identity", "工作流名称"),
        "trigger_command": field("Workflow Identity", "触发命令"),
        "workflow_summary": field("Workflow Identity", "简要描述"),
        "user_goal": field("User Intent", "用户诉求"),
        "business_purpose": field("User Intent", "最终目的"),
        "success_criteria": split_items(field("User Intent", "成功标准")),
        "clarification_rounds": rounds,
        "confirmed_decisions": split_items(field("Clarification Summary", "已确认事项")),
        "resolved_ambiguities": split_items(field("Clarification Summary", "已消解歧义")),
        "trigger_mode": field("Trigger Model", "调用方式"),
        "trigger_details": field("Trigger Model", "触发细节"),
        "primary_inputs": split_items(field("Inputs", "必需输入")),
        "optional_inputs": split_items(field("Inputs", "可选输入")),
        "external_context": split_items(field("Inputs", "所需外部上下文")),
        "primary_outputs": split_items(field("Outputs", "主交付物")),
        "secondary_outputs": split_items(field("Outputs", "次级产物")),
        "output_formats": split_items(field("Outputs", "输出格式")),
        "blocking_conditions": split_items(field("Quality Gates", "阻塞条件")),
        "required_validations": split_items(field("Quality Gates", "必需验证")),
        "definition_of_done": split_items(field("Quality Gates", "完成定义")),
        "blocking_questions": blocking_questions,
        "deferred_questions": deferred_questions,
        "question_resolution_strategy": field("Open Questions", "问题处理策略"),
        "assumptions": assumptions,
        "external_dependencies": external_dependencies,
        "edge_cases": edge_cases,
        "non_goals": non_goals,
        "readback_summary": field("Readback Confirmation", "回读摘要"),
        "readback_confirmation_status": field("Readback Confirmation", "用户确认状态"),
        "readback_corrections": split_items(field("Readback Confirmation", "最近修正")),
    }


def readiness_report_from_data(data: Dict[str, Any]) -> Dict[str, Any]:
    checks = {
        "goal_defined": bool(data.get("user_goal")),
        "purpose_defined": bool(data.get("business_purpose")),
        "success_criteria_defined": bool(data.get("success_criteria")),
        "trigger_defined": bool(data.get("trigger_mode")) and bool(data.get("trigger_details")),
        "inputs_defined": bool(data.get("primary_inputs")),
        "outputs_defined": bool(data.get("primary_outputs")),
        "quality_gates_defined": bool(data.get("blocking_conditions")) and bool(data.get("required_validations")) and bool(data.get("definition_of_done")),
        "dependencies_defined": bool(data.get("external_dependencies")) or bool(data.get("external_context")),
        "edge_cases_covered": len(data.get("edge_cases", [])) >= 3,
        "readback_confirmed": bool(CONFIRMED_STATUS_RE.match(str(data.get("readback_confirmation_status", "")).strip())),
        "no_blocking_open_questions": len(data.get("blocking_questions", [])) == 0,
        "clarification_rounds_sufficient": isinstance(data.get("clarification_rounds"), int) and int(data.get("clarification_rounds", 0) or 0) >= 2,
    }
    blocking_reasons = [
        name for name, passed in checks.items() if not passed
    ]
    ready = not blocking_reasons
    return {
        "status": "READY" if ready else "BLOCKED",
        "ready": ready,
        "clarification_rounds": data.get("clarification_rounds"),
        "readback_confirmation_status": data.get("readback_confirmation_status"),
        "blocking_checks": checks,
        "blocking_reasons": blocking_reasons,
        "blocking_questions": data.get("blocking_questions", []),
        "deferred_questions": data.get("deferred_questions", []),
    }


def clarification_record_from_data(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "workflow_name": data.get("workflow_name", ""),
        "trigger_command": data.get("trigger_command", ""),
        "workflow_summary": data.get("workflow_summary", ""),
        "user_goal": data.get("user_goal", ""),
        "business_purpose": data.get("business_purpose", ""),
        "success_criteria": data.get("success_criteria", []),
        "clarification_rounds": data.get("clarification_rounds"),
        "confirmed_decisions": data.get("confirmed_decisions", []),
        "resolved_ambiguities": data.get("resolved_ambiguities", []),
        "trigger_mode": data.get("trigger_mode", ""),
        "trigger_details": data.get("trigger_details", ""),
        "primary_inputs": data.get("primary_inputs", []),
        "optional_inputs": data.get("optional_inputs", []),
        "external_context": data.get("external_context", []),
        "primary_outputs": data.get("primary_outputs", []),
        "secondary_outputs": data.get("secondary_outputs", []),
        "output_formats": data.get("output_formats", []),
        "blocking_conditions": data.get("blocking_conditions", []),
        "required_validations": data.get("required_validations", []),
        "definition_of_done": data.get("definition_of_done", []),
        "external_dependencies": data.get("external_dependencies", []),
        "edge_cases": data.get("edge_cases", []),
        "non_goals": data.get("non_goals", []),
        "readback_summary": data.get("readback_summary", ""),
        "readback_confirmation_status": data.get("readback_confirmation_status", ""),
        "readback_corrections": data.get("readback_corrections", []),
    }


def open_questions_from_data(data: Dict[str, Any]) -> Dict[str, Any]:
    blocking = data.get("blocking_questions", [])
    deferred = data.get("deferred_questions", [])
    return {
        "blocking_questions": blocking,
        "deferred_questions": deferred,
        "resolution_strategy": data.get("question_resolution_strategy", ""),
        "blocking_count": len(blocking),
        "deferred_count": len(deferred),
    }


def assumption_log_from_data(data: Dict[str, Any]) -> str:
    def lines_for(title: str, items: List[str]) -> List[str]:
        if not items:
            return [f"## {title}", "", "- 无", ""]
        return [f"## {title}", "", *[f"- {item}" for item in items], ""]

    lines: List[str] = [
        "# Assumption Log",
        "",
        f"- workflow_name: `{data.get('workflow_name', '')}`",
        f"- trigger_command: `{data.get('trigger_command', '')}`",
        "",
    ]
    for title, items in (
        ("Current Assumptions", data.get("assumptions", [])),
        ("External Dependencies", data.get("external_dependencies", [])),
        ("Edge Cases", data.get("edge_cases", [])),
        ("Non-Goals", data.get("non_goals", [])),
    ):
        lines.extend(lines_for(title, items))
    return "\n".join(lines).rstrip() + "\n"


def challenge_questions_for_role(role_id: str, data: Dict[str, Any], readiness: Dict[str, Any]) -> List[str]:
    questions: List[str] = []

    if role_id == "scenario-extractor":
        if len(data.get("edge_cases", [])) < 3:
            questions.append("还缺哪些失败路径、边界场景或明确不自动化的情形？")
        if not data.get("primary_outputs"):
            questions.append("最终要交付哪些主要输出，它们各自的使用者是谁？")
        if not data.get("primary_inputs"):
            questions.append("工作流每次执行时必需输入是什么，哪些输入只在特殊场景下出现？")
    elif role_id == "assumption-auditor":
        if not data.get("external_dependencies") and not data.get("external_context"):
            questions.append("是否依赖外部工具、MCP、skill、权限或上下文文档？")
        if not data.get("non_goals"):
            questions.append("有哪些看起来相关但明确不做的范围，避免后续设计误扩张？")
        if not data.get("assumptions"):
            questions.append("当前设计还在依赖哪些默认假设，需要用户显式确认或修正？")
    elif role_id == "constraint-reviewer":
        if not data.get("blocking_conditions"):
            questions.append("什么情况下工作流必须停止、阻塞或升级给用户处理？")
        if not data.get("required_validations"):
            questions.append("最终必须通过哪些验证或检查，才能算设计完成？")
        if not data.get("definition_of_done"):
            questions.append("完成定义是什么，哪些信号表示工作流已经真的可用？")

    for item in data.get("deferred_questions", []):
        text = str(item).strip()
        if text:
            questions.append(text)

    if readiness.get("ready") and not questions:
        return []
    return questions


def clarification_challenge_report_from_data(data: Dict[str, Any], readiness: Dict[str, Any]) -> Dict[str, Any]:
    review_roles: List[Dict[str, Any]] = []
    lead_backlog: List[str] = []

    for role in CHALLENGE_ROLE_SPECS:
        role_questions = challenge_questions_for_role(role["id"], data, readiness)
        review_roles.append(
            {
                "id": role["id"],
                "focus": role["focus"],
                "direct_user_contact": False,
                "status": "PASS" if not role_questions else "CHALLENGE",
                "proposed_questions": role_questions,
            }
        )
        for question in role_questions:
            if question not in lead_backlog:
                lead_backlog.append(question)

    return {
        "lead_role": "requirement-clarification-lead",
        "review_roles": review_roles,
        "lead_question_backlog": lead_backlog,
        "ready_for_handoff": bool(readiness.get("ready")),
        "blocking_questions_cleared": len(data.get("blocking_questions", [])) == 0,
        "deferred_questions": data.get("deferred_questions", []),
    }


def clarification_handoff_from_data(
    data: Dict[str, Any],
    readiness: Dict[str, Any],
    challenge_report: Dict[str, Any],
    *,
    spec_path: Path,
    run_root: Path,
) -> Dict[str, Any]:
    stages_root = run_root / "outputs" / "stages"
    focus_questions = challenge_report.get("lead_question_backlog", [])
    return {
        "ready": bool(readiness.get("ready")),
        "source_files": {
            "draft": str(spec_path),
            "clarification_record": str(stages_root / "clarification-record.json"),
            "open_questions": str(stages_root / "open-questions.json"),
            "challenge_report": str(stages_root / "clarification-challenge-report.json"),
        },
        "s2_inputs": {
            "research_scope": data.get("primary_outputs", []),
            "external_dependencies": data.get("external_dependencies", []),
            "assumptions": data.get("assumptions", []),
            "edge_cases": data.get("edge_cases", []),
            "focus_questions": focus_questions,
            "non_goals": data.get("non_goals", []),
        },
        "s3_inputs": {
            "success_criteria": data.get("success_criteria", []),
            "trigger_model": {
                "mode": data.get("trigger_mode", ""),
                "details": data.get("trigger_details", ""),
            },
            "io_contract": {
                "primary_inputs": data.get("primary_inputs", []),
                "optional_inputs": data.get("optional_inputs", []),
                "primary_outputs": data.get("primary_outputs", []),
                "secondary_outputs": data.get("secondary_outputs", []),
                "output_formats": data.get("output_formats", []),
            },
            "quality_gates": {
                "blocking_conditions": data.get("blocking_conditions", []),
                "required_validations": data.get("required_validations", []),
                "definition_of_done": data.get("definition_of_done", []),
            },
            "design_constraints": [
                *data.get("blocking_conditions", []),
                *data.get("non_goals", []),
            ],
            "deferred_questions": data.get("deferred_questions", []),
        },
    }


def clarification_evidence_from_data(
    data: Dict[str, Any],
    readiness: Dict[str, Any],
    challenge_report: Dict[str, Any],
    handoff: Dict[str, Any],
) -> Dict[str, Any]:
    review_roles = challenge_report.get("review_roles", [])
    return {
        "clarification_rounds": data.get("clarification_rounds"),
        "challenge_rounds": 1,
        "readback_confirmed": bool(readiness.get("blocking_checks", {}).get("readback_confirmed")),
        "blocking_questions_cleared": bool(challenge_report.get("blocking_questions_cleared")),
        "challenge_roles_executed": [role.get("id") for role in review_roles if role.get("id")],
        "lead_role": challenge_report.get("lead_role"),
        "evidence_checks": {
            "clarification_rounds_sufficient": bool(readiness.get("blocking_checks", {}).get("clarification_rounds_sufficient")),
            "challenge_roles_executed": len([role.get("id") for role in review_roles if role.get("id")]) >= len(CHALLENGE_ROLE_SPECS),
            "readback_confirmed": bool(readiness.get("blocking_checks", {}).get("readback_confirmed")),
            "blocking_questions_cleared": bool(challenge_report.get("blocking_questions_cleared")),
            "s2_handoff_ready": bool(handoff.get("ready")) and bool(handoff.get("s2_inputs")),
            "s3_handoff_ready": bool(handoff.get("ready")) and bool(handoff.get("s3_inputs")),
        },
    }
