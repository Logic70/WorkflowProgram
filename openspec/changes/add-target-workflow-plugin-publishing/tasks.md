## 1. Design And OpenSpec

- [x] 1.1 Define the independent target workflow publish lifecycle and evidence model.
- [x] 1.2 Define public `workflowprogram-publish` skill and command exposure.
- [x] 1.3 Define publish eligibility, runtime packaging modes, GitHub publishing behavior, and install instruction output.
- [x] 1.4 Review the design against develop, change-policy, design-review, S5, generated runtime, and marketplace installation mechanisms.

## 2. Prompt And Documentation Assets

- [x] 2.1 Add `.claude/skills/workflowprogram-publish/SKILL.md`.
- [x] 2.2 Add `.claude/commands/workflowprogram-publish.md`.
- [x] 2.3 Update `workflowprogram-orchestrate` so publish requests route to the publish command/skill without adding aliases.
- [x] 2.4 Update HighLevel and LowLevel design docs with the publish lifecycle.
- [x] 2.5 Update README, README.en, HTML/docs guidance, and plugin README with target workflow publish usage.

## 3. Publish Scripts

- [x] 3.1 Add `workflow-publish-entry.py` as the deterministic publish orchestrator.
- [x] 3.2 Add `validate-publish-eligibility.py` for completed-develop evidence, managed state, design-review closure, runtime, and S5 checks.
- [x] 3.3 Add `package-target-plugin.py` for staging marketplace-compatible target plugin payloads.
- [x] 3.4 Add `validate-target-plugin-package.py` for plugin manifest, command/skill exposure, runtime mode, and `claude plugin validate` checks.
- [x] 3.5 Add `github-publish-target-plugin.py` for GitHub auth/repo checks, commit/tag/push planning, and approved execution.

## 4. Runtime And Validator Integration

- [x] 4.1 Extend generated runtime manifest or publish metadata to declare target plugin runtime packaging mode.
- [x] 4.2 Ensure publish validation can consume latest S5, design-review, managed apply, state, and events evidence.
- [x] 4.3 Ensure `workflowprogram_dependency` packages generate dependency install instructions for WorkflowProgram itself.
- [x] 4.4 Ensure `vendored_runtime` packages include only the minimal validated runtime surface.
- [x] 4.5 Ensure publish never invokes managed apply for semantic target workflow changes.

## 5. Tests

- [x] 5.1 Add spec fixtures for valid and invalid publish metadata/options.
- [x] 5.2 Add smoke fixture: publish-eligible-pass.
- [x] 5.3 Add smoke fixture: publish-missing-develop-evidence-fail.
- [x] 5.4 Add smoke fixture: publish-stale-managed-state-fail.
- [x] 5.5 Add smoke fixture: publish-github-auth-missing-blocked.
- [x] 5.6 Add smoke fixture: publish-package-validation-fail.
- [x] 5.7 Add smoke fixture: publish-export-repo-plan.

## 6. Verification

- [x] 6.1 Run `python3 .claude/scripts/validate-workflow.py`.
- [x] 6.2 Run publish script unit checks.
- [x] 6.3 Run `python3 tools/runtime_smoke_matrix.py`.
- [x] 6.4 Run `openspec validate add-target-workflow-plugin-publishing --strict`.

## 7. Release

- [x] 7.1 Rebuild `dist/plugin/` after source asset changes.
- [x] 7.2 Bump WorkflowProgram plugin version.
- [x] 7.3 Commit implementation with a message naming target workflow publishing.
- [x] 7.4 Push to GitHub after validation passes.
