## Design

### 1. Current Capability Assessment

Existing agents provide adjacent capabilities:

| Existing agent | What it does | Why it is insufficient |
| --- | --- | --- |
| `workflow-designer` | Creates workflow designs from requirements and context. | It is the author, not an independent reviewer. |
| `workflow-validator` | Checks generated workflow files for structure and consistency. | It runs after assets exist and does not challenge S3 design decisions before S4. |
| `workflow-verifier` | Validates runtime behavior in an isolated execution environment. | It is downstream runtime verification, not pre-implementation design review. |
| `logic/security/style/performance-reviewer` | Reviews code or focused concerns. | They do not own full WorkflowProgram design closure across requirements, design, spec, tests, and change policy. |

Conclusion: there is no current agent with the exact responsibility of an independent S3 design-review gate.

### 2. Use Design

`workflow-design-reviewer` is an internal agent selected by `workflowprogram-develop` after S3 produces design sources and before S4 candidate generation begins.

It is used for both:

- new workflow creation;
- modification of an existing managed or unmanaged workflow when `change_policy_required=true`.

The reviewer receives a compact, fresh-context packet instead of the full conversation. It must not directly edit files. It only returns structured findings and closure evidence.

#### Review inputs

The develop flow SHALL create `RUN_ROOT/outputs/stages/design-review/design-review-packet.json` containing:

- original user request;
- `route-intent.json`;
- `change-context.json`;
- `existing-workflow-readback.json` when present;
- `change-policy.json` and `impact-analysis.json` when present;
- `clarification-handoff.json`;
- `s1-requirements.yaml`;
- `s2-context-findings.yaml`;
- `s3-design-highlevel.md`;
- `s3-design-lowlevel.md`;
- all `node-designs/*.md`;
- `acceptance-tests.yaml`;
- `traceability-matrix.json`;
- `s3-implementation-plan.md`;
- projected `workflow-spec.yaml`;
- relevant active WorkflowProgram constraints and runtime contract summary.

#### Review lenses

The reviewer SHALL check at least:

- goal fidelity: whether the design still solves the user's actual objective;
- requirement coverage: every `REQ-*` has design, asset, acceptance, and evidence mapping;
- flow closure: every node has clear inputs, outputs, failure paths, and stop conditions;
- spec projection: S3 design decisions are reflected in `workflow-spec.yaml` where executable;
- evidence quality: acceptance tests can actually verify the intended behavior;
- change-policy impact: modification scope, approval, readback, and affected artifacts are coherent;
- runtime compatibility: design does not conflict with `workflow-entry.py`, managed apply, runner, S5 judge, host capability, team, or loop rules;
- complexity control: the design avoids unnecessary agents, loops, node-designs, and heavy ceremony;
- context propagation: outputs required by later nodes are produced by earlier nodes.

#### Review outputs

Each round produces artifacts under `RUN_ROOT/outputs/stages/design-review/`:

- `RUN_ROOT/outputs/stages/design-review/round-<n>.json`;
- `RUN_ROOT/outputs/stages/design-review/issues.json`;
- `RUN_ROOT/outputs/stages/design-review/report.md`.

When closure is reached, the flow also produces:

- `RUN_ROOT/outputs/stages/design-review/closure.json`.

Each issue in `issues.json` SHALL include:

- `id`;
- `round_found`;
- `status`: `open | resolved | accepted_risk | superseded`;
- `severity`: `blocker | major | minor | info`;
- `blocking`: boolean;
- `lens`;
- `affected_requirements`;
- `affected_artifacts`;
- `problem`;
- `why_it_matters`;
- `required_fix`;
- `resolved_by`;
- `resolution_evidence`;
- `residual_risk`.

### 3. Loop And Gate Semantics

The design-review loop runs until there are no open blocking issues.

If review reaches the configured maximum rounds without closure, WorkflowProgram SHALL stop with `BLOCKED/design_review_unresolved`. The maximum round limit prevents runaway execution but does not permit S4 to proceed with unresolved blockers.

Non-blocking issues may remain only if they are explicitly recorded as `accepted_risk` with a reason and owner.

`workflowprogram-develop` may revise S3 design sources and the projected spec between review rounds. It must not fix review issues by editing generated candidate assets directly.

### 4. Implementation Design

#### New agent

Add `.claude/agents/workflow-design-reviewer.md`.

The agent prompt SHALL define:

- fresh-context review posture;
- exact input packet;
- review lenses;
- output JSON schema;
- prohibition on direct file writes;
- explicit distinction between blocking issues and accepted risks.

#### New deterministic scripts

Add `.claude/scripts/generate-design-review-packet.py`.

Responsibilities:

- collect required S1/S2/S3/change-policy artifacts;
- summarize active control-plane constraints;
- emit missing-input diagnostics;
- write `design-review-packet.json`.

Add `.claude/scripts/validate-design-review-gate.py`.

Responsibilities:

- validate packet, issues ledger, round outputs, and closure schema;
- verify no open `blocking=true` issues remain;
- verify every resolved issue has `resolved_by` and `resolution_evidence`;
- verify latest closure references the current design/spec fingerprints;
- emit `RUN_ROOT/outputs/stages/design-review/gate-validation.json`;
- return non-zero when S4 must not proceed.

#### Develop integration

Update `workflowprogram-develop` so S3 explicitly performs:

1. generate S3 design sources;
2. project `workflow-spec.yaml`;
3. generate design-review packet;
4. invoke `workflow-design-reviewer`;
5. revise S3 design sources if blockers exist;
6. repeat review until closed or blocked;
7. only then generate candidate `.claude/*` and `.workflowprogram/*` assets.

#### Entry and write gate integration

`workflow-entry.py` SHOULD validate design-review closure before managed apply whenever develop intent has S3 design artifacts. This hard gate protects target writes even if the prompt-level S4 order is skipped.

Because candidate generation currently happens before `workflow-entry.py run`, the prompt-level develop flow remains responsible for not starting S4 early. The deterministic entry gate is the safety net that blocks target writes if the evidence is absent or failed.

The gate MUST run before `stage_persistent_design_assets()`, `stage_target_runtime_assets()`, and `managed-assets.py apply-staged`.

The gate is required when a product develop run has candidate assets or S3 design artifacts. It must not be triggered for generated target runtime invocations that call the target-side `workflow-runner.py` directly and are not generating or applying WorkflowProgram-managed workflow assets.

#### S5 integration

`workflow-s5-judge.py` SHALL check:

- design-review packet exists when S3 design sources exist;
- closure exists before managed apply success;
- unresolved blockers fail with `failure_kind=design`;
- semantic candidate changes are traceable back to either original requirements or resolved design-review issues.

#### Runtime smoke coverage

Add deterministic fixtures:

- design review closed and develop succeeds;
- design review missing and develop fails before target writes;
- unresolved blocking issue fails;
- accepted non-blocking risk passes with warning;
- modification flow checks change-policy and design-review evidence together.

### 5. Interaction With Existing Mechanisms

This change complements, not replaces:

- `validate-workflow-draft.py`: S1/S2 quality gate;
- `validate-workflow-spec.py`: YAML schema and contract gate;
- `validate-change-policy.py`: modification write gate;
- `managed-assets.py`: target write boundary;
- `workflow-s5-judge.py`: final runtime evidence verdict.

The design-review agent is an upstream semantic challenge. S5 remains the downstream conformance judge.

### 6. Iterative Design Review

#### Round 1: Path And Fixture Compatibility

Finding:

- The first draft used both `outputs/stages/design-review-packet.json` and `outputs/stages/design-review/design-review-packet.json`.
- Existing deterministic develop fixtures do not currently produce design-review evidence, so a hard S5 requirement would break unrelated smoke tests.

Resolution:

- Standardize all artifacts under `outputs/stages/design-review/`.
- Update deterministic fixtures to emit minimal closed design-review evidence for normal develop paths.
- Add explicit negative fixtures for missing and unresolved review evidence instead of relying on accidental absence.

Status: closed.

#### Round 2: Write Gate Placement

Finding:

- `workflow-entry.py` currently stages persistent design/runtime assets and then calls managed apply. If the design-review gate runs after that point, it cannot protect target writes.
- `fixture_host` and `command_adapter` can synthesize managed outputs without going through `workflow-entry.py`, so S5 must also audit the evidence.

Resolution:

- Run `validate-design-review-gate.py` before persistent design/runtime staging and before `managed-assets.py`.
- Add S5 checks for packet, issues, closure, and gate validation so bypassed deterministic providers still fail when evidence is missing or unresolved.

Status: closed.

#### Round 3: Target Runtime False Positive

Finding:

- Generated target workflows use their own target-side runtime wrapper and can run with intent `develop` for the target workflow itself.
- That is not the same as WorkflowProgram product develop generating workflow assets, and should not require S3 design-review evidence.

Resolution:

- The product `workflow-entry.py` gate is scoped to product develop runs with candidate assets or S3 design artifacts.
- Generated target runtime wrappers continue to call target-side `workflow-runner.py` directly and are not blocked by product design-review gate requirements.

Status: closed.

#### Round 4: Stale Closure

Finding:

- A reviewer can close a design packet, but the model may later alter S3 design or `workflow-spec.yaml` before implementation.
- Without fingerprint validation, stale closure could be reused.

Resolution:

- `design-review-packet.json` and `closure.json` carry artifact fingerprints.
- `validate-design-review-gate.py` recomputes current fingerprints and fails stale packets or stale closures.

Status: closed.

#### Round 5: Final Consistency Pass

Checks:

- No new public entry is introduced.
- Change-policy remains the modification gate; design review is an additional S3 semantic gate.
- Design review artifacts remain run evidence, not `workflow-spec.yaml` top-level configuration.
- Missing closure blocks writes as `BLOCKED/design_review_unresolved`.
- S5 preserves final conformance responsibility.

Result:

No new blocking design problems found. Implementation can begin.

## Decisions

- Use `workflow-design-reviewer` as an internal agent, not a user-facing command or skill.
- Put review artifacts under `RUN_ROOT/outputs/stages/design-review/`.
- Keep design review outside `workflow-spec.yaml`; it is run evidence for WorkflowProgram, not a target workflow runtime section.
- Block S4 target writes if design-review closure is missing or unresolved.
- Allow a maximum review round limit only to stop as `BLOCKED`, not to bypass the gate.
