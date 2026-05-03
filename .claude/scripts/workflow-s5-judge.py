#!/usr/bin/env python3
"""
为 WorkflowProgram RUN_ROOT 生成具备 contract 感知能力的 S5 校验结果。

该 judge 刻意保持确定性：
- 输入：RUN_ROOT 证据、TARGET_ROOT 资产、可选的 workflow-spec.yaml
- 输出：validation-runtime-report.md + outputs/stages/s5-validation-summary.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.capability_discovery import capability_discovery_from_spec
from lib.failure_codes import failure_kind_for_result
from lib.host_team_utils import TEAM_EVENT_TYPES, agent_team_contract_from_spec, agent_team_enabled, host_capabilities_from_spec
from lib.reporting import with_report_fields
from lib.spec_utils import path_matches_any, stage_slot_id_map
from lib.yaml_utils import try_load_yaml_mapping


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

    return try_load_yaml_mapping(path)


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


def is_managed_target_path(path: str) -> bool:
    return (
        path.startswith(".claude/")
        or path.startswith(".workflowprogram/design/")
        or path.startswith(".workflowprogram/runtime/")
    )


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


def matching_paths(paths: List[str], pattern: str) -> List[str]:
    """按单个 glob 模式过滤路径列表。"""

    import fnmatch

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
    if "host_capability" in lowered_name:
        return "environment"
    if "environment" in lowered_name:
        return "environment"
    if "team_fan_out" in lowered_name or "team_join" in lowered_name or "team_execution" in lowered_name:
        return "implementation"
    if "team_contract" in lowered_name or "team_evidence" in lowered_name:
        return "design"
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


def is_workflowprogram_product_entry(entry_skill: str) -> bool:
    """判断当前入口是否是 WorkflowProgram 自身的产品命令。"""

    return entry_skill.startswith("workflowprogram-")


def registered_entry_names(spec: Dict[str, Any]) -> set[str]:
    """从 workflow spec 中提取目标工作流已注册的 commands/skills 名称。"""

    registry = spec.get("registry", {})
    if not isinstance(registry, dict):
        return set()

    names: set[str] = set()
    for section in ("commands", "skills"):
        items = registry.get(section, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                text = str(item.get("name", "")).strip()
            else:
                text = str(item).strip()
            if text:
                names.add(text)
    return names


def registered_asset_paths(spec: Dict[str, Any]) -> set[str]:
    """从 registry 中提取所有目标资产路径。"""

    registry = spec.get("registry", {})
    if not isinstance(registry, dict):
        return set()
    paths: set[str] = set()
    for section in ("commands", "skills", "agents", "hooks", "runtime_assets"):
        items = registry.get(section, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                path = str(item.get("file", "")).strip()
                if path:
                    paths.add(path)
    return paths


def declared_artifact_patterns(spec: Dict[str, Any]) -> set[str]:
    """收集 test_contract 中声明的交付物和可选输出 pattern。"""

    test_contract = spec.get("test_contract", {}) if isinstance(spec, dict) else {}
    artifacts = test_contract.get("artifacts", {}) if isinstance(test_contract, dict) else {}
    if not isinstance(artifacts, dict):
        return set()
    values: set[str] = set()
    for field in ("deliverables", "optional_outputs"):
        items = artifacts.get(field, [])
        if isinstance(items, list):
            values.update(str(item).strip() for item in items if str(item).strip())
    return values


def is_declared_target_asset(path: str, registry_paths: set[str], artifact_patterns: set[str]) -> bool:
    """判断 target asset 是否被 registry 或 artifact contract 声明。"""

    if path in registry_paths or path in artifact_patterns:
        return True
    return any(path_matches_any(path, [pattern]) for pattern in artifact_patterns)


def report_schema_errors(payload: Dict[str, Any], expected_schema_name: str) -> List[str]:
    """校验 JSON 报告的公共字段。"""

    errors: List[str] = []
    if not payload:
        errors.append("missing or invalid JSON")
        return errors
    if payload.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    schema_name = str(payload.get("schema_name", "")).strip()
    if schema_name != expected_schema_name:
        errors.append(f"schema_name must be {expected_schema_name}, got {schema_name or '<missing>'}")
    if "error_code" not in payload:
        errors.append("error_code is required")
    if "failure_kind" not in payload:
        errors.append("failure_kind is required")
    if "remediation" not in payload:
        errors.append("remediation is required")
    return errors


def expected_flow_for_intent(spec: Dict[str, Any], intent: str) -> tuple[List[str], List[str], List[str], str] | None:
    """解析某个 intent flow 对应的 required/optional/allowed stage id。"""

    intent_flows = spec.get("intent_flows", {})
    if not isinstance(intent_flows, dict):
        return None
    flow = intent_flows.get(intent, {})
    if not isinstance(flow, dict):
        return None
    slot_map = stage_slot_id_map(spec.get("stages", []))
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


def run_host_probe(spec_path: Path, target_root: Path, run_root: Path, output_name: str) -> Dict[str, Any]:
    """复用标准 host probe 脚本，生成当前宿主的实时就绪报告。"""

    payload = run_validator(
        "probe-host-capabilities.py",
        "--spec",
        str(spec_path),
        "--target-root",
        str(target_root),
        "--run-root",
        str(run_root),
    )
    report = payload.get("report", {}) if isinstance(payload, dict) else {}
    if isinstance(report, dict) and report:
        target_path = run_root / "outputs" / "stages" / output_name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report if isinstance(report, dict) else {}


def run_environment_remediation(spec_path: Path, target_root: Path, run_root: Path) -> Dict[str, Any]:
    """基于当前 run 证据与历史失败生成环境修复提案。"""

    payload = run_validator(
        "generate-environment-remediation.py",
        "--spec",
        str(spec_path),
        "--target-root",
        str(target_root),
        "--run-root",
        str(run_root),
    )
    report = payload.get("report", {}) if isinstance(payload, dict) else {}
    return report if isinstance(report, dict) else {}


def load_event_types(path: Path) -> List[str]:
    if not path.exists():
        return []
    event_types: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            text = str(payload.get("type", "")).strip()
            if text:
                event_types.append(text)
    return event_types


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
    provider_name: str,
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
    derived_failure_kind = failure_kind_for_result(result, failure_code)
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
    generated_registry_entries = registered_entry_names(spec)
    declared_host_capabilities = host_capabilities_from_spec(spec) if isinstance(spec, dict) else []
    declared_capability_discovery = capability_discovery_from_spec(spec) if isinstance(spec, dict) else {}
    capability_discovery_enabled = bool(declared_capability_discovery.get("enabled", False))
    declared_agent_team = agent_team_contract_from_spec(spec) if isinstance(spec, dict) else {}
    team_enabled = agent_team_enabled(declared_agent_team)
    event_types = load_event_types(run_root / "events.jsonl")

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
            if is_workflowprogram_product_entry(entry_skill):
                registered = declared_entry in generated_registry_entries
                add_check(
                    checks["entry"],
                    "declared_generated_main_entry_registered",
                    "PASS" if registered else "FAIL",
                    (
                        f"WorkflowProgram product entry={entry_skill}; generated workflow main_entry={declared_entry}; "
                        f"registered_entries={sorted(generated_registry_entries) or ['<none>']}"
                    ),
                    "test_contract.entry.main_entry",
                )
                add_check(
                    checks["entry"],
                    "workflowprogram_product_entry_wraps_generated_entry",
                    "PASS",
                    f"WorkflowProgram product entry {entry_skill} is allowed to wrap generated workflow main_entry={declared_entry}.",
                    "workflowprogram.product_entry",
                )
            else:
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
        managed_rollback = load_json(run_root / "outputs" / "managed-rollback-manifest.json")
        managed_recover_path = run_root / "outputs" / "managed-recover-instructions.md"
        if managed_entries or managed_result:
            for report_name, payload, schema_name in (
                ("managed-change-plan", managed_plan, "managed-change-plan"),
                ("managed-change-result", managed_result, "managed-change-result"),
            ):
                schema_errors = report_schema_errors(payload, schema_name)
                add_check(
                    checks["boundary"],
                    f"{report_name}_schema_fields",
                    "PASS" if not schema_errors else "FAIL",
                    "; ".join(schema_errors) or f"{report_name} has common report schema fields.",
                    f"outputs/{report_name}.json",
                )
            rollback_schema_errors = report_schema_errors(managed_rollback, "managed-rollback-manifest")
            add_check(
                checks["boundary"],
                "managed_recovery_evidence_present",
                "PASS" if managed_rollback and managed_recover_path.exists() and not rollback_schema_errors else "FAIL",
                (
                    f"rollback_manifest={'present' if managed_rollback else 'missing'}; "
                    f"recover_instructions={'present' if managed_recover_path.exists() else 'missing'}; "
                    f"schema_errors={rollback_schema_errors or ['<none>']}"
                ),
                "outputs/managed-rollback-manifest.json",
            )
            expected_recovery_paths = {
                str(item.get("relative_path", "")).strip()
                for item in [*managed_result.get("applied", []), *managed_conflicts]
                if isinstance(item, dict) and str(item.get("relative_path", "")).strip()
            }
            rollback_entries = managed_rollback.get("entries", []) if isinstance(managed_rollback.get("entries"), list) else []
            rollback_paths = {
                str(item.get("relative_path", "")).strip()
                for item in rollback_entries
                if isinstance(item, dict) and str(item.get("relative_path", "")).strip()
            }
            missing_recovery_paths = sorted(expected_recovery_paths - rollback_paths)
            add_check(
                checks["boundary"],
                "managed_recovery_paths_covered",
                "PASS" if not missing_recovery_paths else "FAIL",
                f"missing rollback coverage={missing_recovery_paths or ['<none>']}",
                "outputs/managed-rollback-manifest.json",
            )
            registry_paths = registered_asset_paths(spec)
            artifact_patterns = declared_artifact_patterns(spec)
            undeclared_assets = [
                path
                for path in managed_rel_paths
                if is_managed_target_path(path) and not is_declared_target_asset(path, registry_paths, artifact_patterns)
            ]
            add_check(
                checks["boundary"],
                "managed_target_assets_declared",
                "PASS" if not undeclared_assets else "FAIL",
                f"undeclared managed target assets={undeclared_assets or ['<none>']}",
                "workflow-spec.yaml.registry",
            )
        managed_policy = str(boundary.get("managed_overwrite_policy", "")).strip()
        changed_managed_paths = [
            item for item in changed_target_paths if is_managed_target_path(item) and item in before_target_index
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
    if state:
        state_schema_errors = []
        if state.get("schema_version") != 1:
            state_schema_errors.append("schema_version must be 1")
        if not str(state.get("schema_name", "")).strip():
            state_schema_errors.append("schema_name is required")
        add_check(
            checks["flow"],
            "state_schema_fields",
            "PASS" if not state_schema_errors else "FAIL",
            "; ".join(state_schema_errors) or "state.json has common schema fields.",
            "state.json",
        )
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
        provider_stage_status = str(parsed_provider.get("stage_status", "")).strip() or str(provider_result.get("stage_status", "")).strip()
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
        provider_recovery = str(parsed_provider.get("next_stage_on_failure", "")).strip() or str(provider_result.get("next_stage_on_failure", "")).strip()
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
            summary_matches = (
                summary_entry == entry_skill
                and (
                    summary_status == result
                    or (
                        summary_status == "PASS"
                        and derived_failure_kind == "environment"
                        and declared_host_capabilities
                    )
                )
            )
            add_check(
                checks["artifacts"],
                "runner_summary_matches_observed",
                "PASS" if summary_matches else "FAIL",
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
                clarification_package = run_validator(
                    "generate-clarification-package.py",
                    "--spec",
                    str(draft_path),
                    "--run-root",
                    str(run_root),
                )
                package_detail = "; ".join(
                    [*clarification_package.get("errors", []), *clarification_package.get("warnings", [])]
                ) or "Structured clarification package generated."
                add_check(
                    checks["artifacts"],
                    "clarification_package_generated",
                    "PASS" if clarification_package.get("status") == "PASS" else "FAIL",
                    package_detail,
                    "generate-clarification-package.py",
                )
                clarification_review = run_validator(
                    "generate-clarification-review.py",
                    "--spec",
                    str(draft_path),
                    "--run-root",
                    str(run_root),
                )
                review_detail = "; ".join(
                    [*clarification_review.get("errors", []), *clarification_review.get("warnings", [])]
                ) or "Internal challenge review and downstream handoff artifacts generated."
                add_check(
                    checks["artifacts"],
                    "clarification_review_generated",
                    "PASS" if clarification_review.get("status") == "PASS" else "FAIL",
                    review_detail,
                    "generate-clarification-review.py",
                )
                for rel_path, check_name in (
                    ("outputs/stages/clarification-record.json", "clarification_record_exists"),
                    ("outputs/stages/open-questions.json", "clarification_open_questions_exists"),
                    ("outputs/stages/assumption-log.md", "clarification_assumption_log_exists"),
                    ("outputs/stages/design-readiness-report.json", "clarification_design_readiness_exists"),
                    ("outputs/stages/clarification-challenge-report.json", "clarification_challenge_report_exists"),
                    ("outputs/stages/clarification-handoff.json", "clarification_handoff_exists"),
                    ("outputs/stages/clarification-evidence.json", "clarification_evidence_exists"),
                ):
                    artifact_path = run_root / rel_path
                    add_check(
                        checks["artifacts"],
                        check_name,
                        "PASS" if artifact_path.exists() else "FAIL",
                        f"{rel_path} {'exists' if artifact_path.exists() else 'is missing'} at {artifact_path}",
                        rel_path,
                    )
                draft_validation = run_validator(
                    "validate-workflow-draft.py",
                    "--spec",
                    str(draft_path),
                    "--run-root",
                    str(run_root),
                )
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
        environment_remediation_report: Dict[str, Any] = {}
        if declared_host_capabilities:
            remediation_spec_for_s6 = run_root / "workflow-spec.yaml"
            target_spec_for_s6 = target_root / ".workflowprogram" / "design" / "workflow-spec.yaml"
            if observed_intent_text in {"validate", "audit"} and target_spec_for_s6.exists():
                remediation_spec_for_s6 = target_spec_for_s6
            environment_remediation_report = run_environment_remediation(remediation_spec_for_s6, target_root, run_root)
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
                if text == ".workflowprogram/design/workflow-spec.yaml":
                    target_spec_path = target_root / ".workflowprogram" / "design" / "workflow-spec.yaml"
                    target_spec = load_yaml(target_spec_path)
                    run_spec = load_yaml(run_root / "workflow-spec.yaml")
                    add_check(
                        checks["artifacts"],
                        "persistent_workflow_spec_valid",
                        "PASS" if target_spec else "FAIL",
                        f"Persistent workflow-spec.yaml {'parsed successfully' if target_spec else 'is missing or invalid'} at {target_spec_path}",
                        "TARGET_ROOT/.workflowprogram/design/workflow-spec.yaml",
                    )
                    if target_spec and run_spec:
                        add_check(
                            checks["artifacts"],
                            "persistent_workflow_spec_matches_run_spec",
                            "PASS" if target_spec == run_spec else "FAIL",
                            "Persistent workflow-spec.yaml should match RUN_ROOT/workflow-spec.yaml for this develop run.",
                            "TARGET_ROOT/.workflowprogram/design/workflow-spec.yaml",
                        )
                if text == ".workflowprogram/design/workflow-view.md":
                    target_view_path = target_root / ".workflowprogram" / "design" / "workflow-view.md"
                    view_exists = target_view_path.exists()
                    view_content = target_view_path.read_text(encoding="utf-8") if view_exists else ""
                    add_check(
                        checks["artifacts"],
                        "persistent_workflow_view_valid",
                        "PASS" if view_exists and "Generated at" in view_content and "workflow-spec.yaml" in view_content else "FAIL",
                        f"Persistent workflow-view.md {'exists and points back to workflow-spec.yaml' if view_exists else 'is missing'} at {target_view_path}",
                        "TARGET_ROOT/.workflowprogram/design/workflow-view.md",
                    )
                if text == ".workflowprogram/design/workflow-lowlevel.md":
                    target_spec_path = target_root / ".workflowprogram" / "design" / "workflow-spec.yaml"
                    target_lowlevel_path = target_root / ".workflowprogram" / "design" / "workflow-lowlevel.md"
                    lowlevel_validation = run_validator(
                        "validate-workflow-lowlevel.py",
                        "--spec",
                        str(target_spec_path),
                        "--lowlevel",
                        str(target_lowlevel_path),
                    )
                    lowlevel_errors = [str(item) for item in lowlevel_validation.get("errors", [])]
                    lowlevel_warnings = [str(item) for item in lowlevel_validation.get("warnings", [])]
                    add_check(
                        checks["artifacts"],
                        "persistent_workflow_lowlevel_valid",
                        "PASS" if not lowlevel_errors else "FAIL",
                        "workflow-lowlevel.md passed deterministic validation."
                        if not lowlevel_errors
                        else "; ".join([*lowlevel_errors, *lowlevel_warnings[:3]]),
                        "TARGET_ROOT/.workflowprogram/design/workflow-lowlevel.md",
                    )
        generated_runtime_contract = spec.get("generated_runtime_contract", {}) if isinstance(spec, dict) else {}
        runtime_root_rel = str(generated_runtime_contract.get("runtime_root", "")).strip() if isinstance(generated_runtime_contract, dict) else ""
        runtime_root_path = target_root / runtime_root_rel if runtime_root_rel else None
        should_validate_generated_runtime = (
            isinstance(generated_runtime_contract, dict)
            and bool(generated_runtime_contract)
            and (
                observed_intent_text == "develop"
                or (runtime_root_path is not None and runtime_root_path.exists())
            )
        )
        if should_validate_generated_runtime:
            target_spec_path = target_root / ".workflowprogram" / "design" / "workflow-spec.yaml"
            runtime_validation = run_validator(
                "validate-generated-runtime.py",
                "--spec",
                str(target_spec_path),
                "--target-root",
                str(target_root),
            )
            runtime_errors = [str(item) for item in runtime_validation.get("errors", [])]
            runtime_warnings = [str(item) for item in runtime_validation.get("warnings", [])]
            add_check(
                checks["artifacts"],
                "persistent_generated_runtime_valid",
                "PASS" if not runtime_errors else "FAIL",
                "generated target runtime assets passed deterministic validation."
                if not runtime_errors
                else "; ".join([*runtime_errors, *runtime_warnings[:3]]),
                "TARGET_ROOT/.workflowprogram/runtime/",
            )
        if capability_discovery_enabled:
            discovery_report_path = run_root / "outputs" / "stages" / "host-capability-candidates.json"
            discovery_instructions_path = run_root / "outputs" / "stages" / "host-bootstrap-instructions.md"
            discovery_report = load_json(discovery_report_path)
            discovery_candidates = discovery_report.get("candidates", []) if isinstance(discovery_report.get("candidates"), list) else []
            discovery_profiles = discovery_report.get("profiles", []) if isinstance(discovery_report.get("profiles"), list) else []
            effective_domains = discovery_report.get("effective_domains", []) if isinstance(discovery_report.get("effective_domains"), list) else []
            instructions_text = discovery_instructions_path.read_text(encoding="utf-8") if discovery_instructions_path.exists() else ""
            unresolved_candidates = [
                item
                for item in discovery_candidates
                if isinstance(item, dict) and str(item.get("status", "")).strip() in {"missing", "recommended"}
            ]
            structured_guidance_errors = [
                str(item.get("id", "<unknown>")).strip() or "<unknown>"
                for item in unresolved_candidates
                if not isinstance(item.get("manual_steps"), list)
                or not item.get("manual_steps")
                or not isinstance(item.get("expected_outputs"), list)
                or not item.get("expected_outputs")
                or not str(item.get("recheck_hint", "")).strip()
            ]
            add_check(
                checks["artifacts"],
                "capability_discovery_report_present",
                "PASS" if discovery_report else "FAIL",
                f"capability discovery report path={discovery_report_path}; candidates={len(discovery_candidates)}; domains={effective_domains or ['<none>']}",
                "capability_discovery",
            )
            add_check(
                checks["artifacts"],
                "capability_discovery_instructions_present",
                "PASS" if discovery_instructions_path.exists() and "## Manual Follow-Up" in instructions_text else "FAIL",
                f"bootstrap instructions path={discovery_instructions_path}; present={discovery_instructions_path.exists()}",
                "capability_discovery",
            )
            add_check(
                checks["artifacts"],
                "capability_discovery_manual_guidance_structured",
                "PASS" if not structured_guidance_errors else "FAIL",
                f"unresolved candidates missing manual guidance={structured_guidance_errors or ['<none>']}",
                "capability_discovery",
            )
            add_check(
                checks["artifacts"],
                "capability_discovery_profiles_present",
                "PASS" if not effective_domains or discovery_profiles else "FAIL",
                f"profile domains={[str(item.get('domain', '')).strip() for item in discovery_profiles if isinstance(item, dict)] or ['<none>']}",
                "capability_discovery",
            )
            reverse_profiles = [
                item
                for item in discovery_profiles
                if isinstance(item, dict) and str(item.get("domain", "")).strip() == "reverse_engineering"
            ]
            reverse_team_missing = [
                "reverse_engineering"
                for item in reverse_profiles
                if bool(item.get("team_default_recommended", False)) and not isinstance(item.get("suggested_agent_team_contract"), dict)
            ]
            add_check(
                checks["artifacts"],
                "capability_discovery_team_defaults_present",
                "PASS" if not reverse_team_missing else "FAIL",
                f"profiles missing suggested team defaults={reverse_team_missing or ['<none>']}",
                "capability_discovery",
            )
            add_check(
                checks["artifacts"],
                "capability_discovery_candidates_status",
                "PASS" if discovery_candidates else "INFO",
                f"candidate ids={[str(item.get('id', '')).strip() for item in discovery_candidates if isinstance(item, dict)] or ['<none>']}",
                "capability_discovery",
            )
        if declared_host_capabilities:
            host_report_path = run_root / "outputs" / "stages" / "host-capability-report.json"
            if observed_intent_text in {"validate", "audit"}:
                target_spec_path = target_root / ".workflowprogram" / "design" / "workflow-spec.yaml"
                spec_for_probe = target_spec_path if target_spec_path.exists() else (run_root / "workflow-spec.yaml")
                host_report = run_host_probe(spec_for_probe, target_root, run_root, "host-capability-probe.json")
                host_report_source = str(spec_for_probe)
            else:
                host_report = load_json(host_report_path)
                if not host_report:
                    host_report = run_host_probe(run_root / "workflow-spec.yaml", target_root, run_root, "host-capability-probe.json")
                    host_report_source = "probe-host-capabilities.py"
                else:
                    host_report_source = str(host_report_path)
            remediation_spec_path = spec_for_probe if observed_intent_text in {"validate", "audit"} else (run_root / "workflow-spec.yaml")
            remediation_report = run_environment_remediation(remediation_spec_path, target_root, run_root)
            environment_remediation_report = remediation_report if remediation_report else environment_remediation_report
            remediation_guide_path = run_root / "outputs" / "stages" / "environment-remediation-guide.md"
            host_items = host_report.get("capabilities", []) if isinstance(host_report.get("capabilities"), list) else []
            host_schema_errors = report_schema_errors(host_report, "host-capability-report")
            add_check(
                checks["artifacts"],
                "host_capability_report_present",
                "PASS" if host_items else "FAIL",
                f"host capability report source={host_report_source}; items={len(host_items)}",
                "host_capabilities",
            )
            add_check(
                checks["artifacts"],
                "host_capability_report_schema_fields",
                "PASS" if not host_schema_errors else "FAIL",
                "; ".join(host_schema_errors) or "host capability report has common report schema fields.",
                "outputs/stages/host-capability-report.json",
            )
            required_missing = [
                str(item.get("id", "")).strip()
                for item in host_items
                if isinstance(item, dict) and bool(item.get("required", False)) and str(item.get("status", "")).strip() != "ready"
            ]
            optional_missing = [
                str(item.get("id", "")).strip()
                for item in host_items
                if isinstance(item, dict) and not bool(item.get("required", False)) and str(item.get("status", "")).strip() != "ready"
            ]
            add_check(
                checks["artifacts"],
                "host_capability_required_ready",
                "PASS" if not required_missing else "FAIL",
                f"required missing={required_missing or ['<none>']}",
                "host_capabilities",
            )
            add_check(
                checks["artifacts"],
                "host_capability_optional_status",
                "PASS" if not optional_missing else "INFO",
                f"optional not-ready={optional_missing or ['<none>']}",
                "host_capabilities",
            )
            remediation_payload = remediation_report or environment_remediation_report
            remediation_schema_errors = report_schema_errors(remediation_payload, "environment-remediation-report") if remediation_payload else []
            user_followups = remediation_payload.get("user_followups", []) if isinstance(remediation_payload.get("user_followups"), list) else []
            repeated_missing = remediation_payload.get("repeated_missing_capabilities", []) if isinstance(remediation_payload.get("repeated_missing_capabilities"), list) else []
            if remediation_payload:
                add_check(
                    checks["artifacts"],
                    "environment_remediation_report_schema_fields",
                    "PASS" if not remediation_schema_errors else "FAIL",
                    "; ".join(remediation_schema_errors) or "environment remediation report has common report schema fields.",
                    "outputs/stages/environment-remediation-report.json",
                )
            prior_environment_run_count = int(remediation_payload.get("prior_environment_run_count", 0) or 0)
            add_check(
                checks["artifacts"],
                "host_capability_remediation_report_present",
                "PASS" if remediation_payload else "FAIL",
                f"remediation report present={bool(remediation_payload)}; prior_environment_run_count={prior_environment_run_count}",
                "environment_remediation",
            )
            guide_text = remediation_guide_path.read_text(encoding="utf-8") if remediation_guide_path.exists() else ""
            add_check(
                checks["artifacts"],
                "host_capability_remediation_guide_present",
                "PASS" if remediation_guide_path.exists() and "## Remediation Actions" in guide_text else "FAIL",
                f"guide path={remediation_guide_path}; present={remediation_guide_path.exists()}",
                "environment_remediation",
            )
            add_check(
                checks["artifacts"],
                "host_capability_manual_steps_visible",
                "PASS" if not required_missing or user_followups else "FAIL",
                f"user followups={[str(item.get('capability_id', '')).strip() for item in user_followups if isinstance(item, dict)] or ['<none>']}",
                "environment_remediation",
            )
            if observed_intent_text == "iterate":
                repeated_status = "PASS" if repeated_missing else ("INFO" if prior_environment_run_count == 0 else "FAIL")
                add_check(
                    checks["artifacts"],
                    "host_capability_repeated_failures_promoted",
                    repeated_status,
                    f"repeated blockers={[str(item.get('capability_id', '')).strip() for item in repeated_missing if isinstance(item, dict)] or ['<none>']}; prior_environment_run_count={prior_environment_run_count}",
                    "environment_remediation",
                )
            project_local_items = [
                item for item in host_items if isinstance(item, dict) and str(item.get("bootstrap_scope", "")).strip() == "project_local"
            ]
            if project_local_items:
                apply_payload = load_json(run_root / "outputs" / "stages" / "host-bootstrap-apply.json")
                bootstrap_manifest_path = target_root / ".workflowprogram" / "bootstrap" / "bootstrap-assets-manifest.json"
                apply_entries = apply_payload.get("applied", []) if isinstance(apply_payload.get("applied"), list) else []
                add_check(
                    checks["artifacts"],
                    "host_bootstrap_apply_recorded",
                    "PASS" if apply_payload or bootstrap_manifest_path.exists() else "FAIL",
                    f"apply_payload={bool(apply_payload)}; bootstrap_manifest={bootstrap_manifest_path.exists()}",
                    "host_capabilities.bootstrap",
                )
                add_check(
                    checks["artifacts"],
                    "host_bootstrap_manifest_present",
                    "PASS" if bootstrap_manifest_path.exists() else "FAIL",
                    f"bootstrap manifest path={bootstrap_manifest_path}; present={bootstrap_manifest_path.exists()}",
                    "host_capabilities.bootstrap",
                )
                expected_outputs = [
                    output
                    for item in project_local_items
                    for output in item.get("project_local_outputs", [])
                    if isinstance(output, str) and output.strip()
                ]
                missing_outputs = [rel for rel in expected_outputs if not (target_root / rel).exists()]
                add_check(
                    checks["artifacts"],
                    "host_bootstrap_outputs_present",
                    "PASS" if not missing_outputs else "FAIL",
                    f"missing outputs={missing_outputs or ['<none>']}",
                    "host_capabilities.bootstrap.project_local_outputs",
                )
                failed_rechecks = [
                    str(entry.get("capability_id", "")).strip()
                    for entry in apply_entries
                    if isinstance(entry, dict) and entry.get("ready_after_apply") is False
                ]
                add_check(
                    checks["artifacts"],
                    "host_bootstrap_recheck_ready",
                    "PASS" if not failed_rechecks else "FAIL",
                    f"failed rechecks={failed_rechecks or ['<none>']}",
                    "host_capabilities.bootstrap",
                )
            host_global_items = [
                item for item in host_items if isinstance(item, dict) and str(item.get("bootstrap_scope", "")).strip() == "host_global"
            ]
            if host_global_items:
                execution_payload = load_json(run_root / "outputs" / "stages" / "host-bootstrap-execution.json")
                attempts = execution_payload.get("attempts", []) if isinstance(execution_payload.get("attempts"), list) else []
                attempted_ids = [str(item.get("capability_id", "")).strip() for item in attempts if isinstance(item, dict)]
                succeeded_ids = [
                    str(item.get("capability_id", "")).strip()
                    for item in attempts
                    if isinstance(item, dict) and str(item.get("status", "")).strip() == "succeeded"
                ]
                add_check(
                    checks["artifacts"],
                    "host_global_bootstrap_execution_recorded",
                    "PASS" if not attempts or execution_payload else "FAIL",
                    f"host_global declared={len(host_global_items)}; attempted={attempted_ids or ['<none>']}",
                    "host_capabilities.bootstrap.adapter",
                )
                add_check(
                    checks["artifacts"],
                    "host_global_bootstrap_attempt_status",
                    "PASS" if not attempts or succeeded_ids else "FAIL",
                    f"succeeded host-global attempts={succeeded_ids or ['<none>']}",
                    "host_capabilities.bootstrap.adapter",
                )
        if team_enabled:
            team_plan = load_json(run_root / "outputs" / "stages" / "team-plan.json")
            team_results = load_json(run_root / "outputs" / "stages" / "team-results.json")
            team_join = load_json(run_root / "outputs" / "stages" / "team-join-summary.json")
            structured_evidence = bool(team_plan) and bool(team_results) and bool(team_join)
            deterministic_provider = provider_name in {"fixture_host", "command_adapter"}
            expected_events_present = TEAM_EVENT_TYPES.issubset(set(event_types))
            evidence_status = "PASS" if structured_evidence and expected_events_present else ("FAIL" if deterministic_provider else "WARN")
            add_check(
                checks["flow"],
                "team_evidence_present",
                evidence_status,
                f"provider={provider_name or '<unknown>'}; structured={structured_evidence}; events={sorted(TEAM_EVENT_TYPES & set(event_types))}",
                "agent_team_contract",
            )
            max_fan_out = int(declared_agent_team.get("max_fan_out", 0) or 0)
            observed_fan_out = int(team_plan.get("fan_out_count", 0) or 0) if team_plan else 0
            add_check(
                checks["flow"],
                "team_fan_out_within_limit",
                "PASS" if not observed_fan_out or observed_fan_out <= max_fan_out else "FAIL",
                f"observed_fan_out={observed_fan_out or 0}; max_fan_out={max_fan_out or 0}",
                "agent_team_contract.max_fan_out",
            )
            join_policy = str(declared_agent_team.get("join_policy", "")).strip()
            join_satisfied = bool(team_join.get("satisfied", False)) if team_join else False
            join_status = "PASS" if (not team_join or join_satisfied) else "FAIL"
            if team_join:
                add_check(
                    checks["flow"],
                    "team_join_policy_satisfied",
                    join_status,
                    f"join_policy={join_policy or '<missing>'}; satisfied={join_satisfied}",
                    "agent_team_contract.join_policy",
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
            "failure_kind": failure_kind_for_result(observed_result, observed_failure_code),
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
        args.provider.strip(),
    )
    observed_failure_kind = failure_kind_for_result(args.result, args.failure_code.strip())
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
    payload = with_report_fields(
        payload,
        schema_name="s5-validation-summary",
        error_code=None if str(final_judgment["failure_code"]) == "none" else str(final_judgment["failure_code"]),
        failure_kind=str(final_judgment["failure_kind"]),
        remediation=[],
    )
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"[{payload['verdict']}] wrote {report_path} and {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
