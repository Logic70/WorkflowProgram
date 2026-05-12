#!/usr/bin/env python3
# AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY
"""Validate a staged target workflow Claude Code plugin package."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from lib.io_utils import iso_now, write_json


PUBLISH_DIR = "outputs/stages/publish"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate target workflow plugin package")
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--repo-mode", default="export_repo", choices=["current_repo", "export_repo", "existing_marketplace"])
    parser.add_argument("--require-claude-validate", action="store_true")
    parser.add_argument("--skip-claude-validate", action="store_true")
    parser.add_argument("--claude-bin", default="claude")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def run_claude_plugin_validate(package_root: Path, claude_bin: str, skip: bool, require: bool) -> Dict[str, Any]:
    if skip:
        return {"status": "SKIPPED", "reason": "skip flag set"}
    binary = shutil.which(claude_bin)
    if not binary:
        return {"status": "FAIL" if require else "SKIPPED", "reason": f"Claude binary not found: {claude_bin}"}
    completed = subprocess.run(
        [binary, "plugin", "validate", str(package_root)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    return {
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def validate_package(
    package_root: Path,
    run_root: Path,
    *,
    repo_mode: str,
    claude_bin: str,
    skip_claude: bool,
    require_claude: bool,
) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    checks: List[Dict[str, Any]] = []

    def check(name: str, passed: bool, detail: str, *, warning: bool = False) -> None:
        checks.append({"name": name, "status": "PASS" if passed else ("WARN" if warning else "FAIL"), "detail": detail})
        if not passed:
            if warning:
                warnings.append(detail)
            else:
                errors.append(detail)

    check("package_root_exists", package_root.exists(), f"package root: {package_root}")
    plugin_json = load_json(package_root / ".claude-plugin" / "plugin.json")
    marketplace_json = load_json(package_root / ".claude-plugin" / "marketplace.json")
    publish_meta = load_json(package_root / ".claude-plugin" / "workflowprogram-publish.json")
    check("plugin_json_present", bool(plugin_json), ".claude-plugin/plugin.json")
    if repo_mode == "existing_marketplace":
        check("marketplace_json_deferred_to_existing_checkout", not bool(marketplace_json), "existing marketplace packages do not replace marketplace.json")
    else:
        check("marketplace_json_present", bool(marketplace_json), ".claude-plugin/marketplace.json")
    check("publish_metadata_present", bool(publish_meta), ".claude-plugin/workflowprogram-publish.json")

    plugin_id = str(plugin_json.get("name", "")).strip()
    if repo_mode != "existing_marketplace":
        marketplace_plugins = marketplace_json.get("plugins", [])
        marketplace_name = ""
        if isinstance(marketplace_plugins, list) and marketplace_plugins and isinstance(marketplace_plugins[0], dict):
            marketplace_name = str(marketplace_plugins[0].get("name", "")).strip()
        check("marketplace_plugin_matches_manifest", bool(plugin_id and plugin_id == marketplace_name), f"plugin={plugin_id}; marketplace={marketplace_name}")
    check("publish_metadata_repo_mode_matches", str(publish_meta.get("repo_mode", repo_mode)).strip() == repo_mode, f"repo_mode={repo_mode}")

    commands = list((package_root / "commands").glob("*.md")) if (package_root / "commands").exists() else []
    skills = list((package_root / "skills").glob("*/SKILL.md")) if (package_root / "skills").exists() else []
    check("public_entry_assets_present", bool(commands or skills), f"commands={len(commands)} skills={len(skills)}")

    runtime_mode = str(publish_meta.get("runtime_mode", "")).strip()
    check("runtime_mode_declared", runtime_mode in {"workflowprogram_dependency", "vendored_runtime"}, f"runtime_mode={runtime_mode or '<missing>'}")
    if runtime_mode == "workflowprogram_dependency":
        readme_text = (package_root / ".claude-plugin" / "README.md").read_text(encoding="utf-8") if (package_root / ".claude-plugin" / "README.md").exists() else ""
        check("workflowprogram_dependency_instructions", "workflowprogram-cn@logic70-plugins" in readme_text, "README includes WorkflowProgram dependency install instructions")
    if runtime_mode == "vendored_runtime":
        required = [
            "bin/workflowprogram-python",
            "scripts/workflow-runner.py",
            "scripts/validate-run-state.py",
            "scripts/validate-workflow-spec.py",
        ]
        missing = [rel for rel in required if not (package_root / rel).exists()]
        check("vendored_runtime_files_present", not missing, f"missing vendored files={missing or ['<none>']}")

    target_runtime = package_root / ".workflowprogram" / "runtime" / "runtime-manifest.json"
    check("target_runtime_manifest_present", target_runtime.exists(), ".workflowprogram/runtime/runtime-manifest.json")
    target_design = package_root / ".workflowprogram" / "design" / "workflow-spec.yaml"
    check("target_design_spec_present", target_design.exists(), ".workflowprogram/design/workflow-spec.yaml")

    claude_validate = run_claude_plugin_validate(package_root, claude_bin, skip_claude, require_claude)
    if claude_validate.get("status") == "FAIL":
        check("claude_plugin_validate", False, str(claude_validate.get("stderr") or claude_validate.get("stdout") or claude_validate.get("reason")))
    elif claude_validate.get("status") == "SKIPPED":
        check("claude_plugin_validate", False, str(claude_validate.get("reason", "skipped")), warning=True)
    else:
        check("claude_plugin_validate", True, "claude plugin validate passed")

    payload = {
        "schema_version": 1,
        "generated_at": iso_now(),
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "package_root": str(package_root),
        "checks": checks,
        "claude_plugin_validate": claude_validate,
    }
    write_json(run_root / PUBLISH_DIR / "plugin-validation-report.json", payload)
    return payload


def main() -> int:
    args = parse_args()
    payload = validate_package(
        Path(args.package_root).resolve(),
        Path(args.run_root).resolve(),
        repo_mode=args.repo_mode,
        claude_bin=args.claude_bin,
        skip_claude=args.skip_claude_validate,
        require_claude=args.require_claude_validate,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"[{payload['status']}] {payload['package_root']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
