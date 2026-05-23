# Tasks

- [x] Add `target_executor_policy` schema validation and fixture/template coverage.
- [x] Remove hardcoded Claude CLI execution from `target-workflow-runner.py`.
- [x] Update generated target runtime wrappers to stop forwarding `--claude-bin`.
- [x] Add manual/current-agent executor evidence validation in runner, state validator, and finalizer.
- [x] Ensure unsupported providers FAIL and do not publish.
- [x] Extend generated-runtime validation for executor policy and wrapper-only command bypass markers.
- [x] Update README, HTML guide, high-level/low-level design docs, and develop skill instructions.
- [x] Add unit tests for unsupported provider, missing evidence, finalizer promotion, and doctor/contract failure.
- [x] Rebuild plugin dist and run full validation.
