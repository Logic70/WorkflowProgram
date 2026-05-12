#!/usr/bin/env python3
"""Plan or execute GitHub publication for a staged target workflow plugin package."""

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
    parser = argparse.ArgumentParser(description="Publish a staged target workflow plugin to GitHub")
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--repository", required=True, help="GitHub repository URL or owner/name")
    parser.add_argument("--repo-mode", default="export_repo", choices=["current_repo", "export_repo"])
    parser.add_argument("--repo-path", default="", help="Local checkout path to update when executing")
    parser.add_argument("--version", default="0.1.0")
    parser.add_argument("--execute", action="store_true", help="Perform git writes and push")
    parser.add_argument("--approved", action="store_true", help="Required for --execute")
    parser.add_argument("--dry-run", action="store_true", help="Simulate successful GitHub publication")
    parser.add_argument("--simulate-auth-missing", action="store_true", help="Force auth-missing blocked result")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def run_command(cmd: List[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, capture_output=True, text=True, check=False)


def sanitize_auth_output(output: str) -> str:
    lines: List[str] = []
    for line in output.splitlines():
        if "Token:" in line:
            lines.append("  - Token: <redacted>")
        else:
            lines.append(line)
    return "\n".join(lines).strip()


def gh_auth_status(simulate_missing: bool) -> Dict[str, Any]:
    if simulate_missing:
        return {"available": bool(shutil.which("gh")), "ready": False, "message": "simulated missing GitHub auth"}
    gh = shutil.which("gh")
    if not gh:
        return {"available": False, "ready": False, "message": "gh CLI not found"}
    completed = run_command([gh, "auth", "status"])
    output = sanitize_auth_output(completed.stdout.strip() or completed.stderr.strip())
    return {
        "available": True,
        "ready": completed.returncode == 0,
        "message": output or f"gh auth status exited with code {completed.returncode}",
    }


def copy_package_to_checkout(package_root: Path, repo_path: Path) -> List[str]:
    dist_root = repo_path / "dist" / "plugin"
    if dist_root.exists():
        shutil.rmtree(dist_root)
    shutil.copytree(package_root, dist_root)
    copied: List[str] = []
    for path in sorted(dist_root.rglob("*")):
        if path.is_file():
            copied.append(path.relative_to(repo_path).as_posix())
    return copied


def publish_to_github(
    *,
    package_root: Path,
    run_root: Path,
    repository: str,
    repo_mode: str,
    repo_path: Path | None,
    version: str,
    execute: bool,
    approved: bool,
    dry_run: bool,
    simulate_auth_missing: bool,
) -> Dict[str, Any]:
    plan = {
        "schema_version": 1,
        "generated_at": iso_now(),
        "repository": repository,
        "repo_mode": repo_mode,
        "repo_path": str(repo_path) if repo_path else None,
        "version": version,
        "package_root": str(package_root),
        "steps": [
            "verify GitHub auth",
            "copy package to publishing checkout",
            "commit dist/plugin payload",
            f"tag v{version}",
            "push branch and tag",
        ],
        "execute": execute,
        "dry_run": dry_run,
    }
    write_json(run_root / PUBLISH_DIR / "github-publish-plan.json", plan)

    auth = gh_auth_status(simulate_auth_missing)
    if dry_run:
        payload = {
            "schema_version": 1,
            "generated_at": iso_now(),
            "status": "PASS",
            "dry_run": True,
            "repository": repository,
            "repo_mode": repo_mode,
            "commit": "dry-run",
            "tag": f"v{version}",
            "auth": auth,
            "message": "GitHub publication simulated successfully.",
        }
        write_json(run_root / PUBLISH_DIR / "github-publish-result.json", payload)
        return payload

    if not auth["ready"]:
        payload = {
            "schema_version": 1,
            "generated_at": iso_now(),
            "status": "BLOCKED",
            "failure_kind": "environment",
            "block_reason": "github_auth_missing",
            "repository": repository,
            "auth": auth,
            "message": "GitHub authentication is not ready; run gh auth login/status outside WorkflowProgram.",
        }
        write_json(run_root / PUBLISH_DIR / "github-publish-result.json", payload)
        return payload

    if not execute or not approved:
        payload = {
            "schema_version": 1,
            "generated_at": iso_now(),
            "status": "BLOCKED",
            "failure_kind": "design",
            "block_reason": "approval_required",
            "repository": repository,
            "auth": auth,
            "message": "GitHub publish execution requires explicit approval.",
        }
        write_json(run_root / PUBLISH_DIR / "github-publish-result.json", payload)
        return payload

    if repo_path is None:
        payload = {
            "schema_version": 1,
            "generated_at": iso_now(),
            "status": "BLOCKED",
            "failure_kind": "environment",
            "block_reason": "repo_path_required",
            "repository": repository,
            "auth": auth,
            "message": "Executing publish requires --repo-path pointing to a clean checkout.",
        }
        write_json(run_root / PUBLISH_DIR / "github-publish-result.json", payload)
        return payload

    repo_path.mkdir(parents=True, exist_ok=True)
    copied = copy_package_to_checkout(package_root, repo_path)
    run_command(["git", "add", "dist/plugin"], cwd=repo_path)
    commit = run_command(["git", "commit", "-m", f"Publish target workflow plugin v{version}"], cwd=repo_path)
    if commit.returncode != 0:
        payload = {
            "schema_version": 1,
            "generated_at": iso_now(),
            "status": "FAIL",
            "failure_kind": "conflict",
            "repository": repository,
            "copied_files": copied,
            "message": commit.stderr.strip() or commit.stdout.strip() or "git commit failed",
        }
        write_json(run_root / PUBLISH_DIR / "github-publish-result.json", payload)
        return payload
    tag = run_command(["git", "tag", f"v{version}"], cwd=repo_path)
    push = run_command(["git", "push", "--follow-tags"], cwd=repo_path)
    payload = {
        "schema_version": 1,
        "generated_at": iso_now(),
        "status": "PASS" if push.returncode == 0 else "FAIL",
        "failure_kind": "none" if push.returncode == 0 else "environment",
        "repository": repository,
        "repo_path": str(repo_path),
        "copied_files": copied,
        "commit_stdout": commit.stdout.strip(),
        "tag_stdout": tag.stdout.strip(),
        "push_stdout": push.stdout.strip(),
        "push_stderr": push.stderr.strip(),
    }
    write_json(run_root / PUBLISH_DIR / "github-publish-result.json", payload)
    return payload


def main() -> int:
    args = parse_args()
    payload = publish_to_github(
        package_root=Path(args.package_root).resolve(),
        run_root=Path(args.run_root).resolve(),
        repository=args.repository,
        repo_mode=args.repo_mode,
        repo_path=Path(args.repo_path).resolve() if args.repo_path.strip() else None,
        version=args.version,
        execute=args.execute,
        approved=args.approved,
        dry_run=args.dry_run,
        simulate_auth_missing=args.simulate_auth_missing,
    )
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"[{payload['status']}] {payload.get('message', payload.get('repository'))}")
    return 0 if payload["status"] == "PASS" else (2 if payload["status"] == "BLOCKED" else 1)


if __name__ == "__main__":
    raise SystemExit(main())
