#!/usr/bin/env python3
"""
WorkflowProgram dist/plugin builder

Source of truth:
    .claude/
    .claude-plugin/

Build output:
    dist/plugin/
"""

from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / ".claude"
PLUGIN_META = ROOT / ".claude-plugin"
DIST = ROOT / "dist" / "plugin"

COMMAND_DESCRIPTIONS = {
    "develop": ("Design a new workflow from requirements", "<requirement> [--auto-approve]"),
    "ship": ("Ship current workflow changes", "[scope] [--auto-approve]"),
    "preflight": ("Run parallel readiness checks before shipping", "[scope]"),
    "hotfix": ("Fast-track a hotfix with reduced scope", "[description]"),
    "evolve-workflow": ("Audit and evolve a workflow repository", "[options] <workflow-path>"),
    "iterate-workflow": ("Iterate a workflow from lessons with approval", "[--dry-run] [--apply] [workflow-path]"),
}

REPLACEMENTS = {
    ".claude/skills/develop/spec-template.md": "${CLAUDE_PLUGIN_ROOT}/skills/develop/spec-template.md",
    ".claude/rules/constraints.md": "${CLAUDE_PLUGIN_ROOT}/rules/constraints.md",
    ".claude/scripts/validate-workflow.ps1": "${CLAUDE_PLUGIN_ROOT}/scripts/validate-workflow.ps1",
    ".claude/scripts/managed-assets.py": "${CLAUDE_PLUGIN_ROOT}/scripts/managed-assets.py",
}

MARKDOWN_HEADER = "<!-- AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY -->\n\n"
SCRIPT_BANNER = "AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY"


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str) -> None:
    ensure_parent(path)
    path.write_text(content, encoding="utf-8", newline="\n")


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def decorate_generated_text(src: Path, content: str) -> str:
    suffix = src.suffix.lower()
    if suffix == ".md":
        return MARKDOWN_HEADER + content
    if suffix in {".py", ".sh", ".ps1"}:
        banner = f"# {SCRIPT_BANNER}\n"
        if content.startswith("#!"):
            first_line, _, remainder = content.partition("\n")
            return f"{first_line}\n{banner}{remainder}"
        return banner + content
    return content


def copy_generated_text(src: Path, dst: Path, *, replace_paths: bool = False) -> None:
    content = src.read_text(encoding="utf-8")
    if replace_paths:
        content = apply_replacements(content)
    write_text(dst, decorate_generated_text(src, content))


def copy_tree_generated(src_dir: Path, dst_dir: Path, *, replace_paths: bool = False) -> None:
    for src in sorted(src_dir.rglob("*")):
        if src.is_file():
            dst = dst_dir / src.relative_to(src_dir)
            copy_generated_text(src, dst, replace_paths=replace_paths)


def copy_plugin_manifest(src_dir: Path, dst_dir: Path) -> None:
    for src in sorted(src_dir.rglob("*")):
        if src.is_file():
            dst = dst_dir / src.relative_to(src_dir)
            ensure_parent(dst)
            shutil.copy2(src, dst)


def apply_replacements(content: str) -> str:
    for old, new in REPLACEMENTS.items():
        content = content.replace(old, new)
    return content


def render_command(src: Path, dst: Path, desc: str, hint: str) -> None:
    body = apply_replacements(src.read_text(encoding="utf-8"))
    frontmatter = f"---\ndescription: {desc}\nargument-hint: {hint}\n---\n\n"
    write_text(dst, MARKDOWN_HEADER + frontmatter + body)


def render_command_wrapper(src: Path, dst: Path, name: str, desc: str, hint: str) -> None:
    body = apply_replacements(src.read_text(encoding="utf-8"))
    meta = (
        f"---\nname: {name}\ndescription: {desc}\nversion: 1.0.0\n"
        f"argument-hint: {hint}\ndisable-model-invocation: true\n---\n\n"
    )
    write_text(dst, MARKDOWN_HEADER + meta + body)


def prepare_output_dirs(root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    for dirname in [".claude-plugin", "agents", "commands", "skills", "rules", "scripts"]:
        (root / dirname).mkdir(parents=True, exist_ok=True)


def build_agents() -> None:
    copy_tree_generated(CLAUDE / "agents", DIST / "agents")


def build_rules() -> None:
    copy_generated_text(CLAUDE / "rules" / "constraints.md", DIST / "rules" / "constraints.md")


def build_scripts() -> None:
    allowed_suffixes = {".py", ".ps1", ".sh"}
    for src in sorted((CLAUDE / "scripts").rglob("*")):
        if not src.is_file():
            continue
        if src.suffix.lower() not in allowed_suffixes:
            continue
        dst = DIST / "scripts" / src.relative_to(CLAUDE / "scripts")
        copy_generated_text(src, dst, replace_paths=True)


def build_skills() -> None:
    copy_tree_generated(CLAUDE / "skills", DIST / "skills")


def build_commands() -> None:
    for src in sorted((CLAUDE / "commands").glob("*.md")):
        name = src.stem
        desc, hint = COMMAND_DESCRIPTIONS[name]
        render_command(src, DIST / "commands" / src.name, desc, hint)
        render_command_wrapper(
            src,
            DIST / "skills" / f"command-{name}" / "SKILL.md",
            name,
            desc,
            hint,
        )


def build_plugin_manifest_dir() -> None:
    copy_plugin_manifest(PLUGIN_META, DIST / ".claude-plugin")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_plugin_metadata() -> dict:
    return json.loads((PLUGIN_META / "plugin.json").read_text(encoding="utf-8"))


def git_output(*args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def source_commit() -> str | None:
    return git_output("rev-parse", "HEAD")


def source_dirty() -> bool | None:
    output = git_output("status", "--short")
    if output is None:
        return None
    return bool(output)


def collect_output_files(root: Path) -> list[dict]:
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name == "build-manifest.json":
            continue
        relative = path.relative_to(root).as_posix()
        files.append(
            {
                "path": relative,
                "sha256": sha256_file(path),
                "size": path.stat().st_size,
            }
        )
    return files


def build_trace_manifest(commit: str | None, dirty: bool | None) -> None:
    plugin_meta = load_plugin_metadata()
    payload = {
        "manifest_version": 1,
        "generated_at": iso_now(),
        "builder": "tools/build_plugin.py",
        "plugin_name": plugin_meta.get("name"),
        "plugin_version": plugin_meta.get("version"),
        "source_commit": commit,
        "source_dirty": dirty,
        "files": collect_output_files(DIST),
    }
    write_text(DIST / "build-manifest.json", json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def main() -> None:
    commit = source_commit()
    dirty = source_dirty()
    prepare_output_dirs(DIST)
    build_plugin_manifest_dir()
    build_agents()
    build_rules()
    build_scripts()
    build_skills()
    build_commands()
    build_trace_manifest(commit, dirty)
    plugin_meta = load_plugin_metadata()
    print("Build complete")
    print(f"  Source: {CLAUDE}")
    print(f"  Manifest: {PLUGIN_META}")
    print(f"  Output: {DIST}")
    print(f"  Plugin: {plugin_meta.get('name')}@{plugin_meta.get('version')}")
    print(f"  Trace manifest: {DIST / 'build-manifest.json'}")


if __name__ == "__main__":
    main()
