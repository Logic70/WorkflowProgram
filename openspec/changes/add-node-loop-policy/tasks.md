# Tasks

## 1. OpenSpec And Design Truth

- [x] 1.1 Add OpenSpec requirements for node-level loop policies, provider behavior, evidence, and TDD subgoal traceability.
- [x] 1.2 Update HighLevel and LowLevel design docs so Ralph-style loops are target `workflow_graph` node policies, not WorkflowProgram S1-S6 replacements.
- [x] 1.3 Update spec templates and product development guidance to identify when a task should use loop execution.

## 2. Spec And Runtime Contract

- [x] 2.1 Extend `validate-workflow-spec.py` to validate `workflow_graph.nodes[*].loop_policy`.
- [x] 2.2 Add `node_loop_execution` to generated runtime capabilities and require it when any loop policy is enabled.
- [x] 2.3 Extend target runtime manifest generation and validation so loop-enabled specs declare loop capability consistently.
- [x] 2.4 Add valid and invalid loop spec fixtures.

## 3. S5 Evidence Contract

- [x] 3.1 Extend S5 judge to validate loop plan, iteration summaries, final verdict, events, iteration limits, verifier gating, and TDD trace markers.
- [x] 3.2 Fail deterministic providers when loop evidence is missing or invalid.
- [x] 3.3 Warn, rather than clean-pass, `claude_cli` when structured loop evidence is missing.

## 4. Deterministic Smoke

- [x] 4.1 Add mock runtime host support for successful loop evidence.
- [x] 4.2 Add mock runtime host support for an iteration-limit failure.
- [x] 4.3 Add runtime smoke presets, expectations, and matrix cases for loop pass/fail.

## 5. Verification

- [x] 5.1 Run loop spec validator fixtures.
- [x] 5.2 Run node-loop smoke fixtures.
- [x] 5.3 Run `runtime_smoke_matrix.py`.
- [x] 5.4 Run `validate-workflow.py`.
