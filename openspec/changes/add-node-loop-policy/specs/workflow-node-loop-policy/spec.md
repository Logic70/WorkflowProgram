# workflow-node-loop-policy Specification

## ADDED Requirements

### Requirement: Target graph nodes may declare loop policy

`workflow-spec.yaml.workflow_graph.nodes[*].loop_policy` MAY declare a Ralph-style loop for a target workflow node, and MUST NOT alter WorkflowProgram's own `S0..S6` lifecycle.

#### Scenario: Loop policy is enabled on one target node

- **GIVEN** WorkflowProgram runs its normal develop flow
- **WHEN** the accepted spec declares `workflow_graph.nodes[*].loop_policy.enabled=true`
- **THEN** the loop applies only to that target graph node
- **AND** WorkflowProgram's product lifecycle remains `S0..S6`.

### Requirement: Loop policy must be safe and machine-verifiable

An enabled loop policy MUST define bounded iteration, structured feedback commands, safe prompt/evidence paths, and explicit stop conditions.

#### Scenario: Feedback command is a shell string

- **GIVEN** a loop policy declares `feedback_commands[*].command: "pytest && echo ok"`
- **WHEN** spec validation runs
- **THEN** validation MUST fail because loop feedback commands must use structured `argv`.

### Requirement: Runtime capability must declare node loop execution

If any target graph node enables loop execution, `generated_runtime_contract.runtime_capabilities` MUST include `node_loop_execution`.

#### Scenario: Loop policy exists but runtime capability is missing

- **GIVEN** a spec declares `loop_policy.enabled=true`
- **AND** `generated_runtime_contract.runtime_capabilities` does not include `node_loop_execution`
- **WHEN** spec validation runs
- **THEN** validation MUST fail.

### Requirement: Loop success requires verifier or test evidence

A loop-enabled node MUST NOT be considered successful based only on model self-report.

#### Scenario: Final verdict says PASS without verifier pass

- **GIVEN** `final-verdict.json` declares `status: PASS`
- **AND** no verifier/test result satisfies the success stop condition
- **WHEN** S5 validates loop evidence
- **THEN** S5 MUST fail deterministic providers or warn non-deterministic providers according to provider capability.

### Requirement: Model-decomposed loop goals must trace to a parent goal

When `goal_source=model_subgoal`, loop evidence MUST include a `parent_goal_ref` that traces the subgoal back to the user goal or upstream node output.

#### Scenario: Model subgoal lacks traceability

- **GIVEN** `loop_policy.goal_source=model_subgoal`
- **AND** `loop-plan.json` omits `parent_goal_ref`
- **WHEN** S5 validates loop evidence
- **THEN** S5 MUST report the loop trace as invalid.

### Requirement: TDD loop policy must record test-first behavior

When `tdd_policy.enabled=true` and `test_first_required=true`, loop evidence MUST show that the failing verifier/test was established before implementation work.

#### Scenario: TDD loop lacks test-first marker

- **GIVEN** `tdd_policy.test_first_required=true`
- **AND** loop evidence does not record test-first behavior
- **WHEN** S5 validates loop evidence
- **THEN** S5 MUST report the TDD trace as invalid.
