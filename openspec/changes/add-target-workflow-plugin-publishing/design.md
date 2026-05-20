## Design

### 1. Scope And Position In The Lifecycle

Publishing is an independent lifecycle after `workflowprogram-develop`.

`develop` produces or updates a target workflow. `publish` answers a different question: whether that completed target workflow can be packaged, validated, committed, pushed, and installed by other Claude Code users through a marketplace repository.

The publish flow must not silently redesign or modify the workflow. If publishing discovers that the workflow design, runtime, command exposure, or host capability contract is not publishable, it stops with a publish report and tells the user which develop/change-policy action is needed.

### 2. Use Design

Expose one Claude Code skill and one Claude Code command:

- skill: `workflowprogram-publish`
- command: `/workflowprogram-cn:workflowprogram-publish`

The command is the normal user entry. The skill contains the procedure and examples so Claude Code can route natural-language requests such as "publish this workflow as a plugin" to the publish flow. `workflowprogram-orchestrate` may route publish intent to this command, but publish does not depend on orchestrate.

The skill asks for missing publish choices only when they cannot be inferred safely:

- target workflow root;
- plugin id and display name;
- GitHub repository owner/name;
- repository visibility;
- publish version or tag;
- runtime packaging mode;
- whether to create a new repo or update an existing repo.

### 3. Publish Eligibility

A target workflow is publishable only when it has completed `workflowprogram-develop` and has current evidence.

Required target-side artifacts:

- `TARGET_ROOT/.workflowprogram/design/workflow-spec.yaml`;
- `TARGET_ROOT/.workflowprogram/design/workflow-maintenance.md`;
- `TARGET_ROOT/.workflowprogram/runtime/runtime-manifest.json`;
- `TARGET_ROOT/.workflowprogram/managed-files.json`;
- generated command/skill/agent assets referenced by the spec.

Required recent run evidence:

- route evidence for a develop run;
- S3 design sources and design-review closure;
- managed plan/result evidence;
- run state and events;
- S5 final verdict `PASS`.

`WARN` is not publishable by default. The publish command may accept an explicit `--allow-warn` style approval, but the publish evidence must record the accepted warnings and generated install instructions must include them.

Publish must fail fast when:

- required develop evidence is missing or stale;
- managed files have unresolved conflicts or drift;
- design-review closure is missing, failed, or stale;
- required host capabilities are unresolved;
- target runtime validation fails;
- command/skill exposure is ambiguous;
- plugin id conflicts with an existing marketplace entry;
- GitHub authentication or repository permission is missing.

### 4. Packaging Model

The publish flow creates a marketplace-compatible plugin payload for the target workflow.

V1 supports two explicit runtime packaging modes:

- `workflowprogram_dependency`: the published target plugin declares that users must install WorkflowProgram from its marketplace first. This is lower risk and matches the current shared-control-plane wrapper model.
- `vendored_runtime`: the publish flow copies the minimal runtime scripts and launcher needed by the target workflow into the target plugin payload. This is the preferred end-user experience once validated, because consumers install only the target workflow plugin.

The publish command must not hide this choice. If the generated runtime cannot be made self-contained safely, it must choose `workflowprogram_dependency` and produce install instructions for both plugins.

Package output is staged as run evidence first:

- `RUN_ROOT/outputs/stages/publish/package-root/`;
- `RUN_ROOT/outputs/stages/publish/plugin-manifest-preview.json`;
- `RUN_ROOT/outputs/stages/publish/plugin-package-plan.json`.

Only after validation and user approval may the package be copied into a Git checkout intended for publishing.

Supported repository modes:

- `current_repo`: the target workflow repository is also the marketplace repository.
- `export_repo`: the target workflow is exported to a separate GitHub repository.

`export_repo` is the safer default for workflows created inside application codebases, because it avoids publishing unrelated project source.

### 5. GitHub And Marketplace Publishing

Publishing uses the user's GitHub account.

The deterministic scripts may call:

- `gh auth status`;
- `gh repo view`;
- `gh repo create`;
- `git status`;
- `git add`;
- `git commit`;
- `git tag`;
- `git push`.

The system must not store GitHub tokens in WorkflowProgram files or publish evidence. If authentication is missing, the flow stops with a remediation plan that tells the user to authenticate GitHub outside WorkflowProgram.

The publish flow produces a marketplace file compatible with Claude Code marketplace installation. Install instructions must include:

- marketplace add command;
- plugin install command;
- expected plugin id and version;
- dependency install commands when `workflowprogram_dependency` is used;
- update instructions;
- rollback/uninstall note.

### 6. Evidence Model

Publish writes machine-readable evidence under `RUN_ROOT/outputs/stages/publish/`:

- `publish-intent.json`;
- `publish-eligibility.json`;
- `publish-options.json`;
- `plugin-package-plan.json`;
- `plugin-manifest-preview.json`;
- `plugin-validation-report.json`;
- `github-publish-plan.json`;
- `github-publish-result.json`;
- `install-instructions.md`;
- `publish-summary.json`.

`publish-summary.json` is the final status source:

- `PASS`: package validated and GitHub publish succeeded;
- `BLOCKED`: missing approval, auth, permissions, choices, or repository readiness;
- `FAIL`: eligibility, package validation, runtime validation, or marketplace validation failed.

Publish failures use `failure_kind`:

- `design`: target workflow is not publishable because design/spec/evidence is incomplete;
- `implementation`: generated plugin package or runtime wrapper is invalid;
- `environment`: local GitHub, git, or Claude Code validation prerequisites are missing;
- `conflict`: repository state or plugin id/version conflicts with existing publication.

### 7. Deterministic Implementation Shape

Add a dedicated publish entry script instead of overloading `workflow-entry.py`:

- `workflow-publish-entry.py`: orchestration for publish-only flow;
- `validate-publish-eligibility.py`: checks completed develop evidence and target workflow state;
- `package-target-plugin.py`: stages plugin payload and manifest preview;
- `validate-target-plugin-package.py`: validates payload, metadata, exposure, runtime mode, and marketplace compatibility;
- `github-publish-target-plugin.py`: creates or updates GitHub repository, commits, tags, and pushes after approval.

`workflow-entry.py` remains the runtime entry for develop/validate/audit/iterate. Publish may reuse shared validators and runtime-generation helpers, but it must not write target workflow assets through managed apply unless the user explicitly routes back to `workflowprogram-develop`.

### 8. Command And Skill Exposure

The public surface after this change is:

- `/workflowprogram-cn:workflowprogram-orchestrate` for general lifecycle routing;
- `/workflowprogram-cn:workflowprogram-develop` for explicit workflow creation/modification;
- `/workflowprogram-cn:workflowprogram-publish` for publishing completed target workflows;
- the matching public skills `workflowprogram-orchestrate`, `workflowprogram-develop`, and `workflowprogram-publish`.

Internal helper skills remain unregistered and referenced only by file path or command text. Publish must not add duplicate aliases such as `/publish`, `/release`, or `/workflowprogram` unless a later exposure change explicitly approves them.

### 9. Interaction With Existing Mechanisms

Publishing does not replace:

- design review: publish consumes design-review closure as eligibility evidence;
- change policy: if publish requires modifying target workflow assets, it stops and asks the user to run develop with change policy;
- S5 judge: publish consumes the latest S5 verdict and may run package-specific validation;
- marketplace-primary-installation: that change remains about installing WorkflowProgram itself, not publishing generated workflows.

Publishing may generate repository metadata, marketplace metadata, and install docs. Those are distribution artifacts, not target workflow semantic changes.

### 10. Iterative Design Review

#### Round 1: Independent Lifecycle Boundary

Finding:

- The first draft risked placing publish as another develop stage, which would blur the meaning of "completed develop" and could allow publish to mutate an unfinished workflow.

Resolution:

- Publish is a separate lifecycle with its own command, skill, scripts, evidence, and summary.
- Publish consumes develop evidence and blocks instead of repairing target workflow design.

Status: closed.

#### Round 2: Runtime Dependency Ambiguity

Finding:

- Current generated target workflows use a shared-control-plane wrapper model. A marketplace plugin used by other users may not have WorkflowProgram installed.

Resolution:

- The publish contract requires explicit runtime packaging mode.
- `workflowprogram_dependency` is allowed and must generate dependency install instructions.
- `vendored_runtime` is allowed only when validation proves the package carries the required runtime.

Status: closed.

#### Round 3: GitHub Security And Account Ownership

Finding:

- Publishing for other users requires GitHub, but WorkflowProgram must not collect or persist credentials.

Resolution:

- Use local `gh` and git authentication only.
- Missing auth becomes `BLOCKED/environment` with remediation.
- Evidence records auth status and repo permission outcome, never tokens.

Status: closed.

#### Round 4: Repository Pollution Risk

Finding:

- Many target workflows are created inside product repositories. Writing marketplace files directly into the product repo could publish unrelated source or disturb application history.

Resolution:

- Stage package output under the run root first.
- Prefer `export_repo` unless the user explicitly chooses `current_repo`.
- Validate the publish checkout's clean state before copying package output.

Status: closed.

#### Round 5: Exposure Surface Creep

Finding:

- Adding multiple command aliases would recreate the entry exposure problem recently consolidated.

Resolution:

- Add exactly one public publish command and one public publish skill.
- Optional orchestrate routing points to that command instead of creating hidden names.

Status: closed.

#### Round 6: Develop Evidence Freshness

Finding:

- A workflow might have old passing S5 evidence but current target files could drift after that run.

Resolution:

- `validate-publish-eligibility.py` compares current managed files and design/runtime fingerprints against latest develop evidence.
- Drift, unresolved conflicts, or stale design-review closure block publishing.

Status: closed.

#### Round 7: Final Consistency Pass

Checks:

- Publish is independent from develop but requires completed develop evidence.
- Publish can run inside Claude Code without Codex-only tools.
- GitHub dependency is explicit and user-owned.
- Runtime dependency mode is explicit.
- Command/skill exposure remains minimal and non-conflicting.
- If publish needs semantic workflow changes, it routes back to develop instead of editing directly.

Result:

- No new design issues identified.
