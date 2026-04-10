#!/usr/bin/env python3
# AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY
"""
WorkflowProgram 目标写入的 managed asset 守卫。

该工具落实一条核心设计规则：
WorkflowProgram 必须先在 RUN_ROOT 下生成候选 workflow 资产，
再判断它们能否安全回写到 TARGET_ROOT/.claude/，
而不能静默覆盖用户修改。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def iso_now() -> str:
    """返回 managed asset 证据文件统一使用的时间戳格式。"""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def make_run_id() -> str:
    """在 managed-assets 独立运行时生成兜底 run id。"""

    return f"managed-assets-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"


def write_text(path: Path, content: str) -> None:
    """创建父目录后写入 UTF-8 文本。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    """通过统一文本写入器写出规范化 JSON。"""

    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def append_event(path: Path, payload: Dict[str, Any]) -> None:
    """为 managed-asset 审计追加一条 JSONL 事件。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def sha256_file(path: Path) -> str:
    """对文件做哈希，便于 manifest 所有权模型检测后续漂移。"""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_plugin_json(start: Path) -> Optional[Path]:
    """定位插件元数据，用于写入 producer version。"""

    candidates: List[Path] = []
    env_plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env_plugin_root:
        candidates.append(Path(env_plugin_root))
    candidates.extend([start, *start.parents])

    for candidate in candidates:
        plugin_json = candidate / ".claude-plugin" / "plugin.json"
        if plugin_json.exists():
            return plugin_json
    return None


def detect_producer_version(explicit: Optional[str]) -> str:
    """解析写入 managed-files.json 的 producer version。"""

    if explicit:
        return explicit
    plugin_json = find_plugin_json(Path(__file__).resolve())
    if plugin_json is None:
        return "unknown"
    try:
        payload = json.loads(plugin_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "unknown"
    return str(payload.get("version", "unknown"))


def resolve_run_root(target_root: Path, explicit: Optional[str]) -> Path:
    """根据显式参数、环境变量或独立默认值解析 RUN_ROOT。"""

    if explicit:
        return Path(explicit).resolve()
    env_run_root = os.environ.get("WORKFLOWPROGRAM_RUN_ROOT")
    if env_run_root:
        return Path(env_run_root).resolve()
    return (target_root / ".workflowprogram" / "runs" / make_run_id()).resolve()


def manifest_path_for(target_root: Path) -> Path:
    """返回 TARGET_ROOT 下规范的 manifest 路径。"""

    return target_root / ".workflowprogram" / "managed-files.json"


def load_manifest(path: Path) -> Dict[str, Any]:
    """加载 managed-file manifest；不存在时返回空白结构。"""

    if not path.exists():
        return {
            "manifest_version": 1,
            "updated_at": None,
            "entries": [],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(path: Path, payload: Dict[str, Any]) -> None:
    """更新 updated_at 后持久化 managed manifest。"""

    payload["updated_at"] = iso_now()
    write_json(path, payload)


def iter_candidate_files(source_root: Path) -> Iterable[Path]:
    """按稳定顺序遍历 staged candidate 文件。"""

    for path in sorted(source_root.rglob("*")):
        if path.is_file():
            yield path


def entry_index(manifest: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """按相对路径给 manifest 条目建立索引，便于做所有权查询。"""

    return {entry["relative_path"]: entry for entry in manifest.get("entries", [])}


@dataclass
class CandidateDecision:
    """单个候选文件的决策记录。

    plan 阶段绝不修改目标目录；
    它只负责给每个候选文件分类，以便 apply-staged 后续严格执行既定动作。
    """

    relative_path: str
    source_path: str
    source_sha256: str
    target_path: str
    target_exists: bool
    target_sha256: Optional[str]
    ownership: Optional[str]
    decision: str
    reason: str
    manifest_entry: Optional[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "source_path": self.source_path,
            "source_sha256": self.source_sha256,
            "target_path": self.target_path,
            "target_exists": self.target_exists,
            "target_sha256": self.target_sha256,
            "ownership": self.ownership,
            "decision": self.decision,
            "reason": self.reason,
            "manifest_entry": self.manifest_entry,
        }


def decide_candidates(target_root: Path, source_root: Path, manifest: Dict[str, Any]) -> List[CandidateDecision]:
    """把每个候选文件归类为 create、update 或 conflict。

    这些决策规则就是 managed-write 契约的代码化表达：
    - 目标不存在 => 可安全创建
    - 目标存在但未托管 => 冲突
    - 目标已托管且自上次应用后未变化 => 可安全更新
    - 目标已托管但发生漂移 => 冲突
    """

    decisions: List[CandidateDecision] = []
    manifest_entries = entry_index(manifest)

    for source_file in iter_candidate_files(source_root):
        relative = source_file.relative_to(source_root).as_posix()
        relative_path = f".claude/{relative}"
        target_path = target_root / relative_path
        source_sha = sha256_file(source_file)
        manifest_entry = manifest_entries.get(relative_path)
        target_exists = target_path.exists()
        target_sha = sha256_file(target_path) if target_exists else None
        ownership = manifest_entry.get("ownership") if manifest_entry else None

        # 目标文件不存在时，总是可以安全创建，因为还没有用户内容需要保护。
        if not target_exists:
            decision = CandidateDecision(
                relative_path=relative_path,
                source_path=str(source_file),
                source_sha256=source_sha,
                target_path=str(target_path),
                target_exists=False,
                target_sha256=None,
                ownership=ownership,
                decision="create",
                reason="Target file does not exist.",
                manifest_entry=manifest_entry,
            )
        # 已存在但未纳入托管的文件，默认视为用户所有。
        elif manifest_entry is None:
            decision = CandidateDecision(
                relative_path=relative_path,
                source_path=str(source_file),
                source_sha256=source_sha,
                target_path=str(target_path),
                target_exists=True,
                target_sha256=target_sha,
                ownership=None,
                decision="conflict-unmanaged-existing",
                reason="Target file exists but is not registered as managed.",
                manifest_entry=None,
            )
        # 只有当线上文件仍与上次托管写入版本完全一致时，managed 文件才允许自动更新。
        elif target_sha == manifest_entry.get("last_applied_hash"):
            decision = CandidateDecision(
                relative_path=relative_path,
                source_path=str(source_file),
                source_sha256=source_sha,
                target_path=str(target_path),
                target_exists=True,
                target_sha256=target_sha,
                ownership=ownership,
                decision="update",
                reason="Managed file matches last applied hash and can be updated.",
                manifest_entry=manifest_entry,
            )
        # 任何漂移都表示用户或其他工具在上次托管写入后改动了文件；
        # 此时必须停止并保留冲突副本，而不是直接覆盖。
        else:
            decision = CandidateDecision(
                relative_path=relative_path,
                source_path=str(source_file),
                source_sha256=source_sha,
                target_path=str(target_path),
                target_exists=True,
                target_sha256=target_sha,
                ownership=ownership,
                decision="conflict-managed-drift",
                reason="Managed file was modified after the last applied version.",
                manifest_entry=manifest_entry,
            )
        decisions.append(decision)

    return decisions


def summarize(decisions: List[CandidateDecision]) -> Dict[str, int]:
    """把逐文件决策汇总成 plan 摘要计数。"""

    summary = {
        "candidate_files": len(decisions),
        "create": 0,
        "update": 0,
        "conflict": 0,
    }
    for item in decisions:
        if item.decision == "create":
            summary["create"] += 1
        elif item.decision == "update":
            summary["update"] += 1
        else:
            summary["conflict"] += 1
    return summary


def ensure_candidate_root(source_root: Path) -> None:
    """校验 staged candidate 根目录存在且为目录。"""

    if not source_root.exists():
        raise FileNotFoundError(f"Candidate source root not found: {source_root}")
    if not source_root.is_dir():
        raise NotADirectoryError(f"Candidate source root must be a directory: {source_root}")


def plan_payload(target_root: Path, source_root: Path, run_root: Path, producer_version: str) -> Dict[str, Any]:
    """在不修改 TARGET_ROOT 的前提下构建结构化 managed-asset plan。"""

    manifest = load_manifest(manifest_path_for(target_root))
    decisions = decide_candidates(target_root, source_root, manifest)
    payload = {
        "generated_at": iso_now(),
        "target_root": str(target_root),
        "source_root": str(source_root),
        "run_root": str(run_root),
        "manifest_path": str(manifest_path_for(target_root)),
        "producer_version": producer_version,
        "summary": summarize(decisions),
        "entries": [item.to_dict() for item in decisions],
    }
    return payload


def emit(run_root: Path, event_type: str, status: str, message: str, **extra: Any) -> None:
    """向共享 RUN_ROOT 事件流追加一条 managed-assets 事件。"""

    append_event(
        run_root / "events.jsonl",
        {
            "ts": iso_now(),
            "type": event_type,
            "stage": "managed-assets",
            "source": "managed-assets",
            "status": status,
            "message": message,
            **extra,
        },
    )


def copy_candidate_for_conflict(run_root: Path, relative_path: str, source_path: Path) -> str:
    """保留无法应用的候选版本副本。"""

    conflict_path = run_root / "outputs" / "conflicts" / relative_path
    conflict_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, conflict_path)
    return str(conflict_path)


def update_manifest_entries(
    manifest: Dict[str, Any],
    applied: List[Dict[str, Any]],
    producer_version: str,
) -> Dict[str, Any]:
    """把新应用的文件合并回 managed manifest。"""

    entries = entry_index(manifest)
    now = iso_now()
    for item in applied:
        entries[item["relative_path"]] = {
            "relative_path": item["relative_path"],
            "producer_version": producer_version,
            "last_applied_hash": item["applied_sha256"],
            "ownership": "managed",
            "last_applied_at": now,
            "last_run_id": item["run_id"],
        }
    manifest["entries"] = [entries[key] for key in sorted(entries.keys())]
    return manifest


def write_markdown_summary(path: Path, result: Dict[str, Any]) -> None:
    """在结构化 JSON 结果旁边写一份人类可读摘要。"""

    lines = [
        "# Managed Asset Apply Summary",
        "",
        f"- Generated at: `{result['generated_at']}`",
        f"- Target root: `{result['target_root']}`",
        f"- Source root: `{result['source_root']}`",
        f"- Run root: `{result['run_root']}`",
        f"- Producer version: `{result['producer_version']}`",
        f"- Applied: `{len(result['applied'])}`",
        f"- Conflicts: `{len(result['conflicts'])}`",
        "",
        "## Applied",
        "",
    ]
    if result["applied"]:
        lines.extend(f"- `{item['relative_path']}` ({item['action']})" for item in result["applied"])
    else:
        lines.append("- None")
    lines.extend(["", "## Conflicts", ""])
    if result["conflicts"]:
        for item in result["conflicts"]:
            lines.append(f"- `{item['relative_path']}`: {item['decision']} ({item['reason']})")
    else:
        lines.append("- None")
    write_text(path, "\n".join(lines) + "\n")


def command_plan(args: argparse.Namespace) -> int:
    """只读 planning 阶段的 CLI 处理器。"""

    target_root = Path(args.target_root).resolve()
    source_root = Path(args.source_root).resolve()
    ensure_candidate_root(source_root)
    run_root = resolve_run_root(target_root, args.run_root)
    producer_version = detect_producer_version(args.producer_version)
    payload = plan_payload(target_root, source_root, run_root, producer_version)
    write_json(run_root / "outputs" / "managed-change-plan.json", payload)
    emit(run_root, "ManagedPlanCreated", "ok", "Created managed asset plan", summary=payload["summary"])
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Plan written: {run_root / 'outputs' / 'managed-change-plan.json'}")
        print(json.dumps(payload["summary"], ensure_ascii=False))
    return 0


def command_apply_staged(args: argparse.Namespace) -> int:
    """apply 阶段的 CLI 处理器。

    这里只会执行 plan 中已被判定为安全的动作。
    所有冲突都会复制到 RUN_ROOT 供检查，并返回专用退出码，
    以便调用方在 S4 终止流水线。
    """

    target_root = Path(args.target_root).resolve()
    source_root = Path(args.source_root).resolve()
    ensure_candidate_root(source_root)
    run_root = resolve_run_root(target_root, args.run_root)
    producer_version = detect_producer_version(args.producer_version)
    plan = plan_payload(target_root, source_root, run_root, producer_version)
    manifest_path = manifest_path_for(target_root)
    manifest = load_manifest(manifest_path)

    applied: List[Dict[str, Any]] = []
    conflicts: List[Dict[str, Any]] = []

    for item in plan["entries"]:
        source_path = Path(item["source_path"])
        target_path = Path(item["target_path"])
        if item["decision"] in {"create", "update"}:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            applied_item = {
                "relative_path": item["relative_path"],
                "action": item["decision"],
                "target_path": item["target_path"],
                "applied_sha256": sha256_file(target_path),
                "run_id": Path(run_root).name,
            }
            applied.append(applied_item)
            emit(run_root, "ManagedAssetApplied", "ok", f"Applied {item['relative_path']}", action=item["decision"])
        else:
            # 冲突副本保留“原本要写入”的版本，方便用户和线上目标文件做 diff。
            conflict_copy = copy_candidate_for_conflict(run_root, item["relative_path"], source_path)
            conflict_item = {
                **item,
                "conflict_copy": conflict_copy,
            }
            conflicts.append(conflict_item)
            emit(run_root, "ManagedAssetConflict", "warn", f"Conflict on {item['relative_path']}", decision=item["decision"])

    manifest = update_manifest_entries(manifest, applied, producer_version)
    save_manifest(manifest_path, manifest)

    result = {
        "generated_at": iso_now(),
        "target_root": str(target_root),
        "source_root": str(source_root),
        "run_root": str(run_root),
        "manifest_path": str(manifest_path),
        "producer_version": producer_version,
        "summary": plan["summary"],
        "applied": applied,
        "conflicts": conflicts,
    }
    write_json(run_root / "outputs" / "managed-change-plan.json", plan)
    write_json(run_root / "outputs" / "managed-change-result.json", result)
    write_markdown_summary(run_root / "outputs" / "managed-change-summary.md", result)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Applied: {len(applied)}")
        print(f"Conflicts: {len(conflicts)}")
        print(f"Result written: {run_root / 'outputs' / 'managed-change-result.json'}")
    return 2 if conflicts else 0


def build_parser() -> argparse.ArgumentParser:
    """为两个 managed-asset 子命令构建 CLI 解析器。"""

    parser = argparse.ArgumentParser(description="Manage WorkflowProgram writes into TARGET_ROOT/.claude")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("plan", "apply-staged"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--target-root", required=True, help="Target project root that owns .claude/")
        sub.add_argument("--source-root", required=True, help="Candidate .claude/ root staged under RUN_ROOT")
        sub.add_argument("--run-root", help="Explicit RUN_ROOT; falls back to WORKFLOWPROGRAM_RUN_ROOT or an auto-created run")
        sub.add_argument("--producer-version", help="Override producer version stored in managed-files.json")
        sub.add_argument("--json", action="store_true", help="Print structured JSON output")
        sub.set_defaults(handler=command_plan if name == "plan" else command_apply_staged)

    return parser


def main() -> int:
    """带稳定非零失败契约的 CLI 入口。"""

    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
