# Add Node Loop Policy

## Problem

Some target workflow tasks need an agent to keep working until a verifier or test says the goal is done. Reverse engineering, exploit triage, report hardening, migration repair, and other iterative tasks often fail if the model performs only one pass.

WorkflowProgram already separates its fixed product lifecycle `S0..S6` from generated target workflow graphs. What is missing is a machine-readable way for a target `workflow_graph` node to request Ralph-style repeated execution while keeping verification deterministic.

## Goals

- Add `workflow_graph.nodes[*].loop_policy` for target workflow nodes that need iterative execution.
- Keep WorkflowProgram's own `S0..S6` lifecycle unchanged.
- Require loop success to be backed by verifier/test evidence, not model self-report.
- Allow loop goals to come from the user or from model-decomposed subgoals that trace back to an upstream/user goal.
- Support TDD-style subgoals where a failing verifier/test must exist before implementation work.
- Add deterministic evidence expectations for `fixture_host` and `command_adapter`.
- Treat `claude_cli` as fresh-process loop execution in V1: contract and evidence are checked, but strong orchestration is not guaranteed.

## Non-Goals

- Do not replace `stages` or `intent_flows` with a graph engine.
- Do not make every node a loop by default.
- Do not let loop execution perform host-global or manual bootstrap actions.
- Do not combine nested agent-team fan-out and node loop orchestration in V1 unless future tests explicitly cover that behavior.
- Do not treat a transcript-only model claim as clean loop evidence.

## Expected Outcome

Generated target workflows can mark specific nodes as loop-enabled. Validators reject unsafe or unverifiable loop policies, generated runtime manifests declare `node_loop_execution`, deterministic providers emit loop evidence, and S5 fails or warns according to provider capability when loop evidence is missing or invalid.
