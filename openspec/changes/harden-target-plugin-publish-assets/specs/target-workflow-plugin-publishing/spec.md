## MODIFIED Requirements

### Requirement: Publish SHALL package a Claude Code marketplace plugin

The publish lifecycle SHALL stage a Claude Code marketplace-compatible plugin package for the target workflow before writing to a GitHub publishing checkout. The staged package SHALL use the installed plugin layout as the source of truth, include support assets referenced by the workflow, and exclude transient cache files.

#### Scenario: Package is staged as run evidence

- **WHEN** publish package creation runs
- **THEN** the package is first written under `RUN_ROOT/outputs/stages/publish/package-root/`
- **AND** `plugin-package-plan.json` records included commands, skills, agents, runtime assets, metadata, support assets, and install docs

#### Scenario: Support assets are included

- **GIVEN** the target workflow references `.workflowprogram/loops/report-render.md`
- **OR** it references files under `config/` or `templates/`
- **WHEN** publish package creation runs
- **THEN** those referenced support assets are copied into package-root
- **AND** cache artifacts such as `__pycache__/` and `*.pyc` are not copied

#### Scenario: Package settings use installed layout

- **GIVEN** the source target workflow settings reference `.claude/commands/demo.md`
- **WHEN** publish package creation runs
- **THEN** the package settings reference `commands/demo.md`
- **AND** all package settings paths resolve inside package-root

#### Scenario: Runtime packaging mode is explicit

- **WHEN** a target workflow plugin package is created
- **THEN** it declares either `workflowprogram_dependency` or `vendored_runtime`
- **AND** the selected mode is validated before GitHub publishing

#### Scenario: Dependency mode includes dependency instructions

- **GIVEN** the selected runtime packaging mode is `workflowprogram_dependency`
- **WHEN** install instructions are generated
- **THEN** they include the WorkflowProgram marketplace install command before the target workflow plugin install command

#### Scenario: Target Python dependencies are documented

- **GIVEN** the target runtime manifest declares Python packages
- **WHEN** publish package creation runs
- **THEN** package-root contains `requirements.txt`
- **AND** the package README describes installing those dependencies

#### Scenario: Vendored runtime mode requires validation

- **GIVEN** the selected runtime packaging mode is `vendored_runtime`
- **WHEN** package validation runs
- **THEN** the package must contain the validated runtime launcher and required runtime scripts
- **AND** validation fails if the target workflow still references an unavailable external WorkflowProgram runtime path

### Requirement: Publish SHALL validate the package before pushing

WorkflowProgram SHALL validate the staged target workflow plugin package before committing or pushing it to GitHub. Validation SHALL use the installed package layout, not the source target workflow layout.

#### Scenario: Plugin validation passes

- **WHEN** package validation runs
- **THEN** `plugin-validation-report.json` records metadata checks, command/skill exposure checks, runtime packaging checks, local reference checks, target runtime compatibility checks, dependency checks, and Claude Code plugin validation results
- **AND** GitHub publishing may proceed only after validation passes

#### Scenario: Plugin validation fails

- **WHEN** package validation finds invalid metadata, ambiguous command exposure, missing runtime files, missing support asset references, unresolved package settings paths, cache artifacts, placeholder metadata, or marketplace incompatibility
- **THEN** publish stops before GitHub writes
- **AND** `publish-summary.json` records `status=FAIL`
- **AND** `failure_kind=implementation`

#### Scenario: Missing prompt package blocks publish

- **GIVEN** `workflow-spec.yaml` references `.workflowprogram/loops/report-render.md`
- **AND** the staged package does not contain that file
- **WHEN** package validation runs
- **THEN** validation fails with a missing local reference

#### Scenario: Source-layout runtime validator blocks publish

- **GIVEN** the staged package has root `commands/`, `skills/`, and `agents/`
- **AND** target runtime validation still requires `.claude/commands`, `.claude/skills`, or `.claude/agents`
- **WHEN** package validation runs
- **THEN** validation fails before GitHub publishing
