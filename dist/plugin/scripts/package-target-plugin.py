#!/usr/bin/env python3
# AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY
"""Stage a WorkflowProgram-generated target workflow as a Claude Code plugin package."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List

from lib.io_utils import iso_now, write_json


PUBLISH_DIR = "outputs/stages/publish"
VALID_RUNTIME_MODES = {"workflowprogram_dependency", "vendored_runtime"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package a target workflow as a Claude Code plugin")
    parser.add_argument("--target-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--plugin-id", required=True)
    parser.add_argument("--plugin-name", default="")
    parser.add_argument("--version", default="0.1.0")
    parser.add_argument("--description", default="WorkflowProgram generated Claude Code workflow plugin")
    parser.add_argument("--repository-url", default="")
    parser.add_argument("--marketplace-name", default="target-workflow-plugins")
    parser.add_argument("--runtime-mode", default="workflowprogram_dependency", choices=sorted(VALID_RUNTIME_MODES))
    parser.add_argument("--workflowprogram-plugin-root", default="")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def sanitize_plugin_id(value: str) -> str:
    return value.strip().lower()


def valid_plugin_id(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9][a-z0-9-]{1,62}", value))


def copy_tree_if_exists(src: Path, dst: Path, included: List[str], package_root: Path) -> None:
    if not src.exists():
        return
    for path in sorted(src.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        included.append(target.relative_to(package_root).as_posix())


def write_text(path: Path, content: str, included: List[str], package_root: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    included.append(path.relative_to(package_root).as_posix())


def package_files(package_root: Path) -> List[Dict[str, Any]]:
    files: List[Dict[str, Any]] = []
    for path in sorted(package_root.rglob("*")):
        if path.is_file():
            files.append({"path": path.relative_to(package_root).as_posix(), "size": path.stat().st_size})
    return files


def vendor_runtime_assets(workflowprogram_plugin_root: Path, package_root: Path, included: List[str]) -> List[str]:
    copied: List[str] = []
    if not workflowprogram_plugin_root.exists():
        return copied
    for rel_path in [
        "bin/workflowprogram-python",
        "requirements.lock.txt",
        "scripts/workflow-runner.py",
        "scripts/validate-run-state.py",
        "scripts/validate-workflow-spec.py",
        "scripts/probe-host-capabilities.py",
        "scripts/apply-host-bootstrap.py",
        "scripts/discover-host-capabilities.py",
        "scripts/generate-environment-remediation.py",
    ]:
        src = workflowprogram_plugin_root / rel_path
        if not src.exists() or not src.is_file():
            continue
        dst = package_root / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(rel_path)
        included.append(rel_path)
    return copied


def package_target_plugin(
    *,
    target_root: Path,
    run_root: Path,
    plugin_id: str,
    plugin_name: str,
    version: str,
    description: str,
    repository_url: str,
    marketplace_name: str,
    runtime_mode: str,
    workflowprogram_plugin_root: Path | None,
) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    normalized_id = sanitize_plugin_id(plugin_id)
    if normalized_id != plugin_id.strip():
        warnings.append(f"plugin id normalized to {normalized_id}")
    if not valid_plugin_id(normalized_id):
        errors.append("plugin id must match [a-z0-9][a-z0-9-]{1,62}")
    if runtime_mode not in VALID_RUNTIME_MODES:
        errors.append(f"runtime mode must be one of {sorted(VALID_RUNTIME_MODES)}")
    if errors:
        payload = {
            "schema_version": 1,
            "generated_at": iso_now(),
            "status": "FAIL",
            "errors": errors,
            "warnings": warnings,
            "package_root": None,
        }
        write_json(run_root / PUBLISH_DIR / "plugin-package-plan.json", payload)
        return payload

    package_root = run_root / PUBLISH_DIR / "package-root"
    if package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True, exist_ok=True)
    included: List[str] = []

    for src_name, dst_name in (
        ("commands", "commands"),
        ("skills", "skills"),
        ("agents", "agents"),
        ("rules", "rules"),
        ("hooks", "hooks"),
    ):
        copy_tree_if_exists(target_root / ".claude" / src_name, package_root / dst_name, included, package_root)

    copy_tree_if_exists(target_root / ".workflowprogram" / "design", package_root / ".workflowprogram" / "design", included, package_root)
    copy_tree_if_exists(target_root / ".workflowprogram" / "runtime", package_root / ".workflowprogram" / "runtime", included, package_root)

    vendored_files: List[str] = []
    if runtime_mode == "vendored_runtime":
        vendored_files = vendor_runtime_assets(workflowprogram_plugin_root or Path(), package_root, included)
        if not vendored_files:
            warnings.append("vendored_runtime selected but no WorkflowProgram runtime files were copied")

    display_name = plugin_name.strip() or normalized_id
    repo = repository_url.strip() or f"https://github.com/<owner>/{normalized_id}"
    plugin_json = {
        "name": normalized_id,
        "version": version,
        "description": description,
        "author": {"name": "<github-user>"},
        "homepage": repo,
        "repository": repo,
        "license": "MIT",
        "keywords": ["claude-code", "workflow", "workflowprogram"],
    }
    marketplace_json = {
        "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
        "name": marketplace_name,
        "description": f"Marketplace for {display_name}",
        "owner": {"name": "<github-user>"},
        "plugins": [
            {
                "name": normalized_id,
                "source": {"source": "git-subdir", "url": repo, "path": "dist/plugin", "ref": "main"},
                "description": description,
                "version": version,
                "homepage": repo,
                "repository": repo,
                "license": "MIT",
                "keywords": ["workflow", "claude-code", "workflowprogram"],
                "category": "workflow",
                "tags": ["workflow", "claude-code"],
                "strict": False,
            }
        ],
    }
    publish_meta = {
        "schema_version": 1,
        "generated_at": iso_now(),
        "plugin_id": normalized_id,
        "plugin_name": display_name,
        "version": version,
        "runtime_mode": runtime_mode,
        "source_target_root": str(target_root),
        "workflowprogram_dependency": runtime_mode == "workflowprogram_dependency",
        "vendored_runtime_files": vendored_files,
    }
    write_json(package_root / ".claude-plugin" / "plugin.json", plugin_json)
    included.append(".claude-plugin/plugin.json")
    write_json(package_root / ".claude-plugin" / "marketplace.json", marketplace_json)
    included.append(".claude-plugin/marketplace.json")
    write_json(package_root / ".claude-plugin" / "workflowprogram-publish.json", publish_meta)
    included.append(".claude-plugin/workflowprogram-publish.json")
    readme_lines = [
        f"# {display_name}",
        "",
        "This Claude Code plugin was packaged from a WorkflowProgram-generated target workflow.",
        "",
        "## Runtime Mode",
        "",
        f"- `{runtime_mode}`",
    ]
    if runtime_mode == "workflowprogram_dependency":
        readme_lines.extend(
            [
                "- Install WorkflowProgram first:",
                "",
                "```text",
                "/plugin marketplace add logic70-plugins https://github.com/Logic70/WorkflowProgram.git",
                "/plugin install workflowprogram-cn@logic70-plugins",
                "```",
            ]
        )
    write_text(package_root / ".claude-plugin" / "README.md", "\n".join(readme_lines) + "\n", included, package_root)

    manifest_preview = {
        "schema_version": 1,
        "generated_at": iso_now(),
        "plugin_json": plugin_json,
        "marketplace_json": marketplace_json,
        "publish_metadata": publish_meta,
    }
    write_json(run_root / PUBLISH_DIR / "plugin-manifest-preview.json", manifest_preview)
    payload = {
        "schema_version": 1,
        "generated_at": iso_now(),
        "status": "PASS",
        "errors": [],
        "warnings": warnings,
        "target_root": str(target_root),
        "package_root": str(package_root),
        "plugin_id": normalized_id,
        "runtime_mode": runtime_mode,
        "included_files": sorted(set(included)),
        "files": package_files(package_root),
    }
    write_json(run_root / PUBLISH_DIR / "plugin-package-plan.json", payload)
    return payload


def main() -> int:
    args = parse_args()
    payload = package_target_plugin(
        target_root=Path(args.target_root).resolve(),
        run_root=Path(args.run_root).resolve(),
        plugin_id=args.plugin_id,
        plugin_name=args.plugin_name,
        version=args.version,
        description=args.description,
        repository_url=args.repository_url,
        marketplace_name=args.marketplace_name,
        runtime_mode=args.runtime_mode,
        workflowprogram_plugin_root=Path(args.workflowprogram_plugin_root).resolve() if args.workflowprogram_plugin_root.strip() else None,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"[{payload['status']}] package-root={payload.get('package_root')}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
