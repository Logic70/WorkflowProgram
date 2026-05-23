# target-executor-provider Specification

## ADDED Requirements

### Requirement: Target executor provider policy

Generated target workflow specs SHALL support `target_executor_policy`.

The policy SHALL validate:

- `default_provider` is one of `fixture_host`, `command_adapter`, `current_agent`, `manual`
- `allowed_providers` is a non-empty list of the same provider enum
- `default_provider` is listed in `allowed_providers`
- `evidence_dir` is a safe relative path under `outputs/stages`
- `unsupported_provider_verdict` is `FAIL`

#### Scenario: unsupported provider is declared

- Given a spec declares `target_executor_policy.default_provider=claude_cli`
- When `validate-workflow-spec.py` runs
- Then validation fails.

### Requirement: Target runtime does not hardcode Claude CLI execution

Generated target runtime wrappers and the shared target runner SHALL NOT invoke `claude -p` or `claude_cli` as an implicit executor.

The compatibility flag `--claude-bin` MAY exist as a deprecated no-op, but it SHALL NOT be forwarded into an executable node command.

#### Scenario: generated runtime is validated

- Given generated target runtime assets
- When `validate-generated-runtime.py` runs
- Then entry and runner wrappers contain no hardcoded Claude CLI executor markers.

### Requirement: Manual and current-agent providers require executor evidence

When the selected executor provider is `current_agent` or `manual`, every executed node SHALL have an executor evidence file under the configured evidence directory.

Evidence SHALL include node id, provider, status, operator, timestamps, input refs, output refs, and output paths.

#### Scenario: evidence is missing

- Given a target workflow defaults to `current_agent`
- And no executor evidence exists for the first node
- When `target-workflow-runner.py` runs
- Then the run returns `FAIL`
- And no target output is published.

### Requirement: Manual and current-agent providers cannot directly PASS

When all manual/current-agent node evidence passes, the runner SHALL return `BLOCKED` with `manual_finalizer_required=true` rather than `PASS`.

The finalizer SHALL promote the state to `PASS` only after validating state, node results, artifact provenance, executor evidence, and required reports.

#### Scenario: evidence passes and finalizer verifies

- Given every node has valid current-agent evidence
- When the target runner runs
- Then `target-state.json.status` is `BLOCKED`
- When the finalizer runs and all required reports pass
- Then `target-state.json.status` becomes `PASS`
- And current-run outputs are published atomically.

### Requirement: Contract or doctor failures block publish

If any required report, doctor, contract, provenance, or finalizer check fails, the finalizer SHALL write `target-state.status=FAIL` and SHALL NOT publish final artifacts.

#### Scenario: required doctor report fails

- Given target runtime node execution succeeded
- And a required doctor report has status `FAIL`
- When the finalizer runs
- Then finalizer returns `FAIL`
- And no manifest or latest marker is published.

### Requirement: Wrapper-only commands cannot bypass target runtime

For managed target runtimes, the registered main command SHALL invoke `.workflowprogram/runtime/workflow-entry.py` and SHALL NOT contain direct report-writing or prompt-heavy node execution instructions.

#### Scenario: command directly writes report output

- Given a managed target workflow main command references direct report output such as `outputs/stride-audit`
- When generated runtime validation runs
- Then validation fails as a wrapper-only violation.
