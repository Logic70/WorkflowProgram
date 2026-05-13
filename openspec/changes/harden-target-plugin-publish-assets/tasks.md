## 1. OpenSpec

- [x] 1.1 Define package-layout validation, support asset discovery, dependency documentation, and clean republish verification.
- [x] 1.2 Iterate design audit until no new path/asset/dependency/repository false-positive issues remain.

## 2. Package Builder

- [x] 2.1 Copy `.workflowprogram/loops`, `config`, `templates`, and discovered support assets into package-root.
- [x] 2.2 Exclude cache/transient files such as `__pycache__`, `*.pyc`, `.pytest_cache`, `.git`, and editor backups.
- [x] 2.3 Rewrite package `.claude/settings.json` to plugin-root layout paths.
- [x] 2.4 Emit package `requirements.txt` and README dependency guidance from target runtime manifest.
- [x] 2.5 Replace placeholder author/owner metadata with repository owner when inferable.

## 3. Package Validator

- [x] 3.1 Validate rewritten settings paths resolve inside package-root.
- [x] 3.2 Extract local references from spec, commands, skills, agents, CLAUDE.md, and design docs.
- [x] 3.3 Fail when declared prompt packages or support file references are missing.
- [x] 3.4 Fail on cache/transient files in package-root.
- [x] 3.5 Run target runtime `--spec` compatibility validation when available.
- [x] 3.6 Validate dependency requirements/README coverage and placeholder metadata.

## 4. FreeSTRIDE Source Alignment

- [x] 4.1 Align report assembler prompt with inline SVG report rendering.
- [x] 4.2 Remove or fix references to missing `config/scripts/generate-dfd-svg.py`.
- [x] 4.3 Ensure `.workflowprogram/loops/*.md`, templates, and config scripts are included by fresh publish.

## 5. Verification

- [x] 5.1 Add targeted unit/regression coverage for package support assets and missing reference failure.
- [x] 5.2 Run `python3 .claude/scripts/validate-workflow.py`.
- [x] 5.3 Run targeted publish smoke fixtures.
- [x] 5.4 Run `openspec validate harden-target-plugin-publish-assets --strict`.
- [x] 5.5 Clear FreeSTRIDE publish repository checkout and republish through `workflowprogram-publish`.
- [x] 5.6 Clone/fetch the freshly published GitHub package and validate it contains required assets and can execute package-level checks.
