#!/usr/bin/env python3
"""
在支持的 runtime host 上运行可重复的 WorkflowProgram smoke 矩阵。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def repo_root() -> Path:
    """无论当前工作目录是什么，都返回仓库根目录。"""
    return Path(__file__).resolve().parents[1]


def base_cases(provider_command: str) -> List[Dict[str, Any]]:
    """返回本地和类 CI 场景共用的默认 smoke 用例矩阵。"""
    return [
        {
            "name": "adapter-develop-pass",
            "fixture": "empty-project",
            "provider": "command_adapter",
            "provider_command": provider_command,
            "expected_result": "PASS",
        },
        {
            "name": "adapter-audit-pass",
            "fixture": "existing-workflow",
            "provider": "command_adapter",
            "provider_command": provider_command,
            "expected_result": "PASS",
        },
        {
            "name": "adapter-iterate-pass",
            "fixture": "existing-workflow",
            "entry_skill": "workflowprogram-iterate",
            "request": "/workflowprogram-iterate evolve constraints from lessons",
            "provider": "command_adapter",
            "provider_command": provider_command,
            "expected_result": "PASS",
        },
        {
            "name": "adapter-broken-fail",
            "fixture": "broken-workflow",
            "provider": "command_adapter",
            "provider_command": provider_command,
            "expected_result": "FAIL",
            "expected_category": "EVIDENCE_FAILURE",
        },
        {
            "name": "adapter-boundary-fail",
            "fixture": "external-write",
            "provider": "command_adapter",
            "provider_command": provider_command,
            "expected_result": "FAIL",
            "expected_category": "S5_BOUNDARY_TARGET_ROOT_BOUNDARY_CHANGES",
        },
        {
            "name": "adapter-managed-conflict-fail",
            "fixture": "managed-conflict",
            "provider": "command_adapter",
            "provider_command": provider_command,
            "expected_result": "FAIL",
            "expected_category": "S5_FLOW_REQUIRED_STAGES_EXECUTED",
        },
        {
            "name": "fixture-develop-pass",
            "fixture": "empty-project",
            "provider": "fixture_host",
            "expected_result": "PASS",
        },
        {
            "name": "fixture-audit-pass",
            "fixture": "existing-workflow",
            "provider": "fixture_host",
            "expected_result": "PASS",
        },
        {
            "name": "fixture-iterate-pass",
            "fixture": "existing-workflow",
            "entry_skill": "workflowprogram-iterate",
            "request": "/workflowprogram-iterate evolve constraints from lessons",
            "provider": "fixture_host",
            "expected_result": "PASS",
        },
    ]


def claude_case(require_pass: bool) -> Dict[str, Any]:
    """返回可选的 Claude CLI 真实宿主 smoke 用例。"""
    return {
        "name": "claude-cli-develop",
        "fixture": "empty-project",
        "provider": "claude_cli",
        "expected_result": "PASS" if require_pass else "PASS_OR_SKIP",
    }


def run_case(case: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    """运行单个 smoke 用例，并将观测结果与期望值比较。"""
    root = repo_root()
    cmd = [
        sys.executable,
        str(root / "tools" / "runtime_smoke.py"),
        "--fixture",
        str(case["fixture"]),
        "--runtime-provider",
        str(case["provider"]),
        "--timeout",
        str(timeout),
        "--json",
    ]
    if case.get("provider_command"):
        cmd.extend(["--provider-command", str(case["provider_command"])])
    if case.get("entry_skill"):
        cmd.extend(["--entry-skill", str(case["entry_skill"])])
    if case.get("request"):
        cmd.extend(["--request", str(case["request"])])

    completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        # JSON 无法解析说明 harness 自身就发生了结构性失败；这里降级成合成失败记录，
        # 而不是让整个矩阵直接崩溃。
        payload = {
            "result": "FAIL",
            "category": "STRUCTURE_FAILURE",
            "message": completed.stderr.strip() or completed.stdout.strip() or "runtime_smoke returned invalid JSON",
        }

    observed_result = str(payload.get("result", "")).strip()
    observed_category = payload.get("category")
    expected_result = str(case["expected_result"])
    expected_category = case.get("expected_category")

    if expected_result == "PASS_OR_SKIP":
        # 真实宿主在未就绪时允许返回 skip；而 adapter 用例应始终按严格 PASS/FAIL 处理。
        ok = observed_result in {"PASS", "ENVIRONMENT-SKIP"}
    else:
        ok = observed_result == expected_result
    if ok and expected_category is not None:
        ok = observed_category == expected_category

    return {
        "name": case["name"],
        "command": cmd,
        "ok": ok,
        "expected_result": expected_result,
        "expected_category": expected_category,
        "observed_result": observed_result,
        "observed_category": observed_category,
        "payload": payload,
        "returncode": completed.returncode,
    }


def parse_args() -> argparse.Namespace:
    """解析 runtime smoke 矩阵的命令行参数。"""
    parser = argparse.ArgumentParser(description="Run WorkflowProgram runtime smoke matrix")
    parser.add_argument(
        "--provider-command",
        default="python3 tools/mock_runtime_host.py",
        help="Provider command for command_adapter cases",
    )
    parser.add_argument("--include-claude-cli", action="store_true", help="Also run a claude_cli smoke case")
    parser.add_argument(
        "--require-claude-pass",
        action="store_true",
        help="When --include-claude-cli is set, require PASS instead of allowing ENVIRONMENT-SKIP",
    )
    parser.add_argument("--timeout", type=int, default=90, help="Per-case timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    return parser.parse_args()


def main() -> int:
    """执行选定矩阵用例，并输出总体验证结论。"""
    args = parse_args()
    cases = base_cases(args.provider_command)
    if args.include_claude_cli:
        cases.append(claude_case(args.require_claude_pass))

    results = [run_case(case, args.timeout) for case in cases]
    failed = [item for item in results if not item["ok"]]
    payload = {
        "status": "PASS" if not failed else "FAIL",
        "case_count": len(results),
        "failed_count": len(failed),
        "cases": results,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"[{payload['status']}] cases={payload['case_count']} failed={payload['failed_count']}")
        for item in results:
            mark = "PASS" if item["ok"] else "FAIL"
            print(
                f"- {mark} {item['name']}: observed={item['observed_result']}"
                + (f"/{item['observed_category']}" if item["observed_category"] else "")
                + f" expected={item['expected_result']}"
                + (f"/{item['expected_category']}" if item["expected_category"] else "")
            )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
