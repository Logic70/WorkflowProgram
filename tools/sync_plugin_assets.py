#!/usr/bin/env python3
"""
WorkflowProgram Plugin Asset Builder

FIXME: Technical Debt - .claude/ directory is temporary
To be retired in favor of native root-level plugin structure in Phase X.
View architecture evolution map for details.

This script is a ONE-WAY BUILD tool (like `npm run build`):
- Source of Truth: .claude/ directory
- Build Output: root-level commands/, skills/, etc.
- Direction: .claude/ → root/ ONLY (never reverse)

DO NOT EDIT files in root-level directories directly.
All changes should be made in .claude/ and then rebuilt.
"""

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / '.claude'

COMMAND_DESCRIPTIONS = {
    'develop': ('Design a new workflow from requirements', '<requirement>'),
    'ship': ('Ship current workflow changes', '[scope]'),
    'preflight': ('Run parallel readiness checks before shipping', '[scope]'),
    'hotfix': ('Fast-track a hotfix with reduced scope', '[description]'),
    'evolve-workflow': ('Audit and evolve a workflow repository', '[options] <workflow-path>'),
    'iterate-workflow': ('Iterate a workflow from lessons with approval', '[--dry-run] [--apply] [workflow-path]'),
}

REPLACEMENTS = {
    '.claude/skills/develop/spec-template.md': '${CLAUDE_PLUGIN_ROOT}/skills/develop/spec-template.md',
    '.claude/rules/constraints.md': '${CLAUDE_PLUGIN_ROOT}/rules/constraints.md',
    '.claude/scripts/validate-workflow.ps1': '${CLAUDE_PLUGIN_ROOT}/scripts/validate-workflow.ps1',
}

AUTO_GENERATED_HEADER = (
    '<!-- AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY -->\n'
    '<!-- Run: python tools/sync_plugin_assets.py -->\n\n'
)

ROOT_DIRS = ['commands', 'skills', 'agents', 'rules', 'scripts']
for dirname in ROOT_DIRS:
    target = ROOT / dirname
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

# Copy agents with auto-generated header
for source in (CLAUDE / 'agents').glob('*.md'):
    content = AUTO_GENERATED_HEADER + source.read_text(encoding='utf-8')
    (ROOT / 'agents' / source.name).write_text(content, encoding='utf-8', newline='\n')

# Copy skills with auto-generated header
for skill_dir in (CLAUDE / 'skills').iterdir():
    if not skill_dir.is_dir():
        continue
    dest = ROOT / 'skills' / skill_dir.name
    dest.mkdir(parents=True, exist_ok=True)
    for source in skill_dir.glob('*'):
        if source.is_file():
            content = AUTO_GENERATED_HEADER + source.read_text(encoding='utf-8')
            (dest / source.name).write_text(content, encoding='utf-8', newline='\n')

# Copy rules with auto-generated header
constraints_source = CLAUDE / 'rules' / 'constraints.md'
content = AUTO_GENERATED_HEADER + constraints_source.read_text(encoding='utf-8')
(ROOT / 'rules' / 'constraints.md').write_text(content, encoding='utf-8', newline='\n')

# Copy scripts with auto-generated header
script_source = CLAUDE / 'scripts' / 'validate-workflow.ps1'
content = AUTO_GENERATED_HEADER + script_source.read_text(encoding='utf-8')
(ROOT / 'scripts' / 'validate-workflow.ps1').write_text(content, encoding='utf-8', newline='\n')

# Generate commands with frontmatter and auto-generated header
for source in (CLAUDE / 'commands').glob('*.md'):
    name = source.stem
    body = source.read_text(encoding='utf-8')
    for old, new in REPLACEMENTS.items():
        body = body.replace(old, new)
    description, arg_hint = COMMAND_DESCRIPTIONS[name]
    frontmatter = (
        '---\n'
        f'description: {description}\n'
        f'argument-hint: {arg_hint}\n'
        '---\n\n'
    )
    full_content = AUTO_GENERATED_HEADER + frontmatter + body
    (ROOT / 'commands' / source.name).write_text(full_content, encoding='utf-8', newline='\n')

    # Also generate skill wrappers
    skill_dir = ROOT / 'skills' / f'command-{name}'
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_frontmatter = (
        '---\n'
        f'name: {name}\n'
        f'description: {description}\n'
        'version: 1.0.0\n'
        f'argument-hint: {arg_hint}\n'
        'disable-model-invocation: true\n'
        '---\n\n'
    )
    skill_content = AUTO_GENERATED_HEADER + skill_frontmatter + body
    (skill_dir / 'SKILL.md').write_text(skill_content, encoding='utf-8', newline='\n')

print("✓ Build complete: .claude/ → root-level directories")
print("  Source of truth: .claude/")
print("  Generated: commands/, skills/, agents/, rules/, scripts/")
print("\nNOTE: Edit files in .claude/ only, then re-run this script.")
