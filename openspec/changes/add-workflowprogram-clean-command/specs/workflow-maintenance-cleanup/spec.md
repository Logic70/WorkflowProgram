## ADDED Requirements

### Requirement: Safe Cleanup Command

WorkflowProgram SHALL provide a `workflowprogram-clean` command that reports cleanup candidates without deleting files unless `--apply` is supplied.

#### Scenario: Dry-run reports candidates without deleting

- **GIVEN** plugin-local Python cache, test artifacts, or target run history exist
- **WHEN** the user runs `workflowprogram-clean` without `--apply`
- **THEN** the command reports planned cleanup items
- **AND** no reported file or directory is deleted

#### Scenario: Apply deletes only allowed candidates

- **GIVEN** cleanup candidates are inside WorkflowProgram-owned cleanup roots
- **WHEN** the user runs `workflowprogram-clean --apply` with an explicit cleanup scope
- **THEN** the command deletes only allowed candidates for that scope
- **AND** the report records each deleted, skipped, or failed item

### Requirement: Python Runtime Cache Cleanup

WorkflowProgram SHALL support explicit cleanup of plugin-local Python dependency state under `${CLAUDE_PLUGIN_DATA}/python`.

#### Scenario: Python runtime cache is reset

- **GIVEN** `${CLAUDE_PLUGIN_DATA}/python/site-packages`, `site-packages.tmp`, `bootstrap-state.json`, or `requirements.lock.txt` exist
- **WHEN** the user runs `workflowprogram-clean --python-runtime --apply`
- **THEN** those plugin-local Python runtime paths are removed
- **AND** the next `workflowprogram-python` or SessionStart bootstrap can recreate the dependency layer

### Requirement: Test Artifact Cleanup

WorkflowProgram SHALL support explicit cleanup of repository-local test transcripts and Python bytecode caches without deleting fixture truth.

#### Scenario: Test artifacts are cleaned

- **GIVEN** timestamped `tests/transcripts/20*/` directories or Python bytecode caches exist
- **WHEN** the user runs `workflowprogram-clean --test-artifacts --apply`
- **THEN** those artifacts are deleted
- **AND** `tests/fixtures/**`, `tests/spec-fixtures/**`, and `tests/expectations/**` are not deleted

### Requirement: Run History Retention

WorkflowProgram SHALL support explicit pruning of `TARGET_ROOT/.workflowprogram/runs/*` using retention guards.

#### Scenario: Keep-last retains newest runs

- **GIVEN** a target workflow has multiple run directories
- **WHEN** the user runs `workflowprogram-clean --target-root <path> --run-history --keep-last 1 --apply`
- **THEN** old run directories outside the retention set are deleted
- **AND** the newest run directory is retained

#### Scenario: Missing retention policy skips run history

- **GIVEN** a target workflow has run history
- **WHEN** the user runs `workflowprogram-clean --target-root <path> --run-history --apply` without `--keep-last` or `--older-than-days`
- **THEN** no run directory is deleted
- **AND** the report marks run-history cleanup as skipped

### Requirement: Cleanup Safety Boundary

WorkflowProgram SHALL refuse cleanup of paths outside the defined ownership boundary.

#### Scenario: User and host state is not cleaned

- **GIVEN** Claude Code marketplace cache, `.claude/history/`, `.claude/memory/`, `.codex/`, `.env*`, `.mcp.json`, or `TARGET_ROOT/.workflowprogram/bootstrap/**` exist
- **WHEN** the user runs `workflowprogram-clean`
- **THEN** those paths are not selected as cleanup candidates
- **AND** they are not deleted by default cleanup behavior
