# Tasks

## 1. Design Truth

- [x] 1.1 Update HighLevel design to separate design source from runtime projection.
- [x] 1.2 Update LowLevel design to define S1/S2/S3 design-source artifacts, node-design escalation, and node-vs-agent policy.
- [x] 1.3 Update consistency/status docs with the new lineage model and non-goals.

## 2. Product Guidance And Templates

- [x] 2.1 Update `workflowprogram-develop` guidance so S1-S3 produce design source before YAML finalization.
- [x] 2.2 Update `workflow-spec-support` templates with `design_refs` and stage IO.
- [x] 2.3 Keep `workflow-spec.yaml` as machine projection and avoid embedding full design prose.

## 3. Schema And State

- [x] 3.1 Add `design_refs` validation to `validate-workflow-spec.py`.
- [x] 3.2 Add design-source artifact kinds to `validate-run-state.py`.
- [x] 3.3 Add design-source artifact kinds and path inference to `workflow-runner.py`.

## 4. Deterministic Evidence

- [x] 4.1 Add minimal design-source artifacts to deterministic fixture host runs.
- [x] 4.2 Add minimal design-source artifacts to command-adapter mock runs.
- [x] 4.3 Add `design_refs` and stage outputs to the minimal spec fixture.

## 5. S5 Verification

- [x] 5.1 Check that `design_refs` paths exist when declared.
- [x] 5.2 Check `node_designs` keys reference declared target graph nodes.
- [x] 5.3 Check requirement ids from `s1-requirements.yaml` appear in `traceability-matrix.json`.

## 6. Verification

- [x] 6.1 Rebuild plugin distribution.
- [x] 6.2 Run spec validation.
- [x] 6.3 Run repository validation.
- [x] 6.4 Run runtime smoke matrix.
- [x] 6.5 Run OpenSpec validation.
