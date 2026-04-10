#!/usr/bin/env python3
"""WorkflowProgram smoke 测试用的参考 runtime host 适配器。

这个 mock host 为 runtime_smoke 提供一条确定性的非 Claude 执行路径，
这样无需 Claude 登录也能验证 provider 抽象和 S5 judge。
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import yaml


def iso_now() -> str:
    """为模拟运行产物返回稳定的 UTC 时间戳。"""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_text(path: Path, content: str) -> None:
    """创建父目录后写入 UTF-8 文本。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    """创建父目录后写入格式化 JSON。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


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
        entry = test_contract.get("entry", {})
        if isinstance(entry, dict):
            entry["main_entry"] = entry_skill
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
    target_path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
        newline="\n",
    )


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


def write_lessons_delta(run_root: Path, intent: str, failure_kind: str, request: str) -> None:
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
            "",
        ]
    )
    write_text(run_root / "outputs" / "stages" / "s6-lessons-delta.md", body + "\n")


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
    plan_entry = {
        "relative_path": ".claude/settings.json",
        "source_path": str(candidate_source),
        "target_path": str(settings_path),
        "decision": "conflict-managed-drift" if conflict else "update",
    }
    write_json(
        outputs / "managed-change-plan.json",
        {
            "generated_at": iso_now(),
            "entries": [plan_entry],
            "summary": {
                "create": 0,
                "update": 0 if conflict else 1,
                "conflict": 1 if conflict else 0,
            },
        },
    )
    result_payload: Dict[str, Any] = {
        "generated_at": iso_now(),
        "target_root": str(target_root),
        "run_root": str(run_root),
        "manifest_path": str(manifest_path),
        "summary": {
            "create": 0,
            "update": 0 if conflict else 1,
            "conflict": 1 if conflict else 0,
        },
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
        result_payload["applied"].append(
            {
                "relative_path": ".claude/settings.json",
                "action": "update",
                "target_path": str(settings_path),
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
                        "relative_path": ".claude/settings.json",
                        "last_applied_hash": "mock-managed-hash",
                        "ownership": "workflowprogram",
                        "producer_version": "mock-runtime-host",
                        "updated_at": iso_now(),
                    }
                ]
            ),
        },
    )
    write_json(outputs / "managed-change-result.json", result_payload)


def create_target_outputs(target_root: Path) -> List[str]:
    """为 PASS 路径 smoke 测试创建一个最小可用的 managed 目标树。"""
    files: List[str] = []
    settings_path = target_root / ".claude" / "settings.json"
    write_text(settings_path, '{\n  "commands": ["example"]\n}\n')
    files.append(".claude/settings.json")
    constraints_path = target_root / ".claude" / "rules" / "constraints.md"
    write_text(constraints_path, "# Constraints\n\n- Keep workflow assets managed.\n")
    files.append(".claude/rules/constraints.md")
    command_path = target_root / ".claude" / "commands" / "example.md"
    write_text(command_path, "## Usage\n\n1. Goal\n2. Verify\n")
    files.append(".claude/commands/example.md")
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
            generated_files = create_target_outputs(target_root)
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
