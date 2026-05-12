## ADDED Requirements

### Requirement: Target workflow publishing SHALL be an independent lifecycle

WorkflowProgram SHALL provide a publish lifecycle that packages and publishes a completed target workflow after `workflowprogram-develop`, without treating publish as another develop stage.

#### Scenario: Completed workflow enters publish

- **GIVEN** a target workflow has completed `workflowprogram-develop`
- **AND** the latest required develop evidence is current and passing
- **WHEN** the user asks to publish the workflow as a Claude Code plugin
- **THEN** WorkflowProgram runs the target workflow publish lifecycle
- **AND** it does not re-enter S1-S6 design/develop unless publish eligibility reports a required design change

#### Scenario: Incomplete workflow is not published

- **GIVEN** a target workflow is missing required develop evidence
- **WHEN** the user asks to publish it
- **THEN** publish stops before package creation
- **AND** `publish-summary.json` records `status=FAIL`
- **AND** `failure_kind=design`

### Requirement: WorkflowProgram SHALL expose a publish skill and command

WorkflowProgram SHALL provide a public `workflowprogram-publish` skill and a public `/workflowprogram-cn:workflowprogram-publish` command for Claude Code users.

#### Scenario: User explicitly runs publish command

- **WHEN** the user invokes `/workflowprogram-cn:workflowprogram-publish`
- **THEN** the command invokes the publish lifecycle
- **AND** it writes publish evidence under `RUN_ROOT/outputs/stages/publish/`

#### Scenario: User asks naturally to publish

- **WHEN** a user asks Claude Code to publish a WorkflowProgram-created workflow as a plugin
- **THEN** the public `workflowprogram-publish` skill provides the routing and procedure
- **AND** `workflowprogram-orchestrate` may route the request to the publish lifecycle without adding a second publish alias

### Requirement: Publish eligibility SHALL require completed develop evidence

Publish eligibility SHALL validate that the target workflow has completed develop, passed final conformance, and has no stale or conflicting managed state.

#### Scenario: Passing develop evidence is accepted

- **GIVEN** the target contains `TARGET_ROOT/.workflowprogram/design/workflow-spec.yaml`
- **AND** the target contains `TARGET_ROOT/.workflowprogram/runtime/runtime-manifest.json`
- **AND** the target contains `TARGET_ROOT/.workflowprogram/managed-files.json`
- **AND** the latest develop run has design-review closure, managed apply evidence, state/events evidence, and S5 `PASS`
- **WHEN** publish eligibility is checked
- **THEN** `publish-eligibility.json` records `eligible=true`

#### Scenario: Stale or drifting target state is blocked

- **GIVEN** latest develop evidence fingerprints do not match current target workflow files
- **WHEN** publish eligibility is checked
- **THEN** `publish-eligibility.json` records `eligible=false`
- **AND** `publish-summary.json` records `status=FAIL`
- **AND** `failure_kind=design`

#### Scenario: Warning evidence requires explicit approval

- **GIVEN** the latest develop evidence contains S5 `WARN`
- **WHEN** the user has not explicitly approved publishing with warnings
- **THEN** publish stops before package creation
- **AND** the summary records that warning acceptance is required

### Requirement: Publish SHALL package a Claude Code marketplace plugin

The publish lifecycle SHALL stage a Claude Code marketplace-compatible plugin package for the target workflow before writing to a GitHub publishing checkout.

#### Scenario: Package is staged as run evidence

- **WHEN** publish package creation runs
- **THEN** the package is first written under `RUN_ROOT/outputs/stages/publish/package-root/`
- **AND** `plugin-package-plan.json` records included commands, skills, agents, runtime assets, metadata, and install docs

#### Scenario: Runtime packaging mode is explicit

- **WHEN** a target workflow plugin package is created
- **THEN** it declares either `workflowprogram_dependency` or `vendored_runtime`
- **AND** the selected mode is validated before GitHub publishing

#### Scenario: Dependency mode includes dependency instructions

- **GIVEN** the selected runtime packaging mode is `workflowprogram_dependency`
- **WHEN** install instructions are generated
- **THEN** they include the WorkflowProgram marketplace install command before the target workflow plugin install command

#### Scenario: Vendored runtime mode requires validation

- **GIVEN** the selected runtime packaging mode is `vendored_runtime`
- **WHEN** package validation runs
- **THEN** the package must contain the validated runtime launcher and required runtime scripts
- **AND** validation fails if the target workflow still references an unavailable external WorkflowProgram runtime path

### Requirement: Publish SHALL use the user's GitHub account without storing credentials

WorkflowProgram SHALL publish through the user's local GitHub and git authentication, and SHALL NOT persist GitHub tokens in WorkflowProgram files or evidence.

#### Scenario: GitHub auth is available

- **GIVEN** `gh auth status` succeeds for the intended GitHub host
- **AND** the user has permission to create or update the target repository
- **WHEN** GitHub publish execution is approved
- **THEN** WorkflowProgram may commit, tag, and push the staged plugin package
- **AND** `github-publish-result.json` records repository, ref, commit, tag, and marketplace metadata paths

#### Scenario: GitHub auth is missing

- **GIVEN** local GitHub authentication is missing or insufficient
- **WHEN** publish checks repository readiness
- **THEN** publish stops with `status=BLOCKED`
- **AND** `failure_kind=environment`
- **AND** the summary provides remediation steps without storing credentials

### Requirement: Publish SHALL validate the package before pushing

WorkflowProgram SHALL validate the staged target workflow plugin package before committing or pushing it to GitHub.

#### Scenario: Plugin validation passes

- **WHEN** package validation runs
- **THEN** `plugin-validation-report.json` records metadata checks, command/skill exposure checks, runtime packaging checks, and Claude Code plugin validation results
- **AND** GitHub publishing may proceed only after validation passes

#### Scenario: Plugin validation fails

- **WHEN** package validation finds invalid metadata, ambiguous command exposure, missing runtime files, or marketplace incompatibility
- **THEN** publish stops before GitHub writes
- **AND** `publish-summary.json` records `status=FAIL`
- **AND** `failure_kind=implementation`

### Requirement: Publish SHALL generate install and update instructions

WorkflowProgram SHALL generate human-readable install instructions for the published target workflow plugin.

#### Scenario: GitHub publish succeeds

- **WHEN** GitHub publish succeeds
- **THEN** `install-instructions.md` includes the marketplace add command, plugin install command, plugin id, version, repository URL, and update guidance

#### Scenario: Publish plan only

- **WHEN** package validation passes but GitHub publishing is not approved
- **THEN** `install-instructions.md` explains the pending GitHub steps
- **AND** `publish-summary.json` records `status=BLOCKED`
- **AND** `block_reason=approval_required`

### Requirement: Publish SHALL not modify semantic workflow design directly

The publish lifecycle SHALL NOT directly modify target workflow semantic design, commands, skills, agents, or runtime behavior to make a workflow publishable.

#### Scenario: Publish discovers required workflow changes

- **WHEN** publish eligibility or package validation discovers that semantic workflow changes are needed
- **THEN** publish stops with a remediation plan
- **AND** the plan instructs the user to run `workflowprogram-develop` with change policy
- **AND** publish does not call managed apply to change target workflow assets
