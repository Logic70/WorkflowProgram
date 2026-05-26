# Harden Target Runtime Bypass Control

## Why

Generated target workflows can still be weakened after runtime hardening if their public command remains prompt-heavy or if a later model/manual step forges final output state. The observed failure mode is `target-state.json=FAIL` while final `run_manifest.json=COMPLETE`, with stale or failing doctor/contract artifacts copied into the publish directory outside the finalizer.

## What Changes

- Require target workflow commands to be wrapper-only when `target_runtime_policy.mode=managed_runtime`.
- Add a target publish state doctor that validates final `manifest`, latest marker, target state, node results, artifact provenance, and required reports agree for the same run.
- Make finalizer-generated manifests identifiable as finalizer-owned and sealed with current-run evidence.
- Extend generated runtime validation and tests so prompt-heavy commands, forged `COMPLETE` manifests, stale latest markers, doctor failures, contract failures, and missing provenance cannot pass.

## Impact

- Existing generated workflows with prompt-heavy public commands must be regenerated or migrated to wrapper-only commands.
- Manual/current-agent execution remains supported, but final `PASS/COMPLETE` can only be produced by the finalizer.
- Target workflows that need rich user guidance must put it in skills/design docs, not in the public command body that can invite model bypass.
