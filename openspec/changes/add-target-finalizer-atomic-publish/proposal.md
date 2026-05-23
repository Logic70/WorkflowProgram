# Add Target Runtime Finalizer Atomic Publish

## Why

Generated target workflows can execute under `target-workflow-runner.py`, but final reports, latest markers, doctor results, and manifests can still be written by separate scripts. That creates multi-owner final state: one file may say `PASS/COMPLETE` while another current-run evidence file says `FAIL`, or an old report can be reused by a new run.

## What Changes

- Add `target_publish_policy` to `workflow-spec.yaml` as the machine-readable contract for run-scoped outputs and atomic final publish.
- Add `target-runtime-finalizer.py` as the only component allowed to publish final target outputs and write latest marker / run manifest.
- Update generated target runtime wrappers and validators so target workflows can call the finalizer after managed graph execution and state validation.
- Update templates, docs, and tests to cover current-run publish and stale/mismatched report failure.

## Non-Goals

- Do not redesign WorkflowProgram's own S0-S6 runner.
- Do not force all legacy target specs to enable publish finalization immediately.
- Do not add domain-specific doctor rules; the finalizer only consumes declared `required_reports`.
