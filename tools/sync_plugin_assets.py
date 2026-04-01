#!/usr/bin/env python3
"""
WorkflowProgram Plugin Asset Builder

FIXME: Technical Debt - .claude/ directory is temporary
To be retired in favor of native root-level plugin structure in Phase X.

ONE-WAY BUILD: .claude/ → root/ ONLY
"""

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
CLAUDE = ROOT / '.claude'

COMMAND_DESCRIPTIONS = {
    'develop': ('Design a new workflow from requirements', '<requirement> [--auto-approve]'),
    'ship': ('Ship current workflow changes', '[scope] [--auto-approve]'),
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

HEADER = '<!-- AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY -->\n\n'

def copy_with_header(src: Path, dst: Path):
    """Copy file with auto-generated header."""
    content = HEADER + src.read_text(encoding='utf-8')
    dst.write_text(content, encoding='utf-8', newline='\n')

# Clean and recreate output directories
for dirname in ['commands', 'skills', 'agents', 'rules', 'scripts']:
    target = ROOT / dirname
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

# Copy agents, rules, scripts with header
for src in (CLAUDE / 'agents').glob('*.md'):
    copy_with_header(src, ROOT / 'agents' / src.name)

copy_with_header(CLAUDE / 'rules' / 'constraints.md', ROOT / 'rules' / 'constraints.md')
copy_with_header(CLAUDE / 'scripts' / 'validate-workflow.ps1', ROOT / 'scripts' / 'validate-workflow.ps1')

# Copy skills with header
for skill_dir in (CLAUDE / 'skills').iterdir():
    if not skill_dir.is_dir():
        continue
    dest = ROOT / 'skills' / skill_dir.name
    dest.mkdir(parents=True, exist_ok=True)
    for src in skill_dir.glob('*'):
        if src.is_file():
            copy_with_header(src, dest / src.name)

# Generate commands with frontmatter and header
for src in (CLAUDE / 'commands').glob('*.md'):
    name = src.stem
    body = src.read_text(encoding='utf-8')
    for old, new in REPLACEMENTS.items():
        body = body.replace(old, new)
    desc, hint = COMMAND_DESCRIPTIONS[name]
    frontmatter = f'---\ndescription: {desc}\nargument-hint: {hint}\n---\n\n'
    (ROOT / 'commands' / src.name).write_text(HEADER + frontmatter + body, encoding='utf-8', newline='\n')

    # Generate skill wrapper
    skill_dir = ROOT / 'skills' / f'command-{name}'
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_meta = f'---\nname: {name}\ndescription: {desc}\nversion: 1.0.0\nargument-hint: {hint}\ndisable-model-invocation: true\n---\n\n'
    (skill_dir / 'SKILL.md').write_text(HEADER + skill_meta + body, encoding='utf-8', newline='\n')

print('✓ Build complete')
print('  Source: .claude/')
print('  Output: commands/, skills/, agents/, rules/, scripts/')
