#!/usr/bin/env python3
# AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY
"""
为 WorkflowProgram 的 smoke 和环境检查提供 runtime host 抽象层。
"""

from __future__ import annotations

import os
import json
import shlex
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


AUTH_STATUS_TIMEOUT_SECONDS = 5
VALID_RUNTIME_PROVIDERS = {"claude_cli", "fixture_host", "command_adapter"}


def iso_now() -> str:
    """返回稳定的 UTC 时间戳。"""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class RuntimeHostConfig:
    """在 smoke 和 runner 层之间传递的 runtime host 选择结果。"""

    provider: str
    claude_bin: str = "claude"
    provider_command: str = ""


@dataclass
class RuntimeHostProbe:
    """具体 runtime host provider 的 available/ready 探测结果。"""

    provider: str
    available: bool
    ready: bool
    message: str


@dataclass
class RuntimeHostInvocation:
    """所有 runtime provider 统一返回的归一化调用结果。

    对其余栈层来说，执行来自 Claude CLI、确定性的 fixture host，
    还是外部 command adapter，都应该被同一套结构抽象掉。
    """

    provider: str
    result: str
    failure_code: str
    message: str
    is_error: bool
    command: List[str] = field(default_factory=list)
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""
    parsed: Optional[Dict[str, Any]] = None
    subagent_evidence: bool = False
    stage_history: List[str] = field(default_factory=list)
    current_stage: str = ""
    stage_status: str = ""
    next_action: str = ""
    next_stage_on_failure: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def parse_bool_env(value: Optional[str]) -> Optional[bool]:
    """解析常见布尔环境变量写法。"""

    if value is None:
        return None
    text = value.strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return None


def resolve_runtime_host_config(
    *,
    provider: str = "",
    claude_bin: str = "claude",
    provider_command: str = "",
) -> RuntimeHostConfig:
    """根据 CLI 参数和环境默认值解析 runtime host 配置。"""

    provider_name = (provider or "").strip() or os.environ.get("WORKFLOWPROGRAM_RUNTIME_PROVIDER", "").strip()
    if not provider_name:
        provider_name = "claude_cli"
    if provider_name not in VALID_RUNTIME_PROVIDERS:
        raise RuntimeError(
            f"unsupported runtime provider '{provider_name}', expected one of {sorted(VALID_RUNTIME_PROVIDERS)}"
        )
    command = provider_command.strip() or os.environ.get("WORKFLOWPROGRAM_RUNTIME_PROVIDER_COMMAND", "").strip()
    return RuntimeHostConfig(provider=provider_name, claude_bin=claude_bin, provider_command=command)


def read_json_from_output(stdout: str, stderr: str) -> Optional[Dict[str, Any]]:
    """尽可能从 provider 输出流中提取 JSON 对象。"""

    candidates: List[str] = []
    for stream in (stdout, stderr):
        for line in stream.splitlines():
            stripped = line.strip()
            if stripped.startswith("{") and stripped.endswith("}"):
                candidates.append(stripped)
    for raw in reversed(candidates):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return None


def detect_subagent_evidence(text: str) -> bool:
    """推断运行输出中是否包含 task/subagent 证据标记。"""

    lowered = text.lower()
    return any(token in lowered for token in ("subagentstart", "subagentstop", "subagent", "taskcreated", "taskcompleted"))


def _claude_command(claude_bin: str, plugin_root: Path, entry_skill: str, request: str) -> List[str]:
    """构造真实运行时使用的 Claude CLI 调用命令。"""

    invocation = f"/{entry_skill} {request}".strip()
    return [
        claude_bin,
        "-p",
        "--plugin-dir",
        str(plugin_root),
        "--output-format",
        "json",
        invocation,
    ]


def _probe_claude(config: RuntimeHostConfig) -> RuntimeHostProbe:
    """检查 Claude CLI 是否存在且已准备好执行。"""

    binary = shutil.which(config.claude_bin)
    if binary is None:
        return RuntimeHostProbe(config.provider, False, False, f"Claude binary not found: {config.claude_bin}")

    # 测试可以覆盖登录状态，这样即使机器上没有交互式 Claude 会话，
    # runtime 校验也能保持确定性。
    override = parse_bool_env(os.environ.get("WORKFLOWPROGRAM_CLAUDE_LOGGED_IN"))
    if override is not None:
        return RuntimeHostProbe(config.provider, True, override, f"WORKFLOWPROGRAM_CLAUDE_LOGGED_IN override={override}")

    try:
        completed = subprocess.run(
            [binary, "auth", "status"],
            capture_output=True,
            text=True,
            check=False,
            timeout=AUTH_STATUS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return RuntimeHostProbe(config.provider, True, False, f"claude auth status timed out after {AUTH_STATUS_TIMEOUT_SECONDS}s")

    output = completed.stdout.strip() or completed.stderr.strip()
    if completed.returncode != 0:
        return RuntimeHostProbe(config.provider, True, False, output or f"claude auth status exited with code {completed.returncode}")

    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return RuntimeHostProbe(config.provider, True, False, f"claude auth status returned non-JSON output: {output or '<empty>'}")

    logged_in = payload.get("loggedIn")
    if logged_in is True:
        return RuntimeHostProbe(config.provider, True, True, output or "claude auth status reported loggedIn=true")
    if logged_in is False:
        return RuntimeHostProbe(config.provider, True, False, output or "claude auth status reported loggedIn=false")
    return RuntimeHostProbe(config.provider, True, False, "claude auth status did not include a boolean loggedIn field")


def _classify_claude_result(stdout: str, stderr: str, parsed: Optional[Dict[str, Any]], returncode: int) -> RuntimeHostInvocation:
    """把原始 Claude CLI 输出归一化为共享调用结果结构。"""

    combined = "\n".join(part for part in [stdout.strip(), stderr.strip()] if part)
    subagent_evidence = detect_subagent_evidence(combined + "\n" + json.dumps(parsed or {}, ensure_ascii=False))

    # 环境类失败会被有意降级为 ENVIRONMENT-SKIP，
    # 这样 smoke 运行仍能产出有价值的证据。
    if "Not logged in · Please run /login" in combined:
        return RuntimeHostInvocation(
            provider="claude_cli",
            result="ENVIRONMENT-SKIP",
            failure_code="CLAUDE_NOT_LOGGED_IN",
            message="Claude CLI is installed but not logged in.",
            is_error=False,
            stdout=stdout,
            stderr=stderr,
            parsed=parsed,
            returncode=returncode,
            subagent_evidence=subagent_evidence,
        )

    # 缺失插件入口属于产品结构问题，而不是宿主问题。
    if "Unknown skill:" in combined or "Unknown command" in combined:
        return RuntimeHostInvocation(
            provider="claude_cli",
            result="FAIL",
            failure_code="STRUCTURE_FAILURE",
            message="Plugin entry was not discovered by Claude CLI.",
            is_error=True,
            stdout=stdout,
            stderr=stderr,
            parsed=parsed,
            returncode=returncode,
            subagent_evidence=subagent_evidence,
        )

    # 如果拿到了结构化 Claude JSON，就应优先于裸 return code，
    # 因为它包含了宿主对执行结果最强的语义解释。
    if parsed is not None:
        result_text = str(parsed.get("result", ""))
        is_error = bool(parsed.get("is_error", False))
        return RuntimeHostInvocation(
            provider="claude_cli",
            result="FAIL" if is_error else "PASS",
            failure_code="RUNTIME_FAILURE" if is_error else "",
            message=result_text or ("Claude CLI returned an error result." if is_error else "Claude CLI completed successfully."),
            is_error=is_error,
            stdout=stdout,
            stderr=stderr,
            parsed=parsed,
            returncode=returncode,
            subagent_evidence=subagent_evidence,
        )

    if returncode != 0:
        return RuntimeHostInvocation(
            provider="claude_cli",
            result="FAIL",
            failure_code="RUNTIME_FAILURE",
            message="Claude CLI exited with non-zero status without structured JSON output.",
            is_error=True,
            stdout=stdout,
            stderr=stderr,
            returncode=returncode,
            subagent_evidence=subagent_evidence,
        )

    return RuntimeHostInvocation(
        provider="claude_cli",
        result="FAIL",
        failure_code="EVIDENCE_FAILURE",
        message="No structured Claude CLI JSON output was captured.",
        is_error=True,
        stdout=stdout,
        stderr=stderr,
        returncode=returncode,
        subagent_evidence=subagent_evidence,
    )


def _command_adapter_base(config: RuntimeHostConfig) -> List[str]:
    """把外部 adapter 命令归一化成可执行的 argv 列表。"""

    if not config.provider_command:
        raise RuntimeError("runtime provider 'command_adapter' requires WORKFLOWPROGRAM_RUNTIME_PROVIDER_COMMAND or --provider-command")
    raw = shlex.split(config.provider_command)
    repo_root = _repo_root()
    normalized: List[str] = []
    for idx, token in enumerate(raw):
        if not token:
            continue
        if idx == 0 and shutil.which(token):
            normalized.append(token)
            continue
        if token.startswith("-"):
            normalized.append(token)
            continue
        if idx > 0 and raw[idx - 1] in {"-m", "--module"}:
            normalized.append(token)
            continue
        candidate = Path(token)
        # 相对 adapter 路径会相对仓库根目录解析，
        # 这样调用方可以直接传项目内脚本，而不必写绝对路径。
        repo_candidate = (repo_root / token).resolve()
        if candidate.is_absolute():
            normalized.append(str(candidate))
        elif repo_candidate.exists():
            normalized.append(str(repo_candidate))
        else:
            normalized.append(token)
    return normalized


def _probe_command_adapter(config: RuntimeHostConfig) -> RuntimeHostProbe:
    """通过 JSON 协议探测外部 command adapter。"""

    try:
        base = _command_adapter_base(config)
    except RuntimeError as exc:
        return RuntimeHostProbe(config.provider, False, False, str(exc))

    binary = shutil.which(base[0]) or (Path(base[0]).resolve() if Path(base[0]).exists() else None)
    if binary is None:
        return RuntimeHostProbe(config.provider, False, False, f"Provider command not found: {base[0]}")

    completed = subprocess.run(
        [*base, "probe", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout.strip() or completed.stderr.strip()
    if completed.returncode != 0:
        return RuntimeHostProbe(config.provider, True, False, output or f"provider probe exited with code {completed.returncode}")
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return RuntimeHostProbe(config.provider, True, False, f"provider probe returned non-JSON output: {output or '<empty>'}")
    available = bool(payload.get("available", True))
    ready = bool(payload.get("ready", available))
    message = str(payload.get("message", output or "provider probe completed")).strip()
    return RuntimeHostProbe(config.provider, available, ready, message)


def probe_runtime_host(config: RuntimeHostConfig) -> RuntimeHostProbe:
    """在不触发真实 workflow 运行的前提下探测选定 runtime host。"""

    if config.provider == "claude_cli":
        return _probe_claude(config)
    if config.provider == "fixture_host":
        return RuntimeHostProbe(config.provider, True, True, "Deterministic fixture host is ready.")
    if config.provider == "command_adapter":
        return _probe_command_adapter(config)
    raise RuntimeError(f"unsupported runtime provider '{config.provider}'")


def _repo_root() -> Path:
    """根据已安装脚本位置返回仓库根目录。"""

    return Path(__file__).resolve().parents[2]


def _write_text(path: Path, content: str) -> None:
    """fixture_host 使用的内部 UTF-8 文本写入器。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    """fixture_host 使用的内部 JSON 写入器。"""

    _write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    """fixture_host 使用的内部 JSONL 追加器。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _entry_exists(plugin_root: Path, entry_skill: str) -> bool:
    """检查插件入口是否能在运行时加载布局中被发现。"""

    candidates = [
        plugin_root / "skills" / entry_skill / "SKILL.md",
        plugin_root / "commands" / f"{entry_skill}.md",
        plugin_root / "skills" / f"command-{entry_skill}" / "SKILL.md",
    ]
    return any(path.exists() for path in candidates)


def _stage_history_for_entry(entry_skill: str) -> List[str]:
    """返回 fixture_host 暴露的简化逻辑阶段历史。"""

    if entry_skill == "workflowprogram-audit":
        return ["validate", "lessons"]
    if entry_skill == "workflowprogram-validate":
        return ["validate"]
    if entry_skill == "workflowprogram-iterate":
        return ["lessons"]
    return ["requirement", "context", "design", "generate", "validate", "lessons"]


def _failure_kind_from_code(failure_code: str) -> str:
    """把低层 failure code 映射为粗粒度 failure_kind 分类。"""

    if not failure_code:
        return "none"
    if failure_code in {"CONFLICT", "CONFLICT_FAILURE"}:
        return "conflict"
    if failure_code in {"STRUCTURE_FAILURE", "INPUT_FAILURE"}:
        return "design"
    if failure_code in {"RUNTIME_HOST_MISSING", "TARGET_NOT_WRITABLE", "RUNTIME_HOST_NOT_READY"}:
        return "environment"
    return "implementation"


def _write_workflow_spec_draft(run_root: Path, entry_skill: str, request: str) -> None:
    """为 fixture_host 生成确定性的 S1 风格 workflow-spec.md。"""

    content = "\n".join(
        [
            "# Workflow Specification",
            "",
            "## Workflow Identity",
            "",
            "- 工作流名称：Fixture Host Generated Workflow",
            f"- 触发命令：/{entry_skill}",
            "- 简要描述：由 fixture_host 生成的确定性规格草案。",
            "",
            "## User Intent",
            "",
            f"- 用户诉求：希望围绕 `{request.strip() or 'default request'}` 形成可复用 workflow。",
            "- 最终目的：让目标项目获得可持续运行和验证的 Claude Code workflow 资产。",
            "- 成功标准：用户需求、交付物和验证门槛都已明确，并可进入 YAML 设计阶段。",
            "",
            "## Clarification Summary",
            "",
            "- 澄清轮次：2",
            "- 已确认事项：目标项目、触发方式、核心输入输出、质量门禁。",
            "- 已消解歧义：用户诉求、最终目的与成功标准已明确，可继续设计。",
            "",
            "## Trigger Model",
            "",
            "- 调用方式：手动命令",
            f"- 触发细节：使用 `/{entry_skill}` 处理 `{request.strip() or 'default request'}`。",
            "",
            "## Inputs",
            "",
            "- 必需输入：用户请求文本",
            "- 可选输入：当前项目中的 workflow 资产",
            "- 所需外部上下文：仓库中的设计文档与 constraints",
            "",
            "## Outputs",
            "",
            "- 主交付物：托管的 `.claude/` workflow 资产",
            "- 次级产物：运行时验证报告和 lessons 增量",
            "- 输出格式：Markdown、JSON、YAML",
            "",
            "## Quality Gates",
            "",
            "- 阻塞条件：审批未决、冲突、边界违规",
            "- 必需验证：managed apply、spec schema、runtime judge",
            "- 完成定义：目标资产与运行时验证结论一致",
            "",
        ]
    )
    _write_text(run_root / "workflow-spec.md", content + "\n")


def _copy_runtime_spec(repo_root: Path, run_root: Path, entry_skill: str) -> Path:
    """为 fixture_host 准备可供 view/lowlevel 生成器消费的 workflow-spec.yaml。"""

    spec_path = repo_root / "tests" / "spec-fixtures" / "valid-minimal.yaml"
    payload = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"fixture spec is invalid: {spec_path}")
    test_contract = payload.get("test_contract", {})
    if isinstance(test_contract, dict):
        entry = test_contract.get("entry", {})
        if isinstance(entry, dict):
            entry["main_entry"] = entry_skill
    target = run_root / "workflow-spec.yaml"
    _write_text(target, yaml.safe_dump(payload, allow_unicode=True, sort_keys=False))
    return target


def _generate_design_docs(spec_path: Path, run_root: Path) -> Dict[str, Path]:
    """基于真实生成器产出 run_root 下的 view / lowlevel。"""

    script_root = _repo_root() / ".claude" / "scripts"
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


def _write_lessons_delta(run_root: Path, entry_skill: str, request: str, failure_kind: str) -> None:
    """为 fixture_host 运行生成确定性的 S6 lessons delta。"""

    content = "\n".join(
        [
            "# S6 Lessons Delta",
            "",
            f"- run_id: `{run_root.name}`",
            f"- failure_kind: `{failure_kind}`",
            f"- entry_skill: `{entry_skill}`",
            "",
            "## Observations",
            "",
            f"- Request: `{request.strip() or 'default request'}`",
            "- Runtime evidence and stage summaries were preserved under RUN_ROOT.",
            "",
            "## Constraint Candidates",
            "",
            "- Keep managed workflow assets confined to `.claude/**` and preserve runtime evidence under RUN_ROOT.",
            "",
        ]
    )
    _write_text(run_root / "outputs" / "stages" / "s6-lessons-delta.md", content + "\n")


def _write_progress_artifacts(
    run_root: Path,
    stage_history: List[str],
    result: str,
    next_action: str,
    *,
    current_stage: str,
    approval_status: str = "approved",
) -> None:
    """落地 S5/S6 检查所需的最小 progress 产物。"""

    progress_root = run_root / "outputs" / "progress"
    _write_json(
        progress_root / "current-progress.json",
        {
            "run_id": run_root.name,
            "current_stage": current_stage,
            "current_node": current_stage,
            "percent": 100 if result == "PASS" else 80,
            "last_status": "ok" if result == "PASS" else "error",
            "last_verdict": result,
            "approval_status": approval_status,
            "next_action": next_action,
        },
    )
    _append_jsonl(
        progress_root / "milestones.jsonl",
        {
            "stage": current_stage,
            "node": current_stage,
            "event": "StageCompleted",
            "status": "ok" if result == "PASS" else "error",
            "result": result,
            "artifact_refs": [],
        },
    )
    _write_text(
        progress_root / "user-progress.md",
        "\n".join(
            [
                "# Workflow Progress",
                "",
                f"- run_id: `{run_root.name}`",
                f"- current_stage: `{current_stage}`",
                f"- current_node: `{current_stage}`",
                f"- percent: `{100 if result == 'PASS' else 80}`",
                f"- last_status: `{'ok' if result == 'PASS' else 'error'}`",
                f"- last_verdict: `{result}`",
                f"- approval_status: `{approval_status}`",
                "",
                "## 历史关键节点结果",
                "",
                f"- Stage history: `{', '.join(stage_history) or 'none'}`",
                f"- Result: `{result}`",
                "",
                "## Next Action",
                "",
                f"- {next_action}",
                "",
            ]
        ),
    )


def _write_runner_evidence(
    run_root: Path,
    target_root: Path,
    entry_skill: str,
    stage_history: List[str],
    result: str,
    failure_code: str,
) -> None:
    """补齐 develop fixture 路径所需的最小 runner 证据。"""

    outputs = run_root / "outputs"
    _write_json(
        outputs / "stages" / "s0-route.json",
        {
            "intent": "develop",
            "entry_skill": entry_skill,
            "target_root": str(target_root),
            "routed_at": iso_now(),
        },
    )
    _write_json(
        outputs / "stages" / "runner-summary.json",
        {
            "run_id": run_root.name,
            "status": result,
            "entry_skill": entry_skill,
            "transition_count": len(stage_history),
            "failure_code": failure_code or None,
        },
    )


def _invoke_fixture_host(
    config: RuntimeHostConfig,
    plugin_root: Path,
    target_root: Path,
    run_root: Path,
    entry_skill: str,
    request: str,
    fixture: str,
) -> RuntimeHostInvocation:
    """执行测试用的内置确定性 provider。

    fixture_host 不试图模拟 Claude 的内部推理，
    它只负责以可重复的方式产出控制面与验证链所需的最小产物。
    """

    if not _entry_exists(plugin_root, entry_skill):
        return RuntimeHostInvocation(
            provider=config.provider,
            result="FAIL",
            failure_code="STRUCTURE_FAILURE",
            message=f"Plugin entry '{entry_skill}' was not found in plugin root.",
            is_error=True,
        )

    # 缺少请求文本用于模拟 S1/input 失败，而且应发生在任何资产生成之前。
    if not request.strip():
        _write_progress_artifacts(
            run_root,
            ["requirement"],
            "FAIL",
            "provide required request arguments and rerun",
            current_stage="requirement",
            approval_status="pending",
        )
        return RuntimeHostInvocation(
            provider=config.provider,
            result="FAIL",
            failure_code="INPUT_FAILURE",
            message="Required request arguments were not provided.",
            is_error=True,
            stage_history=["requirement"],
            current_stage="requirement",
            stage_status="failed",
            next_action="provide required request arguments and rerun",
            next_stage_on_failure="requirement",
        )

    if entry_skill == "workflowprogram-develop":
        # develop fixture 路径会写出与真实运行同类的产物：
        # spec draft、candidate assets、managed apply 输出和 S6 产物。
        _write_workflow_spec_draft(run_root, entry_skill, request)
        spec_path = _copy_runtime_spec(_repo_root(), run_root, entry_skill)
        design_docs = _generate_design_docs(spec_path, run_root)
        candidate_root = run_root / "outputs" / "candidate"
        candidate_claude_root = candidate_root / ".claude"
        _write_json(
            candidate_claude_root / "settings.json",
            {
                "skills": {
                    "generated-smoke": {
                        "description": "Generated by fixture_host for runtime smoke validation",
                        "file": ".claude/skills/generated-smoke/SKILL.md",
                    }
                }
            },
        )
        _write_text(
            candidate_claude_root / "rules" / "constraints.md",
            "\n".join(
                [
                    "# Runtime Smoke Constraints",
                    "",
                    f"- Source fixture: `{fixture}`",
                    f"- Source request: `{request.strip()}`",
                    "- Generated by fixture_host.",
                    "",
                ]
            ),
        )
        _write_text(
            candidate_claude_root / "skills" / "generated-smoke" / "SKILL.md",
            "\n".join(
                [
                    "---",
                    "name: generated-smoke",
                    "description: Generated by fixture_host for runtime smoke validation",
                    "version: 1.0.0",
                    "---",
                    "",
                    "This skill was generated by fixture_host.",
                    "",
                ]
            ),
        )
        _write_text(
            candidate_claude_root / "commands" / "generated-smoke.md",
            "\n".join(
                [
                    "## Usage",
                    "",
                    "```text",
                    "/generated-smoke <request>",
                    "```",
                    "",
                    "Generated by fixture_host.",
                    "",
                ]
            ),
        )
        candidate_design_root = candidate_root / ".workflowprogram" / "design"
        candidate_design_root.mkdir(parents=True, exist_ok=True)
        for source_name, target_name in (
            ("workflow_spec", "workflow-spec.yaml"),
            ("workflow_view", "workflow-view.md"),
            ("workflow_lowlevel", "workflow-lowlevel.md"),
        ):
            shutil.copy2(design_docs[source_name], candidate_design_root / target_name)

        cmd = [
            sys.executable,
            str(_repo_root() / ".claude" / "scripts" / "managed-assets.py"),
            "apply-staged",
            "--target-root",
            str(target_root),
            "--source-root",
            str(candidate_root),
            "--run-root",
            str(run_root),
            "--json",
        ]
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
        payload = read_json_from_output(completed.stdout, completed.stderr)
        if payload is None:
            result_path = run_root / "outputs" / "managed-change-result.json"
            if result_path.exists():
                try:
                    payload = json.loads(result_path.read_text(encoding="utf-8"))
                except Exception:
                    payload = None

        conflicts = payload.get("conflicts", []) if isinstance(payload, dict) else []
        applied = payload.get("applied", []) if isinstance(payload, dict) else []
        # apply-staged 在“保留冲突而非写入”时会返回 2。
        if completed.returncode == 2:
            if fixture == "external-write":
                external_path = target_root / "external-write.txt"
                _write_text(external_path, "external write\n")
            _write_runner_evidence(
                run_root,
                target_root,
                entry_skill,
                ["requirement", "context", "design", "generate"],
                "FAIL",
                "CONFLICT_FAILURE",
            )
            _write_progress_artifacts(
                run_root,
                ["requirement", "context", "design", "generate"],
                "FAIL",
                "resolve managed asset conflicts and rerun",
                current_stage="generate",
            )
            return RuntimeHostInvocation(
                provider=config.provider,
                result="FAIL",
                failure_code="CONFLICT_FAILURE",
                message=f"Managed asset conflicts detected: {len(conflicts)}",
                is_error=True,
                command=cmd,
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
                parsed=payload,
                stage_history=["requirement", "context", "design", "generate"],
                current_stage="generate",
                stage_status="failed",
                next_action="resolve managed asset conflicts and rerun",
                next_stage_on_failure="generate",
                metadata={"applied": applied, "conflicts": conflicts},
            )
        if completed.returncode != 0:
            _write_runner_evidence(
                run_root,
                target_root,
                entry_skill,
                ["requirement", "context", "design", "generate"],
                "FAIL",
                "RUNTIME_FAILURE",
            )
            _write_progress_artifacts(
                run_root,
                ["requirement", "context", "design", "generate"],
                "FAIL",
                "inspect fixture_host apply failure",
                current_stage="generate",
            )
            return RuntimeHostInvocation(
                provider=config.provider,
                result="FAIL",
                failure_code="RUNTIME_FAILURE",
                message=completed.stderr.strip() or completed.stdout.strip() or "fixture_host apply failed",
                is_error=True,
                command=cmd,
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
                parsed=payload,
            )
        if fixture == "external-write":
            external_path = target_root / "external-write.txt"
            _write_text(external_path, "external write\n")
        _write_runner_evidence(
            run_root,
            target_root,
            entry_skill,
            ["requirement", "context", "design", "generate", "validate", "lessons"],
            "PASS",
            "",
        )
        _write_lessons_delta(run_root, entry_skill, request, _failure_kind_from_code(""))
        _write_progress_artifacts(
            run_root,
            ["requirement", "context", "design", "generate", "validate", "lessons"],
            "PASS",
            "complete",
            current_stage="lessons",
        )
        return RuntimeHostInvocation(
            provider=config.provider,
            result="PASS",
            failure_code="",
            message=f"fixture_host applied {len(applied)} managed workflow assets.",
            is_error=False,
            command=cmd,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            parsed=payload,
            stage_history=["requirement", "context", "design", "generate", "validate", "lessons"],
            current_stage="lessons",
            stage_status="done",
            next_action="complete",
            next_stage_on_failure="",
            metadata={"applied": applied, "conflicts": conflicts},
        )

    # 非 develop 流程会刻意保持更轻，只合成足以让阶段契约可观测的产物。
    if entry_skill == "workflowprogram-validate":
        has_settings = (target_root / ".claude" / "settings.json").exists()
        has_constraints = (target_root / ".claude" / "rules" / "constraints.md").exists()
        _write_progress_artifacts(
            run_root,
            ["validate"],
            "PASS" if has_settings and has_constraints else "FAIL",
            "complete" if has_settings and has_constraints else "restore missing workflow assets",
            current_stage="validate",
        )
        if has_settings and has_constraints:
            return RuntimeHostInvocation(
                provider=config.provider,
                result="PASS",
                failure_code="",
                message="fixture_host validated target workflow assets successfully.",
                is_error=False,
                stage_history=["validate"],
                current_stage="validate",
                stage_status="done",
                next_action="complete",
            )
        return RuntimeHostInvocation(
            provider=config.provider,
            result="FAIL",
            failure_code="RUNTIME_FAILURE",
            message="fixture_host validation failed because required workflow assets are missing.",
            is_error=True,
            stage_history=["validate"],
            current_stage="validate",
            stage_status="failed",
            next_action="restore missing workflow assets",
            next_stage_on_failure="generate",
        )

    if entry_skill == "workflowprogram-audit":
        has_claude_root = (target_root / ".claude").exists()
        stage_history = _stage_history_for_entry(entry_skill)
        if has_claude_root:
            _write_lessons_delta(run_root, entry_skill, request, _failure_kind_from_code(""))
        _write_progress_artifacts(
            run_root,
            stage_history,
            "PASS" if has_claude_root else "FAIL",
            "complete" if has_claude_root else "create workflow assets first",
            current_stage=stage_history[-1],
        )
        return RuntimeHostInvocation(
            provider=config.provider,
            result="PASS" if has_claude_root else "FAIL",
            failure_code="" if has_claude_root else "RUNTIME_FAILURE",
            message="fixture_host completed audit." if has_claude_root else "fixture_host found no workflow assets to audit.",
            is_error=not has_claude_root,
            stage_history=stage_history,
            current_stage=stage_history[-1],
            stage_status="done" if has_claude_root else "failed",
            next_action="complete" if has_claude_root else "create workflow assets first",
            next_stage_on_failure="" if has_claude_root else "requirement",
        )

    if entry_skill == "workflowprogram-iterate":
        _write_lessons_delta(run_root, entry_skill, request, _failure_kind_from_code(""))
        _write_progress_artifacts(
            run_root,
            ["lessons"],
            "PASS",
            "complete",
            current_stage="lessons",
        )
        return RuntimeHostInvocation(
            provider=config.provider,
            result="PASS",
            failure_code="",
            message="fixture_host completed iterate flow.",
            is_error=False,
            stage_history=["lessons"],
            current_stage="lessons",
            stage_status="done",
            next_action="complete",
        )

    _write_progress_artifacts(
        run_root,
        _stage_history_for_entry(entry_skill),
        "PASS",
        "complete",
        current_stage=_stage_history_for_entry(entry_skill)[-1],
    )
    return RuntimeHostInvocation(
        provider=config.provider,
        result="PASS",
        failure_code="",
        message=f"fixture_host completed generic invocation for '{entry_skill}'.",
        is_error=False,
        stage_history=_stage_history_for_entry(entry_skill),
        current_stage=_stage_history_for_entry(entry_skill)[-1],
        stage_status="done",
        next_action="complete",
    )


def _invoke_command_adapter(
    config: RuntimeHostConfig,
    plugin_root: Path,
    target_root: Path,
    run_root: Path,
    entry_skill: str,
    request: str,
    timeout: int,
    fixture: str,
) -> RuntimeHostInvocation:
    """调用一个遵循 command-adapter 协议的外部 provider。"""

    base = _command_adapter_base(config)
    cmd = [
        *base,
        "invoke",
        "--plugin-root",
        str(plugin_root),
        "--target-root",
        str(target_root),
        "--run-root",
        str(run_root),
        "--entry-skill",
        entry_skill,
        "--request",
        request,
        "--fixture",
        fixture,
        "--timeout",
        str(timeout),
        "--json",
    ]
    completed = subprocess.run(cmd, cwd=target_root, capture_output=True, text=True, check=False)
    output = completed.stdout.strip() or completed.stderr.strip()
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        if completed.returncode != 0:
            return RuntimeHostInvocation(
                provider=config.provider,
                result="FAIL",
                failure_code="RUNTIME_FAILURE",
                message=output or f"provider invoke exited with code {completed.returncode}",
                is_error=True,
                command=cmd,
                returncode=completed.returncode,
                stdout=completed.stdout,
                stderr=completed.stderr,
            )
        return RuntimeHostInvocation(
            provider=config.provider,
            result="FAIL",
            failure_code="EVIDENCE_FAILURE",
            message=f"provider invoke returned non-JSON output: {output or '<empty>'}",
            is_error=True,
            command=cmd,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    if not isinstance(payload, dict):
        return RuntimeHostInvocation(
            provider=config.provider,
            result="FAIL",
            failure_code="EVIDENCE_FAILURE",
            message="provider invoke must return a JSON object",
            is_error=True,
            command=cmd,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
    result = str(payload.get("result", "")).strip()
    # adapter 契约尽量贴近共享调用结构，
    # 这样上层栈就不需要为每个 provider 写分支。
    if result not in {"PASS", "WARN", "FAIL", "ENVIRONMENT-SKIP"}:
        return RuntimeHostInvocation(
            provider=config.provider,
            result="FAIL",
            failure_code="EVIDENCE_FAILURE",
            message=f"provider invoke returned invalid result='{result}'",
            is_error=True,
            command=cmd,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            parsed=payload,
        )
    return RuntimeHostInvocation(
        provider=config.provider,
        result=result,
        failure_code=str(payload.get("failure_code", "")).strip(),
        message=str(payload.get("message", "")).strip() or "provider invoke completed",
        is_error=bool(payload.get("is_error", result in {"FAIL", "WARN"} and str(payload.get("failure_code", "")).strip())),
        command=cmd,
        returncode=completed.returncode,
        stdout=str(payload.get("stdout", completed.stdout)),
        stderr=str(payload.get("stderr", completed.stderr)),
        parsed=payload,
        subagent_evidence=bool(payload.get("subagent_evidence", False)),
        stage_history=[str(item) for item in payload.get("stage_history", []) if str(item).strip()],
        current_stage=str(payload.get("current_stage", "")).strip(),
        next_action=str(payload.get("next_action", "")).strip(),
        metadata=payload.get("metadata", {}) if isinstance(payload.get("metadata", {}), dict) else {},
    )


def invoke_runtime_host(
    config: RuntimeHostConfig,
    plugin_root: Path,
    target_root: Path,
    run_root: Path,
    entry_skill: str,
    request: str,
    timeout: int,
    fixture: str = "",
) -> RuntimeHostInvocation:
    """把运行请求分发到选定的 provider 实现。"""

    if config.provider == "claude_cli":
        cmd = _claude_command(config.claude_bin, plugin_root, entry_skill, request)
        try:
            completed = subprocess.run(
                cmd,
                cwd=target_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return RuntimeHostInvocation(
                provider=config.provider,
                result="FAIL",
                failure_code="RUNTIME_FAILURE",
                message=f"Claude CLI timed out after {timeout}s.",
                is_error=True,
                command=cmd,
                returncode=1,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
            )
        parsed = read_json_from_output(completed.stdout, completed.stderr)
        invocation = _classify_claude_result(completed.stdout, completed.stderr, parsed, completed.returncode)
        invocation.command = cmd
        invocation.returncode = completed.returncode
        return invocation
    if config.provider == "fixture_host":
        return _invoke_fixture_host(config, plugin_root, target_root, run_root, entry_skill, request, fixture)
    if config.provider == "command_adapter":
        return _invoke_command_adapter(config, plugin_root, target_root, run_root, entry_skill, request, timeout, fixture)
    raise RuntimeError(f"unsupported runtime provider '{config.provider}'")
