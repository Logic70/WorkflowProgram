# Tasks

## 1. OpenSpec And Design

- [x] 1.1 Record the FreeSTRIDE-derived node-design gap and scope boundary.
- [x] 1.2 Define target node-design required sections and projection consistency rules.
- [x] 1.3 Review design/plan through closure lenses until no new actionable issue remains.

## 2. Template And Prompting

- [x] 2.1 Add `workflow-spec-support/target-node-design-template.md`.
- [x] 2.2 Update `workflowprogram-develop` to require the template for complex, looped, security-critical, reverse-engineering, or tool-heavy nodes.
- [x] 2.3 Update `workflow-spec-support/spec-template.md` and `yaml-spec-template.md` to point to the target node design contract.

## 3. Validator

- [x] 3.1 Add `validate-target-node-design.py` with JSON output and deterministic exit codes.
- [x] 3.2 Validate required Markdown sections.
- [x] 3.3 Validate node id, graph path, owner, template, gate, input refs, output refs, loop policy, failure strategy, and verification evidence.
- [x] 3.4 Reject unresolved placeholders.

## 4. Governance And S5 Integration

- [x] 4.1 Extend `validate-target-design-governance.py` to call the node-design validator for existing node-design refs.
- [x] 4.2 Extend `workflow-s5-judge.py` to add per-node node-design content checks.
- [x] 4.3 Add the new validator and template to repository/dist required-path checks.

## 5. Fixtures And Tests

- [x] 5.1 Update deterministic mock runtime host to emit valid node-design content.
- [x] 5.2 Update target design governance unit fixtures if stronger validation affects them.
- [x] 5.3 Add node-design validator unit tests for pass, missing section, owner mismatch, missing output ref, and loop-policy mismatch.

## 6. Docs And Distribution

- [x] 6.1 Update README/plugin README and active design docs with target node-design content validation.
- [x] 6.2 Rebuild `dist/plugin` so marketplace installs include the validator/template/docs changes.

## 7. Verification

- [x] 7.1 Run `openspec validate harden-target-node-design-contract --strict`.
- [x] 7.2 Run `python3 tests/unit/test_target_node_design_validator.py`.
- [x] 7.3 Run affected unit scripts.
- [x] 7.4 Run `python3 .claude/scripts/validate-workflow.py`.
- [x] 7.5 Run relevant runtime smoke fixture.
- [x] 7.6 Run `git diff --check`.
