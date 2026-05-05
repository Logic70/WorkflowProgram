#!/usr/bin/env python3
"""WorkflowProgram smoke 测试用的参考 runtime host 适配器。

这个 mock host 为 runtime_smoke 提供一条确定性的非 Claude 执行路径，
这样无需 Claude 登录也能验证 provider 抽象和 S5 judge。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

SCRIPT_ROOT = Path(__file__).resolve().parents[1] / ".claude" / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from lib.io_utils import iso_now, write_json
from lib.reporting import with_report_fields


def write_text(path: Path, content: str) -> None:
    """创建父目录后写入 UTF-8 文本。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    """向 JSONL 流追加一条 JSON 记录。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def manifest_path_for(target_root: Path) -> Path:
    """Return the managed manifest path used by real managed apply."""
    return target_root / ".workflowprogram" / "managed-files.json"


def copy_runtime_spec(
    repo_root: Path,
    run_root: Path,
    spec_name: str,
    *,
    entry_skill: str,
    deliverables: List[str] | None = None,
    target_root_allow: List[str] | None = None,
    host_capabilities: List[Dict[str, Any]] | None = None,
    agent_team_contract: Dict[str, Any] | None = None,
    capability_discovery: Dict[str, Any] | None = None,
    node_loop_policy: Dict[str, Any] | None = None,
    runtime_capabilities: List[str] | None = None,
) -> None:
    """把 fixture workflow spec 复制到 RUN_ROOT，并按需打补丁。

    mock host 直接复用真实 spec fixture，这样下游 validator 和 judge
    走的仍然是和真实运行一致的解析路径。
    """
    spec_path = repo_root / "tests" / "spec-fixtures" / spec_name
    run_root.mkdir(parents=True, exist_ok=True)
    target_path = run_root / "workflow-spec.yaml"
    payload = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    test_contract = payload.get("test_contract", {})
    if isinstance(test_contract, dict):
        artifacts = test_contract.get("artifacts", {})
        if deliverables is not None and isinstance(artifacts, dict):
            artifacts["deliverables"] = deliverables
    runtime_contract = payload.get("runtime_contract", {})
    if target_root_allow is not None and isinstance(runtime_contract, dict):
        write_boundaries = runtime_contract.get("write_boundaries", {})
        if isinstance(write_boundaries, dict):
            current = write_boundaries.get("target_root_allow", [])
            merged: List[str] = []
            for item in current if isinstance(current, list) else []:
                text = str(item).strip()
                if text and text not in merged:
                    merged.append(text)
            for item in target_root_allow:
                text = str(item).strip()
                if text and text not in merged:
                    merged.append(text)
            write_boundaries["target_root_allow"] = merged
    generated_runtime_contract = payload.get("generated_runtime_contract", {})
    if runtime_capabilities is not None and isinstance(generated_runtime_contract, dict):
        generated_runtime_contract["runtime_capabilities"] = runtime_capabilities
    if host_capabilities is not None:
        payload["host_capabilities"] = host_capabilities
        if isinstance(generated_runtime_contract, dict):
            caps = generated_runtime_contract.get("runtime_capabilities", [])
            if isinstance(caps, list) and "host_capability_probe" not in caps:
                caps.append("host_capability_probe")
                generated_runtime_contract["runtime_capabilities"] = caps
    if agent_team_contract is not None:
        payload["agent_team_contract"] = agent_team_contract
        if isinstance(generated_runtime_contract, dict):
            caps = generated_runtime_contract.get("runtime_capabilities", [])
            if isinstance(caps, list) and "team_orchestration" not in caps:
                caps.append("team_orchestration")
                generated_runtime_contract["runtime_capabilities"] = caps
    if capability_discovery is not None:
        payload["capability_discovery"] = capability_discovery
        if isinstance(generated_runtime_contract, dict):
            caps = generated_runtime_contract.get("runtime_capabilities", [])
            if isinstance(caps, list) and "capability_discovery" not in caps:
                caps.append("capability_discovery")
                generated_runtime_contract["runtime_capabilities"] = caps
    if node_loop_policy is not None:
        graph = payload.get("workflow_graph", {})
        nodes = graph.get("nodes", []) if isinstance(graph, dict) else []
        if isinstance(nodes, list) and nodes:
            nodes[-1]["loop_policy"] = node_loop_policy
        if isinstance(generated_runtime_contract, dict):
            caps = generated_runtime_contract.get("runtime_capabilities", [])
            if isinstance(caps, list) and "node_loop_execution" not in caps:
                caps.append("node_loop_execution")
                generated_runtime_contract["runtime_capabilities"] = caps
    target_path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
        newline="\n",
    )


def host_capability_missing_contract() -> List[Dict[str, Any]]:
    return [
        {
            "id": "missing_binary",
            "kind": "external_binary",
            "name": "Missing Binary",
            "required": True,
            "probe": {
                "binary": "workflowprogram_missing_binary_xyz",
                "args": ["--version"],
            },
            "bootstrap": {
                "scope": "host_global",
                "summary": "Install the missing binary globally",
                "project_local_outputs": [],
            },
            "approval_required": True,
        }
    ]


def host_capability_project_local_contract() -> List[Dict[str, Any]]:
    return [
        {
            "id": "project_local_marker",
            "kind": "external_binary",
            "name": "Project Local Marker",
            "required": True,
            "probe": {
                "binary": "workflowprogram_missing_binary_xyz",
                "args": ["--version"],
            },
            "bootstrap": {
                "scope": "project_local",
                "summary": "Create reusable project-local bootstrap assets",
                "assets": [
                    {
                        "path": ".workflowprogram/bootstrap/project-local-marker.json",
                        "format": "json",
                        "content": {
                            "kind": "project_local_marker",
                            "status": "ready",
                        },
                    },
                    {
                        "path": ".workflowprogram/bootstrap/config/tool-config.json",
                        "format": "json",
                        "content": {
                            "binary": "workflowprogram_missing_binary_xyz",
                            "mode": "project_local",
                            "managed_by": "WorkflowProgram",
                        },
                    },
                    {
                        "path": ".workflowprogram/bootstrap/bin/project-local-wrapper.sh",
                        "format": "shell",
                        "executable": True,
                        "content": "#!/usr/bin/env bash\nprintf 'project-local bootstrap ready\\n'\n",
                    },
                ],
            },
            "approval_required": False,
        }
    ]


def host_capability_host_global_contract(target_root: Path) -> List[Dict[str, Any]]:
    shim_dir = (target_root.parent / "host-global" / "bin").resolve()
    shim_name = "workflowprogram_python3_host_global"
    shim_path = (shim_dir / shim_name).resolve()
    return [
        {
            "id": "host_global_python3_shim",
            "kind": "external_binary",
            "name": "Host Global Python 3 Shim",
            "required": True,
            "probe": {
                "binary": shim_name,
                "args": ["--version"],
                "search_paths": [str(shim_dir)],
            },
            "bootstrap": {
                "scope": "host_global",
                "summary": "Create an approval-gated host-global shim for python3",
                "project_local_outputs": [],
                "adapter": {
                    "type": "symlink_binary",
                    "source_binary": "python3",
                    "target_path": str(shim_path),
                },
            },
            "approval_required": True,
        }
    ]


def agent_team_contract_fixture(*, max_fan_out: int = 2) -> Dict[str, Any]:
    return {
        "enabled": True,
        "max_fan_out": max_fan_out,
        "join_policy": "all_must_pass",
        "roles": [
            {
                "id": "reviewer",
                "responsibility": "Review generated assets",
                "ownership_stage_slots": ["S5"],
                "output_patterns": ["outputs/stages/team/S5/reviewer/review-report.md"],
                "required": True,
            },
            {
                "id": "security_reviewer",
                "responsibility": "Review security-sensitive outputs",
                "ownership_stage_slots": ["S5"],
                "output_patterns": ["outputs/stages/team/S5/security_reviewer/review-report.md"],
                "required": True,
            },
            {
                "id": "lead_reviewer",
                "responsibility": "Join team review results",
                "ownership_stage_slots": ["S5"],
                "output_patterns": ["outputs/stages/team/S5/lead_reviewer/join-summary.md"],
                "required": True,
            },
        ],
        "execution": [
            {
                "stage_slot": "S5",
                "role_ids": ["reviewer", "security_reviewer"],
                "join_role": "lead_reviewer",
            }
        ],
    }


def node_loop_policy_fixture(*, max_iterations: int = 3) -> Dict[str, Any]:
    return {
        "enabled": True,
        "mode": "ralph",
        "goal_source": "model_subgoal",
        "parent_goal_ref": "user_goal.workflow_quality",
        "max_iterations": max_iterations,
        "fresh_context_each_iteration": True,
        "prompt_package": ".workflowprogram/loops/implement/prompt-package.md",
        "tdd_policy": {
            "enabled": True,
            "test_first_required": True,
            "red_green_refactor": True,
        },
        "feedback_commands": [
            {
                "id": "validate_generated_workflow",
                "kind": "test",
                "argv": ["python3", ".workflowprogram/runtime/validate-run-state.py", "--json"],
                "timeout_seconds": 120,
                "failure_effect": "feedback",
            }
        ],
        "stop_conditions": {
            "success": ["verifier_passed"],
            "max_iterations": "fail",
            "no_progress_iterations": 2,
            "hard_fail_on": ["unsafe_write"],
        },
        "evidence_outputs": [
            "outputs/stages/loops/implement/loop-plan.json",
            "outputs/stages/loops/implement/iteration-summary.jsonl",
            "outputs/stages/loops/implement/final-verdict.json",
        ],
    }


def capability_discovery_reverse_engineering() -> Dict[str, Any]:
    return {
        "enabled": True,
        "domains": ["reverse_engineering"],
        "include_local_installed": True,
        "include_curated_profiles": True,
        "infer_from_request": True,
    }


def run_json_script(repo_root: Path, script_name: str, *args: str) -> Dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, str(repo_root / ".claude" / "scripts" / script_name), *args, "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or f"{script_name} failed")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{script_name} returned invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{script_name} must return a JSON object")
    return payload


def write_host_capability_outputs(
    repo_root: Path,
    run_root: Path,
    target_root: Path,
    *,
    apply_project_local: bool,
) -> Dict[str, Any]:
    probe_payload = run_json_script(
        repo_root,
        "probe-host-capabilities.py",
        "--spec",
        str(run_root / "workflow-spec.yaml"),
        "--target-root",
        str(target_root),
        "--run-root",
        str(run_root),
    )
    bootstrap_payload: Dict[str, Any] | None = None
    if apply_project_local:
        bootstrap_args = [
            "--spec",
            str(run_root / "workflow-spec.yaml"),
            "--target-root",
            str(target_root),
            "--run-root",
            str(run_root),
        ]
        bootstrap_payload = run_json_script(
            repo_root,
            "apply-host-bootstrap.py",
            *bootstrap_args,
        )
        probe_payload = run_json_script(
            repo_root,
            "probe-host-capabilities.py",
            "--spec",
            str(run_root / "workflow-spec.yaml"),
            "--target-root",
            str(target_root),
            "--run-root",
            str(run_root),
        )
    return {
        "report": probe_payload.get("report", {}),
        "bootstrap": bootstrap_payload,
    }


def seed_prior_host_capability_failure(target_root: Path, report: Dict[str, Any]) -> None:
    """为 remediation loop 构造一条历史环境失败运行。"""

    prior_run_root = target_root / ".workflowprogram" / "runs" / "prior-host-capability-failure"
    prior_report = dict(report) if isinstance(report, dict) else {}
    prior_report["run_root"] = str(prior_run_root)
    prior_report["target_root"] = str(target_root)
    write_json(prior_run_root / "state.json", {
        "values": {
            "request_id": "prior-host-capability-failure",
            "failure_kind": "environment",
        }
    })
    write_json(prior_run_root / "outputs" / "stages" / "host-capability-report.json", prior_report)


def write_capability_discovery_outputs(repo_root: Path, run_root: Path, target_root: Path, request: str) -> Dict[str, Any]:
    payload = run_json_script(
        repo_root,
        "discover-host-capabilities.py",
        "--spec",
        str(run_root / "workflow-spec.yaml"),
        "--target-root",
        str(target_root),
        "--run-root",
        str(run_root),
        "--request",
        request,
    )
    return {
        "report": payload.get("report", {}),
        "report_path": payload.get("report_path"),
        "instructions_path": payload.get("instructions_path"),
    }


def write_team_evidence(
    run_root: Path,
    contract: Dict[str, Any],
    *,
    overflow: bool = False,
    join_satisfied: bool = True,
) -> None:
    roles = contract.get("roles", []) if isinstance(contract.get("roles"), list) else []
    execution = contract.get("execution", []) if isinstance(contract.get("execution"), list) else []
    fanout_roles = ["reviewer", "security_reviewer"]
    if overflow:
        fanout_roles.append("lead_reviewer")
    plan = {
        "generated_at": iso_now(),
        "execution": execution,
        "fan_out_count": len(fanout_roles),
        "roles": fanout_roles,
        "max_fan_out": contract.get("max_fan_out"),
    }
    results = {
        "generated_at": iso_now(),
        "roles": [
            {"id": role_id, "status": "PASS", "output": f"outputs/stages/team/S5/{role_id}/review-report.md"}
            for role_id in fanout_roles
        ],
    }
    join_summary = {
        "generated_at": iso_now(),
        "join_policy": contract.get("join_policy"),
        "join_role": execution[0].get("join_role") if execution else "",
        "satisfied": join_satisfied,
        "fan_out_count": len(fanout_roles),
    }
    write_json(run_root / "outputs" / "stages" / "team-plan.json", plan)
    write_json(run_root / "outputs" / "stages" / "team-results.json", results)
    write_json(run_root / "outputs" / "stages" / "team-join-summary.json", join_summary)
    for role_id in fanout_roles:
        output_path = run_root / "outputs" / "stages" / "team" / "S5" / role_id / "review-report.md"
        write_text(output_path, f"# Team Output\n\n- role: `{role_id}`\n- status: `PASS`\n")
    append_jsonl(run_root / "events.jsonl", {"ts": iso_now(), "type": "TeamFanOutStart", "stage": "S5", "source": "mock-runtime-host", "status": "ok", "message": "Started team fan-out", "role_ids": fanout_roles})
    for role_id in fanout_roles:
        append_jsonl(run_root / "events.jsonl", {"ts": iso_now(), "type": "TeamRoleStarted", "stage": "S5", "source": "mock-runtime-host", "status": "running", "message": f"Started role {role_id}", "role_id": role_id})
        append_jsonl(run_root / "events.jsonl", {"ts": iso_now(), "type": "TeamRoleCompleted", "stage": "S5", "source": "mock-runtime-host", "status": "ok", "message": f"Completed role {role_id}", "role_id": role_id})
    append_jsonl(run_root / "events.jsonl", {"ts": iso_now(), "type": "TeamJoinCompleted", "stage": "S5", "source": "mock-runtime-host", "status": "ok" if join_satisfied else "error", "message": "Team join completed", "join_policy": contract.get("join_policy"), "satisfied": join_satisfied})


def write_loop_evidence(
    run_root: Path,
    *,
    node_id: str = "implement",
    iterations: int = 2,
    final_status: str = "PASS",
    verifier_passed: bool = True,
    stop_reason: str = "verifier_passed",
) -> None:
    loop_root = run_root / "outputs" / "stages" / "loops" / node_id
    plan = {
        "generated_at": iso_now(),
        "node_id": node_id,
        "mode": "ralph",
        "goal_source": "model_subgoal",
        "parent_goal_ref": "user_goal.workflow_quality",
        "max_iterations": 3,
        "fresh_context_each_iteration": True,
        "test_first_observed": True,
        "prompt_package": f".workflowprogram/loops/{node_id}/prompt-package.md",
    }
    write_json(loop_root / "loop-plan.json", plan)
    iteration_path = loop_root / "iteration-summary.jsonl"
    for index in range(1, iterations + 1):
        status = "PASS" if index == iterations and final_status == "PASS" else "FAIL"
        entry = {
            "iteration": index,
            "status": status,
            "feedback_command_id": "validate_generated_workflow",
            "agent_result": "updated target workflow outputs" if status == "FAIL" else "no changes needed",
            "verifier_passed": status == "PASS",
        }
        append_jsonl(iteration_path, entry)
        iteration_dir = loop_root / "iterations" / str(index)
        write_json(iteration_dir / "feedback-commands.json", {"iteration": index, "commands": [{"id": "validate_generated_workflow", "status": status}]})
        write_json(iteration_dir / "agent-result.json", {"iteration": index, "status": status})
        write_json(iteration_dir / "verifier-result.json", {"iteration": index, "status": status, "passed": status == "PASS"})
    write_json(
        loop_root / "final-verdict.json",
        {
            "generated_at": iso_now(),
            "node_id": node_id,
            "status": final_status,
            "stop_reason": stop_reason,
            "iterations": iterations,
            "verifier_passed": verifier_passed,
        },
    )
    append_jsonl(run_root / "events.jsonl", {"ts": iso_now(), "type": "LoopStart", "stage": "S4", "source": "mock-runtime-host", "status": "ok", "node_id": node_id})
    for index in range(1, iterations + 1):
        append_jsonl(run_root / "events.jsonl", {"ts": iso_now(), "type": "LoopIterationStart", "stage": "S4", "source": "mock-runtime-host", "status": "running", "node_id": node_id, "iteration": index})
        append_jsonl(run_root / "events.jsonl", {"ts": iso_now(), "type": "LoopFeedbackCommandCompleted", "stage": "S4", "source": "mock-runtime-host", "status": "ok", "node_id": node_id, "iteration": index})
        append_jsonl(run_root / "events.jsonl", {"ts": iso_now(), "type": "LoopAgentCompleted", "stage": "S4", "source": "mock-runtime-host", "status": "ok", "node_id": node_id, "iteration": index})
        append_jsonl(run_root / "events.jsonl", {"ts": iso_now(), "type": "LoopVerifierCompleted", "stage": "S4", "source": "mock-runtime-host", "status": "ok", "node_id": node_id, "iteration": index, "passed": index == iterations and verifier_passed})
    append_jsonl(run_root / "events.jsonl", {"ts": iso_now(), "type": "LoopStop", "stage": "S4", "source": "mock-runtime-host", "status": final_status.lower(), "node_id": node_id, "stop_reason": stop_reason})


def infer_intent(entry_skill: str) -> str:
    """根据入口技能名推断 workflow intent。"""
    if entry_skill.endswith("-audit"):
        return "audit"
    if entry_skill.endswith("-validate"):
        return "validate"
    if entry_skill.endswith("-iterate"):
        return "iterate"
    if entry_skill.endswith("-orchestrate"):
        return "orchestrate"
    return "develop"


def stage_history_for_intent(intent: str) -> List[str]:
    """返回给定 intent 对应的模拟 stage history。"""
    if intent == "audit":
        return ["validate", "lessons"]
    if intent == "validate":
        return ["validate"]
    if intent == "iterate":
        return ["lessons"]
    return ["requirement", "context", "design", "generate", "validate", "lessons"]


def derive_failure_kind(category: str) -> str:
    """把 smoke 层失败码映射为 runtime failure_kind。"""
    if category in {"", "none"}:
        return "none"
    if category in {"CONFLICT", "CONFLICT_FAILURE"}:
        return "conflict"
    if category in {"STRUCTURE_FAILURE", "MISSING_ARGUMENT", "INPUT_FAILURE"}:
        return "design"
    if category in {"RUNTIME_HOST_MISSING", "TARGET_NOT_WRITABLE", "RUNTIME_HOST_NOT_READY"}:
        return "environment"
    return "implementation"


def write_workflow_spec_draft(run_root: Path, entry_skill: str, request: str) -> None:
    """为 develop 类流程生成确定性的 S1 草案产物。"""
    draft = "\n".join(
        [
            "# Workflow Specification",
            "",
            "## Workflow Identity",
            "",
            "- 工作流名称：Mock Generated Workflow",
            f"- 触发命令：/{entry_skill}",
            "- 简要描述：由 mock_runtime_host 生成的确定性工作流草案。",
            "",
            "## User Intent",
            "",
            f"- 用户诉求：围绕 `{request.strip() or 'default request'}` 建立清晰的 workflow 方案。",
            "- 最终目的：把用户要解决的问题转成可交付、可验证、可迭代的目标工作流。",
            "- 成功标准：需求、目的、成功标准与质量门禁都已确认，可进入设计阶段。",
            "",
            "## Clarification Summary",
            "",
            "- 澄清轮次：2",
            "- 已确认事项：触发方式；核心输入输出；质量门禁；目标交付物；非目标边界。",
            "- 已消解歧义：用户诉求；最终目的；成功标准；默认交付范围已经明确。",
            "",
            "## Open Questions",
            "",
            "- 阻塞未决问题：无",
            "- 可延后问题：可在 S3 继续细化的命名与文档措辞",
            "- 问题处理策略：阻塞问题必须在 S1 清零；可延后问题进入假设日志并在设计阶段追踪。",
            "",
            "## Assumptions and Boundaries",
            "",
            "- 当前假设：目标项目路径可访问；用户接受托管 workflow 资产；已有约束文件可读取。",
            "- 外部依赖：当前仓库中的 workflow 设计文档；constraints；目标项目现有 `.claude` 资产（如存在）。",
            "- 关键边界场景：审批未完成时不得进入 S4；目标资产冲突时不得静默覆盖；环境依赖缺失时必须显式失败或给出 remediation。",
            "- 明确不做：不直接修改应用代码；不跳过 S5 验证；不绕过 managed apply 边界。",
            "",
            "## Target Workflow Graph Readback",
            "",
            "- 目标 workflow_graph 节点：entry -> generate-assets -> validate-assets",
            "- 目标 workflow_graph 入口与转移：entry 从注册命令进入；entry -> generate-assets；generate-assets -> validate-assets。",
            "- 目标输出是否已映射到 `registry` 或 `test_contract.artifacts`：是，`.claude/` 与 `.workflowprogram/` 交付物均由 registry 或 deliverables 声明。",
            "",
            "## File Plan",
            "",
            "- 需要创建的文件：`.claude/settings.json`；`.claude/commands/example.md`；`.workflowprogram/design/workflow-spec.yaml`；`.workflowprogram/runtime/workflow-entry.py`。",
            "- 需要修改的文件：`.claude/rules/constraints.md`。",
            "",
            "## Readback Confirmation",
            "",
            "- 回读摘要：本工作流将围绕请求形成可验证的 Claude Code workflow 资产，明确交付物、质量门禁和非目标边界。",
            "- 用户确认状态：confirmed",
            "- 最近修正：无",
            "",
            "## Trigger Model",
            "",
            "- 调用方式：手动命令",
            f"- 触发细节：使用 `/{entry_skill}` 处理请求 `{request.strip() or 'default request'}`。",
            "",
            "## Inputs",
            "",
            "- 必需输入：用户请求文本",
            "- 可选输入：目标项目上下文",
            "- 所需外部上下文：当前仓库中的 workflow 设计与约束文件",
            "",
            "## Outputs",
            "",
            "- 主交付物：WorkflowProgram 管理的 `.claude/` 资产",
            "- 次级产物：运行时验证报告与 lessons 增量",
            "- 输出格式：Markdown、YAML、JSON",
            "",
            "## Quality Gates",
            "",
            "- 阻塞条件：审批未完成或运行边界违规",
            "- 必需验证：spec schema、managed apply、S5 runtime judge",
            "- 完成定义：工作流资产生成完成且验证结论为 PASS/WARN",
            "",
        ]
    )
    write_text(run_root / "workflow-spec.md", draft + "\n")


def write_lessons_delta(
    run_root: Path,
    intent: str,
    failure_kind: str,
    request: str,
    *,
    extra_candidates: List[str] | None = None,
) -> None:
    """生成确定性的 S6 lessons delta 产物。"""
    run_id = run_root.name
    body = "\n".join(
        [
            "# S6 Lessons Delta",
            "",
            f"- run_id: `{run_id}`",
            f"- failure_kind: `{failure_kind}`",
            f"- intent: `{intent}`",
            "",
            "## Observations",
            "",
            f"- 本轮请求：`{request.strip() or 'default request'}`",
            "- 控制面证据和阶段流已被写入 RUN_ROOT。",
            "",
            "## Constraint Candidates",
            "",
            "- 继续将运行时证据限制在 RUN_ROOT，并只将托管产物写入 TARGET_ROOT/.claude。",
            *[f"- {item}" for item in (extra_candidates or [])],
            "",
        ]
    )
    write_text(run_root / "outputs" / "stages" / "s6-lessons-delta.md", body + "\n")


def generate_design_docs(repo_root: Path, run_root: Path) -> Dict[str, Path]:
    """基于真实生成器产出 workflow-view.md 与 workflow-lowlevel.md。"""

    spec_path = run_root / "workflow-spec.yaml"
    script_root = repo_root / ".claude" / "scripts"
    outputs = {
        "workflow_spec": spec_path,
        "workflow_view": run_root / "workflow-view.md",
        "workflow_lowlevel": run_root / "workflow-lowlevel.md",
    }
    for script_name, out_path in (
        ("generate-workflow-view.py", outputs["workflow_view"]),
        ("generate-workflow-lowlevel.py", outputs["workflow_lowlevel"]),
    ):
        completed = subprocess.run(
            [
                sys.executable,
                str(script_root / script_name),
                "--spec",
                str(spec_path),
                "--out",
                str(out_path),
                "--json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or f"{script_name} failed")
    return outputs


def generate_target_runtime_assets(repo_root: Path, spec_path: Path, out_root: Path) -> Dict[str, Path]:
    """基于真实生成器产出 target-side runtime 资产。"""

    script_path = repo_root / ".claude" / "scripts" / "generate-target-runtime.py"
    completed = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--spec",
            str(spec_path),
            "--out-root",
            str(out_root),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "generate-target-runtime.py failed")
    payload = json.loads(completed.stdout)
    files = payload.get("files", {})
    return {
        "entry_script": Path(str(files.get("entry_script", ""))).resolve(),
        "runner_script": Path(str(files.get("runner_script", ""))).resolve(),
        "state_validator_script": Path(str(files.get("state_validator_script", ""))).resolve(),
        "runtime_manifest": Path(str(files.get("runtime_manifest", ""))).resolve(),
    }


def write_progress_outputs(
    run_root: Path,
    stage_history: List[str],
    result: str,
    category: str,
    *,
    current_stage: str,
    next_action: str,
    approval_status: str = "approved",
) -> None:
    """写出后续校验步骤所需的 progress 产物。"""
    outputs = run_root / "outputs"
    write_json(
        outputs / "progress" / "current-progress.json",
        {
            "run_id": run_root.name,
            "updated_at": iso_now(),
            "current_stage": current_stage,
            "current_node": current_stage,
            "percent": 100 if result == "PASS" else 80,
            "last_status": "ok" if result == "PASS" else "error",
            "last_verdict": result,
            "next_action": next_action,
            "approval_status": approval_status,
            "stage_history": stage_history,
            "result": result,
            "category": category or None,
        },
    )
    append_jsonl(
        outputs / "progress" / "milestones.jsonl",
        {
            "ts": iso_now(),
            "stage_history": stage_history,
            "result": result,
        },
    )
    write_text(
        outputs / "progress" / "user-progress.md",
        "# Workflow Progress\n\n"
        f"- run_id: `{run_root.name}`\n"
        f"- current_stage: `{current_stage}`\n"
        f"- current_node: `{current_stage}`\n"
        f"- percent: `{100 if result == 'PASS' else 80}`\n"
        f"- last_status: `{'ok' if result == 'PASS' else 'error'}`\n"
        f"- last_verdict: `{result}`\n"
        f"- approval_status: `{approval_status}`\n"
        f"- updated_at: `{iso_now()}`\n\n"
        "## 历史关键节点结果\n\n"
        f"- Stage history: `{', '.join(stage_history) or 'none'}`\n"
        f"- Result: `{result}`\n\n"
        "## Next Action\n\n"
        f"- {next_action}\n",
    )


def write_runner_evidence(
    run_root: Path,
    target_root: Path,
    intent: str,
    entry_skill: str,
    stage_history: List[str],
    result: str,
    category: str,
) -> None:
    """产出由 runner 负责、供 S5 校验消费的最小证据集。"""
    outputs = run_root / "outputs"
    write_json(
        outputs / "stages" / "s0-route.json",
        {
            "intent": intent,
            "entry_skill": entry_skill,
            "target_root": str(target_root),
            "routed_at": iso_now(),
        },
    )
    write_json(
        outputs / "stages" / "runner-summary.json",
        {
            "run_id": run_root.name,
            "status": result,
            "entry_skill": entry_skill,
            "transition_count": len(stage_history),
            "failure_code": category or None,
        },
    )


def write_managed_outputs(run_root: Path, target_root: Path, conflict: bool) -> None:
    """产出确定性的 managed-apply 结果，并可选生成冲突副本。"""
    outputs = run_root / "outputs"
    settings_path = target_root / ".claude" / "settings.json"
    manifest_path = manifest_path_for(target_root)
    candidate_source = run_root / "outputs" / "candidate" / ".claude" / "settings.json"
    write_text(candidate_source, '{\n  "commands": ["example"],\n  "managed": true\n}\n')
    rules_source = run_root / "outputs" / "candidate" / ".claude" / "rules" / "constraints.md"
    command_source = run_root / "outputs" / "candidate" / ".claude" / "commands" / "example.md"
    design_spec_source = run_root / "outputs" / "candidate" / ".workflowprogram" / "design" / "workflow-spec.yaml"
    design_view_source = run_root / "outputs" / "candidate" / ".workflowprogram" / "design" / "workflow-view.md"
    design_lowlevel_source = run_root / "outputs" / "candidate" / ".workflowprogram" / "design" / "workflow-lowlevel.md"
    runtime_root = run_root / "outputs" / "candidate" / ".workflowprogram" / "runtime"
    write_text(rules_source, "# Constraints\n\n- Keep workflow assets managed.\n")
    write_text(command_source, "## Usage\n\n1. Goal\n2. Verify\n")
    design_spec_source.parent.mkdir(parents=True, exist_ok=True)
    for source_path, run_path in (
        (design_spec_source, run_root / "workflow-spec.yaml"),
        (design_view_source, run_root / "workflow-view.md"),
        (design_lowlevel_source, run_root / "workflow-lowlevel.md"),
    ):
        source_path.write_text(run_path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    runtime_files = generate_target_runtime_assets(Path(__file__).resolve().parents[1], run_root / "workflow-spec.yaml", runtime_root)
    plan_entries = [
        {
            "relative_path": ".claude/settings.json",
            "source_path": str(candidate_source),
            "target_path": str(settings_path),
            "decision": "conflict-managed-drift" if conflict else "update",
        },
        {
            "relative_path": ".claude/rules/constraints.md",
            "source_path": str(rules_source),
            "target_path": str(target_root / ".claude" / "rules" / "constraints.md"),
            "decision": "create",
        },
        {
            "relative_path": ".claude/commands/example.md",
            "source_path": str(command_source),
            "target_path": str(target_root / ".claude" / "commands" / "example.md"),
            "decision": "create",
        },
        {
            "relative_path": ".workflowprogram/design/workflow-spec.yaml",
            "source_path": str(design_spec_source),
            "target_path": str(target_root / ".workflowprogram" / "design" / "workflow-spec.yaml"),
            "decision": "create",
        },
        {
            "relative_path": ".workflowprogram/design/workflow-view.md",
            "source_path": str(design_view_source),
            "target_path": str(target_root / ".workflowprogram" / "design" / "workflow-view.md"),
            "decision": "create",
        },
        {
            "relative_path": ".workflowprogram/design/workflow-lowlevel.md",
            "source_path": str(design_lowlevel_source),
            "target_path": str(target_root / ".workflowprogram" / "design" / "workflow-lowlevel.md"),
            "decision": "create",
        },
        {
            "relative_path": ".workflowprogram/runtime/workflow-entry.py",
            "source_path": str(runtime_files["entry_script"]),
            "target_path": str(target_root / ".workflowprogram" / "runtime" / "workflow-entry.py"),
            "decision": "create",
        },
        {
            "relative_path": ".workflowprogram/runtime/workflow-runner.py",
            "source_path": str(runtime_files["runner_script"]),
            "target_path": str(target_root / ".workflowprogram" / "runtime" / "workflow-runner.py"),
            "decision": "create",
        },
        {
            "relative_path": ".workflowprogram/runtime/validate-run-state.py",
            "source_path": str(runtime_files["state_validator_script"]),
            "target_path": str(target_root / ".workflowprogram" / "runtime" / "validate-run-state.py"),
            "decision": "create",
        },
        {
            "relative_path": ".workflowprogram/runtime/runtime-manifest.json",
            "source_path": str(runtime_files["runtime_manifest"]),
            "target_path": str(target_root / ".workflowprogram" / "runtime" / "runtime-manifest.json"),
            "decision": "create",
        },
    ]
    managed_summary = {
        "create": 9,
        "update": 0 if conflict else 1,
        "conflict": 1 if conflict else 0,
    }
    write_json(
        outputs / "managed-change-plan.json",
        with_report_fields(
            {
                "generated_at": iso_now(),
                "entries": plan_entries,
                "summary": managed_summary,
            },
            schema_name="managed-change-plan",
            error_code="CONFLICT" if conflict else None,
            failure_kind="conflict" if conflict else "none",
            remediation=[{"code": "RESOLVE_MANAGED_CONFLICTS", "summary": "Review conflict copies."}] if conflict else [],
        ),
    )
    result_payload: Dict[str, Any] = {
        "generated_at": iso_now(),
        "target_root": str(target_root),
            "run_root": str(run_root),
            "manifest_path": str(manifest_path),
            "summary": managed_summary,
            "applied": [],
        "conflicts": [],
    }
    if conflict:
        # 冲突模式要模拟真实 managed-apply 语义：保留 RUN_ROOT 下的候选副本，
        # 且不直接改动被管理的目标文件。
        conflict_copy = run_root / "outputs" / "conflicts" / ".claude" / "settings.json"
        write_text(conflict_copy, '{"conflict": true}\n')
        result_payload["conflicts"].append(
            {
                "relative_path": ".claude/settings.json",
                "target_path": str(settings_path),
                "decision": "conflict-managed-drift",
                "conflict_copy": str(conflict_copy),
            }
        )
    else:
        for entry in plan_entries:
            result_payload["applied"].append(
                {
                    "relative_path": entry["relative_path"],
                    "action": entry["decision"],
                    "target_path": entry["target_path"],
                    "applied_sha256": "mock-managed-applied-hash",
                    "before_sha256": "mock-managed-before-hash" if entry["decision"] == "update" else None,
                    "before_snapshot": None,
                    "run_id": run_root.name,
                }
            )
    write_json(
        manifest_path,
        {
            "manifest_version": 1,
            "updated_at": iso_now(),
            "entries": (
                []
                if conflict
                else [
                    {
                        "relative_path": ".claude/commands/example.md",
                        "last_applied_hash": "mock-managed-hash-command",
                        "ownership": "workflowprogram",
                        "producer_version": "mock-runtime-host",
                        "updated_at": iso_now(),
                    },
                    {
                        "relative_path": ".claude/rules/constraints.md",
                        "last_applied_hash": "mock-managed-hash-rules",
                        "ownership": "workflowprogram",
                        "producer_version": "mock-runtime-host",
                        "updated_at": iso_now(),
                    },
                    {
                        "relative_path": ".claude/settings.json",
                        "last_applied_hash": "mock-managed-hash",
                        "ownership": "workflowprogram",
                        "producer_version": "mock-runtime-host",
                        "updated_at": iso_now(),
                    },
                    {
                        "relative_path": ".workflowprogram/design/workflow-lowlevel.md",
                        "last_applied_hash": "mock-managed-hash-lowlevel",
                        "ownership": "workflowprogram",
                        "producer_version": "mock-runtime-host",
                        "updated_at": iso_now(),
                    },
                    {
                        "relative_path": ".workflowprogram/design/workflow-spec.yaml",
                        "last_applied_hash": "mock-managed-hash-spec",
                        "ownership": "workflowprogram",
                        "producer_version": "mock-runtime-host",
                        "updated_at": iso_now(),
                    },
                    {
                        "relative_path": ".workflowprogram/design/workflow-view.md",
                        "last_applied_hash": "mock-managed-hash-view",
                        "ownership": "workflowprogram",
                        "producer_version": "mock-runtime-host",
                        "updated_at": iso_now(),
                    },
                    {
                        "relative_path": ".workflowprogram/runtime/runtime-manifest.json",
                        "last_applied_hash": "mock-managed-hash-runtime-manifest",
                        "ownership": "workflowprogram",
                        "producer_version": "mock-runtime-host",
                        "updated_at": iso_now(),
                    },
                    {
                        "relative_path": ".workflowprogram/runtime/validate-run-state.py",
                        "last_applied_hash": "mock-managed-hash-runtime-validator",
                        "ownership": "workflowprogram",
                        "producer_version": "mock-runtime-host",
                        "updated_at": iso_now(),
                    },
                    {
                        "relative_path": ".workflowprogram/runtime/workflow-entry.py",
                        "last_applied_hash": "mock-managed-hash-runtime-entry",
                        "ownership": "workflowprogram",
                        "producer_version": "mock-runtime-host",
                        "updated_at": iso_now(),
                    },
                    {
                        "relative_path": ".workflowprogram/runtime/workflow-runner.py",
                        "last_applied_hash": "mock-managed-hash-runtime-runner",
                        "ownership": "workflowprogram",
                        "producer_version": "mock-runtime-host",
                        "updated_at": iso_now(),
                    }
                ]
            ),
        },
    )
    result_payload = with_report_fields(
        result_payload,
        schema_name="managed-change-result",
        error_code="CONFLICT" if conflict else None,
        failure_kind="conflict" if conflict else "none",
        remediation=[{"code": "REVIEW_MANAGED_CONFLICTS", "summary": "Resolve conflicts before re-running."}] if conflict else [],
    )
    write_json(outputs / "managed-change-result.json", result_payload)
    rollback_entries: List[Dict[str, Any]] = []
    for item in result_payload.get("applied", []) if isinstance(result_payload.get("applied"), list) else []:
        rollback_entries.append(
            {
                "relative_path": item.get("relative_path"),
                "target_path": item.get("target_path"),
                "action": item.get("action"),
                "rollback_action": "restore_before_snapshot" if item.get("action") == "update" else "delete_created_file",
                "safe_if_current_sha256_equals": item.get("applied_sha256"),
                "before_sha256": item.get("before_sha256"),
            }
        )
    for item in result_payload.get("conflicts", []) if isinstance(result_payload.get("conflicts"), list) else []:
        rollback_entries.append(
            {
                "relative_path": item.get("relative_path"),
                "target_path": item.get("target_path"),
                "action": "conflict",
                "rollback_action": "none",
                "conflict_copy": item.get("conflict_copy"),
            }
        )
    write_json(
        outputs / "managed-rollback-manifest.json",
        with_report_fields(
            {
                "generated_at": iso_now(),
                "target_root": str(target_root),
                "run_root": str(run_root),
                "entries": rollback_entries,
            },
            schema_name="managed-rollback-manifest",
            error_code="CONFLICT" if conflict else None,
            failure_kind="conflict" if conflict else "none",
            remediation=[{"code": "MANUAL_CONFLICT_REVIEW", "summary": "Review conflict_copy before applying."}] if conflict else [],
        ),
    )
    write_text(
        outputs / "managed-recover-instructions.md",
        "# Managed Asset Recovery Instructions\n\n"
        "- Created files: delete only if current hash matches applied hash.\n"
        "- Updated files: restore only if current hash matches applied hash.\n"
        "- Conflicts: no target change was made; review conflict copies manually.\n",
    )


def create_target_outputs(run_root: Path, target_root: Path, *, include_claude_assets: bool = True) -> List[str]:
    """为 PASS 路径 smoke 测试创建一个最小可用的目标树。"""
    files: List[str] = []
    if include_claude_assets:
        settings_path = target_root / ".claude" / "settings.json"
        write_text(settings_path, '{\n  "commands": ["example"]\n}\n')
        files.append(".claude/settings.json")
        constraints_path = target_root / ".claude" / "rules" / "constraints.md"
        write_text(constraints_path, "# Constraints\n\n- Keep workflow assets managed.\n")
        files.append(".claude/rules/constraints.md")
        command_path = target_root / ".claude" / "commands" / "example.md"
        write_text(command_path, "## Usage\n\n1. Goal\n2. Verify\n")
        files.append(".claude/commands/example.md")
    design_root = target_root / ".workflowprogram" / "design"
    design_root.mkdir(parents=True, exist_ok=True)
    for name in ("workflow-spec.yaml", "workflow-view.md", "workflow-lowlevel.md"):
        source_path = run_root / name
        target_path = design_root / name
        target_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
        files.append(f".workflowprogram/design/{name}")
    runtime_root = target_root / ".workflowprogram" / "runtime"
    runtime_files = generate_target_runtime_assets(Path(__file__).resolve().parents[1], run_root / "workflow-spec.yaml", runtime_root)
    files.extend(
        [
            ".workflowprogram/runtime/workflow-entry.py",
            ".workflowprogram/runtime/workflow-runner.py",
            ".workflowprogram/runtime/validate-run-state.py",
            ".workflowprogram/runtime/runtime-manifest.json",
        ]
    )
    return files


def write_validation_report(target_root: Path, title: str, bullets: List[str]) -> None:
    """向目标项目写入简洁的 validation Markdown 报告。"""
    body = "\n".join(bullets)
    write_text(target_root / "validation-report.md", f"# {title}\n\n{body}\n")


def parse_args() -> argparse.Namespace:
    """解析 `command_adapter` smoke 运行使用的 provider 协议参数。"""
    parser = argparse.ArgumentParser(description="Reference command-provider runtime host")
    sub = parser.add_subparsers(dest="command", required=True)

    probe = sub.add_parser("probe")
    probe.add_argument("--json", action="store_true")

    invoke = sub.add_parser("invoke")
    invoke.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    invoke.add_argument("--plugin-root", required=True)
    invoke.add_argument("--target-root", required=True)
    invoke.add_argument("--run-root", required=True)
    invoke.add_argument("--fixture", required=True)
    invoke.add_argument("--entry-skill", required=True)
    invoke.add_argument("--request", default="")
    invoke.add_argument("--timeout", default="90")
    invoke.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    """实现 runtime_host.py 所期望的最小 probe/invoke 协议。"""
    args = parse_args()
    if args.command == "probe":
        payload = {
            "available": True,
            "ready": True,
            "message": "mock_runtime_host is ready.",
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(payload["message"])
        return 0

    repo_root = Path(args.repo_root).resolve()
    target_root = Path(args.target_root).resolve()
    run_root = Path(args.run_root).resolve()
    run_root.mkdir(parents=True, exist_ok=True)
    intent = infer_intent(args.entry_skill)

    if args.entry_skill.startswith("missing-"):
        # 未知入口技能用于模拟 workflow 注册层面的结构性错误。
        copy_runtime_spec(
            repo_root,
            run_root,
            "invalid-entry.yaml",
            entry_skill=args.entry_skill,
            deliverables=[],
        )
        stage_history: List[str] = []
        write_progress_outputs(
            run_root,
            stage_history,
            "FAIL",
            "STRUCTURE_FAILURE",
            current_stage="requirement",
            next_action="register the missing entry and rerun",
        )
        write_runner_evidence(run_root, target_root, intent, args.entry_skill, stage_history, "FAIL", "STRUCTURE_FAILURE")
        payload = {
            "result": "FAIL",
            "failure_code": "STRUCTURE_FAILURE",
            "message": "Mock host rejected an unknown workflow entry.",
            "is_error": True,
            "stage_history": stage_history,
            "current_stage": "requirement",
            "next_action": "register the missing entry and rerun",
        }
    elif not args.request.strip():
        # 空请求要在 requirement 阶段提前失败，用来模拟“缺少必需参数”，
        # 并确保在任何生成资产之前就终止。
        copy_runtime_spec(
            repo_root,
            run_root,
            "valid-minimal.yaml",
            entry_skill=args.entry_skill,
            deliverables=[],
        )
        stage_history = ["requirement"]
        write_progress_outputs(
            run_root,
            stage_history,
            "FAIL",
            "MISSING_ARGUMENT",
            current_stage="requirement",
            next_action="provide the required request arguments",
            approval_status="pending",
        )
        write_runner_evidence(run_root, target_root, intent, args.entry_skill, stage_history, "FAIL", "MISSING_ARGUMENT")
        payload = {
            "result": "FAIL",
            "failure_code": "MISSING_ARGUMENT",
            "message": "Mock host rejected an empty request payload.",
            "is_error": True,
            "stage_history": stage_history,
            "stage_status": "failed",
            "current_stage": "requirement",
            "next_action": "provide the required request arguments",
        }
    elif args.fixture == "broken-workflow":
        # broken fixture 仍然会产出看起来完整的证据，便于 S5 judge 证明
        # “失败是因为检测到了正确的问题”，而不是流程本身没跑起来。
        copy_runtime_spec(
            repo_root,
            run_root,
            "valid-minimal.yaml",
            entry_skill=args.entry_skill,
            deliverables=["validation-report.md"],
            target_root_allow=["validation-report.md"],
        )
        stage_history = stage_history_for_intent(intent)
        write_validation_report(
            target_root,
            "Broken Workflow Validation",
            [
                "- Result: `FAIL`",
                "- Failure code: `EVIDENCE_FAILURE`",
                "- Finding: broken workflow assets were detected in `.claude/`.",
            ],
        )
        if "requirement" in stage_history:
            write_workflow_spec_draft(run_root, args.entry_skill, args.request)
        if "lessons" in stage_history:
            write_lessons_delta(run_root, intent, derive_failure_kind("EVIDENCE_FAILURE"), args.request)
        write_progress_outputs(
            run_root,
            stage_history,
            "FAIL",
            "EVIDENCE_FAILURE",
            current_stage=stage_history[-1] if stage_history else "validate",
            next_action="repair broken workflow assets and rerun validate",
        )
        write_runner_evidence(run_root, target_root, intent, args.entry_skill, stage_history, "FAIL", "EVIDENCE_FAILURE")
        payload = {
            "result": "FAIL",
            "failure_code": "EVIDENCE_FAILURE",
            "message": "Mock host detected broken workflow assets and stopped validation.",
            "is_error": True,
            "stage_history": stage_history,
            "stage_status": "failed",
            "current_stage": stage_history[-1] if stage_history else "validate",
            "next_action": "repair broken workflow assets and rerun validate",
            "generated_files": [],
        }
    else:
        stage_history = stage_history_for_intent(intent)
        request_lower = args.request.lower()
        if "managed-conflict" in request_lower:
            # 冲突请求用于模拟 managed drift：在进入 S5/S6 之前就停止，
            # 只保留冲突证据。
            copy_runtime_spec(
                repo_root,
                run_root,
                "valid-minimal.yaml",
                entry_skill=args.entry_skill,
            )
            generate_design_docs(repo_root, run_root)
            generated_files = [
                ".claude/settings.json",
                ".claude/rules/constraints.md",
            ]
            if "requirement" in stage_history:
                write_workflow_spec_draft(run_root, args.entry_skill, args.request)
            write_progress_outputs(
                run_root,
                stage_history[:-1],
                "FAIL",
                "CONFLICT",
                current_stage="generate",
                next_action="resolve managed conflicts and rerun generate",
            )
            write_runner_evidence(run_root, target_root, intent, args.entry_skill, stage_history[:-1], "FAIL", "CONFLICT")
            write_managed_outputs(run_root, target_root, conflict=True)
            payload = {
                "result": "FAIL",
                "failure_code": "CONFLICT_FAILURE",
                "message": "Mock host detected a managed asset conflict and kept candidate copies.",
                "is_error": True,
                "stage_history": stage_history[:-1],
                "stage_status": "failed",
                "current_stage": "generate",
                "next_action": "resolve managed conflicts and rerun generate",
                "generated_files": generated_files,
            }
        elif args.fixture == "host-capability-missing-develop":
            copy_runtime_spec(
                repo_root,
                run_root,
                "valid-minimal.yaml",
                entry_skill=args.entry_skill,
                host_capabilities=host_capability_missing_contract(),
                runtime_capabilities=["state_transitions", "run_state_validation", "host_capability_probe"],
            )
            design_docs = generate_design_docs(repo_root, run_root)
            candidate_root = run_root / "outputs" / "candidate"
            write_text(candidate_root / ".claude" / "rules" / "constraints.md", "# Constraints\n\n- Keep workflow assets managed.\n")
            write_text(candidate_root / ".claude" / "commands" / "example.md", "## Usage\n\n1. Goal\n2. Verify\n")
            for source_name, target_name in (
                ("workflow_spec", "workflow-spec.yaml"),
                ("workflow_view", "workflow-view.md"),
                ("workflow_lowlevel", "workflow-lowlevel.md"),
            ):
                destination = candidate_root / ".workflowprogram" / "design" / target_name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(design_docs[source_name].read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
            generate_target_runtime_assets(repo_root, run_root / "workflow-spec.yaml", candidate_root / ".workflowprogram" / "runtime")
            generated_files = create_target_outputs(run_root, target_root)
            write_managed_outputs(run_root, target_root, conflict=False)
            host_outputs = write_host_capability_outputs(repo_root, run_root, target_root, apply_project_local=False)
            if "requirement" in stage_history:
                write_workflow_spec_draft(run_root, args.entry_skill, args.request)
            if "lessons" in stage_history:
                write_lessons_delta(
                    run_root,
                    intent,
                    "environment",
                    args.request,
                    extra_candidates=["Add host_capability bootstrap guidance for missing_binary."],
                )
            write_progress_outputs(
                run_root,
                stage_history,
                "FAIL",
                "HOST_CAPABILITY_MISSING",
                current_stage=stage_history[-1] if stage_history else "lessons",
                next_action="resolve required host capabilities and rerun",
            )
            write_runner_evidence(run_root, target_root, intent, args.entry_skill, stage_history, "FAIL", "HOST_CAPABILITY_MISSING")
            payload = {
                "result": "FAIL",
                "failure_code": "HOST_CAPABILITY_MISSING",
                "message": "Mock host completed workflow generation, but required host capabilities are missing.",
                "is_error": True,
                "stage_history": stage_history,
                "stage_status": "failed",
                "current_stage": stage_history[-1] if stage_history else "lessons",
                "next_action": "resolve required host capabilities and rerun",
                "generated_files": generated_files,
                "metadata": {"host_capability_report": host_outputs.get("report", {})},
            }
        elif args.fixture == "host-capability-project-local-bootstrap":
            copy_runtime_spec(
                repo_root,
                run_root,
                "valid-minimal.yaml",
                entry_skill=args.entry_skill,
                host_capabilities=host_capability_project_local_contract(),
                runtime_capabilities=["state_transitions", "run_state_validation", "host_capability_probe"],
            )
            design_docs = generate_design_docs(repo_root, run_root)
            candidate_root = run_root / "outputs" / "candidate"
            write_text(candidate_root / ".claude" / "rules" / "constraints.md", "# Constraints\n\n- Keep workflow assets managed.\n")
            write_text(candidate_root / ".claude" / "commands" / "example.md", "## Usage\n\n1. Goal\n2. Verify\n")
            for source_name, target_name in (
                ("workflow_spec", "workflow-spec.yaml"),
                ("workflow_view", "workflow-view.md"),
                ("workflow_lowlevel", "workflow-lowlevel.md"),
            ):
                destination = candidate_root / ".workflowprogram" / "design" / target_name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(design_docs[source_name].read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
            generate_target_runtime_assets(repo_root, run_root / "workflow-spec.yaml", candidate_root / ".workflowprogram" / "runtime")
            generated_files = create_target_outputs(run_root, target_root)
            write_managed_outputs(run_root, target_root, conflict=False)
            host_outputs = write_host_capability_outputs(repo_root, run_root, target_root, apply_project_local=True)
            if "requirement" in stage_history:
                write_workflow_spec_draft(run_root, args.entry_skill, args.request)
            if "lessons" in stage_history:
                write_lessons_delta(run_root, intent, "none", args.request)
            write_progress_outputs(
                run_root,
                stage_history,
                "PASS",
                "",
                current_stage=stage_history[-1] if stage_history else "lessons",
                next_action="complete",
            )
            write_runner_evidence(run_root, target_root, intent, args.entry_skill, stage_history, "PASS", "")
            payload = {
                "result": "PASS",
                "failure_code": "",
                "message": "Mock host applied project-local bootstrap and satisfied host capability requirements.",
                "is_error": False,
                "stage_history": stage_history,
                "stage_status": "done",
                "current_stage": stage_history[-1] if stage_history else "lessons",
                "next_action": "complete",
                "generated_files": generated_files,
                "metadata": {"host_capability_report": host_outputs.get("report", {})},
            }
        elif args.fixture == "host-capability-host-global-bootstrap":
            copy_runtime_spec(
                repo_root,
                run_root,
                "valid-minimal.yaml",
                entry_skill=args.entry_skill,
                host_capabilities=host_capability_host_global_contract(target_root),
                runtime_capabilities=["state_transitions", "run_state_validation", "host_capability_probe"],
            )
            design_docs = generate_design_docs(repo_root, run_root)
            candidate_root = run_root / "outputs" / "candidate"
            write_text(candidate_root / ".claude" / "rules" / "constraints.md", "# Constraints\n\n- Keep workflow assets managed.\n")
            write_text(candidate_root / ".claude" / "commands" / "example.md", "## Usage\n\n1. Goal\n2. Verify\n")
            for source_name, target_name in (
                ("workflow_spec", "workflow-spec.yaml"),
                ("workflow_view", "workflow-view.md"),
                ("workflow_lowlevel", "workflow-lowlevel.md"),
            ):
                destination = candidate_root / ".workflowprogram" / "design" / target_name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(design_docs[source_name].read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
            generate_target_runtime_assets(repo_root, run_root / "workflow-spec.yaml", candidate_root / ".workflowprogram" / "runtime")
            generated_files = create_target_outputs(run_root, target_root)
            write_managed_outputs(run_root, target_root, conflict=False)
            host_outputs = write_host_capability_outputs(
                repo_root,
                run_root,
                target_root,
                apply_project_local=False,
            )
            if "requirement" in stage_history:
                write_workflow_spec_draft(run_root, args.entry_skill, args.request)
            if "lessons" in stage_history:
                write_lessons_delta(run_root, intent, "none", args.request)
            write_progress_outputs(
                run_root,
                stage_history,
                "PASS",
                "",
                current_stage=stage_history[-1] if stage_history else "lessons",
                next_action="complete",
            )
            write_runner_evidence(run_root, target_root, intent, args.entry_skill, stage_history, "PASS", "")
            payload = {
                "result": "PASS",
                "failure_code": "",
                "message": "Mock host applied approved host-global bootstrap and satisfied host capability requirements.",
                "is_error": False,
                "stage_history": stage_history,
                "stage_status": "done",
                "current_stage": stage_history[-1] if stage_history else "lessons",
                "next_action": "complete",
                "generated_files": generated_files,
                "metadata": {"host_capability_report": host_outputs.get("report", {})},
            }
        elif args.fixture == "capability-discovery-reverse-engineering":
            copy_runtime_spec(
                repo_root,
                run_root,
                "valid-minimal.yaml",
                entry_skill=args.entry_skill,
                capability_discovery=capability_discovery_reverse_engineering(),
                runtime_capabilities=["state_transitions", "run_state_validation", "capability_discovery"],
            )
            design_docs = generate_design_docs(repo_root, run_root)
            candidate_root = run_root / "outputs" / "candidate"
            write_text(candidate_root / ".claude" / "rules" / "constraints.md", "# Constraints\n\n- Keep workflow assets managed.\n")
            write_text(candidate_root / ".claude" / "commands" / "example.md", "## Usage\n\n1. Goal\n2. Verify\n")
            for source_name, target_name in (
                ("workflow_spec", "workflow-spec.yaml"),
                ("workflow_view", "workflow-view.md"),
                ("workflow_lowlevel", "workflow-lowlevel.md"),
            ):
                destination = candidate_root / ".workflowprogram" / "design" / target_name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(design_docs[source_name].read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
            generate_target_runtime_assets(repo_root, run_root / "workflow-spec.yaml", candidate_root / ".workflowprogram" / "runtime")
            generated_files = create_target_outputs(run_root, target_root)
            write_managed_outputs(run_root, target_root, conflict=False)
            discovery_outputs = write_capability_discovery_outputs(repo_root, run_root, target_root, args.request)
            if "requirement" in stage_history:
                write_workflow_spec_draft(run_root, args.entry_skill, args.request)
            if "lessons" in stage_history:
                write_lessons_delta(run_root, intent, "none", args.request)
            write_progress_outputs(
                run_root,
                stage_history,
                "PASS",
                "",
                current_stage=stage_history[-1] if stage_history else "lessons",
                next_action="review capability candidates and finalize host requirements",
            )
            write_runner_evidence(run_root, target_root, intent, args.entry_skill, stage_history, "PASS", "")
            payload = {
                "result": "PASS",
                "failure_code": "",
                "message": "Mock host generated capability discovery recommendations for reverse engineering.",
                "is_error": False,
                "stage_history": stage_history,
                "stage_status": "done",
                "current_stage": stage_history[-1] if stage_history else "lessons",
                "next_action": "review capability candidates and finalize host requirements",
                "generated_files": generated_files,
                "metadata": {"capability_discovery_report": discovery_outputs.get("report", {})},
            }
        elif args.fixture in {"host-capability-validate", "host-capability-audit"}:
            host_entry_skill = "workflowprogram-validate" if args.fixture == "host-capability-validate" else "workflowprogram-audit"
            intent = infer_intent(host_entry_skill)
            stage_history = stage_history_for_intent(intent)
            copy_runtime_spec(
                repo_root,
                run_root,
                "valid-minimal.yaml",
                entry_skill=host_entry_skill,
                deliverables=["validation-report.md"],
                target_root_allow=["validation-report.md"],
                host_capabilities=[
                    {
                        "id": "python3_runtime",
                        "kind": "external_binary",
                        "name": "Python 3",
                        "required": True,
                        "probe": {"binary": "python3", "args": ["--version"]},
                        "bootstrap": {"scope": "manual_only", "summary": "Python 3 should already exist", "project_local_outputs": []},
                        "approval_required": True,
                    }
                ],
                runtime_capabilities=["state_transitions", "run_state_validation", "host_capability_probe"],
            )
            generate_design_docs(repo_root, run_root)
            generated_files = create_target_outputs(run_root, target_root, include_claude_assets=False)
            host_outputs = write_host_capability_outputs(repo_root, run_root, target_root, apply_project_local=False)
            write_validation_report(
                target_root,
                "Workflow Validation",
                [
                    "- Result: `PASS`",
                    f"- Entry skill: `{host_entry_skill}`",
                    "- Host capabilities were probed successfully.",
                ],
            )
            if "requirement" in stage_history:
                write_workflow_spec_draft(run_root, host_entry_skill, args.request)
            if "lessons" in stage_history:
                write_lessons_delta(run_root, intent, "none", args.request)
            write_progress_outputs(
                run_root,
                stage_history,
                "PASS",
                "",
                current_stage=stage_history[-1] if stage_history else "validate",
                next_action="complete",
            )
            write_runner_evidence(run_root, target_root, intent, host_entry_skill, stage_history, "PASS", "")
            payload = {
                "result": "PASS",
                "failure_code": "",
                "message": "Mock host validated host capabilities successfully.",
                "is_error": False,
                "stage_history": stage_history,
                "stage_status": "done",
                "current_stage": stage_history[-1] if stage_history else "validate",
                "next_action": "complete",
                "generated_files": generated_files,
                "metadata": {"host_capability_report": host_outputs.get("report", {})},
            }
        elif args.fixture == "host-capability-iterate":
            copy_runtime_spec(
                repo_root,
                run_root,
                "valid-minimal.yaml",
                entry_skill=args.entry_skill,
                host_capabilities=host_capability_missing_contract(),
                runtime_capabilities=["state_transitions", "run_state_validation", "host_capability_probe"],
            )
            generate_design_docs(repo_root, run_root)
            generated_files = create_target_outputs(run_root, target_root, include_claude_assets=False)
            write_managed_outputs(run_root, target_root, conflict=False)
            host_outputs = write_host_capability_outputs(repo_root, run_root, target_root, apply_project_local=False)
            seed_prior_host_capability_failure(target_root, host_outputs.get("report", {}))
            write_lessons_delta(
                run_root,
                intent,
                "environment",
                args.request,
                extra_candidates=["Add host_capability bootstrap coverage for missing_binary recurring failures."],
            )
            write_progress_outputs(
                run_root,
                stage_history,
                "FAIL",
                "HOST_CAPABILITY_MISSING",
                current_stage=stage_history[-1] if stage_history else "lessons",
                next_action="add host capability bootstrap guidance",
            )
            write_runner_evidence(run_root, target_root, intent, args.entry_skill, stage_history, "FAIL", "HOST_CAPABILITY_MISSING")
            payload = {
                "result": "FAIL",
                "failure_code": "HOST_CAPABILITY_MISSING",
                "message": "Mock host identified recurring host capability failures during iterate.",
                "is_error": True,
                "stage_history": stage_history,
                "stage_status": "failed",
                "current_stage": stage_history[-1] if stage_history else "lessons",
                "next_action": "add host capability bootstrap guidance",
                "generated_files": generated_files,
                "metadata": {"host_capability_report": host_outputs.get("report", {})},
            }
        elif args.fixture == "agent-team-develop-pass":
            team_contract = agent_team_contract_fixture(max_fan_out=2)
            copy_runtime_spec(
                repo_root,
                run_root,
                "valid-minimal.yaml",
                entry_skill=args.entry_skill,
                agent_team_contract=team_contract,
                runtime_capabilities=["state_transitions", "run_state_validation", "team_orchestration"],
            )
            design_docs = generate_design_docs(repo_root, run_root)
            candidate_root = run_root / "outputs" / "candidate"
            write_text(candidate_root / ".claude" / "rules" / "constraints.md", "# Constraints\n\n- Keep workflow assets managed.\n")
            write_text(candidate_root / ".claude" / "commands" / "example.md", "## Usage\n\n1. Goal\n2. Verify\n")
            for source_name, target_name in (
                ("workflow_spec", "workflow-spec.yaml"),
                ("workflow_view", "workflow-view.md"),
                ("workflow_lowlevel", "workflow-lowlevel.md"),
            ):
                destination = candidate_root / ".workflowprogram" / "design" / target_name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(design_docs[source_name].read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
            generate_target_runtime_assets(repo_root, run_root / "workflow-spec.yaml", candidate_root / ".workflowprogram" / "runtime")
            generated_files = create_target_outputs(run_root, target_root)
            write_managed_outputs(run_root, target_root, conflict=False)
            write_team_evidence(run_root, team_contract, overflow=False, join_satisfied=True)
            if "requirement" in stage_history:
                write_workflow_spec_draft(run_root, args.entry_skill, args.request)
            if "lessons" in stage_history:
                write_lessons_delta(run_root, intent, "none", args.request)
            write_progress_outputs(run_root, stage_history, "PASS", "", current_stage=stage_history[-1], next_action="complete")
            write_runner_evidence(run_root, target_root, intent, args.entry_skill, stage_history, "PASS", "")
            payload = {
                "result": "PASS",
                "failure_code": "",
                "message": "Mock host completed deterministic team orchestration successfully.",
                "is_error": False,
                "stage_history": stage_history,
                "stage_status": "done",
                "current_stage": stage_history[-1],
                "next_action": "complete",
                "generated_files": generated_files,
            }
        elif args.fixture == "agent-team-fanout-fail":
            team_contract = agent_team_contract_fixture(max_fan_out=2)
            copy_runtime_spec(
                repo_root,
                run_root,
                "valid-minimal.yaml",
                entry_skill=args.entry_skill,
                agent_team_contract=team_contract,
                runtime_capabilities=["state_transitions", "run_state_validation", "team_orchestration"],
            )
            design_docs = generate_design_docs(repo_root, run_root)
            candidate_root = run_root / "outputs" / "candidate"
            write_text(candidate_root / ".claude" / "rules" / "constraints.md", "# Constraints\n\n- Keep workflow assets managed.\n")
            write_text(candidate_root / ".claude" / "commands" / "example.md", "## Usage\n\n1. Goal\n2. Verify\n")
            for source_name, target_name in (
                ("workflow_spec", "workflow-spec.yaml"),
                ("workflow_view", "workflow-view.md"),
                ("workflow_lowlevel", "workflow-lowlevel.md"),
            ):
                destination = candidate_root / ".workflowprogram" / "design" / target_name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(design_docs[source_name].read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
            generate_target_runtime_assets(repo_root, run_root / "workflow-spec.yaml", candidate_root / ".workflowprogram" / "runtime")
            generated_files = create_target_outputs(run_root, target_root)
            write_managed_outputs(run_root, target_root, conflict=False)
            write_team_evidence(run_root, team_contract, overflow=True, join_satisfied=True)
            if "requirement" in stage_history:
                write_workflow_spec_draft(run_root, args.entry_skill, args.request)
            if "lessons" in stage_history:
                write_lessons_delta(run_root, intent, "implementation", args.request)
            write_progress_outputs(run_root, stage_history, "FAIL", "TEAM_ORCHESTRATION_FAILURE", current_stage=stage_history[-1], next_action="reduce team fan-out and rerun")
            write_runner_evidence(run_root, target_root, intent, args.entry_skill, stage_history, "FAIL", "TEAM_ORCHESTRATION_FAILURE")
            payload = {
                "result": "FAIL",
                "failure_code": "TEAM_ORCHESTRATION_FAILURE",
                "message": "Mock host exceeded agent team max_fan_out.",
                "is_error": True,
                "stage_history": stage_history,
                "stage_status": "failed",
                "current_stage": stage_history[-1],
                "next_action": "reduce team fan-out and rerun",
                "generated_files": generated_files,
            }
        elif args.fixture in {"agent-team-validate", "agent-team-audit"}:
            team_contract = agent_team_contract_fixture(max_fan_out=2)
            team_entry_skill = "workflowprogram-validate" if args.fixture == "agent-team-validate" else "workflowprogram-audit"
            intent = infer_intent(team_entry_skill)
            stage_history = stage_history_for_intent(intent)
            copy_runtime_spec(
                repo_root,
                run_root,
                "valid-minimal.yaml",
                entry_skill=team_entry_skill,
                deliverables=["validation-report.md"],
                target_root_allow=["validation-report.md"],
                agent_team_contract=team_contract,
                runtime_capabilities=["state_transitions", "run_state_validation", "team_orchestration"],
            )
            generate_design_docs(repo_root, run_root)
            generated_files = create_target_outputs(run_root, target_root, include_claude_assets=False)
            write_team_evidence(run_root, team_contract, overflow=False, join_satisfied=True)
            write_validation_report(
                target_root,
                "Workflow Team Validation",
                [
                    "- Result: `PASS`",
                    f"- Entry skill: `{team_entry_skill}`",
                    "- Team orchestration evidence was captured.",
                ],
            )
            if "requirement" in stage_history:
                write_workflow_spec_draft(run_root, team_entry_skill, args.request)
            if "lessons" in stage_history:
                write_lessons_delta(run_root, intent, "none", args.request)
            write_progress_outputs(run_root, stage_history, "PASS", "", current_stage=stage_history[-1], next_action="complete")
            write_runner_evidence(run_root, target_root, intent, team_entry_skill, stage_history, "PASS", "")
            payload = {
                "result": "PASS",
                "failure_code": "",
                "message": "Mock host validated team orchestration successfully.",
                "is_error": False,
                "stage_history": stage_history,
                "stage_status": "done",
                "current_stage": stage_history[-1],
                "next_action": "complete",
                "generated_files": generated_files,
            }
        elif args.fixture == "node-loop-develop-pass":
            loop_policy = node_loop_policy_fixture(max_iterations=3)
            copy_runtime_spec(
                repo_root,
                run_root,
                "valid-minimal.yaml",
                entry_skill=args.entry_skill,
                node_loop_policy=loop_policy,
                runtime_capabilities=["state_transitions", "run_state_validation", "node_loop_execution"],
            )
            design_docs = generate_design_docs(repo_root, run_root)
            candidate_root = run_root / "outputs" / "candidate"
            write_text(candidate_root / ".claude" / "rules" / "constraints.md", "# Constraints\n\n- Loop success requires verifier evidence.\n")
            write_text(candidate_root / ".claude" / "commands" / "example.md", "## Usage\n\n1. Goal\n2. Iterate until verified\n")
            for source_name, target_name in (
                ("workflow_spec", "workflow-spec.yaml"),
                ("workflow_view", "workflow-view.md"),
                ("workflow_lowlevel", "workflow-lowlevel.md"),
            ):
                destination = candidate_root / ".workflowprogram" / "design" / target_name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(design_docs[source_name].read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
            generate_target_runtime_assets(repo_root, run_root / "workflow-spec.yaml", candidate_root / ".workflowprogram" / "runtime")
            generated_files = create_target_outputs(run_root, target_root)
            write_managed_outputs(run_root, target_root, conflict=False)
            write_loop_evidence(run_root, node_id="implement", iterations=2, final_status="PASS", verifier_passed=True)
            if "requirement" in stage_history:
                write_workflow_spec_draft(run_root, args.entry_skill, args.request)
            if "lessons" in stage_history:
                write_lessons_delta(run_root, intent, "none", args.request)
            write_progress_outputs(run_root, stage_history, "PASS", "", current_stage=stage_history[-1], next_action="complete")
            write_runner_evidence(run_root, target_root, intent, args.entry_skill, stage_history, "PASS", "")
            payload = {
                "result": "PASS",
                "failure_code": "",
                "message": "Mock host completed deterministic node loop successfully.",
                "is_error": False,
                "stage_history": stage_history,
                "stage_status": "done",
                "current_stage": stage_history[-1],
                "next_action": "complete",
                "generated_files": generated_files,
            }
        elif args.fixture == "node-loop-max-iterations-fail":
            loop_policy = node_loop_policy_fixture(max_iterations=2)
            copy_runtime_spec(
                repo_root,
                run_root,
                "valid-minimal.yaml",
                entry_skill=args.entry_skill,
                node_loop_policy=loop_policy,
                runtime_capabilities=["state_transitions", "run_state_validation", "node_loop_execution"],
            )
            design_docs = generate_design_docs(repo_root, run_root)
            candidate_root = run_root / "outputs" / "candidate"
            write_text(candidate_root / ".claude" / "rules" / "constraints.md", "# Constraints\n\n- Stop loop at max_iterations.\n")
            write_text(candidate_root / ".claude" / "commands" / "example.md", "## Usage\n\n1. Goal\n2. Iterate until verified\n")
            for source_name, target_name in (
                ("workflow_spec", "workflow-spec.yaml"),
                ("workflow_view", "workflow-view.md"),
                ("workflow_lowlevel", "workflow-lowlevel.md"),
            ):
                destination = candidate_root / ".workflowprogram" / "design" / target_name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(design_docs[source_name].read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
            generate_target_runtime_assets(repo_root, run_root / "workflow-spec.yaml", candidate_root / ".workflowprogram" / "runtime")
            generated_files = create_target_outputs(run_root, target_root)
            write_managed_outputs(run_root, target_root, conflict=False)
            write_loop_evidence(run_root, node_id="implement", iterations=3, final_status="FAIL", verifier_passed=False, stop_reason="max_iterations")
            if "requirement" in stage_history:
                write_workflow_spec_draft(run_root, args.entry_skill, args.request)
            if "lessons" in stage_history:
                write_lessons_delta(run_root, intent, "implementation", args.request)
            write_progress_outputs(run_root, stage_history, "FAIL", "NODE_LOOP_MAX_ITERATIONS", current_stage=stage_history[-1], next_action="tighten loop feedback or raise max_iterations")
            write_runner_evidence(run_root, target_root, intent, args.entry_skill, stage_history, "FAIL", "NODE_LOOP_MAX_ITERATIONS")
            payload = {
                "result": "FAIL",
                "failure_code": "NODE_LOOP_MAX_ITERATIONS",
                "message": "Mock host exceeded node loop max_iterations.",
                "is_error": True,
                "stage_history": stage_history,
                "stage_status": "failed",
                "current_stage": stage_history[-1],
                "next_action": "tighten loop feedback or raise max_iterations",
                "generated_files": generated_files,
            }
        elif args.fixture == "existing-workflow":
            # audit/iterate 类流程复用已有 target，主要生成验证产物，
            # 而不是创建新的 managed 资产。
            copy_runtime_spec(
                repo_root,
                run_root,
                "valid-minimal.yaml",
                entry_skill=args.entry_skill,
                deliverables=["validation-report.md"],
                target_root_allow=["validation-report.md"],
            )
            write_validation_report(
                target_root,
                "Workflow Audit Report",
                [
                    "- Result: `PASS`",
                    f"- Entry skill: `{args.entry_skill}`",
                    "- Audit summary: existing workflow assets were reviewed successfully.",
                ],
            )
            generated_files = ["validation-report.md"]
            if "requirement" in stage_history:
                write_workflow_spec_draft(run_root, args.entry_skill, args.request)
            if "lessons" in stage_history:
                write_lessons_delta(run_root, intent, derive_failure_kind(""), args.request)
            write_progress_outputs(
                run_root,
                stage_history,
                "PASS",
                "",
                current_stage=stage_history[-1] if stage_history else "lessons",
                next_action="complete",
            )
            write_runner_evidence(run_root, target_root, intent, args.entry_skill, stage_history, "PASS", "")
            payload = {
                "result": "PASS",
                "failure_code": "",
                "message": "Mock host completed workflow audit successfully.",
                "is_error": False,
                "stage_history": stage_history,
                "stage_status": "done",
                "current_stage": stage_history[-1] if stage_history else "lessons",
                "next_action": "complete",
                "generated_files": generated_files,
            }
        else:
            # 默认 PASS 路径会写入 managed 资产，以及真实 validator 链所需的
            # runner/progress 证据。
            copy_runtime_spec(
                repo_root,
                run_root,
                "valid-minimal.yaml",
                entry_skill=args.entry_skill,
            )
            design_docs = generate_design_docs(repo_root, run_root)
            candidate_root = run_root / "outputs" / "candidate"
            write_text(candidate_root / ".claude" / "rules" / "constraints.md", "# Constraints\n\n- Keep workflow assets managed.\n")
            write_text(candidate_root / ".claude" / "commands" / "example.md", "## Usage\n\n1. Goal\n2. Verify\n")
            for source_name, target_name in (
                ("workflow_spec", "workflow-spec.yaml"),
                ("workflow_view", "workflow-view.md"),
                ("workflow_lowlevel", "workflow-lowlevel.md"),
            ):
                destination = candidate_root / ".workflowprogram" / "design" / target_name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(design_docs[source_name].read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
            generate_target_runtime_assets(repo_root, run_root / "workflow-spec.yaml", candidate_root / ".workflowprogram" / "runtime")
            generated_files = create_target_outputs(run_root, target_root)
            if "requirement" in stage_history:
                write_workflow_spec_draft(run_root, args.entry_skill, args.request)
            if "lessons" in stage_history:
                write_lessons_delta(run_root, intent, derive_failure_kind(""), args.request)
            write_progress_outputs(
                run_root,
                stage_history,
                "PASS",
                "",
                current_stage=stage_history[-1] if stage_history else "lessons",
                next_action="complete",
            )
            write_runner_evidence(run_root, target_root, intent, args.entry_skill, stage_history, "PASS", "")
            write_managed_outputs(run_root, target_root, conflict=False)
            if "external-write" in request_lower:
                # 这里故意违反 target_root_allow，用于证明 boundary 检查能抓住意外写入。
                write_text(target_root / "rogue-output.txt", "unexpected external write\n")
            payload = {
                "result": "PASS",
                "failure_code": "",
                "message": "Mock host completed workflow execution successfully.",
                "is_error": False,
                "stage_history": stage_history,
                "stage_status": "done",
                "current_stage": stage_history[-1] if stage_history else "lessons",
                "next_action": "complete",
                "generated_files": generated_files,
            }

    write_text(run_root / "outputs" / "mock-runtime-host.log", f"fixture={args.fixture}\nentry={args.entry_skill}\nrequest={args.request}\n")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["message"])
    return 0 if payload["result"] in {"PASS", "WARN", "ENVIRONMENT-SKIP"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
