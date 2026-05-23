# Proposal: Target Executor Provider Evidence

## Why

Generated target runtimes currently assume a callable Claude CLI executor path. That is invalid when ClaudeCode is configured to use a third-party API model, or when node work is performed by the current ClaudeCode session or a human operator.

The generated runtime must separate workflow control from executor implementation. If a provider cannot automatically execute nodes, the runtime must require structured evidence and finalizer verification before any PASS or publish.

## What Changes

- Add `target_executor_policy` to workflow specs and templates.
- Remove hardcoded `claude -p` / `claude_cli` execution from generated target runtime wrappers and shared target runner.
- Support automatic providers `fixture_host` and `command_adapter`.
- Support non-automatic `current_agent` and `manual` providers via per-node executor evidence.
- Require finalizer promotion from manual/current-agent `BLOCKED` to `PASS`.
- Ensure unsupported executor providers fail and never publish.
- Extend docs, generated runtime validation, and unit tests.

## Impact

- Existing deterministic tests continue to use `fixture_host`.
- New generated target workflows default to `current_agent` evidence mode, which matches ClaudeCode current-session usage without assuming local CLI executability.
- Target slash commands remain wrapper-only; direct report writing outside runtime evidence cannot produce a clean PASS.
