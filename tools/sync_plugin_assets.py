#!/usr/bin/env python3
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

ROOT_DIRS = ['commands', 'skills', 'agents', 'rules', 'scripts']
for dirname in ROOT_DIRS:
    target = ROOT / dirname
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

for source in (CLAUDE / 'agents').glob('*.md'):
    shutil.copy2(source, ROOT / 'agents' / source.name)

for skill_dir in (CLAUDE / 'skills').iterdir():
    if not skill_dir.is_dir():
        continue
    dest = ROOT / 'skills' / skill_dir.name
    shutil.copytree(skill_dir, dest)

shutil.copy2(CLAUDE / 'rules' / 'constraints.md', ROOT / 'rules' / 'constraints.md')
shutil.copy2(CLAUDE / 'scripts' / 'validate-workflow.ps1', ROOT / 'scripts' / 'validate-workflow.ps1')

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
    (ROOT / 'commands' / source.name).write_text(frontmatter + body, encoding='utf-8', newline='\n')

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
    (skill_dir / 'SKILL.md').write_text(skill_frontmatter + body, encoding='utf-8', newline='\n')
