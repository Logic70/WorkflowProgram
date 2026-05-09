## 1. Design And OpenSpec

- [x] 1.1 Audit current agents and confirm no existing agent owns S3 design-review closure.
- [x] 1.2 Define usage design for the internal `workflow-design-reviewer` role.
- [x] 1.3 Define implementation design for packet generation, review loop, gate validation, develop integration, and S5 checks.
- [x] 1.4 Review this change against existing requirement clarification, change-policy, node-design, loop, team, and S5 mechanisms.

## 2. Agent And Prompt Assets

- [x] 2.1 Add `.claude/agents/workflow-design-reviewer.md` with review lenses, input contract, output schema, and no-write rules.
- [x] 2.2 Update `workflowprogram-develop` so S3 describes the review loop and prohibits S4 before review closure.
- [x] 2.3 Update active HighLevel and LowLevel docs with the S3 -> design review -> S4 gate.
- [x] 2.4 Rebuild `dist/plugin/` after source asset changes.

## 3. Deterministic Gate Scripts

- [x] 3.1 Add `generate-design-review-packet.py`.
- [x] 3.2 Add `validate-design-review-gate.py`.
- [x] 3.3 Add unit/spec fixtures for valid closure, missing closure, unresolved blocker, stale closure, and accepted non-blocking risk.
- [x] 3.4 Extend `validate-workflow.py` to require the new scripts, agent, and documented gate markers.

## 4. Runtime Integration

- [x] 4.1 Integrate design-review gate validation into `workflow-entry.py` before managed apply for develop runs.
- [x] 4.2 Extend `workflow-s5-judge.py` with design-review artifact and boundary checks.
- [x] 4.3 Extend `workflow-runner.py` and `validate-run-state.py` artifact kinds for design-review evidence if recorded in `state.json`.
- [x] 4.4 Ensure missing or failed design-review closure returns `BLOCKED/design_review_unresolved`, not a generic runner failure.
- [x] 4.5 Update `fixture_host` and `command_adapter` deterministic providers to emit closed design-review evidence for normal develop paths.

## 5. Smoke And Regression Tests

- [x] 5.1 Add deterministic runtime fixture for closed design review pass.
- [x] 5.2 Add deterministic runtime fixture for missing design-review closure fail.
- [x] 5.3 Add deterministic runtime fixture for unresolved blocking design-review issue fail.
- [x] 5.4 Add deterministic runtime fixture for accepted non-blocking risk pass with warning.
- [x] 5.5 Add modification-flow fixture that combines change policy and design review evidence.
- [x] 5.6 Run `python3 .claude/scripts/validate-workflow.py`.
- [x] 5.7 Run `python3 tools/runtime_smoke_matrix.py`.
- [x] 5.8 Run `openspec validate add-s3-design-review-agent-gate --strict`.

## 6. Release

- [x] 6.1 Update plugin version if implementation changes marketplace assets.
- [x] 6.2 Rebuild and verify plugin package.
- [x] 6.3 Commit implementation with a message naming the design-review gate.
- [x] 6.4 Push to GitHub after validation passes.
