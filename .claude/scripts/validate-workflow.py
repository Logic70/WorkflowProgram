#!/usr/bin/env python3
"""
跨平台的 WorkflowProgram 仓库校验脚本。

它负责校验 WorkflowProgram 仓库结构与一致性，
并替代 validate-workflow.ps1，提供 Mac/Linux/Windows 共用实现。

用法：
    python validate-workflow.py [ROOT_PATH]

退出码：
    0 - 校验通过
    1 - 校验失败
"""

import hashlib
import importlib.util
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

ACTIVE_DESIGN_DOCS = {
    "docs/workflowprogram-stage-highlevel-design.md": [
        "runtime_contract",
        "test_contract",
        "workflow-entry.py",
        "workflowprogram-validate",
        "runtime_smoke.py",
        "validation-runtime-report.md",
        "s5-validation-summary.json",
    ],
    "docs/workflowprogram-stage-lowlevel-design.md": [
        "runtime_contract",
        "test_contract",
        "workflow-entry.py",
        "runtime_contract.<field>",
        "implemented_now",
        "runner 只负责控制面",
        "workflowprogram-validate",
        "runtime_smoke.py",
        "validation-runtime-report.md",
        "s5-validation-summary.json",
    ],
    "docs/workflowprogram-stage-consistency-check.md": [
        "runtime_contract",
        "test_contract",
        "当前无显式冲突",
    ],
}

ACTIVE_ENTRY_DOCS = {
    ".claude/commands/develop.md": [
        "runtime_contract",
        "test_contract",
        "workflow-entry.py",
        "runtime_contract.<field>",
        "workflowprogram-validate",
        "runtime_smoke.py",
        "s5-validation-summary.json",
    ],
    ".claude/skills/workflowprogram-develop/SKILL.md": [
        "runtime_contract",
        "test_contract",
        "workflow-entry.py",
        "implemented_now",
        "workflowprogram-validate",
        "runtime_smoke.py",
        "s5-validation-summary.json",
        ".workflowprogram/design/",
    ],
}

ACTIVE_TEMPLATE_DOC = {
    ".claude/skills/workflow-spec-support/yaml-spec-template.md": [
        "stage_slot: S5",
        "workflowprogram-validate",
        "validation-runtime-report.md",
        "test_contract",
        ".workflowprogram/design/workflow-lowlevel.md",
    ],
}

ACTIVE_PLAN_DOC = {
    "docs/workflowprogram-test-change-plan.md": [
        "P1",
        "workflowprogram-validate",
        "runtime_smoke.py",
        "workflowprogram-design-status.md",
        "capability matrix",
    ],
}

ACTIVE_STATUS_DOCS = {
    "docs/workflowprogram-design-status.md": [
        "当前生效设计真源",
        "历史追溯文档",
        "已关闭决策",
        "workflow-entry.py",
    ],
}

CAPABILITY_MATRIX_PATH = "docs/workflowprogram-capability-matrix.json"

SOURCE_DIST_FILE_ROOTS = {
    ".claude/agents": "agents",
    ".claude/commands": "commands",
    ".claude/rules": "rules",
    ".claude/scripts": "scripts",
    ".claude/skills": "skills",
    ".claude-plugin": ".claude-plugin",
}


class ValidationResult:
    """收集校验通过项与错误项。"""

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
    """从 Markdown 内容中解析 YAML frontmatter。"""
    match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not match:
        raise ValueError("Missing YAML frontmatter")

    frontmatter = {}
    for line in match.group(1).split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # 这里仅需要最简单的 `key: value` 解析，因此故意保持无依赖，
        # 不再额外引入 YAML 解析器。
        match_kv = re.match(r'^([^:#]+):\s*(.+?)\s*$', line)
        if match_kv:
            key = match_kv.group(1).strip()
            value = match_kv.group(2).strip().strip('"\'')
            frontmatter[key] = value

    return frontmatter


def sha256_file(path: Path) -> str:
    """返回文件的 SHA-256 摘要。"""
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def iter_source_files(root: Path) -> List[Path]:
    """递归枚举源码文件，并跳过 Python 缓存产物。"""
    files: List[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        files.append(path)
    return files


def load_build_plugin_module(root: Path):
    """加载 `build_plugin.py`，让 dist 期望值复用真实构建逻辑。"""
    module_path = root / "tools" / "build_plugin.py"
    spec = importlib.util.spec_from_file_location("workflowprogram_build_plugin", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load build_plugin.py from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_dist_bytes(build_plugin: Any, source_root_rel: str, source_file: Path) -> bytes:
    """计算某个源码文件在 dist/plugin 中应产出的精确字节内容。"""
    if source_root_rel == ".claude-plugin":
        return source_file.read_bytes()

    content = source_file.read_text(encoding="utf-8")
    if source_root_rel == ".claude/commands":
        name = source_file.stem
        desc, hint = build_plugin.COMMAND_DESCRIPTIONS[name]
        frontmatter = f"---\ndescription: {desc}\nargument-hint: {hint}\n---\n\n"
        rendered = build_plugin.MARKDOWN_HEADER + frontmatter + build_plugin.apply_replacements(content)
        return rendered.encode("utf-8")

    if source_root_rel == ".claude/scripts":
        rendered = build_plugin.decorate_generated_text(source_file, build_plugin.apply_replacements(content))
        return rendered.encode("utf-8")

    rendered = build_plugin.decorate_generated_text(source_file, content)
    return rendered.encode("utf-8")


def expected_wrapper_bytes(build_plugin: Any, source_file: Path) -> bytes:
    """计算 `skills/command-*` 下 wrapper 文件应有的生成内容。"""
    name = source_file.stem
    desc, hint = build_plugin.COMMAND_DESCRIPTIONS[name]
    body = build_plugin.apply_replacements(source_file.read_text(encoding="utf-8"))
    meta = (
        f"---\nname: {name}\ndescription: {desc}\nversion: 1.0.0\n"
        f"argument-hint: {hint}\ndisable-model-invocation: true\n---\n\n"
    )
    return (build_plugin.MARKDOWN_HEADER + meta + body).encode("utf-8")


def validate_required_paths(root: Path, result: ValidationResult) -> None:
    """校验必需文件和目录是否存在。"""
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
        ".claude/scripts/route-intent.py",
        ".claude/scripts/runtime_host.py",
        ".claude/scripts/generate-workflow-view.py",
        ".claude/scripts/generate-workflow-lowlevel.py",
        ".claude/scripts/validate-workflow-lowlevel.py",
        ".claude/scripts/validate-lessons-delta.py",
        ".claude/scripts/validate-run-state.py",
        ".claude/scripts/validate-workflow-draft.py",
        ".claude/scripts/validate-workflow-spec.py",
        ".claude/scripts/workflow-entry.py",
        ".claude/scripts/workflow-runner.py",
        ".claude/scripts/workflow-s5-judge.py",
        ".claude/scripts/stage-progress.py",
        ".claude/scripts/validate-workflow.ps1",
        ".claude/scripts/validate-workflow.py",  # Self-check
        ".claude-plugin/plugin.json",
        ".claude-plugin/marketplace.json",
        "tools/build_plugin.py",
        "tools/generate-view.py",
        "tools/mock_runtime_host.py",
        "tools/runtime_smoke.py",
        "tools/runtime_smoke_matrix.py",
        "tests/fixtures",
        "tests/spec-fixtures",
        "tests/expectations",
        "tests/transcripts",
        "docs/workflowprogram-stage-highlevel-design.md",
        "docs/workflowprogram-stage-lowlevel-design.md",
        "docs/workflowprogram-stage-consistency-check.md",
        "docs/workflowprogram-test-change-plan.md",
        "docs/workflowprogram-design-status.md",
        "docs/workflowprogram-capability-matrix.json",
        "docs/phase-07-implementation-plan.md",
        ".claude/skills/workflow-spec-support/yaml-spec-template.md",
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


def validate_document_contracts(root: Path, result: ValidationResult) -> None:
    """校验当前生效的设计文档和入口文档是否反映了最新契约模型。"""
    for relative_path, markers in ACTIVE_PLAN_DOC.items():
        full_path = root / relative_path
        if not full_path.exists():
            result.add_error(f"Missing active plan doc: {relative_path}")
            continue
        try:
            content = full_path.read_text(encoding='utf-8')
        except Exception as e:
            result.add_error(f"Cannot read active plan doc '{relative_path}': {e}")
            continue

        result.add_pass(f"Active plan doc present: {relative_path}")
        for marker in markers:
            if marker in content:
                result.add_pass(f"Active plan doc '{relative_path}' includes '{marker}'")
            else:
                result.add_error(f"Active plan doc '{relative_path}' is missing '{marker}'")

    for relative_path, markers in ACTIVE_STATUS_DOCS.items():
        full_path = root / relative_path
        if not full_path.exists():
            result.add_error(f"Missing active status doc: {relative_path}")
            continue
        try:
            content = full_path.read_text(encoding='utf-8')
        except Exception as e:
            result.add_error(f"Cannot read active status doc '{relative_path}': {e}")
            continue

        result.add_pass(f"Active status doc present: {relative_path}")
        for marker in markers:
            if marker in content:
                result.add_pass(f"Active status doc '{relative_path}' includes '{marker}'")
            else:
                result.add_error(f"Active status doc '{relative_path}' is missing '{marker}'")

    for relative_path, markers in ACTIVE_DESIGN_DOCS.items():
        full_path = root / relative_path
        if not full_path.exists():
            result.add_error(f"Missing active design doc: {relative_path}")
            continue
        try:
            content = full_path.read_text(encoding='utf-8')
        except Exception as e:
            result.add_error(f"Cannot read active design doc '{relative_path}': {e}")
            continue

        result.add_pass(f"Active design doc present: {relative_path}")
        for marker in markers:
            if marker in content:
                result.add_pass(f"Active design doc '{relative_path}' includes '{marker}'")
            else:
                result.add_error(f"Active design doc '{relative_path}' is missing '{marker}'")

    for relative_path, markers in ACTIVE_ENTRY_DOCS.items():
        full_path = root / relative_path
        if not full_path.exists():
            result.add_error(f"Missing active entry doc: {relative_path}")
            continue
        try:
            content = full_path.read_text(encoding='utf-8')
        except Exception as e:
            result.add_error(f"Cannot read active entry doc '{relative_path}': {e}")
            continue

        result.add_pass(f"Active entry doc present: {relative_path}")
        for marker in markers:
            if marker in content:
                result.add_pass(f"Active entry doc '{relative_path}' includes '{marker}'")
            else:
                result.add_error(f"Active entry doc '{relative_path}' is missing '{marker}'")

    for relative_path, markers in ACTIVE_TEMPLATE_DOC.items():
        full_path = root / relative_path
        if not full_path.exists():
            result.add_error(f"Missing active template doc: {relative_path}")
            continue
        try:
            content = full_path.read_text(encoding='utf-8')
        except Exception as e:
            result.add_error(f"Cannot read active template doc '{relative_path}': {e}")
            continue

        result.add_pass(f"Active template doc present: {relative_path}")
        for marker in markers:
            if marker in content:
                result.add_pass(f"Active template doc '{relative_path}' includes '{marker}'")
            else:
                result.add_error(f"Active template doc '{relative_path}' is missing '{marker}'")


def validate_settings_json(root: Path, result: ValidationResult) -> Optional[Dict]:
    """校验 settings.json 格式，并在成功时返回解析结果。"""
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
    """校验命令文档是否结构正确且已注册。"""
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

    # 每个命令不仅要存在于磁盘上，还要保持产品入口 wrapper 所依赖的 staged prompt 结构。
    for cmd_file in sorted(commands_dir.glob("*.md")):
        relative = f".claude/commands/{cmd_file.name}"

        try:
            with open(cmd_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            result.add_error(f"Cannot read command '{cmd_file.name}': {e}")
            continue

        # Usage / Stage / Goal / Verify 共同保证命令文档结构稳定，
        # 这样人工阅读和构建工具都能依赖同一套形态。
        if re.search(r'^## Usage\s*$', content, re.MULTILINE):
            result.add_pass(f"Command '{cmd_file.name}' has a Usage section")
        else:
            result.add_error(f"Command '{cmd_file.name}' is missing a Usage section")

        # 检查 staged 结构
        if re.search(r'^## Stage \d+:', content, re.MULTILINE):
            result.add_pass(f"Command '{cmd_file.name}' uses staged structure")
        else:
            result.add_error(f"Command '{cmd_file.name}' is missing numbered stages")

        # 检查 Goal 和 Verify
        if '**Goal**:' in content and '**Verify**:' in content:
            result.add_pass(f"Command '{cmd_file.name}' defines Goal and Verify")
        else:
            result.add_error(f"Command '{cmd_file.name}' is missing Goal or Verify")

        # 检查注册情况
        if relative in registered_commands.values():
            result.add_pass(f"Command '{cmd_file.name}' is registered in settings.json")
        else:
            result.add_error(f"Command '{cmd_file.name}' exists on disk but is not registered in settings.json")


def validate_skills(root: Path, settings: Dict, result: ValidationResult) -> None:
    """校验 skill 是否结构正确且已注册。"""
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

    # 检查每个 skill 目录
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

            # frontmatter 被视为契约元数据，因为构建层和 UI 层都依赖它向用户暴露 skill。
            for field in ["name", "description", "version"]:
                if field in frontmatter and frontmatter[field]:
                    result.add_pass(f"Skill '{skill_dir.name}' includes frontmatter field '{field}'")
                else:
                    result.add_error(f"Skill '{skill_dir.name}' is missing frontmatter field '{field}'")

            # 检查注册情况（internal skill 可豁免）
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
    """校验 skills-first 的主入口是否已经注册。"""
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
    """校验 constraints.md 是否同时包含 ALWAYS 与 NEVER 规则。"""
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
    """校验插件元数据文件，并返回解析后的 plugin.json 内容。"""
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


def validate_capability_matrix(root: Path, result: ValidationResult) -> None:
    """校验用于跟踪实现覆盖度的 capability matrix。"""
    matrix_path = root / CAPABILITY_MATRIX_PATH
    if not matrix_path.exists():
        result.add_error(f"Missing capability matrix: {CAPABILITY_MATRIX_PATH}")
        return

    try:
        payload = json.loads(matrix_path.read_text(encoding="utf-8"))
    except Exception as e:
        result.add_error(f"Cannot parse capability matrix '{CAPABILITY_MATRIX_PATH}': {e}")
        return

    if payload.get("version") == 1:
        result.add_pass("Capability matrix version is 1")
    else:
        result.add_error("Capability matrix must declare version=1")

    capabilities = payload.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        result.add_error("Capability matrix must define a non-empty capabilities list")
        return

    for capability in capabilities:
        if not isinstance(capability, dict):
            result.add_error("Capability matrix entries must be mapping objects")
            continue
        capability_id = str(capability.get("id", "")).strip()
        checks = capability.get("checks")
        if not capability_id:
            result.add_error("Capability matrix entry is missing id")
            continue
        if not isinstance(checks, list) or not checks:
            result.add_error(f"Capability '{capability_id}' must define non-empty checks")
            continue
        result.add_pass(f"Capability matrix defines checks for '{capability_id}'")
        for check in checks:
            if not isinstance(check, dict):
                result.add_error(f"Capability '{capability_id}' contains a non-mapping check")
                continue
            relative_path = str(check.get("file", "")).strip()
            markers = check.get("markers")
            if not relative_path:
                result.add_error(f"Capability '{capability_id}' contains a check without file")
                continue
            full_path = root / relative_path
            if not full_path.exists():
                result.add_error(f"Capability '{capability_id}' references a missing file: {relative_path}")
                continue
            result.add_pass(f"Capability '{capability_id}' references existing file: {relative_path}")
            if not isinstance(markers, list) or not markers:
                result.add_error(f"Capability '{capability_id}' check for '{relative_path}' must include non-empty markers")
                continue
            try:
                content = full_path.read_text(encoding="utf-8")
            except Exception as e:
                result.add_error(f"Cannot read capability matrix file '{relative_path}': {e}")
                continue
            for marker in markers:
                marker_text = str(marker)
                if marker_text in content:
                    result.add_pass(f"Capability '{capability_id}' file '{relative_path}' includes '{marker_text}'")
                else:
                    result.add_error(f"Capability '{capability_id}' file '{relative_path}' is missing '{marker_text}'")


def validate_dist_plugin(root: Path, plugin_meta: Optional[Dict[str, Any]], result: ValidationResult) -> None:
    """根据源码树和 build trace manifest 校验 dist/plugin。"""
    dist_root = root / "dist" / "plugin"
    if not dist_root.exists():
        result.add_pass("dist/plugin not present; build output validation skipped")
        return
    build_plugin = load_build_plugin_module(root)

    required_paths = [
        dist_root / ".claude-plugin" / "plugin.json",
        dist_root / ".claude-plugin" / "marketplace.json",
        dist_root / "build-manifest.json",
        dist_root / "scripts" / "managed-assets.py",
        dist_root / "scripts" / "route-intent.py",
        dist_root / "scripts" / "runtime_host.py",
        dist_root / "scripts" / "generate-workflow-view.py",
        dist_root / "scripts" / "generate-workflow-lowlevel.py",
        dist_root / "scripts" / "stage-progress.py",
        dist_root / "scripts" / "validate-lessons-delta.py",
        dist_root / "scripts" / "validate-workflow-lowlevel.py",
        dist_root / "scripts" / "validate-run-state.py",
        dist_root / "scripts" / "validate-workflow-draft.py",
        dist_root / "scripts" / "validate-workflow-spec.py",
        dist_root / "scripts" / "workflow-entry.py",
        dist_root / "scripts" / "workflow-runner.py",
        dist_root / "scripts" / "workflow-s5-judge.py",
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

    manifest_paths = set()
    for item in files:
        path = item.get("path")
        sha256 = item.get("sha256")
        if not path:
            result.add_error("build-manifest contains an entry without path")
            continue
        manifest_paths.add(str(path))
        if not sha256 or len(sha256) != 64:
            result.add_error(f"build-manifest entry '{path}' is missing a valid sha256")
            continue
        built_file = dist_root / path
        if built_file.exists():
            result.add_pass(f"build-manifest file exists: {path}")
            actual_sha = sha256_file(built_file)
            if actual_sha == sha256:
                result.add_pass(f"build-manifest sha256 matches built file: {path}")
            else:
                result.add_error(f"build-manifest sha256 mismatch for {path}")
        else:
            result.add_error(f"build-manifest references a missing file: {path}")
    for source_root_rel, dist_root_rel in SOURCE_DIST_FILE_ROOTS.items():
        # 基于真源文件重新计算期望输出，这样一旦有人手改 dist/plugin，就会立刻被发现。
        source_root = root / source_root_rel
        destination_root = dist_root / dist_root_rel
        for source_file in iter_source_files(source_root):
            relative = source_file.relative_to(source_root)
            built_file = destination_root / relative
            dist_relative = str(built_file.relative_to(dist_root)).replace("\\", "/")
            if built_file.exists():
                result.add_pass(f"Build output contains mapped source file: {dist_relative}")
                if built_file.read_bytes() == expected_dist_bytes(build_plugin, source_root_rel, source_file):
                    result.add_pass(f"Build output matches source content: {dist_relative}")
                else:
                    result.add_error(f"Build output content drift for {dist_relative}")
            else:
                result.add_error(f"Build output is missing mapped source file: {dist_relative}")
                continue
            if dist_relative in manifest_paths:
                result.add_pass(f"build-manifest tracks mapped source file: {dist_relative}")
            else:
                result.add_error(f"build-manifest is missing mapped source file: {dist_relative}")

    command_source_root = root / ".claude" / "commands"
    for source_file in iter_source_files(command_source_root):
        name = source_file.stem
        wrapper_relative = f"skills/command-{name}/SKILL.md"
        wrapper_file = dist_root / wrapper_relative
        if wrapper_file.exists():
            result.add_pass(f"Build output contains command wrapper: {wrapper_relative}")
            if wrapper_file.read_bytes() == expected_wrapper_bytes(build_plugin, source_file):
                result.add_pass(f"Build output matches command wrapper source: {wrapper_relative}")
            else:
                result.add_error(f"Build output content drift for {wrapper_relative}")
        else:
            result.add_error(f"Build output is missing command wrapper: {wrapper_relative}")
            continue
        if wrapper_relative in manifest_paths:
            result.add_pass(f"build-manifest tracks command wrapper: {wrapper_relative}")
        else:
            result.add_error(f"build-manifest is missing command wrapper: {wrapper_relative}")


def print_report(result: ValidationResult) -> None:
    """以结构化格式打印校验报告。"""
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
    """针对指定根目录运行整套仓库校验。"""
    # 若未显式传入路径，则默认使用仓库根目录。
    if len(sys.argv) > 1:
        root = Path(sys.argv[1]).resolve()
    else:
        # `.claude/scripts/validate-workflow.py` 位于仓库根目录下两级位置。
        root = Path(__file__).resolve().parents[2]

    print(f"Validating WorkflowProgram at: {root}")

    result = ValidationResult()

    # 这里的顺序是刻意安排的：先确保文件存在并解析 settings，
    # 后续检查才能安全假定核心仓库结构已经成立。
    validate_required_paths(root, result)
    settings = validate_settings_json(root, result)

    if settings:
        validate_commands(root, settings, result)
        validate_skills(root, settings, result)
        validate_primary_skill_set(settings, result)

    validate_document_contracts(root, result)
    validate_capability_matrix(root, result)
    validate_constraints(root, result)
    plugin_meta = validate_plugin_metadata(root, result)
    validate_dist_plugin(root, plugin_meta, result)

    # 输出完整的通过/失败报告，而不是首错即停，便于一次性完成仓库清理。
    print_report(result)

    sys.exit(0 if result.is_valid else 1)


if __name__ == '__main__':
    main()
