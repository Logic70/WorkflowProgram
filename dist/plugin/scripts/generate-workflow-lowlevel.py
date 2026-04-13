#!/usr/bin/env python3
# AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY
"""
根据 workflow-spec.yaml 生成目标工作流的维护级 LowLevel 说明。

定位：
- workflow-spec.yaml: 机器可执行真源
- workflow-view.md: 人类只读概览
- workflow-lowlevel.md: 维护/迭代指导，不得覆盖 YAML 语义
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from lib.io_utils import utc_now
from lib.yaml_utils import load_yaml_mapping


REQUIRED_TOP_KEYS = [
    "meta",
    "stages",
    "intent_flows",
    "agent_refs",
    "skills",
    "registry",
    "constraints",
    "resource_limits",
    "runtime_contract",
    "test_contract",
]

GENERATED_LINE_RE = re.compile(
    r"^_Generated at .* from workflow-spec\.yaml \(spec_sha256=([0-9a-f]{64})\)_$",
    re.MULTILINE,
)


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate workflow-lowlevel.md from workflow-spec.yaml")
    parser.add_argument("--spec", default="workflow-spec.yaml", help="Path to workflow-spec.yaml")
    parser.add_argument("--out", default="workflow-lowlevel.md", help="Path to generated workflow-lowlevel.md")
    parser.add_argument("--json", action="store_true", help="Print structured result")
    return parser.parse_args()


def load_spec(path: Path) -> Dict[str, Any]:
    return load_yaml_mapping(path)


def ensure_spec_shape(spec: Dict[str, Any]) -> List[str]:
    missing = [key for key in REQUIRED_TOP_KEYS if key not in spec]
    stages = spec.get("stages")
    if stages is None or not isinstance(stages, list):
        raise ValueError("workflow-spec.yaml field 'stages' must be a list")
    return missing


def format_value(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) if value else "-"
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    if value in (None, ""):
        return "-"
    return str(value)


def render_truth_hierarchy() -> List[str]:
    return [
        "## Truth Hierarchy",
        "",
        "- `workflow-spec.yaml`：唯一机器真源。任何影响执行、校验、阶段流转、输入输出边界的内容都必须先进入这里。",
        "- `workflow-view.md`：从 YAML 单向渲染出的只读概览，便于快速审查，不允许反向改语义。",
        "- `workflow-lowlevel.md`：维护与迭代指导文档，用于解释阶段职责、证据归属和修改方法；不得覆盖 YAML 语义。",
        "",
    ]


def render_meta(meta: Dict[str, Any]) -> List[str]:
    return [
        "## Workflow Identity",
        "",
        f"- name: `{format_value(meta.get('name'))}`",
        f"- version: `{format_value(meta.get('version'))}`",
        f"- target_platform: `{format_value(meta.get('target_platform'))}`",
        f"- source_design: `{format_value(meta.get('source_design'))}`",
        f"- complexity: `{format_value(meta.get('complexity'))}`",
        "",
    ]


def render_intent_flows(spec: Dict[str, Any]) -> List[str]:
    lines: List[str] = ["## Intent Flow Contract", ""]
    intent_flows = spec.get("intent_flows", {})
    if not isinstance(intent_flows, dict) or not intent_flows:
        return lines + ["- None", ""]
    for intent in ("develop", "audit", "iterate", "validate"):
        flow = intent_flows.get(intent, {})
        if not isinstance(flow, dict):
            lines.append(f"- {intent}: invalid")
            continue
        lines.append(
            f"- {intent}: required=`{format_value(flow.get('required_stage_slots', []))}` "
            f"optional=`{format_value(flow.get('optional_stage_slots', []))}`"
        )
    lines.extend(
        [
            "",
            "维护规则：修改某个意图的阶段流时，只能编辑 `workflow-spec.yaml.intent_flows`，再重新生成视图与 LowLevel 文档。",
            "",
        ]
    )
    return lines


def render_stage_guidance(stages: List[Dict[str, Any]]) -> List[str]:
    lines: List[str] = ["## Stage Contracts", ""]
    for stage in stages:
        stage_slot = format_value(stage.get("stage_slot"))
        stage_id = format_value(stage.get("id"))
        stage_name = format_value(stage.get("name"))
        lines.extend(
            [
                f"### `{stage_slot}` · `{stage_id}` · {stage_name}",
                "",
                f"- pattern: `{format_value(stage.get('pattern'))}`",
                f"- agent_ref: `{format_value(stage.get('agent_ref'))}`",
                f"- input: `{format_value(stage.get('input'))}`",
                f"- output: `{format_value(stage.get('output'))}`",
                f"- gate: `{format_value(stage.get('gate'))}`",
                f"- on_approve: `{format_value(stage.get('on_approve'))}`",
                f"- on_reject: `{format_value(stage.get('on_reject'))}`",
                f"- max_retries: `{format_value(stage.get('max_retries'))}`",
                "- 维护说明：若某阶段的输入/输出/转移会影响执行或校验，必须先回写 `workflow-spec.yaml`，不得只改本文档。",
                "",
            ]
        )
    return lines


def render_contract_guide(spec: Dict[str, Any]) -> List[str]:
    runtime_contract = spec.get("runtime_contract", {})
    test_contract = spec.get("test_contract", {})
    write_boundaries = runtime_contract.get("write_boundaries", {}) if isinstance(runtime_contract, dict) else {}
    required_evidence = runtime_contract.get("required_evidence", []) if isinstance(runtime_contract, dict) else []
    failure_kinds = runtime_contract.get("failure_kinds", []) if isinstance(runtime_contract, dict) else []
    return [
        "## Runtime And Test Contract",
        "",
        f"- target_root_allow: `{format_value(write_boundaries.get('target_root_allow', []))}`",
        f"- run_root_allow: `{format_value(write_boundaries.get('run_root_allow', []))}`",
        f"- required_evidence: `{format_value(required_evidence)}`",
        f"- failure_kinds: `{format_value(failure_kinds)}`",
        f"- test_categories: `{format_value([name for name in ('entry', 'boundary', 'flow', 'artifacts', 'failure') if name in test_contract])}`",
        "",
        "维护规则：任何会改变 verdict、边界、证据或失败分类的调整，都必须更新 `workflow-spec.yaml.runtime_contract` 或 `workflow-spec.yaml.test_contract`，而不是只更新解释文字。",
        "",
    ]


def render_delivery_rules() -> List[str]:
    return [
        "## Persistent Design Assets",
        "",
        "- develop 成功后，应把 `workflow-spec.yaml`、`workflow-view.md`、`workflow-lowlevel.md` 持久化到 `TARGET_ROOT/.workflowprogram/design/`。",
        "- 持久化副本属于 WorkflowProgram 托管资产，必须走 managed apply / manifest，而不是直接裸写目标目录。",
        "- 目标侧副本用于后续 audit / iterate / 人工维护理解当前工作流；当前运行的控制面输入仍以 `RUN_ROOT/workflow-spec.yaml` 为准。",
        "",
    ]


def render_maintenance_rules() -> List[str]:
    return [
        "## Maintenance Rules",
        "",
        "- 修改执行语义：先改 `workflow-spec.yaml`，再重新生成 `workflow-view.md` 与 `workflow-lowlevel.md`。",
        "- 修改设计解释：可重生成 `workflow-lowlevel.md`，但不得引入与 YAML 冲突的新约束。",
        "- 修改目标项目资产：必须通过 WorkflowProgram 的 develop / iterate 流程，避免手工破坏 manifest 与边界契约。",
        "- 排查运行问题：先看 `TARGET_ROOT/.workflowprogram/design/`，再看 `RUN_ROOT/state.json`、`events.jsonl`、`validation-runtime-report.md`。",
        "",
    ]


def normalize_lowlevel_content(content: str) -> str:
    normalized = content.replace("\r\n", "\n")
    return GENERATED_LINE_RE.sub(
        r"_Generated at <normalized> from workflow-spec.yaml (spec_sha256=\1)_",
        normalized,
    )


def render_lowlevel(spec: Dict[str, Any], spec_sha256: str, generated_at: str | None = None) -> str:
    lines: List[str] = [
        "# Workflow LowLevel Guide",
        "",
        f"_Generated at {generated_at or utc_now()} from workflow-spec.yaml (spec_sha256={spec_sha256})_",
        "",
        "> 本文件用于维护与迭代指导，不得覆盖 workflow-spec.yaml 语义。",
        "",
    ]
    lines.extend(render_truth_hierarchy())
    lines.extend(render_meta(spec.get("meta", {})))
    lines.extend(render_intent_flows(spec))
    lines.extend(render_stage_guidance(spec.get("stages", [])))
    lines.extend(render_contract_guide(spec))
    lines.extend(render_delivery_rules())
    lines.extend(render_maintenance_rules())
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    spec_path = Path(args.spec).resolve()
    out_path = Path(args.out).resolve()
    payload = {"status": "PASS", "spec": str(spec_path), "out": str(out_path), "missing_top_keys": []}
    try:
        spec = load_spec(spec_path)
        spec_sha256 = sha256_file(spec_path)
        payload["missing_top_keys"] = ensure_spec_shape(spec)
        payload["spec_sha256"] = spec_sha256
        render = render_lowlevel(spec, spec_sha256)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(render, encoding="utf-8", newline="\n")
    except Exception as exc:
        payload["status"] = "FAIL"
        payload["error"] = str(exc)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Error: {exc}")
        return 1

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Generated {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
