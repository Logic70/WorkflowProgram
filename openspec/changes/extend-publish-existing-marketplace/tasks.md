## 1. Design

- [x] 1.1 Define `existing_marketplace` publish lifecycle and repo layout.
- [x] 1.2 Define merge conflicts, version bump policy, and checkout clean requirements.
- [x] 1.3 Define publish evidence and install-instruction behavior.

## 2. Publish Control Plane

- [x] 2.1 Extend `workflow-publish-entry.py` inputs and orchestration for `existing_marketplace`.
- [x] 2.2 Add `merge-target-marketplace.py`.
- [x] 2.3 Extend `package-target-plugin.py` to omit replacement marketplace manifests for existing-marketplace packaging.
- [x] 2.4 Extend `github-publish-target-plugin.py` to apply merged marketplace updates into an existing checkout.
- [x] 2.5 Extend `validate-target-plugin-package.py` or companion evidence checks for marketplace merge validation.

## 3. Prompts And Docs

- [x] 3.1 Update `workflowprogram-publish` skill.
- [x] 3.2 Update publish command usage.
- [x] 3.3 Update README, plugin README, and design docs with reuse-existing-marketplace guidance.

## 4. Fixtures And Smoke

- [x] 4.1 Add expectations for append/update/block/fail existing-marketplace fixtures.
- [x] 4.2 Extend fixture host and runtime smoke presets.
- [x] 4.3 Extend runtime smoke matrix.

## 5. Verification

- [x] 5.1 Run py_compile for changed publish scripts.
- [x] 5.2 Run targeted publish smoke fixtures.
- [x] 5.3 Run `python3 .claude/scripts/validate-workflow.py`.
- [x] 5.4 Run `python3 tools/runtime_smoke_matrix.py`.
- [x] 5.5 Run `openspec validate extend-publish-existing-marketplace --strict`.
