# Design

## Layering

`loop_policy` belongs to target workflow nodes:

```text
WorkflowProgram S0..S6 control plane
  -> accepted workflow-spec.yaml
  -> target workflow_graph
  -> node.loop_policy
```

The product lifecycle remains `S0..S6`. Loop semantics do not create new WorkflowProgram stages.

## Loop Policy Shape

```yaml
workflow_graph:
  nodes:
    - id: reverse_analysis
      role: iterative reverse analysis
      template: reverse_engineering
      owner: reverser
      input_refs: [user_input.binary]
      output_refs:
        - outputs/reverse-report.md
      gate: reviewer_approval
      loop_policy:
        enabled: true
        mode: ralph
        goal_source: model_subgoal
        parent_goal_ref: user_goal.reverse_binary
        max_iterations: 5
        fresh_context_each_iteration: true
        prompt_package: .workflowprogram/loops/reverse_analysis/prompt-package.md
        tdd_policy:
          enabled: true
          test_first_required: true
          red_green_refactor: true
        feedback_commands:
          - id: pytest_reverse_report
            kind: test
            argv: [python3, -m, pytest, tests/reverse_report]
            timeout_seconds: 120
            failure_effect: feedback
        stop_conditions:
          success:
            - verifier_passed
          max_iterations: fail
          no_progress_iterations: 2
        evidence_outputs:
          - outputs/stages/loops/reverse_analysis/loop-plan.json
          - outputs/stages/loops/reverse_analysis/iteration-summary.jsonl
          - outputs/stages/loops/reverse_analysis/final-verdict.json
```

## Provider Semantics

- `fixture_host` and `command_adapter` are deterministic providers. If `loop_policy.enabled=true`, they must produce structured loop evidence and S5 must fail when evidence is missing or violates the policy.
- `claude_cli` starts each requested loop iteration as a fresh process when `fresh_context_each_iteration=true`. V1 checks contract and evidence, but missing structured evidence is a warning instead of a clean pass.
- A loop may stop with `PASS` only when a verifier/test result satisfies `stop_conditions.success`.

## Evidence

Required evidence for each loop-enabled node:

- `RUN_ROOT/outputs/stages/loops/<node_id>/loop-plan.json`
- `RUN_ROOT/outputs/stages/loops/<node_id>/iteration-summary.jsonl`
- `RUN_ROOT/outputs/stages/loops/<node_id>/final-verdict.json`
- Event types: `LoopStart`, `LoopIterationStart`, `LoopFeedbackCommandCompleted`, `LoopAgentCompleted`, `LoopVerifierCompleted`, `LoopStop`

If `goal_source=model_subgoal`, evidence must include `parent_goal_ref`. If `tdd_policy.enabled=true`, evidence must include a test-first marker.

## Safety Rules

- `feedback_commands[*].argv` is structured argv only; shell strings are not allowed.
- `prompt_package` must be a safe relative path under `.workflowprogram/loops/**`.
- `evidence_outputs` must stay under `outputs/stages/loops/<node_id>/**`.
- Loop nodes do not execute `host_global` or `manual_only` bootstrap.
- V1 treats loop plus explicit agent-team orchestration as separate evidence systems. A future change may add nested team-in-loop execution if needed.
