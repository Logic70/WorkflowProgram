#!/usr/bin/env python3
# AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY
"""
为 WorkflowProgram RUN_ROOT 生成具备 contract 感知能力的 S5 校验结果。

该 judge 刻意保持确定性：
- 输入：RUN_ROOT 证据、TARGET_ROOT 资产、可选的 workflow-spec.yaml
- 输出：validation-runtime-report.md + outputs/stages/s5-validation-summary.json
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


RESULTS = {"PASS", "WARN", "FAIL", "ENVIRONMENT-SKIP"}
CATEGORY_ORDER = ("entry", "boundary", "flow", "artifacts", "failure")
SELF_GENERATED_FILES = {
    "validation-runtime-report.md",
    "outputs/stages/s5-validation-summary.json",
}
FAILURE_KIND_BY_CATEGORY = {
    "entry": "design",
    "flow": "design",
    "failure": "design",
    "boundary": "implementation",
    "artifacts": "implementation",
}


def preprocess_yaml_text(text: str) -> str:
    """在解析 YAML 前去掉 BOM 和开头的 HTML 注释。"""

    cleaned = text.lstrip("\ufeff")
    while True:
        stripped = cleaned.lstrip()
        if not stripped.startswith("<!--"):
            return cleaned
        end = stripped.find("-->")
        if end < 0:
            return cleaned
        cleaned = stripped[end + 3 :].lstrip("\r\n")


def load_json(path: Path) -> Dict[str, Any]:
    """供确定性 judge 使用的尽力而为 JSON 加载器。"""

    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_yaml(path: Path) -> Dict[str, Any]:
    """供 workflow-spec.yaml 使用的尽力而为 YAML 加载器。"""

    if not path.exists():
        return {}
    try:
        payload = yaml.safe_load(preprocess_yaml_text(path.read_text(encoding="utf-8")))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_snapshot(path: Path) -> List[Dict[str, Any]]:
    """加载由 runtime_smoke.py 产出的标准化快照格式。"""

    payload = load_json(path)
    entries = payload.get("entries", [])
    if not isinstance(entries, list):
        return []
    normalized: List[Dict[str, Any]] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        rel_path = str(item.get("path", "")).strip()
        if not rel_path:
            continue
        normalized.append(
            {
                "path": rel_path,
                "sha256": str(item.get("sha256", "")).strip(),
                "size": item.get("size"),
            }
        )
    return normalized


def validate_managed_manifest(path: Path) -> List[str]:
    errors: List[str] = []
    payload = load_json(path)
    if not payload:
        return [f"managed manifest is missing or invalid JSON: {path}"]
    updated_at = str(payload.get("updated_at", "")).strip()
    entries = payload.get("entries")
    if not updated_at:
        errors.append("managed manifest is missing updated_at")
    if not isinstance(entries, list):
        errors.append("managed manifest entries must be a list")
    return errors


def snapshot_index(entries: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """按相对路径为快照条目建立索引，便于快速 diff 查询。"""

    return {str(item["path"]): item for item in entries if str(item.get("path", "")).strip()}


def diff_snapshot_paths(before: List[Dict[str, Any]], after: List[Dict[str, Any]]) -> List[str]:
    """返回两份快照之间发生变化的相对路径集合。"""

    before_index = snapshot_index(before)
    after_index = snapshot_index(after)
    changed: List[str] = []
    for rel_path in sorted(set(before_index) | set(after_index)):
        before_item = before_index.get(rel_path)
        after_item = after_index.get(rel_path)
        if before_item is None or after_item is None:
            changed.append(rel_path)
            continue
        if before_item.get("sha256") != after_item.get("sha256"):
            changed.append(rel_path)
    return changed


def path_matches_any(path: str, patterns: List[str]) -> bool:
    """判断变更路径是否被任意声明的 glob 允许。"""

    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def matching_paths(paths: List[str], pattern: str) -> List[str]:
    """按单个 glob 模式过滤路径列表。"""

    return [path for path in paths if fnmatch.fnmatch(path, pattern)]


def find_first_status(
    checks: Dict[str, List[Dict[str, str]]],
    statuses: set[str],
) -> Optional[Dict[str, str]]:
    """按 category 顺序返回首个命中目标状态的检查项。"""

    for category in CATEGORY_ORDER:
        for item in checks.get(category, []):
            if item.get("status") in statuses:
                return {"category": category, **item}
    return None


def failure_kind_for_check(category: str, name: str) -> str:
    """把失败/警告检查映射回粗粒度 failure_kind 分类。"""

    lowered_name = name.lower()
    if "conflict" in lowered_name:
        return "conflict"
    if "environment" in lowered_name:
        return "environment"
    return FAILURE_KIND_BY_CATEGORY.get(category, "implementation")


def failure_code_for_check(category: str, name: str) -> str:
    """根据检查项身份生成稳定的机器可读 failure code。"""

    slug = re.sub(r"[^A-Za-z0-9]+", "_", f"{category}_{name}").strip("_").upper()
    return f"S5_{slug or 'CHECK_FAILED'}"


def infer_expected_intent(entry_skill: str) -> str:
    """根据入口技能名推断期望的逻辑 intent。"""

    if entry_skill.endswith("-audit"):
        return "audit"
    if entry_skill.endswith("-validate"):
        return "validate"
    if entry_skill.endswith("-iterate"):
        return "iterate"
    if entry_skill.endswith("-orchestrate"):
        return "orchestrate"
    return "develop"


def stage_slot_to_id_map(spec: Dict[str, Any]) -> Dict[str, str]:
    """把逻辑 stage slot（S1..S6）映射到 spec 中可执行的 stage id。"""

    mapping: Dict[str, str] = {}
    stages = spec.get("stages", [])
    if not isinstance(stages, list):
        return mapping
    for item in stages:
        if not isinstance(item, dict):
            continue
        stage_id = str(item.get("id", "")).strip()
        stage_slot = str(item.get("stage_slot", "")).strip()
        if stage_id and stage_slot and stage_slot not in mapping:
            mapping[stage_slot] = stage_id
    return mapping


def expected_flow_for_intent(spec: Dict[str, Any], intent: str) -> tuple[List[str], List[str], List[str], str] | None:
    """解析某个 intent flow 对应的 required/optional/allowed stage id。"""

    intent_flows = spec.get("intent_flows", {})
    if not isinstance(intent_flows, dict):
        return None
    flow = intent_flows.get(intent, {})
    if not isinstance(flow, dict):
        return None
    slot_map = stage_slot_to_id_map(spec)
    required_slots = flow.get("required_stage_slots", [])
    optional_slots = flow.get("optional_stage_slots", [])
    if not isinstance(required_slots, list):
        return None
    required_ids = [slot_map[slot] for slot in required_slots if str(slot).strip() in slot_map]
    optional_ids = [slot_map[slot] for slot in optional_slots if isinstance(optional_slots, list) and str(slot).strip() in slot_map] if isinstance(optional_slots, list) else []
    allowed_slots = [
        slot
        for slot in ("S1", "S2", "S3", "S4", "S5", "S6")
        if slot in {
            str(item).strip()
            for item in ([*required_slots, *optional_slots] if isinstance(optional_slots, list) else required_slots)
            if str(item).strip()
        }
    ]
    allowed_ids = [slot_map[slot] for slot in allowed_slots if slot in slot_map]
    if not required_ids:
        return None
    return required_ids, optional_ids, allowed_ids, f"intent_flows.{intent}"


def add_check(bucket: List[Dict[str, str]], name: str, status: str, detail: str, source: str) -> None:
    """向某个 category bucket 追加一条结构化检查结果。"""

    bucket.append(
        {
            "name": name,
            "status": status,
            "detail": detail,
            "source": source,
        }
    )


def run_validator(script_name: str, *args: str) -> Dict[str, Any]:
    """运行确定性的辅助校验器，并归一化其 JSON 输出。"""

    script_path = Path(__file__).resolve().parent / script_name
    cmd = [sys.executable, str(script_path), *args, "--json"]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = {
            "status": "FAIL",
            "errors": [completed.stderr.strip() or completed.stdout.strip() or f"{script_name} returned invalid JSON"],
            "warnings": [],
        }
    if completed.returncode != 0 and payload.get("status") == "PASS":
        payload["status"] = "FAIL"
        payload.setdefault("errors", []).append(f"{script_name} exited with code {completed.returncode}")
    return payload if isinstance(payload, dict) else {"status": "FAIL", "errors": [f"{script_name} returned non-object payload"], "warnings": []}


def map_failure_kind(result: str, failure_code: str) -> str:
    """把观测到的 verdict/failure-code 组合转换成 failure_kind。"""

    if result == "PASS":
        return "none"
    if result == "ENVIRONMENT-SKIP":
        return "environment"
    if failure_code in {"CONFLICT", "CONFLICT_FAILURE"}:
        return "conflict"
    if failure_code in {"STRUCTURE_FAILURE", "MISSING_ARGUMENT", "INPUT_FAILURE"}:
        return "design"
    if failure_code == "STRUCTURE_FAILURE":
        return "design"
    if failure_code in {"RUNTIME_FAILURE", "EVIDENCE_FAILURE"}:
        return "implementation"
    return "implementation"


def derive_contract(run_root: Path, fallback_categories: List[str]) -> Dict[str, Any]:
    """推导当前运行实际生效的 contract 上下文。

    如果 workflow-spec.yaml 存在，judge 会直接读取 runtime_contract 和 test_contract。
    否则回退到 fixture 提供的 category 期望值，这样即使是负例 smoke，
    也仍然能产出结构化检查项。
    """

    spec_path = run_root / "workflow-spec.yaml"
    spec = load_yaml(spec_path)
    if spec:
        runtime_contract = spec.get("runtime_contract", {})
        test_contract = spec.get("test_contract", {})
        if isinstance(runtime_contract, dict) and isinstance(test_contract, dict) and test_contract:
            categories = [name for name in CATEGORY_ORDER if name in test_contract]
            failure = test_contract.get("failure", {}) if isinstance(test_contract.get("failure"), dict) else {}
            env_skip = runtime_contract.get("environment_skip", [])
            env_codes: List[str] = []
            if isinstance(env_skip, list):
                for item in env_skip:
                    if isinstance(item, dict) and item.get("code"):
                        env_codes.append(str(item["code"]))
            implemented_now = failure.get("implemented_now", [])
            if not isinstance(implemented_now, list):
                implemented_now = []
            return {
                "contract_source": "workflow-spec.yaml.test_contract",
                "contract_categories": categories,
                "implemented_failure_kinds": [str(item) for item in implemented_now if str(item).strip()],
                "environment_skip_codes": env_codes,
                "runtime_contract": runtime_contract,
                "test_contract": test_contract,
                "spec_path": str(spec_path),
            }
    return {
        "contract_source": "fixture_preset",
        "contract_categories": fallback_categories,
        "implemented_failure_kinds": [],
        "environment_skip_codes": [],
        "runtime_contract": {},
        "test_contract": {},
        "spec_path": str(spec_path) if spec_path.exists() else None,
    }


def target_matches(target_root: Path, pattern: str) -> bool:
    """检查 target-root 的 glob 模式是否至少命中一个路径。"""

    return any(target_root.glob(pattern))


def build_checks(
    run_root: Path,
    target_root: Path,
    result: str,
    failure_code: str,
    summary_message: str,
    entry_skill: str,
    request: str,
    checked_files: List[str],
    contract: Dict[str, Any],
) -> Dict[str, List[Dict[str, str]]]:
    """构建完整的、按 category 组织的 S5 检查矩阵。

    这是 judge 的核心。它会把以下信息合并起来：
    - 观测到的运行时证据
    - workflow-spec 中的 runtime_contract/test_contract
    - target 的前后快照
    - 辅助校验器结果
    最终收敛为一组确定性的 entry/boundary/flow/artifacts/failure 检查。
    """

    checks: Dict[str, List[Dict[str, str]]] = {name: [] for name in CATEGORY_ORDER}
    spec = load_yaml(run_root / "workflow-spec.yaml")
    route_payload = load_json(run_root / "outputs" / "stages" / "s0-route.json")
    runtime_contract = contract.get("runtime_contract", {})
    test_contract = contract.get("test_contract", {})
    derived_failure_kind = map_failure_kind(result, failure_code)
    provider_result = load_json(run_root / "outputs" / "runtime-provider-result.json")
    parsed_provider = provider_result.get("parsed", {}) if isinstance(provider_result.get("parsed"), dict) else {}
    before_target = load_snapshot(run_root / "outputs" / "target-root-before.json")
    after_target = load_snapshot(run_root / "outputs" / "target-root-files.json")
    before_target_index = snapshot_index(before_target)
    changed_target_paths = diff_snapshot_paths(before_target, after_target) if before_target or after_target else []
    after_target_paths = [str(item.get("path", "")).strip() for item in after_target if str(item.get("path", "")).strip()]
    expected_intent = infer_expected_intent(entry_skill)
    observed_intent = route_payload.get("intent") if isinstance(route_payload, dict) else ""
    observed_intent_text = str(observed_intent).strip() or expected_intent

    # entry 检查先回答“是不是用正确的产品入口、以正确的请求形态触发了执行”，
    # 再继续看更深层的运行时行为。
    entry = test_contract.get("entry", {}) if isinstance(test_contract.get("entry"), dict) else {}
    if entry:
        add_check(
            checks["entry"],
            "smoke_entry_invoked",
            "PASS" if entry_skill else "FAIL",
            f"Observed smoke entry skill: {entry_skill or '<missing>'}",
            "smoke.invocation",
        )
        declared_entry = str(entry.get("main_entry", "")).strip()
        if declared_entry:
            status = "PASS" if declared_entry == entry_skill else "FAIL"
            detail = f"Declared main_entry={declared_entry}; smoke entry={entry_skill}"
            add_check(checks["entry"], "declared_main_entry", status, detail, "test_contract.entry.main_entry")
        required_args = entry.get("required_args", [])
        requires_arguments = isinstance(required_args, list) and any(str(item).strip() == "$ARGUMENTS" for item in required_args)
        if requires_arguments:
            add_check(
                checks["entry"],
                "required_arguments_present",
                "PASS" if request.strip() else "FAIL",
                "Request payload is non-empty." if request.strip() else "Request payload is empty while $ARGUMENTS is required.",
                "test_contract.entry.required_args",
            )
            missing_arg_verdict = str(entry.get("missing_arg_verdict", "")).strip()
            if not request.strip() and missing_arg_verdict:
                observed = result
                status = "PASS" if observed == missing_arg_verdict else "FAIL"
                add_check(
                    checks["entry"],
                    "missing_argument_behavior",
                    status,
                    f"Observed verdict={observed}; expected missing_arg_verdict={missing_arg_verdict}; raw failure_code={failure_code or 'none'}",
                    "test_contract.entry.missing_arg_verdict",
                )
        invalid_verdict = str(entry.get("invalid_entry_verdict", "")).strip()
        if invalid_verdict and failure_code == "STRUCTURE_FAILURE":
            status = "PASS" if invalid_verdict == "FAIL" else "WARN"
            add_check(
                checks["entry"],
                "invalid_entry_behavior",
                status,
                f"Observed invalid-entry style failure via code={failure_code}",
                "test_contract.entry.invalid_entry_verdict",
            )
    elif "entry" in contract.get("contract_categories", []):
        add_check(checks["entry"], "contract_source_fallback", "INFO", "Entry checks derived from fixture preset.", "fixture_preset")

    # boundary 检查会把观测到的文件系统变更，与 runtime contract 及 managed-write 策略做比较。
    boundary = test_contract.get("boundary", {}) if isinstance(test_contract.get("boundary"), dict) else {}
    write_boundaries = runtime_contract.get("write_boundaries", {}) if isinstance(runtime_contract, dict) else {}
    if boundary:
        has_ref = str(boundary.get("write_boundaries_ref", "")).strip() == "runtime_contract.write_boundaries"
        add_check(
            checks["boundary"],
            "write_boundaries_reference",
            "PASS" if has_ref else "FAIL",
            "Boundary contract must reference runtime_contract.write_boundaries.",
            "test_contract.boundary.write_boundaries_ref",
        )
        run_root_allow = write_boundaries.get("run_root_allow", []) if isinstance(write_boundaries, dict) else []
        allow_spec = isinstance(run_root_allow, list) and "workflow-spec.yaml" in [str(item) for item in run_root_allow]
        add_check(
            checks["boundary"],
            "run_root_spec_boundary",
            "PASS" if allow_spec else "FAIL",
            "workflow-spec.yaml should be allowed in RUN_ROOT for control-plane execution.",
            "runtime_contract.write_boundaries.run_root_allow",
        )
        target_root_allow = write_boundaries.get("target_root_allow", []) if isinstance(write_boundaries, dict) else []
        target_patterns = [str(item).strip() for item in target_root_allow if str(item).strip()]
        disallowed_changes = [item for item in changed_target_paths if not path_matches_any(item, target_patterns)]
        if before_target or after_target:
            add_check(
                checks["boundary"],
                "target_root_boundary_changes",
                "PASS" if not disallowed_changes else "FAIL",
                f"Changed target-root paths={changed_target_paths or ['<none>']}; disallowed={disallowed_changes or ['<none>']}",
                "runtime_contract.write_boundaries.target_root_allow",
            )
        external_write_policy = str(boundary.get("external_write_policy", "")).strip()
        if external_write_policy:
            status = "PASS" if external_write_policy != "deny" or not disallowed_changes else "FAIL"
            add_check(
                checks["boundary"],
                "external_write_policy",
                status,
                f"external_write_policy={external_write_policy}; disallowed_changes={disallowed_changes or ['<none>']}",
                "test_contract.boundary.external_write_policy",
            )
        managed_plan = load_json(run_root / "outputs" / "managed-change-plan.json")
        managed_entries = managed_plan.get("entries", []) if isinstance(managed_plan.get("entries"), list) else []
        managed_rel_paths = [str(item.get("relative_path", "")).strip() for item in managed_entries if str(item.get("relative_path", "")).strip()]
        managed_result = load_json(run_root / "outputs" / "managed-change-result.json")
        managed_conflicts = managed_result.get("conflicts", []) if isinstance(managed_result.get("conflicts"), list) else []
        managed_policy = str(boundary.get("managed_overwrite_policy", "")).strip()
        changed_managed_paths = [
            item for item in changed_target_paths if item.startswith(".claude/") and item in before_target_index
        ]
        unexpected_managed_changes = [item for item in changed_managed_paths if item not in managed_rel_paths]
        if managed_entries:
            missing_candidate_sources = []
            for item in managed_entries:
                source_path = str(item.get("source_path", "")).strip()
                if not source_path:
                    missing_candidate_sources.append("<missing>")
                    continue
                if not Path(source_path).exists():
                    missing_candidate_sources.append(source_path)
            add_check(
                checks["boundary"],
                "managed_candidate_sources_present",
                "PASS" if not missing_candidate_sources else "FAIL",
                f"Missing managed candidate source_path={missing_candidate_sources or ['<none>']}",
                "outputs/managed-change-plan.json",
            )
        if managed_policy:
            if unexpected_managed_changes:
                add_check(
                    checks["boundary"],
                    "managed_overwrite_policy_observed",
                    "FAIL",
                    f"managed_overwrite_policy={managed_policy}; unexpected managed changes={unexpected_managed_changes}",
                    "test_contract.boundary.managed_overwrite_policy",
                )
            elif managed_conflicts:
                add_check(
                    checks["boundary"],
                    "managed_overwrite_policy_observed",
                    "PASS" if managed_policy == "reject-unmanaged-overwrite" else "WARN",
                    f"managed_overwrite_policy={managed_policy}; observed conflicts={len(managed_conflicts)}",
                    "test_contract.boundary.managed_overwrite_policy",
                )
            elif managed_rel_paths:
                add_check(
                    checks["boundary"],
                    "managed_overwrite_policy_observed",
                    "PASS",
                    f"managed_overwrite_policy={managed_policy}; planned managed paths={managed_rel_paths}",
                    "test_contract.boundary.managed_overwrite_policy",
                )
            else:
                add_check(
                    checks["boundary"],
                    "managed_overwrite_policy_observed",
                    "INFO",
                    f"managed_overwrite_policy={managed_policy}; no managed conflicts were observed.",
                    "test_contract.boundary.managed_overwrite_policy",
                )
        conflict_expectation = str(boundary.get("conflict_expectation", "")).strip()
        if conflict_expectation:
            if managed_conflicts:
                missing_conflict_copy = []
                missing_candidate_source = []
                plan_entries_by_path = {
                    str(item.get("relative_path", "")).strip(): item for item in managed_entries if str(item.get("relative_path", "")).strip()
                }
                for item in managed_conflicts:
                    conflict_copy = str(item.get("conflict_copy", "")).strip()
                    if not conflict_copy:
                        missing_conflict_copy.append("<missing>")
                        continue
                    if not Path(conflict_copy).exists():
                        missing_conflict_copy.append(conflict_copy)
                    plan_entry = plan_entries_by_path.get(str(item.get("relative_path", "")).strip())
                    source_path = str(plan_entry.get("source_path", "")).strip() if isinstance(plan_entry, dict) else ""
                    if not source_path:
                        missing_candidate_source.append("<missing>")
                    elif not Path(source_path).exists():
                        missing_candidate_source.append(source_path)
                add_check(
                    checks["boundary"],
                    "conflict_artifacts_preserved",
                    "PASS" if not missing_conflict_copy and not missing_candidate_source else "FAIL",
                    f"conflict_expectation={conflict_expectation}; missing_conflict_copy={missing_conflict_copy or ['<none>']}; missing_candidate_source={missing_candidate_source or ['<none>']}",
                    "test_contract.boundary.conflict_expectation",
                )
            else:
                add_check(
                    checks["boundary"],
                    "conflict_artifacts_preserved",
                    "INFO",
                    f"conflict_expectation={conflict_expectation}; no conflicts were observed.",
                    "test_contract.boundary.conflict_expectation",
                )
    elif "boundary" in contract.get("contract_categories", []):
        add_check(checks["boundary"], "contract_source_fallback", "INFO", "Boundary checks derived from fixture preset.", "fixture_preset")

    # flow 检查会结合 provider 证据和 state.json 兜底信息，
    # 推断 stage history、审批门禁和失败恢复路径。
    flow = test_contract.get("flow", {}) if isinstance(test_contract.get("flow"), dict) else {}
    state = load_json(run_root / "state.json")
    stage_history = []
    if isinstance(provider_result.get("stage_history"), list):
        stage_history = [str(item) for item in provider_result.get("stage_history", []) if str(item).strip()]
    elif isinstance(parsed_provider.get("stage_history"), list):
        stage_history = [str(item) for item in parsed_provider.get("stage_history", []) if str(item).strip()]
    values = state.get("values")
    if not stage_history and isinstance(values, dict):
        raw_history = values.get("stage_history", [])
        if isinstance(raw_history, list):
            stage_history = [str(item) for item in raw_history]
    if flow:
        intent_flow = expected_flow_for_intent(spec, observed_intent_text)
        required_stage_source = "test_contract.flow.required_stages"
        skippable_stage_source = "test_contract.flow.skippable_stages"
        required_stages = flow.get("required_stages", [])
        skippable_stages = flow.get("skippable_stages", [])
        allowed_stages: List[str] = []
        if intent_flow is not None:
            required_stages, skippable_stages, allowed_stages, flow_source = intent_flow
            required_stage_source = f"{flow_source}.required_stage_slots"
            skippable_stage_source = f"{flow_source}.optional_stage_slots"
        if result in {"PASS", "WARN"}:
            add_check(
                checks["flow"],
                "stage_history_available",
                "PASS" if stage_history else "FAIL",
                f"Observed stage_history={stage_history or ['<none>']}",
                "runtime-provider.stage_history",
            )
        if isinstance(required_stages, list) and required_stages:
            if stage_history:
                missing = [str(item) for item in required_stages if str(item) not in stage_history]
                add_check(
                    checks["flow"],
                    "required_stages_executed",
                    "PASS" if not missing else "FAIL",
                    f"Observed stage_history={stage_history}; missing={missing or 'none'}",
                    required_stage_source,
                )
            else:
                add_check(
                    checks["flow"],
                    "required_stages_executed",
                    "FAIL" if result in {"PASS", "WARN"} else "INFO",
                    "No runner stage_history found in provider/state evidence; flow could not be fully judged.",
                    required_stage_source,
                )
        if allowed_stages and stage_history:
            unexpected = [stage for stage in stage_history if stage not in allowed_stages]
            add_check(
                checks["flow"],
                "unexpected_stages_absent",
                "PASS" if not unexpected else "FAIL",
                f"Observed stage_history={stage_history}; allowed={allowed_stages}; unexpected={unexpected or ['<none>']}",
                f"{required_stage_source}+{skippable_stage_source}",
            )
            if not unexpected:
                observed_positions = [allowed_stages.index(stage) for stage in stage_history]
                ordered = observed_positions == sorted(observed_positions)
                add_check(
                    checks["flow"],
                    "stage_order_valid",
                    "PASS" if ordered else "FAIL",
                    f"Observed stage_history={stage_history}; allowed_order={allowed_stages}",
                    f"{required_stage_source}+{skippable_stage_source}",
                )
        terminal_conditions = flow.get("terminal_conditions", {})
        provider_stage_status = str(parsed_provider.get("stage_status", "")).strip()
        if isinstance(terminal_conditions, dict) and result in terminal_conditions:
            if result in {"PASS", "WARN"}:
                add_check(
                    checks["flow"],
                    "stage_status_available",
                    "PASS" if provider_stage_status else "FAIL",
                    f"Observed stage_status={provider_stage_status or '<missing>'}",
                    "runtime-provider.stage_status",
                )
            if provider_stage_status:
                expected_stage_status = str(terminal_conditions.get(result, "")).strip()
                add_check(
                    checks["flow"],
                    "terminal_condition_observed",
                    "PASS" if provider_stage_status == expected_stage_status else "FAIL",
                    f"Observed stage_status={provider_stage_status}; expected={expected_stage_status}",
                    "test_contract.flow.terminal_conditions",
                )
            else:
                add_check(
                    checks["flow"],
                    "terminal_condition_declared",
                    "FAIL" if result in {"PASS", "WARN"} else "INFO",
                    f"Verdict {result} maps to terminal state {terminal_conditions.get(result)}, but provider did not expose stage_status.",
                    "test_contract.flow.terminal_conditions",
                )
        if isinstance(skippable_stages, list) and stage_history:
            present = [str(item) for item in skippable_stages if str(item) in stage_history]
            absent = [str(item) for item in skippable_stages if str(item) not in stage_history]
            add_check(
                checks["flow"],
                "skippable_stages_observed",
                "PASS",
                f"Present skippable stages={present or ['<none>']}; absent skippable stages={absent or ['<none>']}",
                skippable_stage_source,
            )
        failure_recovery = flow.get("failure_recovery", {})
        provider_recovery = str(parsed_provider.get("next_stage_on_failure", "")).strip()
        if result == "FAIL" and isinstance(failure_recovery, dict) and failure_recovery:
            expected_recovery = str(failure_recovery.get(derived_failure_kind, "")).strip()
            if expected_recovery and provider_recovery:
                add_check(
                    checks["flow"],
                    "failure_recovery_target",
                    "PASS" if provider_recovery == expected_recovery else "FAIL",
                    f"Observed next_stage_on_failure={provider_recovery}; expected={expected_recovery}",
                    "test_contract.flow.failure_recovery",
                )
            elif expected_recovery:
                add_check(
                    checks["flow"],
                    "failure_recovery_target",
                    "INFO",
                    f"Expected recovery target={expected_recovery}, but provider did not expose next_stage_on_failure.",
                    "test_contract.flow.failure_recovery",
                )
    elif "flow" in contract.get("contract_categories", []):
        add_check(checks["flow"], "contract_source_fallback", "INFO", "Flow checks derived from fixture preset.", "fixture_preset")

    # artifact 检查确保“最小证据集”和“面向用户的交付物”
    # 都与 spec 对本次运行后的期望一致。
    artifacts = test_contract.get("artifacts", {}) if isinstance(test_contract.get("artifacts"), dict) else {}
    evidence_paths: List[str] = []
    for rel_path in checked_files + sorted(SELF_GENERATED_FILES):
        if rel_path not in evidence_paths:
            evidence_paths.append(rel_path)
    for rel_path in evidence_paths:
        if rel_path in SELF_GENERATED_FILES:
            status = "PASS"
            detail = f"{rel_path} is generated by the S5 judge."
        else:
            status = "PASS" if (run_root / rel_path).exists() else "FAIL"
            detail = f"{rel_path} {'exists' if status == 'PASS' else 'is missing'} in RUN_ROOT."
        add_check(checks["artifacts"], f"evidence:{rel_path}", status, detail, "runtime_smoke.evidence")
    if artifacts:
        evidence_ref = str(artifacts.get("evidence_ref", "")).strip()
        if evidence_ref:
            add_check(
                checks["artifacts"],
                "evidence_reference",
                "PASS" if evidence_ref == "runtime_contract.required_evidence" else "FAIL",
                f"evidence_ref={evidence_ref}",
                "test_contract.artifacts.evidence_ref",
            )
        required_evidence = runtime_contract.get("required_evidence", []) if isinstance(runtime_contract, dict) else []
        if isinstance(required_evidence, list):
            missing_required = []
            for rel_path in [str(item).strip() for item in required_evidence if str(item).strip()]:
                if not (run_root / rel_path).exists():
                    missing_required.append(rel_path)
            add_check(
                checks["artifacts"],
                "required_runtime_evidence",
                "PASS" if not missing_required else "FAIL",
                f"Missing required_evidence={missing_required or ['<none>']}",
                "runtime_contract.required_evidence",
            )
        if route_payload:
            route_entry = str(route_payload.get("entry_skill", "")).strip()
            route_intent = str(route_payload.get("intent", "")).strip()
            add_check(
                checks["artifacts"],
                "route_evidence_matches_invocation",
                "PASS" if route_entry == entry_skill and route_intent == expected_intent else "FAIL",
                f"Observed route entry_skill={route_entry or '<missing>'}; intent={route_intent or '<missing>'}; expected entry_skill={entry_skill}; intent={expected_intent}",
                "outputs/stages/s0-route.json",
            )
        runner_summary = load_json(run_root / "outputs" / "stages" / "runner-summary.json")
        if runner_summary:
            summary_entry = str(runner_summary.get("entry_skill", "")).strip()
            summary_status = str(runner_summary.get("status", "")).strip()
            add_check(
                checks["artifacts"],
                "runner_summary_matches_observed",
                "PASS" if summary_entry == entry_skill and summary_status == result else "FAIL",
                f"Observed runner-summary entry_skill={summary_entry or '<missing>'}; status={summary_status or '<missing>'}; expected entry_skill={entry_skill}; status={result}",
                "outputs/stages/runner-summary.json",
            )
        requires_s1_draft = observed_intent_text == "develop" and (
            result in {"PASS", "WARN"} or any(stage in stage_history for stage in ["context", "design", "generate", "validate", "lessons"])
        )
        draft_path = run_root / "workflow-spec.md"
        if requires_s1_draft:
            add_check(
                checks["artifacts"],
                "workflow_spec_draft_exists",
                "PASS" if draft_path.exists() else "FAIL",
                f"workflow-spec.md {'exists' if draft_path.exists() else 'is missing'} at {draft_path}",
                "S1.workflow-spec.md",
            )
            if draft_path.exists():
                draft_validation = run_validator("validate-workflow-draft.py", "--spec", str(draft_path))
                detail = "; ".join(
                    [*draft_validation.get("errors", []), *draft_validation.get("warnings", [])]
                ) or "workflow-spec.md passed deterministic S1 quality validation."
                add_check(
                    checks["artifacts"],
                    "workflow_spec_draft_valid",
                    "PASS" if draft_validation.get("status") == "PASS" else "FAIL",
                    detail,
                    "validate-workflow-draft.py",
                )
        requires_s6_delta = "lessons" in stage_history or (observed_intent_text in {"develop", "audit", "iterate"} and result in {"PASS", "WARN"})
        optional_s6_delta = observed_intent_text == "validate"
        delta_path = run_root / "outputs" / "stages" / "s6-lessons-delta.md"
        if requires_s6_delta or (optional_s6_delta and delta_path.exists()):
            add_check(
                checks["artifacts"],
                "s6_lessons_delta_exists",
                "PASS" if delta_path.exists() else "FAIL",
                f"s6-lessons-delta.md {'exists' if delta_path.exists() else 'is missing'} at {delta_path}",
                "S6.outputs/stages/s6-lessons-delta.md",
            )
            if delta_path.exists():
                lessons_validation = run_validator(
                    "validate-lessons-delta.py",
                    "--run-root",
                    str(run_root),
                    "--run-id",
                    run_root.name,
                    "--failure-kind",
                    derived_failure_kind,
                )
                detail = "; ".join(
                    [*lessons_validation.get("errors", []), *lessons_validation.get("warnings", [])]
                ) or "S6 lessons delta and user progress passed deterministic validation."
                add_check(
                    checks["artifacts"],
                    "s6_lessons_delta_valid",
                    "PASS" if lessons_validation.get("status") == "PASS" else "FAIL",
                    detail,
                    "validate-lessons-delta.py",
                )
        deliverables = artifacts.get("deliverables", [])
        if isinstance(deliverables, list):
            for pattern in deliverables:
                text = str(pattern).strip()
                if not text:
                    continue
                matched_paths = matching_paths(after_target_paths, text)
                changed_matches = matching_paths(changed_target_paths, text)
                if result in {"PASS", "WARN"}:
                    status = "PASS" if changed_matches else "FAIL"
                else:
                    status = "INFO"
                add_check(
                    checks["artifacts"],
                    f"deliverable:{text}",
                    status,
                    f"Deliverable pattern {text}; matched_paths={matched_paths or ['<none>']}; changed_matches={changed_matches or ['<none>']}",
                    "test_contract.artifacts.deliverables",
                )
                if text == ".workflowprogram/managed-files.json":
                    manifest_path = target_root / ".workflowprogram" / "managed-files.json"
                    manifest_errors = validate_managed_manifest(manifest_path) if manifest_path.exists() else [f"managed manifest not found: {manifest_path}"]
                    add_check(
                        checks["artifacts"],
                        "managed_manifest_valid",
                        "PASS" if not manifest_errors else "FAIL",
                        "managed-files.json passed deterministic validation." if not manifest_errors else "; ".join(manifest_errors),
                        "TARGET_ROOT/.workflowprogram/managed-files.json",
                    )
                    managed_result = load_json(run_root / "outputs" / "managed-change-result.json")
                    manifest_ref = str(managed_result.get("manifest_path", "")).strip() if isinstance(managed_result, dict) else ""
                    add_check(
                        checks["artifacts"],
                        "managed_manifest_path_matches_result",
                        "PASS" if manifest_ref == str(manifest_path) else "FAIL",
                        f"managed-change-result manifest_path={manifest_ref or '<missing>'}; expected={manifest_path}",
                        "outputs/managed-change-result.json",
                    )
    elif "artifacts" in contract.get("contract_categories", []):
        add_check(checks["artifacts"], "contract_source_fallback", "INFO", "Artifact checks derived from fixture preset.", "fixture_preset")

    # failure 检查会把观测到的失败回连到 declared implemented_now
    # 覆盖范围以及 environment skip 引用。
    failure = test_contract.get("failure", {}) if isinstance(test_contract.get("failure"), dict) else {}
    implemented_now = contract.get("implemented_failure_kinds", [])
    add_check(
        checks["failure"],
        "derived_failure_kind",
        "PASS" if derived_failure_kind in {"none", "design", "implementation", "environment", "conflict"} else "FAIL",
        f"Derived failure_kind={derived_failure_kind}; raw failure_code={failure_code or 'none'}",
        "judge.mapping",
    )
    if result == "ENVIRONMENT-SKIP":
        add_check(
            checks["failure"],
            "environment_skip_reason",
            "PASS",
            summary_message,
            "runtime_contract.environment_skip",
        )
    if failure:
        if implemented_now:
            status = "PASS" if derived_failure_kind in implemented_now else "WARN"
            add_check(
                checks["failure"],
                "implemented_now_coverage",
                status,
                f"implemented_now={implemented_now}; observed={derived_failure_kind}",
                "test_contract.failure.implemented_now",
            )
        failure_ref = str(failure.get("failure_kinds_ref", "")).strip()
        if failure_ref:
            add_check(
                checks["failure"],
                "failure_kinds_reference",
                "PASS" if failure_ref == "runtime_contract.failure_kinds" else "FAIL",
                f"failure_kinds_ref={failure_ref}",
                "test_contract.failure.failure_kinds_ref",
            )
        env_ref = str(failure.get("environment_skip_ref", "")).strip()
        if env_ref:
            add_check(
                checks["failure"],
                "environment_skip_reference",
                "PASS" if env_ref == "runtime_contract.environment_skip" else "FAIL",
                f"environment_skip_ref={env_ref}",
                "test_contract.failure.environment_skip_ref",
            )
        if result == "ENVIRONMENT-SKIP":
            declared_codes = contract.get("environment_skip_codes", [])
            if isinstance(declared_codes, list):
                add_check(
                    checks["failure"],
                    "environment_skip_code_declared",
                    "PASS" if failure_code in declared_codes else "FAIL",
                    f"Observed environment failure_code={failure_code or 'none'}; declared_codes={declared_codes or ['<none>']}",
                    "runtime_contract.environment_skip",
                )
    elif "failure" in contract.get("contract_categories", []):
        add_check(checks["failure"], "contract_source_fallback", "INFO", "Failure checks derived from fixture preset.", "fixture_preset")

    return checks


def compute_final_judgment(
    observed_result: str,
    observed_failure_code: str,
    checks: Dict[str, List[Dict[str, str]]],
) -> Dict[str, Any]:
    """把检查矩阵收敛为最终 S5 verdict。

    如果 judge 发现 contract 层面的失败，它会覆盖原始观测结果，
    因为产品契约比 provider 的局部判断更严格。
    """

    first_fail = find_first_status(checks, {"FAIL"})
    first_warn = find_first_status(checks, {"WARN"})

    if first_fail is not None:
        category = str(first_fail["category"])
        name = str(first_fail["name"])
        return {
            "verdict": "FAIL",
            "failure_kind": failure_kind_for_check(category, name),
            "failure_code": failure_code_for_check(category, name),
            "judge_basis": first_fail,
        }

    if observed_result == "FAIL":
        return {
            "verdict": "FAIL",
            "failure_kind": map_failure_kind(observed_result, observed_failure_code),
            "failure_code": observed_failure_code or "none",
            "judge_basis": None,
        }

    if observed_result == "ENVIRONMENT-SKIP":
        return {
            "verdict": "ENVIRONMENT-SKIP",
            "failure_kind": "environment",
            "failure_code": observed_failure_code or "none",
            "judge_basis": None,
        }

    if first_warn is not None or observed_result == "WARN":
        basis = first_warn
        failure_kind = failure_kind_for_check(str(basis["category"]), str(basis["name"])) if basis else "implementation"
        failure_code = failure_code_for_check(str(basis["category"]), str(basis["name"])) if basis else (observed_failure_code or "none")
        return {
            "verdict": "WARN",
            "failure_kind": failure_kind,
            "failure_code": failure_code,
            "judge_basis": basis,
        }

    return {
        "verdict": "PASS",
        "failure_kind": "none",
        "failure_code": "none",
        "judge_basis": None,
    }


def render_summary(
    summary_message: str,
    observed_result: str,
    observed_failure_code: str,
    final_result: str,
    final_failure_code: str,
    judge_basis: Optional[Dict[str, Any]],
) -> str:
    """渲染摘要区块，并在需要时带上 judge override 说明。"""

    summary = summary_message.strip() or "No runtime summary was provided."
    observed_code = observed_failure_code or "none"
    final_code = final_failure_code or "none"
    if observed_result == final_result and observed_code == final_code:
        return summary
    override = f"Judge override: observed `{observed_result}` / `{observed_code}`, final `{final_result}` / `{final_code}`."
    if judge_basis:
        override += (
            f" Triggered by `{judge_basis.get('category', 'unknown')}.{judge_basis.get('name', 'unknown')}`: "
            f"{judge_basis.get('detail', 'no detail')}"
        )
    return f"{summary}\n\n{override}"


def render_report(
    run_root: Path,
    target_root: Path,
    fixture: str,
    entry_skill: str,
    observed_result: str,
    observed_failure_kind: str,
    observed_failure_code: str,
    final_result: str,
    final_failure_kind: str,
    final_failure_code: str,
    summary_message: str,
    judge_basis: Optional[Dict[str, Any]],
    contract: Dict[str, Any],
    checks: Dict[str, List[Dict[str, str]]],
) -> str:
    """渲染人类可读的 validation-runtime-report.md 文档。"""

    summary_block = render_summary(
        summary_message,
        observed_result,
        observed_failure_code,
        final_result,
        final_failure_code,
        judge_basis,
    )
    lines = [
        "# Runtime Validation Report",
        "",
        f"- Run root: `{run_root}`",
        f"- Target root: `{target_root}`",
        f"- Fixture: `{fixture}`",
        f"- Entry skill: `{entry_skill}`",
        f"- Observed result: `{observed_result}`",
        f"- Observed failure kind: `{observed_failure_kind}`",
        f"- Observed failure code: `{observed_failure_code or 'none'}`",
        f"- Final verdict: `{final_result}`",
        f"- Final failure kind: `{final_failure_kind}`",
        f"- Final failure code: `{final_failure_code or 'none'}`",
        f"- Contract source: `{contract.get('contract_source', 'unknown')}`",
        f"- Contract categories: `{', '.join(contract.get('contract_categories', [])) or 'none'}`",
        "",
        "## Summary",
        "",
        summary_block,
        "",
    ]
    if contract.get("spec_path"):
        lines.extend(
            [
                "## Spec Source",
                "",
                f"- `{contract['spec_path']}`",
                "",
            ]
        )

    for category in CATEGORY_ORDER:
        lines.extend([f"## {category.title()} Checks", ""])
        bucket = checks.get(category, [])
        if not bucket:
            lines.append("- No checks were derived for this category.")
            lines.append("")
            continue
        for item in bucket:
            lines.append(
                f"- [{item['status']}] `{item['name']}`: {item['detail']} (source: `{item['source']}`)"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    """解析独立执行 S5 judgment 所需的命令行参数。"""

    parser = argparse.ArgumentParser(description="Write S5 validation outputs from RUN_ROOT evidence")
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--target-root", required=True)
    parser.add_argument("--result", required=True, choices=sorted(RESULTS))
    parser.add_argument("--failure-code", default="")
    parser.add_argument("--summary-message", default="")
    parser.add_argument("--entry-skill", default="")
    parser.add_argument("--request", default="")
    parser.add_argument("--fixture", default="")
    parser.add_argument("--provider", default="")
    parser.add_argument("--fallback-contract-categories", default="")
    parser.add_argument("--checked-file", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    """运行确定性的 S5 judgment，并同时产出报告和 JSON 摘要。"""

    args = parse_args()
    run_root = Path(args.run_root).resolve()
    target_root = Path(args.target_root).resolve()
    fallback_categories = [item.strip() for item in args.fallback_contract_categories.split(",") if item.strip()]
    contract = derive_contract(run_root, fallback_categories)
    checks = build_checks(
        run_root,
        target_root,
        args.result,
        args.failure_code.strip(),
        args.summary_message.strip(),
        args.entry_skill.strip(),
        args.request,
        args.checked_file,
        contract,
    )
    observed_failure_kind = map_failure_kind(args.result, args.failure_code.strip())
    final_judgment = compute_final_judgment(args.result, args.failure_code.strip(), checks)
    summary_path = run_root / "outputs" / "stages" / "s5-validation-summary.json"
    report_path = run_root / "validation-runtime-report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    report_text = render_report(
        run_root,
        target_root,
        args.fixture.strip(),
        args.entry_skill.strip(),
        args.result,
        observed_failure_kind,
        args.failure_code.strip(),
        str(final_judgment["verdict"]),
        str(final_judgment["failure_kind"]),
        str(final_judgment["failure_code"]),
        args.summary_message.strip(),
        final_judgment.get("judge_basis"),
        contract,
        checks,
    )
    report_path.write_text(report_text, encoding="utf-8", newline="\n")

    payload = {
        "verdict": final_judgment["verdict"],
        "failure_kind": final_judgment["failure_kind"],
        "failure_code": final_judgment["failure_code"],
        "observed_verdict": args.result,
        "observed_failure_kind": observed_failure_kind,
        "observed_failure_code": args.failure_code.strip() or "none",
        "environment_reason": args.summary_message.strip() if args.result == "ENVIRONMENT-SKIP" else None,
        "contract_source": contract.get("contract_source"),
        "contract_categories": contract.get("contract_categories", []),
        "implemented_failure_kinds": contract.get("implemented_failure_kinds", []),
        "environment_skip_codes": contract.get("environment_skip_codes", []),
        "provider": args.provider.strip() or None,
        "checked_files": sorted({*args.checked_file, *SELF_GENERATED_FILES}),
        "checks_by_category": checks,
        "judge_basis": final_judgment.get("judge_basis"),
        "summary": args.summary_message.strip(),
        "report_path": str(report_path),
    }
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"[{payload['verdict']}] wrote {report_path} and {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
