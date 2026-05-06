# Requirement Logic Interview Design

## Baseline

This change builds on the existing S1 deep clarification system:

- one user-facing `requirement-clarification-lead`
- internal challenge roles
- structured clarification package
- final readback
- deterministic S2/S3 handoff

The missing piece is the interview method itself. The lead must not only collect fields; it must uncover the task logic that will drive workflow design.

## Core Concept

S1 SHALL maintain a `requirement-logic-map.json` built from seven logic lenses:

1. `purpose`: why the workflow exists and what outcome matters
2. `object_model`: what objects the workflow reads, transforms, classifies, or produces
3. `process_model`: what meaningful steps the work must go through
4. `decision_model`: what choices the workflow must make and what inputs drive them
5. `evidence_model`: what evidence makes each intermediate/final output trustworthy
6. `acceptance_model`: concrete scenarios that prove useful behavior
7. `boundary_model`: stop, defer, manual-confirm, non-goal, and degradation rules

The lead asks questions in this order by default, but may skip or compress lenses when the request is simple and already clear.

## Seven Logic Lenses

Each lens has a specific job. A lens is not a questionnaire section; it is a way to decide what the workflow must understand before design can safely continue.

### Lens 1: `purpose`

**Task:** Convert the user's request from a desired artifact into a reasoned goal.

**Content to capture:**

- `problem_statement`: what problem or friction exists now
- `desired_outcome`: what useful state the workflow should create
- `primary_user`: who consumes the result
- `success_metric`: how usefulness is judged
- `priority`: must/should/could goals
- `non_goals`: outcomes explicitly outside scope

**Goal:** S2/S3 should understand why the workflow exists, not only what files to create.

**Exit criteria:**

- The desired outcome is observable.
- At least one success metric or acceptance signal exists.
- Non-goals are explicit enough to prevent scope creep.

**Good question patterns:**

- "What decision or action should become easier after this workflow runs?"
- "If the workflow produces a report, what will you do with that report?"
- "Which result would make this workflow useless even if it technically runs?"

**Downstream impact:** Determines workflow scope, acceptance scenarios, and whether a feature is a core requirement or optional enhancement.

### Lens 2: `object_model`

**Task:** Identify the objects that the workflow reads, transforms, classifies, validates, or produces.

**Content to capture:**

- `input_objects`: source artifacts such as code, binary, issue, test output, design doc, trace, API schema
- `derived_objects`: intermediate models such as DFD, call graph, threat list, dependency map, migration plan
- `output_objects`: final artifacts such as report, patch, test plan, workflow asset, finding list
- `object_fields`: required properties for each important object
- `source_of_truth`: which object wins when sources disagree
- `unknown_handling`: what to do when an object is incomplete or ambiguous

**Goal:** The workflow graph should be grounded in concrete objects rather than vague "analysis" steps.

**Exit criteria:**

- Primary inputs and outputs are named.
- Critical intermediate objects are identified for complex workflows.
- Source-of-truth and unknown-handling rules are clear for `L/XL` workflows.

**Good question patterns:**

- "What artifact is the source of truth: code, docs, runtime traces, or user-supplied architecture?"
- "What intermediate model must exist before the workflow can make the next decision?"
- "If this object cannot be inferred completely, should the workflow mark `unknown`, ask you, or block?"

**Downstream impact:** Drives S2 context collection, S3 node design, evidence schemas, and target workflow inputs/outputs.

### Lens 3: `process_model`

**Task:** Decompose the work into meaningful stages or target workflow nodes.

**Content to capture:**

- `steps`: ordered or graph-based work units
- `step_inputs` and `step_outputs`
- `preconditions`: what must be true before a step runs
- `completion_signal`: how the step knows it is done
- `human_touchpoints`: where user review or approval is needed
- `candidate_nodes`: target `workflow_graph.nodes[*]` candidates

**Goal:** S3 should have a defensible target workflow structure before writing `workflow-spec.yaml`.

**Exit criteria:**

- Each must-have requirement maps to at least one process step.
- Step order or dependency relation is clear.
- Complex steps that need dedicated `node-design` are identifiable.

**Good question patterns:**

- "Before threat analysis starts, what must already be known?"
- "Which step can be automated deterministically, and which step needs model judgment?"
- "Where should the workflow pause for user confirmation rather than continuing?"

**Downstream impact:** Becomes `workflow_graph`, stage/node ownership, loop policy candidates, and implementation plan tasks.

### Lens 4: `decision_model`

**Task:** Identify decisions the workflow must make and the rules, heuristics, or user inputs that control them.

**Content to capture:**

- `decisions`: named choices the workflow must make
- `decision_inputs`: facts or evidence used to decide
- `decision_rules`: deterministic rules, model heuristics, scoring, thresholds, or user choices
- `fallbacks`: what happens if decision inputs are missing
- `confidence`: whether the decision needs confidence labels or review
- `decision_owner`: script, model, user, reviewer, agent team

**Goal:** Avoid hidden model judgment. Every important branch should be explainable and testable.

**Exit criteria:**

- Branching choices are named.
- Decision inputs and fallback behavior are known.
- User-confirmed decisions are distinguished from model-inferred decisions.

**Good question patterns:**

- "How should the workflow choose between static analysis, dynamic testing, fuzzing, or manual review?"
- "What confidence level is enough to proceed without asking you?"
- "If two rules conflict, which one wins?"

**Downstream impact:** Drives `workflow_graph.transitions`, gates, verifier selection, agent/team use, and failure recovery.

### Lens 5: `evidence_model`

**Task:** Define what evidence proves each output, decision, and intermediate model is trustworthy.

**Content to capture:**

- `evidence_items`: files, logs, snippets, traces, commands, screenshots, test results, citations
- `evidence_links`: which requirement, object, process step, or decision each evidence item supports
- `minimum_evidence`: evidence required for PASS
- `confidence_policy`: how uncertain findings are labeled
- `auditability`: what must be preserved in RUN_ROOT or target artifacts
- `invalid_evidence`: evidence that is not acceptable

**Goal:** Prevent success based only on model self-report.

**Exit criteria:**

- Must-have outputs have required evidence.
- Decision-heavy workflows define confidence or uncertainty handling.
- S5 can verify at least structural evidence existence.

**Good question patterns:**

- "What evidence should a reviewer see before trusting this generated finding?"
- "Does every threat need code evidence, DFD evidence, and a selected test method?"
- "Should missing evidence fail the workflow, warn, or create a follow-up question?"

**Downstream impact:** Drives `runtime_contract.required_evidence`, S5 checks, traceability matrix, report schema, and acceptance tests.

### Lens 6: `acceptance_model`

**Task:** Convert the clarified logic into concrete scenarios that prove the workflow behaves correctly.

**Content to capture:**

- `scenarios`: happy path, incomplete input, ambiguous input, known failure, regression case
- `given_when_then`: condition/action/expected result
- `expected_outputs`: files, fields, findings, status, evidence
- `negative_cases`: what must not happen
- `acceptance_owner`: user, validator, S5 judge, external test, manual review
- `coverage_links`: which `REQ-*` and process/decision/evidence refs each scenario covers

**Goal:** Development should be able to satisfy tests, not vague intent.

**Exit criteria:**

- At least one acceptance scenario covers each must-have requirement for `M+`.
- `L/XL` workflows include negative or ambiguity scenarios.
- Expected outputs are machine-checkable where possible.

**Good question patterns:**

- "Give one example input where the workflow should definitely pass."
- "Give one example where the workflow should stop instead of guessing."
- "What exact output fields should exist for the result to be useful?"

**Downstream impact:** Becomes `acceptance-tests.yaml`, S5 criteria, fixture design, and implementation validation.

### Lens 7: `boundary_model`

**Task:** Define what the workflow must not do, when it must stop, and which assumptions can be carried forward.

**Content to capture:**

- `non_goals`: explicitly excluded work
- `stop_conditions`: hard blockers
- `manual_confirmations`: actions needing user approval
- `defer_rules`: uncertainties allowed to pass into S2/S3 as assumptions
- `safety_constraints`: write boundaries, host changes, destructive actions, external services
- `degradation_policy`: behavior when tools, context, or capabilities are unavailable

**Goal:** Prevent the workflow from silently expanding scope or taking unsafe action.

**Exit criteria:**

- Blocking versus non-blocking uncertainty is separated.
- Manual approval points are identified.
- Host/tool/capability gaps have stop, degrade, or bootstrap policy.

**Good question patterns:**

- "What should the workflow never modify automatically?"
- "Which missing information should block design, and which can be logged as an assumption?"
- "If a required tool or MCP is unavailable, should the workflow fail, degrade, or generate setup instructions?"

**Downstream impact:** Drives gates, write boundaries, host capability bootstrap, failure_kind mapping, and S5 boundary checks.

## Lens Coverage Rules

The lens map should be compact for simple requests and strict for complex ones:

- `S`: `purpose`, `object_model`, `acceptance_model`, and `boundary_model` must be explicit; other lenses may be minimal.
- `M`: all seven lenses must exist; process/evidence/acceptance links are required for must-have requirements.
- `L`: all seven lenses must be populated with at least one process step, decision, evidence item, acceptance scenario, and boundary.
- `XL`: all `L` rules apply, plus candidate target workflow nodes, uncertainty handling, and negative/stop scenarios are required before readback.

`open_logic_gaps[]` may contain deferred gaps, but blocking gaps must be empty before S1 exits.

## Adaptive Interview Loop

Each clarification round follows the same internal loop:

```text
current requirement state
  -> identify weakest logic lens
  -> generate 1-3 narrow questions
  -> ask user through the clarification lead
  -> update requirement logic map
  -> run internal challenge
  -> decide continue / readback / block / defer
```

Questions should be narrow enough that the answer changes design. A question is weak if either answer would produce the same workflow.

## Question Backlog

`question-backlog.json` records why the next questions are worth asking.

Minimum fields:

- `generated_at`
- `round`
- `complexity`
- `weakest_lenses`
- `questions[]`

Each question includes:

- `id`
- `lens`
- `question`
- `why_it_matters`
- `blocks_design`
- `expected_answer_shape`
- `linked_requirement_ids`
- `status`: `pending | answered | deferred | dropped`

This prevents the lead from asking a pile of generic questions. Every question must have a design consequence.

## Requirement Logic Map

`requirement-logic-map.json` is the deterministic S1 model consumed by S2/S3.

Minimum structure:

```json
{
  "schema_version": 1,
  "complexity": "S|M|L|XL",
  "purpose": {...},
  "object_model": {"objects": [...]},
  "process_model": {"steps": [...]},
  "decision_model": {"decisions": [...]},
  "evidence_model": {"evidence": [...]},
  "acceptance_model": {"scenarios": [...]},
  "boundary_model": {"boundaries": [...]},
  "requirement_links": [
    {
      "requirement_id": "REQ-001",
      "process_refs": [],
      "decision_refs": [],
      "evidence_refs": [],
      "acceptance_refs": [],
      "boundary_refs": []
    }
  ],
  "open_logic_gaps": []
}
```

For simple workflows, some arrays may be short. For complex workflows, each `REQ-*` should link to at least one process, evidence, and acceptance reference, unless explicitly marked as deferred or informational.

## Complexity Triage

S1 should classify clarification depth before asking many questions:

- `S`: direct asset/task generation; one readback may be enough if all core fields are present
- `M`: several workflow steps or validation rules; use all seven lenses but keep questions compact
- `L`: domain reasoning, tool selection, multiple evidence types, or target graph design; require logic map coverage
- `XL`: security, reverse engineering, migration, compliance, multi-agent/team, or loop/TDD workflows; require node candidates and acceptance scenarios before S3

The complexity value is not just documentation. It determines how strict `validate-workflow-draft.py` should be.

## STRIDE Example

For "create a STRIDE security testing workflow", good S1 questions are not:

- "What edge cases should we consider?"

Good S1 questions are:

- "What code artifact is the source of truth for building the DFD: routes/controllers, service calls, infrastructure config, or user-provided architecture docs?"
- "If the workflow cannot infer a complete trust boundary, should it mark the DFD element as `unknown`, ask the user, or block threat analysis?"
- "Must each threat link to a DFD element, STRIDE category, code evidence, and selected test method?"
- "Should test methods be selected by threat type, by affected component, or from a fixed checklist?"

These questions alter workflow nodes, evidence, and acceptance tests.

## S2/S3 Handoff

`clarification-handoff.json` SHALL include:

- `logic_map_path`
- `question_backlog_path`
- `s2_inputs.logic_lenses`
- `s3_inputs.workflow_node_candidates`
- `s3_inputs.acceptance_scenarios`

S2 uses the map to decide what context to inspect. S3 uses it to design nodes, decisions, evidence, and acceptance tests.

## Validation Strategy

`validate-workflow-draft.py` should add logic-depth checks:

- `question-backlog.json` exists when S1 complexity is `M+`
- `requirement-logic-map.json` exists when S1 reaches design-ready state
- all seven lens keys exist
- pending blocking questions are empty
- every `REQ-*` has logic links appropriate to complexity
- generic-only question patterns cannot satisfy depth for `L/XL`
- readback references the logic model, not only prose scope

For `S` complexity, validation should allow lightweight maps to avoid overburdening simple workflows.

## Compatibility

This change does not alter `intent_flows`, stage slots, runtime host providers, or generated target runtime. It only strengthens S1's design-readiness gate and the S1-to-S2/S3 handoff.
