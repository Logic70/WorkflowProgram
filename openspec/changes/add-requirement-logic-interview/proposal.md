# Add Requirement Logic Interview

## Why

`S1` already requires multiple clarification rounds, structured clarification artifacts, internal challenge roles, and readback confirmation. That fixed the basic handoff problem, but the current clarification behavior can still be too broad.

The failure mode is not "the model asks no questions". The failure mode is that it asks generic questions:

- "What are the edge cases?"
- "What are the inputs and outputs?"
- "What constraints should we consider?"

Those questions produce detail, but they do not force the model to understand the user's task logic. Complex workflows such as STRIDE security testing, reverse engineering, migration repair, or TDD implementation need the clarification lead to uncover:

- what domain object is being transformed
- how the process should reason step by step
- where decisions happen
- what evidence makes an output trustworthy
- how acceptance tests should prove the workflow behavior
- which uncertainties block design versus which can become explicit assumptions

## What Changes

Add a `requirement-logic-interview` layer inside `S1`.

This does not replace the existing deep clarification package. It adds a structured interview strategy and a machine-readable requirement logic map that later stages can consume.

New or modified S1 outputs:

- `outputs/stages/question-backlog.json`
- `outputs/stages/requirement-logic-map.json`
- existing `clarification-record.json` gains links to logic lenses and question rounds
- existing `clarification-handoff.json` includes logic-map references for `S2/S3`
- existing `s1-requirements.yaml` links each `REQ-*` to process, decision, evidence, and acceptance nodes when applicable

## Capabilities

### New Capability

- `workflow-requirement-logic-interview`: Defines a layered, adaptive S1 interview method that turns raw user intent into a verifiable task logic model.

### Modified Capabilities

- `workflow-deep-requirement-clarification`: Keeps its role topology and artifacts, but the lead now uses a logic-lens question strategy.
- `workflow-design-source-lineage`: Uses `requirement-logic-map.json` as an earlier design-source input for S2/S3 and S5 traceability.

## Goals

- Make S1 questions narrow, sequential, and tied to requirement logic.
- Prevent "wide but shallow" clarification from passing as design-ready.
- Keep the user-facing experience coherent: one lead, no parallel agent voices.
- Preserve lightweight handling for simple workflows.
- Give S2/S3 a deterministic model of object/process/decision/evidence/acceptance logic.

## Non-Goals

- Do not make every request go through a heavyweight business-analysis workshop.
- Do not replace OpenSpec, `workflow-spec.md`, or `s1-requirements.yaml`.
- Do not force domain-specific schemas for every possible workflow type in V1.
- Do not require the user to answer a long questionnaire before any design can proceed.
- Do not let internal challenge roles speak directly to the user.

## Impact

- Updates active S1 design docs and `workflowprogram-develop` guidance.
- Extends clarification generation/review utilities to emit logic-map artifacts.
- Extends `validate-workflow-draft.py` so it can reject shallow or generic clarification when logic depth is required.
- Adds draft fixtures proving shallow-generic clarification fails and logic-driven clarification passes.
