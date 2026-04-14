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

**Prerequisites**: Python 3.10+, `pyyaml`

```bash
git clone https://github.com/Logic70/WorkflowProgram-CN
cd WorkflowProgram-CN
pip install pyyaml
python tools/build_plugin.py
```

After the build finishes, `dist/plugin/` is the plugin directory you can load.

## Quick Start

Launch Claude Code in your target project and load the plugin:

```bash
cd your-project
claude --plugin-dir /path/to/WorkflowProgram-CN/dist/plugin
```

Then describe what you want in natural language:

```text
"Design a code review workflow for this project"
"Audit the workflow structure of this project"
"Validate the workflow assets in this project"
```

`workflowprogram-orchestrate` will route the request to the correct entry skill. You can also call the leaf entries directly:

| Entry | Purpose |
|------|------|
| `workflowprogram-develop` | Full design-to-delivery flow |
| `workflowprogram-audit` | Audit an existing workflow structure |
| `workflowprogram-validate` | Produce a validation verdict for workflow assets |
| `workflowprogram-iterate` | Turn lessons into improvement proposals |

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
| `S3` | Design and approval: produce `workflow-spec.yaml` |
| `S4` | Generate candidate assets and apply them in a managed way |
| `S5` | Validate the workflow and produce the verdict |
| `S6` | Feed lessons and constraint candidates back into the next run |

Different intents follow different stage paths: `develop` uses `S1-S6`, `audit` uses `S5-S6`, `validate` uses `S5`, and `iterate` uses `S6`.

### AI vs Python Responsibilities

- **AI**: understand user intent, refine design decisions, and generate candidate assets inside each stage.
- **Python**: `workflow-entry.py` drives the deterministic script chain, `workflow-runner.py` controls state transitions, and `workflow-s5-judge.py` produces the verdict.

Execution order is decided by programs, not by hoping the model remembers the next step.

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
│   ├── commands/                # Orchestration entry commands
│   ├── skills/                  # Skills, including product entry skills
│   ├── agents/                  # Expert agent definitions
│   ├── rules/constraints.md     # Long-lived constraints
│   └── scripts/                 # Python scripts and shared libraries
├── .claude-plugin/              # Plugin metadata
├── dist/plugin/                 # Build output loaded by --plugin-dir
├── docs/                        # Design docs, tutorials, implementation plans
├── tests/                       # Fixtures, expectations, transcripts
└── tools/                       # Build scripts, smoke tools, mock hosts
```

## Development And Validation

```bash
# Repository-level validation
python .claude/scripts/validate-workflow.py

# Smoke test a single fixture
python tools/runtime_smoke.py --fixture empty-project --runtime-provider fixture_host

# Run the smoke matrix
python tools/runtime_smoke_matrix.py

# Rebuild the plugin
python tools/build_plugin.py
```

## Tutorials

- [HTML tutorial (Chinese)](docs/workflowprogram-101-html/index.html)
- [HTML tutorial (English)](docs/workflowprogram-101-html/index.en.html)
- [Single-page overview (English)](docs/workflowprogram-101.en.md)
- [Chapter guide (Chinese)](docs/workflowprogram-101/index.md)
- [Chapter guide (English)](docs/workflowprogram-101-en/index.md)

## License

MIT
