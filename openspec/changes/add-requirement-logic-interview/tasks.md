# Tasks

## 1. OpenSpec Contract

- [x] 1.1 Define `workflow-requirement-logic-interview` as an S1/develop-only capability.
- [x] 1.2 Specify the seven logic lenses: purpose, object, process, decision, evidence, acceptance, boundary.
- [x] 1.3 Specify `question-backlog.json` and `requirement-logic-map.json`.
- [x] 1.4 Define lightweight versus strict behavior by complexity.

## 2. Design Docs And Product Guidance

- [x] 2.1 Update `docs/workflowprogram-stage-highlevel-design.md` so S1 is a requirement logic interview, not only a clarification package.
- [x] 2.2 Update `docs/workflowprogram-stage-lowlevel-design.md` with artifact schemas, loop steps, and exit gates.
- [x] 2.3 Update `.claude/skills/workflowprogram-develop/SKILL.md` with the seven-lens question strategy and examples.
- [x] 2.4 Update `docs/workflowprogram-stage-consistency-check.md` to include the new S1-to-S2/S3 logic handoff.

## 3. Templates

- [x] 3.1 Extend `.claude/skills/workflow-spec-support/spec-template.md` so drafts naturally capture logic-lens answers.
- [x] 3.2 Extend `.claude/skills/workflow-spec-support/yaml-spec-template.md` design refs or S1 outputs if `requirement-logic-map.json` should be tracked as design source.
- [x] 3.3 Ensure generated examples avoid broad generic questions and include design-consequential question examples.

## 4. Script Implementation

- [x] 4.1 Extend `generate-clarification-package.py` / `lib/clarification_utils.py` to derive `question-backlog.json`.
- [x] 4.2 Extend `generate-clarification-package.py` / `lib/clarification_utils.py` to derive `requirement-logic-map.json`.
- [x] 4.3 Extend `generate-clarification-review.py` so challenge roles rank weakest logic lenses and propose narrow follow-up questions.
- [x] 4.4 Extend `clarification-handoff.json` with `logic_map_path`, `question_backlog_path`, S2 logic lens inputs, S3 node candidates, and acceptance scenarios.

## 5. Validation

- [x] 5.1 Extend `validate-workflow-draft.py` to require the new artifacts for design-ready `M+` drafts.
- [x] 5.2 Validate all seven lens keys exist in `requirement-logic-map.json`.
- [x] 5.3 Validate no blocking logic gaps remain before S1 exits.
- [x] 5.4 Validate `REQ-*` entries link to process/evidence/acceptance refs according to complexity.
- [x] 5.5 Add a shallow-generic-question failure fixture.
- [x] 5.6 Add a STRIDE-style deep-logic success fixture.

## 6. Runtime And S5 Evidence

- [x] 6.1 Update deterministic fixture/mock runtime host outputs to include the new S1 artifacts.
- [x] 6.2 Extend S5 artifact checks so declared design refs or S1 evidence include the logic map when present.
- [x] 6.3 Ensure `state.json` artifact kind inference recognizes `question_backlog` and `requirement_logic_map` if they become stage outputs.

## 7. Dist And Verification

- [x] 7.1 Rebuild `dist/plugin`.
- [x] 7.2 Run `python3 .claude/scripts/validate-workflow.py`.
- [x] 7.3 Run `git diff --check`.
- [x] 7.4 Run targeted draft fixture validation.
- [x] 7.5 Run smoke matrix if runtime fixture outputs or state artifact kinds change.
- [x] 7.6 Update implementation audit when the capability is implemented.
