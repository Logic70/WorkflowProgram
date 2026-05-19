# WorkflowProgram-CN

[中文](README.md) | [English](README.en.md)

A **meta workflow engine** for Claude Code workspaces. It does not ship business code. It helps you turn workflows into deliverable, verifiable, and iterable products.

## What Problems It Solves

Most Claude Code workflows start as "one `SKILL.md` plus a few agents and some manual `settings.json` edits". That is enough to get something running, but it quickly breaks down:

- Documentation and runtime behavior drift apart
- Step order depends on model memory
- Target projects get overwritten directly and conflicts are hard to recover
- Failures are hard to localize and lack structured evidence
- Lessons stay in chat history and never influence the next run

WorkflowProgram addresses these issues with four layers: **truth source**, **control plane**, **validation layer**, and **feedback loop**.

## Installation

**Prerequisite**: a host `python3` interpreter with Python 3.10+ is available.

The primary installation path is the Claude Code marketplace:

```bash
claude plugin marketplace add Logic70/WorkflowProgram
claude plugin install workflowprogram-cn@logic70-plugins
```

If you are already inside the Claude Code interactive UI, you can run:

```text
/plugin marketplace add Logic70/WorkflowProgram
/plugin install workflowprogram-cn@logic70-plugins
/reload-plugins
```

After installation:

1. Restart `claude`, or run `/reload-plugins` in the current session
2. On first session start, the plugin bootstraps its private Python dependency layer into `${CLAUDE_PLUGIN_DATA}/python/site-packages`
3. For minimal troubleshooting, run `workflowprogram-doctor`
4. To clean plugin Python caches, test artifacts, or old target workflow runs, run `workflowprogram-clean`; it is dry-run by default and requires `--apply` to delete files

Troubleshooting:

- If you see `Unknown skill: workflowprogram-orchestrate`, the current Claude session usually has not reloaded the plugin. Run `/reload-plugins` or restart `claude`, then use `/workflowprogram-cn:workflowprogram-orchestrate ...`; do not ask the model to hand-write `Skill(workflowprogram-orchestrate)`.
- If you see `bin/workflowprogram-python: Permission denied`, the installed launcher lost its executable bit. Update/reinstall from the latest marketplace payload. As a temporary local fix, run `chmod +x ~/.claude/plugins/cache/logic70-plugins/workflowprogram-cn/0.1.7/bin/workflowprogram-*`.

Source builds of `dist/plugin/` remain useful for repository development and debugging, but they are no longer the primary end-user install model.

## Quick Start

Launch Claude Code in your target project:

```bash
cd your-project
claude
```

Then use the primary entry, or describe what you want in natural language:

```text
/workflowprogram-cn:workflowprogram-orchestrate Design a code review workflow for this project
```

Natural-language examples:

```text
"Design a code review workflow for this project"
"Audit the workflow structure of this project"
"Validate the workflow assets in this project"
"Publish this completed workflow as a Claude Code plugin"
```

`workflowprogram-orchestrate` will route the request to the correct entry skill. The leaf entries below are advanced explicit intents or debugging targets; ordinary usage should start from orchestrate:

| Entry | Purpose |
|------|------|
| `workflowprogram-develop` | Full design-to-delivery flow |
| `workflowprogram-audit` | Audit an existing workflow structure |
| `workflowprogram-validate` | Produce a validation verdict for workflow assets |
| `workflowprogram-iterate` | Turn lessons into improvement proposals |
| `workflowprogram-publish` | Publish a completed target workflow as a marketplace plugin |

## Core Concepts

### Three Roots

| Root | Role | Meaning |
|------|------|------|
| `PLUGIN_ROOT` | Capability source | WorkflowProgram skills, scripts, and templates (`dist/plugin/`). Read-only. |
| `TARGET_ROOT` | Delivery target | The user project. Final `.claude/` assets are written here through managed apply only. |
| `RUN_ROOT` | Runtime evidence | Isolated per-run workspace at `TARGET_ROOT/.workflowprogram/runs/<run-id>/`. |

### Stage Model `S0..S6`

| Stage | Responsibility |
|------|------|
| `S0` | Route: identify intent and prepare the target environment |
| `S1` | Clarify requirements through multi-turn dialogue |
| `S2` | Explore project context and reusable assets |
| `S3` | Design, review, and approval: produce `workflow-spec.yaml`, then pass the internal `workflow-design-reviewer` gate |
| `S4` | Generate candidate assets and apply them in a managed way |
| `S5` | Validate the workflow and produce the verdict |
| `S6` | Feed lessons and constraint candidates back into the next run |

Every request passes through `S0` first. `workflow-spec.yaml.intent_flows` then defines the logical requirements for `S1-S6`. In the default template, `develop` uses `S1-S6`, `audit` uses `S5-S6`, `validate` uses `S5` with optional `S6`, and `iterate` uses `S6` with optional `S5`.

### S1 Requirement Logic Interview

For `develop`, S1 is no longer a generic input/output clarification step. It now asks through seven logic lenses:

- `purpose`: why the workflow exists and what success looks like
- `object_model`: what the workflow reads, transforms, classifies, or produces
- `process_model`: which business steps or target workflow nodes are needed
- `decision_model`: which branches, strategies, thresholds, or approvals change execution
- `evidence_model`: what evidence makes intermediate and final outputs trustworthy
- `acceptance_model`: which positive, negative, and ambiguous scenarios prove behavior
- `boundary_model`: when the workflow must stop, degrade, defer, or stay out of scope

S1 emits `question-backlog.json` and `requirement-logic-map.json`. The backlog records why each question changes design; the logic map links `REQ-*` items to process/evidence/acceptance elements. For `L/XL` requests, broad prompts such as "what edge cases should we consider?" are rejected by `validate-workflow-draft.py` and cannot be treated as design-ready.

### S3 Design Review Gate

After S3 design sources and `workflow-spec.yaml` are ready, `develop` generates `design-review-packet.json` and asks the internal `workflow-design-reviewer` to review goal fidelity, requirement coverage, flow closure, YAML projection, evidence quality, change impact, and runtime compatibility from a fresh context. S4 managed writes continue only when both `closure.json` and `gate-validation.json` pass; unresolved blockers stop the run as `design_review_unresolved`.

### AI vs Python Responsibilities

- **AI**: understand user intent, refine design decisions, and generate candidate assets inside each stage.
- **Python**: `workflow-entry.py` drives the deterministic script chain, including spec/view/lowlevel/runtime rendering, managed apply, capability probing, and environment remediation; `workflow-runner.py` controls state transitions; `workflow-s5-judge.py` produces the verdict.

Execution order is decided by programs, not by hoping the model remembers the next step.

### Target Runtime And Optional Capability Layers

- A successful develop flow persists not only `.claude/` assets, but also `TARGET_ROOT/.workflowprogram/design/{workflow-spec.yaml,workflow-view.md,workflow-lowlevel.md}`, plus the target design-source archive under `TARGET_ROOT/.workflowprogram/design/source/**`.
- Target design source uses `target-design-overview.md`, `target-design-detail.md`, `target-acceptance-tests.yaml`, and `target-traceability-matrix.json`; `workflow-view.md` / `workflow-lowlevel.md` are YAML-derived views, not new design truth.
- The target project also receives its own deterministic runtime wrapper at `TARGET_ROOT/.workflowprogram/runtime/{workflow-entry.py,workflow-runner.py,validate-run-state.py,runtime-manifest.json}`.
- If a workflow declares `capability_discovery`, the entry path first generates candidate `skill / MCP / CLI` recommendations plus manual guidance.
- If a workflow declares `host_capabilities`, both the entry path and S5 consume `host-capability-report.json`, `environment-remediation-report.json`, and `environment-remediation-guide.md`.
- If a workflow declares `agent_team_contract`, S5 also validates structured Team evidence such as `team-plan.json`, `team-results.json`, and `team-join-summary.json`.
- A target workflow that fully passed `workflowprogram-develop` can enter the independent publish lifecycle. `/workflowprogram-cn:workflowprogram-publish` checks develop/S5/design-review/managed/target-design-source evidence, stages a Claude Code marketplace plugin package, and uses the user's GitHub account for the publish plan or approved execution.

### Before Publishing

Before calling `/workflowprogram-cn:workflowprogram-publish`, the user should have:

1. A target workflow that fully completed `workflowprogram-develop`, with still-valid S5, design-review, and managed evidence.
2. A chosen `plugin-id`, display name, and version.
3. An existing GitHub repository dedicated to publishing that target workflow. The current flow does not create a new repository automatically.
4. `gh` installed and authenticated locally, with push access to the target repository.
5. For real GitHub writes instead of `--dry-run`, a local checkout of that publishing repository for `--repo-path`.
6. To reuse an existing marketplace instead of generating a standalone marketplace, that checkout must already contain `.claude-plugin/marketplace.json`, and the publish command must use `--repo-mode existing_marketplace`.

Minimal command:

```text
/workflowprogram-cn:workflowprogram-publish <target-root> --plugin-id <id> --repo <owner/repo-or-url>
```

Existing marketplace example:

```text
/workflowprogram-cn:workflowprogram-publish <target-root> --plugin-id <id> --repo <owner/repo-or-url> --repo-mode existing_marketplace --repo-path <marketplace-checkout>
```

This mode plans the plugin payload under `plugins/<plugin-id>/` and merges the existing marketplace manifest. Updating an existing same-name plugin still requires explicit update intent and a version increase.

Real GitHub writes still require explicit approval. If the repository, auth, permissions, or local checkout are missing, the publish flow returns `BLOCKED` with remediation guidance instead of attempting a partial release.

### Managed Write Flow

AI never writes directly into the target project. Instead it:

1. Writes candidate assets to `RUN_ROOT/outputs/candidate/`
2. Uses `managed-assets.py plan` to build a change plan
3. Uses `managed-assets.py apply-staged` to apply only safe changes
4. Preserves conflict copies instead of silently overwriting user files

### Three Validation Layers

| Layer | Responsibility | Key Outputs |
|----|------|---------|
| Runner | Hard control-plane constraints such as boundaries, evidence, and enums | `state.json`, `events.jsonl` |
| S5 Judge | Workflow-level verdict based on `test_contract` | `s5-validation-summary.json`, `validation-runtime-report.md` |
| Runtime Smoke | End-to-end dynamic harness | `tools/runtime_smoke.py` |

### Feedback Loop

- `lessons.md`: append-only log for failures, conflicts, and candidate constraints
- `constraints.md`: long-lived ALWAYS/NEVER rules loaded by new sessions
- `s6-lessons-delta.md`: per-run lessons delta validated by `validate-lessons-delta.py`

## Repository Layout

```text
WorkflowProgram-CN/
├── CLAUDE.md                    # Collaboration and runtime conventions
├── README.md
├── README.en.md
├── lessons.md                   # Lessons log
├── .claude/
│   ├── settings.json            # Commands and skills registry
│   ├── commands/                # Source command entries
│   ├── skills/                  # Skills and templates
│   ├── agents/                  # Expert agent definitions
│   ├── rules/constraints.md     # Long-lived constraints
│   └── scripts/                 # Deterministic script chain, validators, and shared libraries
├── .claude-plugin/              # Plugin metadata and plugin-root source assets
├── dist/plugin/                 # Build output and canonical marketplace payload
├── docs/                        # Design docs, tutorials, implementation plans
├── tests/                       # Fixtures, expectations, transcripts
└── tools/                       # Build scripts, smoke tools, mock hosts
```

## Development And Validation

```bash
# Repository-level validation
python .claude/scripts/validate-workflow.py

# Spec / lowlevel / generated runtime validation
python .claude/scripts/validate-workflow-spec.py --spec <workflow-spec.yaml>
python .claude/scripts/validate-workflow-lowlevel.py --spec <workflow-spec.yaml> --lowlevel <workflow-lowlevel.md>
python .claude/scripts/validate-generated-runtime.py --spec <workflow-spec.yaml> --runtime-root <target-runtime-root>

# Smoke test a single fixture
python tools/runtime_smoke.py --fixture empty-project --runtime-provider fixture_host

# Run the smoke matrix, including capability / host / team cases
python tools/runtime_smoke_matrix.py

# Cleanup maintenance regression
python tools/test_clean_workflowprogram.py

# Rebuild the plugin
python tools/build_plugin.py
```

## WorkflowProgram 101

Use these entry points when you want the tutorial rather than the reference README:

- [WorkflowProgram 101 HTML tutorial (Chinese)](docs/workflowprogram-101-html/index.html)
- [WorkflowProgram 101 HTML tutorial (English)](docs/workflowprogram-101-html/index.en.html)
- [WorkflowProgram 101 single-page overview (English)](docs/workflowprogram-101.en.md)
- [WorkflowProgram 101 chapter guide (Chinese)](docs/workflowprogram-101/index.md)
- [WorkflowProgram 101 chapter guide (English)](docs/workflowprogram-101-en/index.md)

## License

MIT
