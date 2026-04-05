#!/usr/bin/env python3
"""
Workflow Validation Script (Cross-Platform)

Validates WorkflowProgram repository structure and consistency.
Replaces validate-workflow.ps1 for Mac/Linux/Windows compatibility.

Usage:
    python validate-workflow.py [ROOT_PATH]

Exit codes:
    0 - Validation passed
    1 - Validation failed
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


REQUIRED_PRIMARY_SKILLS = [
    'workflowprogram-orchestrate',
    'workflowprogram-develop',
    'workflowprogram-audit',
    'workflowprogram-iterate',
    'workflowprogram-validate',
]

FORBIDDEN_LEGACY_PATHS = [
    'commands',
    'skills',
    'agents',
    'rules',
    'scripts',
    'tools/sync_plugin_assets.py',
]


class ValidationResult:
    """Collects validation passes and errors."""

    def __init__(self):
        self.passes: List[str] = []
        self.errors: List[str] = []

    def add_pass(self, message: str):
        self.passes.append(message)

    def add_error(self, message: str):
        self.errors.append(message)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


def parse_frontmatter(content: str) -> Dict[str, str]:
    """Parse YAML frontmatter from markdown content."""
    match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        raise ValueError("Missing YAML frontmatter")

    frontmatter = {}
    for line in match.group(1).split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # Match key: value patterns
        match_kv = re.match(r'^([^:#]+):\s*(.+?)\s*$', line)
        if match_kv:
            key = match_kv.group(1).strip()
            value = match_kv.group(2).strip().strip('"\'')
            frontmatter[key] = value

    return frontmatter


def validate_required_paths(root: Path, result: ValidationResult) -> None:
    """Validate required files and directories exist."""
    required_paths = [
        "CLAUDE.md",
        "README.md",
        "lessons.md",
        "validation-report.md",
        ".claude/settings.json",
        ".claude/commands",
        ".claude/skills",
        ".claude/rules/constraints.md",
        ".claude/scripts/managed-assets.py",
        ".claude/scripts/stage-progress.py",
        ".claude/scripts/validate-workflow.ps1",
        ".claude/scripts/validate-workflow.py",  # Self-check
        ".claude-plugin/plugin.json",
        ".claude-plugin/marketplace.json",
        "tools/build_plugin.py",
        "tools/runtime_smoke.py",
        "tests/fixtures",
        "tests/expectations",
        "tests/transcripts",
    ]

    for relative_path in required_paths:
        full_path = root / relative_path
        if full_path.exists():
            result.add_pass(f"Found {relative_path}")
        else:
            result.add_error(f"Missing required path: {relative_path}")

    for relative_path in FORBIDDEN_LEGACY_PATHS:
        full_path = root / relative_path
        if full_path.exists():
            result.add_error(f"Legacy compatibility path must not exist: {relative_path}")
        else:
            result.add_pass(f"Legacy compatibility path removed: {relative_path}")


def validate_settings_json(root: Path, result: ValidationResult) -> Optional[Dict]:
    """Validate settings.json format and return parsed content."""
    settings_path = root / ".claude/settings.json"

    if not settings_path.exists():
        result.add_error("Missing .claude/settings.json")
        return None

    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        result.add_pass("Parsed .claude/settings.json")
        return settings
    except json.JSONDecodeError as e:
        result.add_error(f"Invalid JSON in .claude/settings.json: {e}")
        return None


def validate_commands(root: Path, settings: Dict, result: ValidationResult) -> None:
    """Validate commands are properly structured and registered."""
    commands_dir = root / ".claude/commands"
    if not commands_dir.exists():
        result.add_error("Missing .claude/commands directory")
        return

    registered_commands = {}
    if settings and 'commands' in settings:
        for cmd_name, cmd_info in settings['commands'].items():
            file_path = cmd_info.get('file', '')
            registered_commands[cmd_name] = file_path
            full_path = root / file_path

            if full_path.exists():
                result.add_pass(f"Registered command '{cmd_name}' points to an existing file")
            else:
                result.add_error(f"Registered command '{cmd_name}' points to a missing file: {file_path}")

    # Check each command file
    for cmd_file in sorted(commands_dir.glob("*.md")):
        relative = f".claude/commands/{cmd_file.name}"

        try:
            with open(cmd_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            result.add_error(f"Cannot read command '{cmd_file.name}': {e}")
            continue

        # Check Usage section
        if re.search(r'^## Usage\s*$', content, re.MULTILINE):
            result.add_pass(f"Command '{cmd_file.name}' has a Usage section")
        else:
            result.add_error(f"Command '{cmd_file.name}' is missing a Usage section")

        # Check staged structure
        if re.search(r'^## Stage \d+:', content, re.MULTILINE):
            result.add_pass(f"Command '{cmd_file.name}' uses staged structure")
        else:
            result.add_error(f"Command '{cmd_file.name}' is missing numbered stages")

        # Check Goal and Verify
        if '**Goal**:' in content and '**Verify**:' in content:
            result.add_pass(f"Command '{cmd_file.name}' defines Goal and Verify")
        else:
            result.add_error(f"Command '{cmd_file.name}' is missing Goal or Verify")

        # Check registration
        if relative in registered_commands.values():
            result.add_pass(f"Command '{cmd_file.name}' is registered in settings.json")
        else:
            result.add_error(f"Command '{cmd_file.name}' exists on disk but is not registered in settings.json")


def validate_skills(root: Path, settings: Dict, result: ValidationResult) -> None:
    """Validate skills are properly structured and registered."""
    skills_dir = root / ".claude/skills"
    if not skills_dir.exists():
        result.add_error("Missing .claude/skills directory")
        return

    registered_skills = {}
    if settings and 'skills' in settings:
        for skill_name, skill_info in settings['skills'].items():
            file_path = skill_info.get('file', '')
            registered_skills[skill_name] = file_path
            full_path = root / file_path

            if full_path.exists():
                result.add_pass(f"Registered skill '{skill_name}' points to an existing file")
            else:
                result.add_error(f"Registered skill '{skill_name}' points to a missing file: {file_path}")

    # Check each skill directory
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            result.add_error(f"Skill directory '{skill_dir.name}' is missing SKILL.md")
            continue

        try:
            with open(skill_md, 'r', encoding='utf-8') as f:
                content = f.read()

            frontmatter = parse_frontmatter(content)

            # Check required frontmatter fields
            for field in ["name", "description", "version"]:
                if field in frontmatter and frontmatter[field]:
                    result.add_pass(f"Skill '{skill_dir.name}' includes frontmatter field '{field}'")
                else:
                    result.add_error(f"Skill '{skill_dir.name}' is missing frontmatter field '{field}'")

            # Check registration (internal skills exempt)
            is_internal = frontmatter.get("internal", "").lower() == "true"
            relative_skill = f".claude/skills/{skill_dir.name}/SKILL.md"

            if is_internal:
                result.add_pass(f"Internal support skill '{skill_dir.name}' is exempt from settings registration")
            elif relative_skill in registered_skills.values():
                result.add_pass(f"Skill '{skill_dir.name}' is registered in settings.json")
            else:
                result.add_error(f"Skill '{skill_dir.name}' exists on disk but is not registered in settings.json")

        except ValueError as e:
            result.add_error(f"Skill '{skill_dir.name}': {e}")
        except Exception as e:
            result.add_error(f"Cannot validate skill '{skill_dir.name}': {e}")


def validate_primary_skill_set(settings: Dict, result: ValidationResult) -> None:
    """Validate that skills-first primary entry points are registered."""
    if not settings or 'skills' not in settings:
        result.add_error('settings.json is missing skills registration')
        return

    registered = settings['skills']
    for skill_name in REQUIRED_PRIMARY_SKILLS:
        if skill_name in registered:
            result.add_pass(f"Primary skill '{skill_name}' is registered in settings.json")
        else:
            result.add_error(f"Missing required primary skill registration: {skill_name}")


def validate_constraints(root: Path, result: ValidationResult) -> None:
    """Validate constraints.md contains ALWAYS and NEVER rules."""
    constraints_path = root / ".claude/rules/constraints.md"

    if not constraints_path.exists():
        result.add_error("Missing .claude/rules/constraints.md")
        return

    try:
        with open(constraints_path, 'r', encoding='utf-8') as f:
            content = f.read()

        has_always = 'ALWAYS' in content
        has_never = 'NEVER' in content

        if has_always and has_never:
            result.add_pass("constraints.md includes BOTH ALWAYS and NEVER rules")
        else:
            missing = []
            if not has_always:
                missing.append("ALWAYS")
            if not has_never:
                missing.append("NEVER")
            result.add_error(f"constraints.md must include BOTH ALWAYS and NEVER rules (missing: {', '.join(missing)})")
    except Exception as e:
        result.add_error(f"Cannot validate constraints.md: {e}")


def validate_plugin_metadata(root: Path, result: ValidationResult) -> Optional[Dict[str, Any]]:
    plugin_json_path = root / ".claude-plugin" / "plugin.json"
    marketplace_json_path = root / ".claude-plugin" / "marketplace.json"

    plugin_meta: Optional[Dict[str, Any]] = None
    try:
        plugin_meta = json.loads(plugin_json_path.read_text(encoding="utf-8"))
        result.add_pass("Parsed .claude-plugin/plugin.json")
        for field in ["name", "version", "description"]:
            if plugin_meta.get(field):
                result.add_pass(f"plugin.json includes field '{field}'")
            else:
                result.add_error(f"plugin.json is missing field '{field}'")
    except Exception as e:
        result.add_error(f"Cannot parse .claude-plugin/plugin.json: {e}")

    try:
        marketplace_meta = json.loads(marketplace_json_path.read_text(encoding="utf-8"))
        result.add_pass("Parsed .claude-plugin/marketplace.json")
        plugins = marketplace_meta.get("plugins")
        if isinstance(plugins, list) and plugins:
            result.add_pass("marketplace.json defines at least one plugin entry")
        else:
            result.add_error("marketplace.json must define at least one plugin entry")
    except Exception as e:
        result.add_error(f"Cannot parse .claude-plugin/marketplace.json: {e}")

    return plugin_meta


def validate_dist_plugin(root: Path, plugin_meta: Optional[Dict[str, Any]], result: ValidationResult) -> None:
    dist_root = root / "dist" / "plugin"
    if not dist_root.exists():
        result.add_pass("dist/plugin not present; build output validation skipped")
        return

    required_paths = [
        dist_root / ".claude-plugin" / "plugin.json",
        dist_root / ".claude-plugin" / "marketplace.json",
        dist_root / "build-manifest.json",
        dist_root / "scripts" / "managed-assets.py",
        dist_root / "scripts" / "stage-progress.py",
    ]
    for path in required_paths:
        relative = path.relative_to(root)
        if path.exists():
            result.add_pass(f"Build output contains {relative}")
        else:
            result.add_error(f"Build output is missing {relative}")

    manifest_path = dist_root / "build-manifest.json"
    if not manifest_path.exists():
        return

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        result.add_pass("Parsed dist/plugin/build-manifest.json")
    except Exception as e:
        result.add_error(f"Cannot parse dist/plugin/build-manifest.json: {e}")
        return

    for field in ["manifest_version", "generated_at", "plugin_name", "plugin_version", "files"]:
        if field in manifest:
            result.add_pass(f"build-manifest.json includes field '{field}'")
        else:
            result.add_error(f"build-manifest.json is missing field '{field}'")

    if plugin_meta:
        if manifest.get("plugin_name") == plugin_meta.get("name"):
            result.add_pass("build-manifest plugin_name matches source plugin.json")
        else:
            result.add_error("build-manifest plugin_name does not match source plugin.json")
        if manifest.get("plugin_version") == plugin_meta.get("version"):
            result.add_pass("build-manifest plugin_version matches source plugin.json")
        else:
            result.add_error("build-manifest plugin_version does not match source plugin.json")

    files = manifest.get("files", [])
    if not isinstance(files, list):
        result.add_error("build-manifest files must be a list")
        return

    has_managed_assets = False
    has_stage_progress = False
    for item in files:
        path = item.get("path")
        sha256 = item.get("sha256")
        if not path:
            result.add_error("build-manifest contains an entry without path")
            continue
        if not sha256 or len(sha256) != 64:
            result.add_error(f"build-manifest entry '{path}' is missing a valid sha256")
            continue
        built_file = dist_root / path
        if built_file.exists():
            result.add_pass(f"build-manifest file exists: {path}")
        else:
            result.add_error(f"build-manifest references a missing file: {path}")
        if path == "scripts/managed-assets.py":
            has_managed_assets = True
        if path == "scripts/stage-progress.py":
            has_stage_progress = True

    if has_managed_assets:
        result.add_pass("build-manifest tracks scripts/managed-assets.py")
    else:
        result.add_error("build-manifest must include scripts/managed-assets.py")

    if has_stage_progress:
        result.add_pass("build-manifest tracks scripts/stage-progress.py")
    else:
        result.add_error("build-manifest must include scripts/stage-progress.py")


def print_report(result: ValidationResult) -> None:
    """Print validation report in structured format."""
    print("\n" + "=" * 50)
    print("Workflow Validation Summary")
    print("=" * 50)

    print(f"\n✓ PASS: {len(result.passes)}")
    for item in result.passes:
        print(f"  [PASS] {item}")

    print(f"\n✗ FAIL: {len(result.errors)}")
    for item in result.errors:
        print(f"  [FAIL] {item}")

    print("\n" + "=" * 50)
    if result.is_valid:
        print("Result: ALL CHECKS PASSED ✓")
    else:
        print(f"Result: {len(result.errors)} ERROR(S) FOUND ✗")
    print("=" * 50 + "\n")


def main():
    """Main entry point."""
    # Determine root path
    if len(sys.argv) > 1:
        root = Path(sys.argv[1]).resolve()
    else:
        # Default: parent of script's parent (.claude/scripts/ -> root)
        root = Path(__file__).resolve().parents[2]

    print(f"Validating WorkflowProgram at: {root}")

    result = ValidationResult()

    # Run validations
    validate_required_paths(root, result)
    settings = validate_settings_json(root, result)

    if settings:
        validate_commands(root, settings, result)
        validate_skills(root, settings, result)
        validate_primary_skill_set(settings, result)

    validate_constraints(root, result)
    plugin_meta = validate_plugin_metadata(root, result)
    validate_dist_plugin(root, plugin_meta, result)

    # Print report
    print_report(result)

    # Exit with appropriate code
    sys.exit(0 if result.is_valid else 1)


if __name__ == '__main__':
    main()
