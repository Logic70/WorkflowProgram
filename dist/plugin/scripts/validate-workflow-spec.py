#!/usr/bin/env python3
# AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY
"""
按 WorkflowProgram 的低层契约校验 workflow-spec.yaml。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

from lib.diagnostics import DiagnosticCollector
from lib.spec_utils import stage_slot_id_map
from lib.yaml_utils import load_yaml_mapping


REQUIRED_TOP_KEYS = {
    "meta",
    "stages",
    "intent_flows",
    "agent_refs",
    "skills",
    "registry",
    "constraints",
    "resource_limits",
    "runtime_contract",
    "generated_runtime_contract",
    "test_contract",
}

REQUIRED_META_KEYS = {
    "name",
    "version",
    "target_platform",
    "source_design",
    "complexity",
}

VALID_COMPLEXITY = {"S", "M", "L", "XL"}
VALID_INTENT = {"develop", "audit", "iterate", "validate"}
VALID_STAGE_SLOTS = {"S1", "S2", "S3", "S4", "S5", "S6"}
REQUIRED_STAGE_SLOT_ORDER = ["S1", "S2", "S3", "S4", "S5", "S6"]
VALID_PATTERNS = {
    "Sequential",
    "Fan-out/Fan-in",
    "Explore",
    "Event-Driven",
    "Test-Driven",
    "Specialized",
    "Specialized Agent",
}
VALID_TERMINALS = {"abort", "end", "done", "complete", "stop", "finish"}
VALID_VERDICT = {"PASS", "WARN", "FAIL", "ENVIRONMENT-SKIP"}
VALID_STAGE_STATUS = {"running", "blocked", "failed", "done"}
REQUIRED_FAILURE_KINDS = {"none", "design", "implementation", "environment", "conflict"}
VALID_ENV_SKIP_CHECKS = {
    "runtime_host_available",
    "runtime_host_ready",
    "target_root_writable",
}
DEPRECATED_ENV_SKIP_CHECKS = {
    "claude_cli_available",
    "claude_cli_logged_in",
}
REQUIRED_RUNTIME_CONTRACT_KEYS = {"write_boundaries", "required_evidence", "failure_kinds", "environment_skip"}
REQUIRED_GENERATED_RUNTIME_KEYS = {
    "runtime_root",
    "design_spec_path",
    "entry_script",
    "runner_script",
    "state_validator_script",
    "runtime_manifest",
    "run_root_dir",
    "mode",
}
VALID_ENTRY_TYPES = {"slash_command", "natural_language", "hybrid"}
RUNTIME_REF_PATTERN = re.compile(r"^runtime_contract\.([A-Za-z_][A-Za-z0-9_]*)$")


def parse_args() -> argparse.Namespace:
    """解析独立 spec 校验所需的命令行参数。"""

    parser = argparse.ArgumentParser(description="Validate workflow-spec.yaml")
    parser.add_argument("--spec", required=True, help="Path to workflow-spec.yaml")
    parser.add_argument("--json", action="store_true", help="Print structured report")
    return parser.parse_args()


def add_error(errors: List[str], msg: str) -> None:
    """追加一条 schema 错误信息。"""

    errors.append(msg)


def add_warn(warnings: List[str], msg: str) -> None:
    """追加一条不阻塞执行的 schema warning。"""

    warnings.append(msg)


def require_mapping(value: Any, field: str, errors: List[str]) -> Dict[str, Any]:
    """要求字段必须是 mapping/object，同时尽量保持校验器继续运行。"""

    if isinstance(value, dict):
        return value
    add_error(errors, f"{field} must be a mapping/object")
    return {}


def require_list(value: Any, field: str, errors: List[str]) -> List[Any]:
    """要求字段必须是列表，同时尽量保持校验器继续运行。"""

    if isinstance(value, list):
        return value
    add_error(errors, f"{field} must be a list")
    return []


def validate_top_level(spec: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """校验顶层控制面区段是否齐全。"""

    missing = sorted(REQUIRED_TOP_KEYS - set(spec.keys()))
    for key in missing:
        add_error(errors, f"Missing top-level key: {key}")
    extra = sorted(set(spec.keys()) - REQUIRED_TOP_KEYS)
    if extra:
        add_warn(warnings, f"Extra top-level keys: {', '.join(extra)}")


def validate_meta(meta: Dict[str, Any], errors: List[str]) -> None:
    """校验用于标识 workflow spec 本身的元数据。"""

    missing = sorted(REQUIRED_META_KEYS - set(meta.keys()))
    for key in missing:
        add_error(errors, f"meta.{key} is required")

    complexity = str(meta.get("complexity", ""))
    if complexity and complexity not in VALID_COMPLEXITY:
        add_error(errors, f"meta.complexity must be one of {sorted(VALID_COMPLEXITY)}")


def validate_stages(
    stages: List[Any],
    agent_refs: Set[str],
    errors: List[str],
    warnings: List[str],
) -> Set[str]:
    """校验可执行阶段声明及其局部不变量。

    这里强制执行显式 `stage_slot` 模型，避免后续脚本再根据位置猜逻辑阶段。
    """

    stage_ids: Set[str] = set()
    transition_refs: List[str] = []
    observed_slots: List[str] = []
    seen_slots: Set[str] = set()

    if not stages:
        add_error(errors, "stages must not be empty")
        return stage_ids

    for idx, raw_stage in enumerate(stages):
        prefix = f"stages[{idx}]"
        stage = require_mapping(raw_stage, prefix, errors)
        stage_id = str(stage.get("id", "")).strip()
        stage_slot = str(stage.get("stage_slot", "")).strip()
        stage_name = str(stage.get("name", "")).strip()
        pattern = str(stage.get("pattern", "")).strip()

        if not stage_id:
            add_error(errors, f"{prefix}.id is required")
        elif not re.match(r"^[A-Za-z0-9_-]+$", stage_id):
            add_error(errors, f"{prefix}.id has invalid format: {stage_id}")
        elif stage_id in stage_ids:
            add_error(errors, f"Duplicate stage id: {stage_id}")
        else:
            stage_ids.add(stage_id)

        if not stage_name:
            add_error(errors, f"{prefix}.name is required")

        if not stage_slot:
            add_error(errors, f"{prefix}.stage_slot is required")
        elif stage_slot not in VALID_STAGE_SLOTS:
            add_error(errors, f"{prefix}.stage_slot must be one of {REQUIRED_STAGE_SLOT_ORDER}")
        elif stage_slot in seen_slots:
            add_error(errors, f"Duplicate stage_slot: {stage_slot}")
        else:
            seen_slots.add(stage_slot)
            observed_slots.append(stage_slot)

        if not pattern:
            add_error(errors, f"{prefix}.pattern is required")
        elif pattern not in VALID_PATTERNS:
            add_error(errors, f"{prefix}.pattern must be one of {sorted(VALID_PATTERNS)}")

        agent_ref = stage.get("agent_ref")
        if agent_ref is not None:
            agent_ref_str = str(agent_ref).strip()
            if agent_ref_str and agent_ref_str not in agent_refs:
                add_error(errors, f"{prefix}.agent_ref '{agent_ref_str}' not found in agent_refs")

        if "max_retries" in stage:
            value = stage["max_retries"]
            if not isinstance(value, int) or value < 0:
                add_error(errors, f"{prefix}.max_retries must be a non-negative integer")

        gate = stage.get("gate")
        if gate is not None and str(gate).strip() and str(gate) != "user_approval":
            add_warn(warnings, f"{prefix}.gate is uncommon: {gate}")

        for tkey in ("on_approve", "on_reject"):
            target = stage.get(tkey)
            if target is None:
                continue
            target_str = str(target).strip()
            if not target_str:
                continue
            transition_refs.append(target_str)

        steps = stage.get("steps")
        if steps is not None:
            if not isinstance(steps, list):
                add_error(errors, f"{prefix}.steps must be a list")
            elif not steps:
                add_warn(warnings, f"{prefix}.steps is empty")

        actions = stage.get("actions")
        if actions is not None:
            if not isinstance(actions, list):
                add_error(errors, f"{prefix}.actions must be a list")
            elif not actions:
                add_warn(warnings, f"{prefix}.actions is empty")

        output = stage.get("output")
        if output is None:
            add_warn(warnings, f"{prefix}.output is empty; recommend declaring explicit outputs")

    for ref in transition_refs:
        if ref not in stage_ids and ref not in VALID_TERMINALS:
            add_error(errors, f"Transition target '{ref}' is neither a stage id nor terminal {sorted(VALID_TERMINALS)}")

    missing_slots = [slot for slot in REQUIRED_STAGE_SLOT_ORDER if slot not in seen_slots]
    if missing_slots:
        add_error(errors, f"stages missing required stage_slot values: {', '.join(missing_slots)}")
    if observed_slots and observed_slots != REQUIRED_STAGE_SLOT_ORDER:
        add_error(errors, f"stages must appear in stage_slot order: {', '.join(REQUIRED_STAGE_SLOT_ORDER)}")

    return stage_ids


def validate_agent_refs(agent_refs: List[Any], errors: List[str]) -> Set[str]:
    """校验声明的可复用 agent 引用。"""

    names: Set[str] = set()
    if not agent_refs:
        add_error(errors, "agent_refs must not be empty")
        return names
    for idx, item in enumerate(agent_refs):
        text = str(item).strip()
        if not text:
            add_error(errors, f"agent_refs[{idx}] must not be empty")
            continue
        if text in names:
            add_error(errors, f"Duplicate agent ref: {text}")
            continue
        names.add(text)
    return names


def validate_skills(skills: List[Any], errors: List[str]) -> None:
    """校验 spec 中声明的逻辑 skill 列表。"""

    names: Set[str] = set()
    for idx, item in enumerate(skills):
        prefix = f"skills[{idx}]"
        if isinstance(item, dict):
            name = str(item.get("name", "")).strip()
        else:
            name = str(item).strip()
        if not name:
            add_error(errors, f"{prefix}.name is required")
            continue
        if name in names:
            add_error(errors, f"Duplicate skill name in spec: {name}")
            continue
        names.add(name)


def validate_registry(registry: Dict[str, Any], errors: List[str]) -> None:
    """校验 spec 中声明的目标 `.claude` registry 条目。"""

    commands = require_list(registry.get("commands", []), "registry.commands", errors)
    skills = require_list(registry.get("skills", []), "registry.skills", errors)

    for idx, item in enumerate(commands):
        prefix = f"registry.commands[{idx}]"
        cmd = require_mapping(item, prefix, errors)
        name = str(cmd.get("name", "")).strip()
        file_path = str(cmd.get("file", "")).strip()
        if not name:
            add_error(errors, f"{prefix}.name is required")
        if not file_path or not file_path.startswith(".claude/commands/"):
            add_error(errors, f"{prefix}.file must start with .claude/commands/")

    for idx, item in enumerate(skills):
        prefix = f"registry.skills[{idx}]"
        skill = require_mapping(item, prefix, errors)
        name = str(skill.get("name", "")).strip()
        file_path = str(skill.get("file", "")).strip()
        if not name:
            add_error(errors, f"{prefix}.name is required")
        if not file_path or not file_path.startswith(".claude/skills/"):
            add_error(errors, f"{prefix}.file must start with .claude/skills/")


def validate_intent_flows(intent_flows: Dict[str, Any], slot_map: Dict[str, str], errors: List[str]) -> None:
    """校验机器可读的 intent -> stage flow 映射。

    这些检查用于保证 HighLevel 的 intent 语义与可执行 stage flow 保持一致，
    而不是依赖自由文本描述。
    """

    missing = sorted(VALID_INTENT - set(intent_flows.keys()))
    for key in missing:
        add_error(errors, f"intent_flows.{key} is required")

    for intent in sorted(VALID_INTENT):
        prefix = f"intent_flows.{intent}"
        raw_flow = intent_flows.get(intent, {})
        if not isinstance(raw_flow, dict):
            add_error(errors, f"{prefix} must be a mapping")
            continue

        required_slots = raw_flow.get("required_stage_slots")
        optional_slots = raw_flow.get("optional_stage_slots", [])
        if not isinstance(required_slots, list) or not required_slots:
            add_error(errors, f"{prefix}.required_stage_slots must be a non-empty list")
            required_values: List[str] = []
        else:
            required_values = [str(item).strip() for item in required_slots]
        if not isinstance(optional_slots, list):
            add_error(errors, f"{prefix}.optional_stage_slots must be a list")
            optional_values: List[str] = []
        else:
            optional_values = [str(item).strip() for item in optional_slots]

        for idx, value in enumerate(required_values):
            if value not in VALID_STAGE_SLOTS:
                add_error(errors, f"{prefix}.required_stage_slots[{idx}] must be one of {REQUIRED_STAGE_SLOT_ORDER}")
            elif value not in slot_map:
                add_error(errors, f"{prefix}.required_stage_slots[{idx}] references missing stage_slot: {value}")
        for idx, value in enumerate(optional_values):
            if value not in VALID_STAGE_SLOTS:
                add_error(errors, f"{prefix}.optional_stage_slots[{idx}] must be one of {REQUIRED_STAGE_SLOT_ORDER}")
            elif value not in slot_map:
                add_error(errors, f"{prefix}.optional_stage_slots[{idx}] references missing stage_slot: {value}")
        overlap = sorted(set(required_values) & set(optional_values))
        if overlap:
            add_error(errors, f"{prefix} required/optional overlap: {', '.join(overlap)}")

        if intent == "develop":
            if required_values != REQUIRED_STAGE_SLOT_ORDER:
                add_error(errors, f"{prefix}.required_stage_slots must be exactly {REQUIRED_STAGE_SLOT_ORDER}")
            if optional_values:
                add_error(errors, f"{prefix}.optional_stage_slots must be empty")
        elif intent == "audit":
            if required_values != ["S5", "S6"]:
                add_error(errors, f"{prefix}.required_stage_slots must be exactly ['S5', 'S6']")
            if optional_values:
                add_error(errors, f"{prefix}.optional_stage_slots must be empty")
        elif intent == "iterate":
            if required_values != ["S6"]:
                add_error(errors, f"{prefix}.required_stage_slots must be exactly ['S6']")
            if set(optional_values) - {"S5"}:
                add_error(errors, f"{prefix}.optional_stage_slots may only contain S5")
        elif intent == "validate":
            if required_values != ["S5"]:
                add_error(errors, f"{prefix}.required_stage_slots must be exactly ['S5']")
            if set(optional_values) - {"S6"}:
                add_error(errors, f"{prefix}.optional_stage_slots may only contain S6")


def validate_constraints(constraints: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """校验未来可能沉淀为 constraints.md 的规则候选。"""

    always = constraints.get("always")
    never = constraints.get("never")
    if not isinstance(always, list):
        add_error(errors, "constraints.always must be a list")
    elif not always:
        add_warn(warnings, "constraints.always is empty")
    if not isinstance(never, list):
        add_error(errors, "constraints.never must be a list")
    elif not never:
        add_warn(warnings, "constraints.never is empty")


def validate_resource_limits(resource_limits: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """校验 workflow spec 携带的执行预算限制。"""

    for field in ("max_parallel_agents", "max_retries_per_stage", "max_validation_loops"):
        value = resource_limits.get(field)
        if value is None:
            add_error(errors, f"resource_limits.{field} is required")
            continue
        if not isinstance(value, int) or value <= 0:
            add_error(errors, f"resource_limits.{field} must be a positive integer")

    max_parallel = resource_limits.get("max_parallel_agents")
    if isinstance(max_parallel, int) and max_parallel > 4:
        add_warn(warnings, "resource_limits.max_parallel_agents > 4 may violate constraints.md")


def validate_runtime_contract(runtime_contract: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """校验 runner 消费的运行时硬契约。"""

    missing = sorted(REQUIRED_RUNTIME_CONTRACT_KEYS - set(runtime_contract.keys()))
    for key in missing:
        add_error(errors, f"runtime_contract.{key} is required")

    write_boundaries = runtime_contract.get("write_boundaries")
    if not isinstance(write_boundaries, dict):
        add_error(errors, "runtime_contract.write_boundaries must be a mapping")
    else:
        for key in ("target_root_allow", "run_root_allow", "temp_root_allow", "deny"):
            value = write_boundaries.get(key)
            if not isinstance(value, list):
                add_error(errors, f"runtime_contract.write_boundaries.{key} must be a list")
                continue
            if not value:
                add_warn(warnings, f"runtime_contract.write_boundaries.{key} is empty")
            for idx, item in enumerate(value):
                if not str(item).strip():
                    add_error(errors, f"runtime_contract.write_boundaries.{key}[{idx}] must not be empty")

    required_evidence = runtime_contract.get("required_evidence")
    if not isinstance(required_evidence, list):
        add_error(errors, "runtime_contract.required_evidence must be a list")
    else:
        if not required_evidence:
            add_error(errors, "runtime_contract.required_evidence must not be empty")
        for idx, item in enumerate(required_evidence):
            text = str(item).strip()
            if not text:
                add_error(errors, f"runtime_contract.required_evidence[{idx}] must not be empty")
            elif text.startswith("/"):
                add_error(errors, f"runtime_contract.required_evidence[{idx}] must be relative path")

    failure_kinds = runtime_contract.get("failure_kinds")
    if not isinstance(failure_kinds, list):
        add_error(errors, "runtime_contract.failure_kinds must be a list")
    else:
        values = {str(item).strip() for item in failure_kinds if str(item).strip()}
        missing_kinds = sorted(REQUIRED_FAILURE_KINDS - values)
        if missing_kinds:
            add_error(errors, f"runtime_contract.failure_kinds missing required values: {', '.join(missing_kinds)}")

    env_skip = runtime_contract.get("environment_skip")
    if not isinstance(env_skip, list):
        add_error(errors, "runtime_contract.environment_skip must be a list")
    else:
        if not env_skip:
            add_warn(warnings, "runtime_contract.environment_skip is empty")
        seen_codes: Set[str] = set()
        for idx, item in enumerate(env_skip):
            prefix = f"runtime_contract.environment_skip[{idx}]"
            if not isinstance(item, dict):
                add_error(errors, f"{prefix} must be a mapping")
                continue
            code = str(item.get("code", "")).strip()
            check = str(item.get("check", "")).strip()
            message = str(item.get("message", "")).strip()
            if not code:
                add_error(errors, f"{prefix}.code is required")
            elif code in seen_codes:
                add_error(errors, f"{prefix}.code duplicated: {code}")
            else:
                seen_codes.add(code)
            if not check:
                add_error(errors, f"{prefix}.check is required")
            elif check in DEPRECATED_ENV_SKIP_CHECKS:
                add_error(errors, f"{prefix}.check '{check}' is deprecated; use runtime_host_* checks instead")
            elif check not in VALID_ENV_SKIP_CHECKS:
                add_error(errors, f"{prefix}.check must be one of {sorted(VALID_ENV_SKIP_CHECKS)}")
            if not message:
                add_error(errors, f"{prefix}.message is required")


def resolve_runtime_ref(
    ref: Any,
    field: str,
    runtime_contract: Dict[str, Any],
    errors: List[str],
) -> str:
    """校验 `runtime_contract.<field>` 引用语法及目标字段是否存在。"""

    text = str(ref).strip()
    if not text:
        add_error(errors, f"{field} is required")
        return ""
    match = RUNTIME_REF_PATTERN.match(text)
    if not match:
        add_error(errors, f"{field} must use ref syntax runtime_contract.<field>")
        return ""
    target = match.group(1)
    if target not in runtime_contract:
        add_error(errors, f"{field} references missing runtime_contract field: {target}")
        return ""
    return target


def validate_test_contract(
    test_contract: Dict[str, Any],
    runtime_contract: Dict[str, Any],
    stage_ids: Set[str],
    slot_map: Dict[str, str],
    intent_flows: Dict[str, Any],
    registered_entries: Set[str],
    errors: List[str],
    warnings: List[str],
) -> None:
    """校验 workflow 的 S5 judgment contract。

    这里最关键的规则是：test_contract 可以引用 runtime_contract，
    但不能复制或削弱 runtime 的执行语义。
    """

    required_sections = {"entry", "boundary", "flow", "artifacts", "failure"}
    missing = sorted(required_sections - set(test_contract.keys()))
    for key in missing:
        add_error(errors, f"test_contract.{key} is required")

    # entry 检查定义了工作流应如何被调用。
    entry = require_mapping(test_contract.get("entry", {}), "test_contract.entry", errors)
    main_entry = str(entry.get("main_entry", "")).strip()
    if not main_entry:
        add_error(errors, "test_contract.entry.main_entry is required")
    elif main_entry not in registered_entries:
        add_error(errors, f"test_contract.entry.main_entry '{main_entry}' not found in registry.commands or registry.skills")
    entry_type = str(entry.get("entry_type", "")).strip()
    if entry_type not in VALID_ENTRY_TYPES:
        add_error(errors, f"test_contract.entry.entry_type must be one of {sorted(VALID_ENTRY_TYPES)}")
    required_args = entry.get("required_args")
    if not isinstance(required_args, list):
        add_error(errors, "test_contract.entry.required_args must be a list")
    else:
        for idx, item in enumerate(required_args):
            if not str(item).strip():
                add_error(errors, f"test_contract.entry.required_args[{idx}] must not be empty")
    for key in ("missing_arg_verdict", "invalid_entry_verdict"):
        verdict = str(entry.get(key, "")).strip()
        if verdict not in VALID_VERDICT:
            add_error(errors, f"test_contract.entry.{key} must be one of {sorted(VALID_VERDICT)}")

    # boundary 检查必须回指 runtime_contract，
    # 不能把同一份写入边界语义复制成第二份真源。
    boundary = require_mapping(test_contract.get("boundary", {}), "test_contract.boundary", errors)
    if "write_boundaries" in boundary:
        add_error(errors, "test_contract.boundary must not duplicate runtime_contract.write_boundaries")
    resolve_runtime_ref(boundary.get("write_boundaries_ref"), "test_contract.boundary.write_boundaries_ref", runtime_contract, errors)
    for key in ("managed_overwrite_policy", "conflict_expectation", "external_write_policy"):
        value = str(boundary.get(key, "")).strip()
        if not value:
            add_error(errors, f"test_contract.boundary.{key} is required")

    # flow 检查默认锚定到 develop intent flow。
    flow = require_mapping(test_contract.get("flow", {}), "test_contract.flow", errors)
    required_stages = flow.get("required_stages")
    if not isinstance(required_stages, list) or not required_stages:
        add_error(errors, "test_contract.flow.required_stages must be a non-empty list")
    else:
        for idx, item in enumerate(required_stages):
            stage_id = str(item).strip()
            if not stage_id:
                add_error(errors, f"test_contract.flow.required_stages[{idx}] must not be empty")
            elif stage_id not in stage_ids:
                add_error(errors, f"test_contract.flow.required_stages[{idx}] references unknown stage: {stage_id}")
    skippable_stages = flow.get("skippable_stages")
    if not isinstance(skippable_stages, list):
        add_error(errors, "test_contract.flow.skippable_stages must be a list")
    else:
        for idx, item in enumerate(skippable_stages):
            stage_id = str(item).strip()
            if not stage_id:
                add_error(errors, f"test_contract.flow.skippable_stages[{idx}] must not be empty")
            elif stage_id not in stage_ids:
                add_error(errors, f"test_contract.flow.skippable_stages[{idx}] references unknown stage: {stage_id}")
    develop_flow = intent_flows.get("develop", {}) if isinstance(intent_flows, dict) else {}
    if isinstance(develop_flow, dict):
        required_slots = develop_flow.get("required_stage_slots", [])
        optional_slots = develop_flow.get("optional_stage_slots", [])
        if isinstance(required_slots, list):
            expected_required = [slot_map[slot] for slot in required_slots if slot in slot_map]
            observed_required = [str(item).strip() for item in required_stages] if isinstance(required_stages, list) else []
            if observed_required and observed_required != expected_required:
                add_error(
                    errors,
                    f"test_contract.flow.required_stages must match develop intent_flows mapping: expected {expected_required}, got {observed_required}",
                )
        if isinstance(optional_slots, list):
            expected_optional = [slot_map[slot] for slot in optional_slots if slot in slot_map]
            observed_optional = [str(item).strip() for item in skippable_stages] if isinstance(skippable_stages, list) else []
            if observed_optional != expected_optional:
                add_error(
                    errors,
                    f"test_contract.flow.skippable_stages must match develop intent_flows mapping: expected {expected_optional}, got {observed_optional}",
                )
    failure_recovery = flow.get("failure_recovery")
    if not isinstance(failure_recovery, dict):
        add_error(errors, "test_contract.flow.failure_recovery must be a mapping")
    else:
        declared_failure_kinds = runtime_contract.get("failure_kinds", [])
        if not isinstance(declared_failure_kinds, list):
            declared_failure_kinds = []
        declared_failure_set = {str(item).strip() for item in declared_failure_kinds if str(item).strip()}
        for failure_kind, stage_id in failure_recovery.items():
            failure_name = str(failure_kind).strip()
            target_stage = str(stage_id).strip()
            if not failure_name:
                add_error(errors, "test_contract.flow.failure_recovery contains empty failure kind")
                continue
            if failure_name not in declared_failure_set:
                add_error(errors, f"test_contract.flow.failure_recovery.{failure_name} must be declared in runtime_contract.failure_kinds")
            if not target_stage:
                add_error(errors, f"test_contract.flow.failure_recovery.{failure_name} must not be empty")
                continue
            if target_stage not in stage_ids:
                add_error(errors, f"test_contract.flow.failure_recovery.{failure_name} references unknown stage: {target_stage}")
    terminal_conditions = flow.get("terminal_conditions")
    if not isinstance(terminal_conditions, dict):
        add_error(errors, "test_contract.flow.terminal_conditions must be a mapping")
    else:
        for verdict in VALID_VERDICT:
            if verdict not in terminal_conditions:
                add_error(errors, f"test_contract.flow.terminal_conditions.{verdict} is required")
                continue
            stage_status = str(terminal_conditions.get(verdict, "")).strip()
            if stage_status not in VALID_STAGE_STATUS:
                add_error(errors, f"test_contract.flow.terminal_conditions.{verdict} must be one of {sorted(VALID_STAGE_STATUS)}")

    # artifact 检查定义了 S5 在执行后期望检查的对象。
    artifacts = require_mapping(test_contract.get("artifacts", {}), "test_contract.artifacts", errors)
    if "required_evidence" in artifacts:
        add_error(errors, "test_contract.artifacts must not duplicate runtime_contract.required_evidence")
    deliverables = artifacts.get("deliverables")
    if not isinstance(deliverables, list) or not deliverables:
        add_error(errors, "test_contract.artifacts.deliverables must be a non-empty list")
    else:
        deliverable_values = [str(item).strip() for item in deliverables if str(item).strip()]
        for idx, item in enumerate(deliverables):
            if not str(item).strip():
                add_error(errors, f"test_contract.artifacts.deliverables[{idx}] must not be empty")
        develop_flow = intent_flows.get("develop", {}) if isinstance(intent_flows, dict) else {}
        required_slots = develop_flow.get("required_stage_slots", []) if isinstance(develop_flow, dict) else []
        if isinstance(required_slots, list) and "S4" in [str(item).strip() for item in required_slots]:
            if ".workflowprogram/managed-files.json" not in deliverable_values:
                add_error(
                    errors,
                    "test_contract.artifacts.deliverables must include .workflowprogram/managed-files.json for develop flows with S4",
                )
    resolve_runtime_ref(artifacts.get("evidence_ref"), "test_contract.artifacts.evidence_ref", runtime_contract, errors)
    optional_outputs = artifacts.get("optional_outputs")
    if optional_outputs is None:
        add_warn(warnings, "test_contract.artifacts.optional_outputs is missing; prefer explicit declaration")
    elif not isinstance(optional_outputs, list):
        add_error(errors, "test_contract.artifacts.optional_outputs must be a list")
    else:
        for idx, item in enumerate(optional_outputs):
            if not str(item).strip():
                add_error(errors, f"test_contract.artifacts.optional_outputs[{idx}] must not be empty")

    # failure 检查描述的是当前覆盖范围，而不是另一套运行时语义。
    failure = require_mapping(test_contract.get("failure", {}), "test_contract.failure", errors)
    for duplicated in ("failure_kinds", "environment_skip"):
        if duplicated in failure:
            add_error(errors, f"test_contract.failure must not duplicate runtime_contract.{duplicated}")
    failure_target = resolve_runtime_ref(
        failure.get("failure_kinds_ref"),
        "test_contract.failure.failure_kinds_ref",
        runtime_contract,
        errors,
    )
    env_target = resolve_runtime_ref(
        failure.get("environment_skip_ref"),
        "test_contract.failure.environment_skip_ref",
        runtime_contract,
        errors,
    )
    implemented_now = failure.get("implemented_now")
    if not isinstance(implemented_now, list) or not implemented_now:
        add_error(errors, "test_contract.failure.implemented_now must be a non-empty list")
    else:
        declared_failure_kinds = runtime_contract.get(failure_target, []) if failure_target else []
        if not isinstance(declared_failure_kinds, list):
            declared_failure_kinds = []
        declared_values = {str(item).strip() for item in declared_failure_kinds if str(item).strip()}
        for idx, item in enumerate(implemented_now):
            value = str(item).strip()
            if not value:
                add_error(errors, f"test_contract.failure.implemented_now[{idx}] must not be empty")
                continue
            if value not in declared_values:
                add_error(
                    errors,
                    f"test_contract.failure.implemented_now[{idx}]='{value}' must be a subset of runtime_contract.failure_kinds",
                )
    if env_target != "environment_skip":
        add_error(errors, "test_contract.failure.environment_skip_ref must reference runtime_contract.environment_skip")


def parse_stage_outputs(output: Any) -> List[str]:
    """把阶段 output 声明归一化为路径列表。"""

    if output is None:
        return []
    if isinstance(output, list):
        return [str(item).strip() for item in output if str(item).strip()]
    text = str(output).strip()
    if not text:
        return []
    if "\n" in text:
        return [line.strip() for line in text.splitlines() if line.strip()]
    return [text]


def validate_generated_runtime_contract(
    generated_runtime_contract: Dict[str, Any],
    stages: List[Any],
    intent_flows: Dict[str, Any],
    test_contract: Dict[str, Any],
    errors: List[str],
    warnings: List[str],
) -> None:
    """校验目标侧 deterministic runtime 合同。"""

    missing = sorted(REQUIRED_GENERATED_RUNTIME_KEYS - set(generated_runtime_contract.keys()))
    for key in missing:
        add_error(errors, f"generated_runtime_contract.{key} is required")

    normalized: Dict[str, str] = {}
    for key in REQUIRED_GENERATED_RUNTIME_KEYS:
        value = str(generated_runtime_contract.get(key, "")).strip()
        if not value:
            add_error(errors, f"generated_runtime_contract.{key} must not be empty")
            continue
        normalized[key] = value
        if key != "mode" and not value.startswith(".workflowprogram/"):
            add_error(errors, f"generated_runtime_contract.{key} must stay under .workflowprogram/: {value}")

    mode = normalized.get("mode", "")
    if mode and mode != "shared-control-plane-wrapper":
        add_warn(warnings, f"generated_runtime_contract.mode is uncommon: {mode}")

    develop_flow = intent_flows.get("develop", {}) if isinstance(intent_flows, dict) else {}
    required_slots = develop_flow.get("required_stage_slots", []) if isinstance(develop_flow, dict) else []
    requires_s4 = isinstance(required_slots, list) and "S4" in [str(item).strip() for item in required_slots]
    if not requires_s4:
        return

    stage_list = [item for item in stages if isinstance(item, dict)]
    generate_stage = next((stage for stage in stage_list if str(stage.get("stage_slot", "")).strip() == "S4"), None)
    if generate_stage is None:
        add_error(errors, "generated_runtime_contract requires an S4 stage to persist target runtime assets")
        return

    stage_outputs = set(parse_stage_outputs(generate_stage.get("output")))
    required_stage_outputs = {
        "outputs/candidate/.workflowprogram/runtime",
        normalized.get("entry_script", ""),
        normalized.get("runner_script", ""),
        normalized.get("state_validator_script", ""),
        normalized.get("runtime_manifest", ""),
    }
    for item in sorted(path for path in required_stage_outputs if path):
        if item not in stage_outputs:
            add_error(errors, f"S4 output must declare generated runtime artifact: {item}")

    artifacts = test_contract.get("artifacts", {}) if isinstance(test_contract, dict) else {}
    deliverables = artifacts.get("deliverables", []) if isinstance(artifacts, dict) else []
    deliverable_values = {str(item).strip() for item in deliverables if str(item).strip()} if isinstance(deliverables, list) else set()
    for item in (
        normalized.get("entry_script", ""),
        normalized.get("runner_script", ""),
        normalized.get("state_validator_script", ""),
        normalized.get("runtime_manifest", ""),
    ):
        if item and item not in deliverable_values:
            add_error(errors, f"test_contract.artifacts.deliverables must include generated runtime asset: {item}")


def validate_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    """运行完整 workflow-spec 校验器，并返回结构化报告。"""

    collector = DiagnosticCollector()
    errors = collector.errors
    warnings = collector.warnings

    validate_top_level(spec, errors, warnings)
    meta = require_mapping(spec.get("meta", {}), "meta", errors)
    validate_meta(meta, errors)

    agent_refs_list = require_list(spec.get("agent_refs", []), "agent_refs", errors)
    agent_refs = validate_agent_refs(agent_refs_list, errors)

    stages = require_list(spec.get("stages", []), "stages", errors)
    stage_ids = validate_stages(stages, agent_refs, errors, warnings)
    slot_map = stage_slot_id_map(stages)

    intent_flows = require_mapping(spec.get("intent_flows", {}), "intent_flows", errors)
    validate_intent_flows(intent_flows, slot_map, errors)

    skills = require_list(spec.get("skills", []), "skills", errors)
    validate_skills(skills, errors)

    registry = require_mapping(spec.get("registry", {}), "registry", errors)
    validate_registry(registry, errors)
    registered_entries: Set[str] = set()
    for collection in ("commands", "skills"):
        items = registry.get(collection, [])
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    name = str(item.get("name", "")).strip()
                    if name:
                        registered_entries.add(name)

    constraints = require_mapping(spec.get("constraints", {}), "constraints", errors)
    validate_constraints(constraints, errors, warnings)

    resource_limits = require_mapping(spec.get("resource_limits", {}), "resource_limits", errors)
    validate_resource_limits(resource_limits, errors, warnings)

    runtime_contract = require_mapping(spec.get("runtime_contract", {}), "runtime_contract", errors)
    validate_runtime_contract(runtime_contract, errors, warnings)

    generated_runtime_contract = require_mapping(spec.get("generated_runtime_contract", {}), "generated_runtime_contract", errors)
    validate_generated_runtime_contract(generated_runtime_contract, stages, intent_flows, spec.get("test_contract", {}), errors, warnings)

    test_contract = require_mapping(spec.get("test_contract", {}), "test_contract", errors)
    validate_test_contract(test_contract, runtime_contract, stage_ids, slot_map, intent_flows, registered_entries, errors, warnings)

    return collector.payload()


def main() -> int:
    """schema 校验的 CLI 入口。"""

    args = parse_args()
    spec_path = Path(args.spec).resolve()
    if not spec_path.exists():
        diagnostics = DiagnosticCollector()
        diagnostics.error(f"spec not found: {spec_path}")
        if args.json:
            print(json.dumps(diagnostics.payload(spec=str(spec_path)), ensure_ascii=False, indent=2))
        else:
            print(f"Error: spec not found: {spec_path}", file=sys.stderr)
        return 1

    try:
        payload = load_yaml_mapping(spec_path)
    except Exception as exc:
        diagnostics = DiagnosticCollector()
        diagnostics.error(f"failed to parse YAML: {exc}")
        if args.json:
            print(json.dumps(diagnostics.payload(spec=str(spec_path)), ensure_ascii=False, indent=2))
        else:
            print(f"Error: failed to parse YAML: {exc}", file=sys.stderr)
        return 1

    report = validate_spec(payload)
    report["spec"] = str(spec_path)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"[{report['status']}] spec={spec_path}")
        for item in report["errors"]:
            print(f"[ERROR] {item}")
        for item in report["warnings"]:
            print(f"[WARN] {item}")

    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
