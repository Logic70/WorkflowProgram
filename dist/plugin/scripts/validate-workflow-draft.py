#!/usr/bin/env python3
# AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY
"""
校验人类可读的 WorkflowProgram S1 草案规格。
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List


PLACEHOLDER_RE = re.compile(r"\bTBD\b|待补", re.IGNORECASE)
REQUIRED_SECTIONS: Dict[str, List[str]] = {
    "User Intent": ["用户诉求", "最终目的", "成功标准"],
    "Clarification Summary": ["澄清轮次", "已确认事项", "已消解歧义"],
    "Trigger Model": ["调用方式", "触发细节"],
    "Inputs": ["必需输入", "可选输入", "所需外部上下文"],
    "Outputs": ["主交付物", "次级产物", "输出格式"],
    "Quality Gates": ["阻塞条件", "必需验证", "完成定义"],
}


def load_text(path: Path) -> str:
    """返回草案内容；如果文件不存在则返回空字符串。"""
    return path.read_text(encoding="utf-8") if path.exists() else ""


def extract_sections(text: str) -> Dict[str, str]:
    """把 Markdown 草案按二级标题拆成多个区段。"""
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
    """从区段内容中提取 `- label: value` 形式的字段。"""
    pattern = re.compile(rf"^- {re.escape(label)}[：:]\s*(.*)$", re.MULTILINE)
    match = pattern.search(section_text)
    if not match:
        return ""
    return match.group(1).strip()


def validate_draft(path: Path) -> Dict[str, object]:
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

    clarification_block = sections.get("Clarification Summary", "")
    if clarification_block:
        rounds_text = section_value(clarification_block, "澄清轮次")
        try:
            rounds = int(rounds_text)
        except ValueError:
            errors.append("section 'Clarification Summary' field '澄清轮次' must be an integer")
        else:
            if rounds < 2:
                errors.append("section 'Clarification Summary' field '澄清轮次' must be >= 2")

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "spec": str(path),
    }


def parse_args() -> argparse.Namespace:
    """解析草案校验所需的命令行参数。"""
    parser = argparse.ArgumentParser(description="Validate WorkflowProgram workflow-spec.md draft quality gates")
    parser.add_argument("--spec", required=True, help="Path to workflow-spec.md")
    parser.add_argument("--json", action="store_true", help="Print JSON payload")
    return parser.parse_args()


def main() -> int:
    """执行校验并输出结构化或可读诊断结果。"""
    args = parse_args()
    payload = validate_draft(Path(args.spec).resolve())
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
