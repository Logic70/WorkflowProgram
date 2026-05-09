## Design

### 1. Entry Taxonomy

WorkflowProgram SHALL distinguish three entry categories:

| Category | Public? | Purpose |
| --- | --- | --- |
| Primary explicit command | Yes | `/workflowprogram-cn:workflowprogram-orchestrate <request>`; stable user command for all workflow requests. |
| Natural-language skill | Yes | `workflowprogram-orchestrate`; semantic router used when the user does not type a slash command. |
| Leaf workflow skills | Advanced/internal | `workflowprogram-develop/audit/iterate/validate`; one-to-one intent handlers selected by routing or explicit advanced use. |
| Legacy compatibility commands | Compatibility only | Existing `develop`, `evolve-workflow`, `iterate-workflow`, etc.; retained but not recommended and not duplicated as command wrapper skills. |
| Internal support skills | No | `workflow-spec-support`, `validate-file`, generated templates, and low-level checklists. |

The primary entry is the orchestrator, not a new workflow lifecycle. It resolves intent and context, then hands off to the same deterministic control plane that already handles `develop`, change policy, managed apply, runner execution, and S5 evidence.

### 2. Command Versus Skill Responsibility

Commands are stable trigger anchors. Skills are semantic and execution guidance assets.

Public commands SHALL be thin dispatchers. They may explain how to invoke the control plane, but MUST NOT duplicate the full S1-S6 lifecycle in a way that can drift from `workflowprogram-develop` and `workflow-entry.py`.

`workflowprogram-orchestrate` SHALL remain the only natural-language WorkflowProgram entry. It MUST:

- resolve `TARGET_ROOT`
- call or instruct deterministic execution through `workflow-entry.py run`
- preserve `route-intent.json` and `change-context.json`
- route modification requests to `workflowprogram-develop` with change-policy evidence when required

Leaf skills MAY remain discoverable as advanced explicit entries, but docs SHALL not present them as the ordinary first choice.

### 3. Marketplace Frontmatter Rules

Generated Markdown files under `dist/plugin/commands/**` and `dist/plugin/skills/**/SKILL.md` MUST keep YAML frontmatter as the first bytes of the file when frontmatter exists.

The auto-generated marker SHALL be placed after frontmatter, or omitted for files where the marker would break Claude Code discovery. This is required because Claude Code currently displays the first parseable description; when the comment precedes frontmatter the UI can show the marker instead of the actual entry description.

### 4. Command Wrapper Policy

The build process currently generates `dist/plugin/skills/command-*` wrappers for every source command. That creates duplicate public-looking entries such as `command-develop` and weakens the entry taxonomy.

The new policy is:

- Do not generate `skills/command-*` wrappers for marketplace distribution, unless a future command explicitly opts in.
- Legacy commands remain as `dist/plugin/commands/*.md`.
- Any compatibility command that stays visible must be described as compatibility-only and should point users to `/workflowprogram-cn:workflowprogram-orchestrate`.

### 5. Documentation Contract

Active user-facing docs SHALL use the namespaced marketplace command form:

```text
/workflowprogram-cn:workflowprogram-orchestrate <request>
```

Docs MAY mention natural-language routing, but they MUST NOT tell users to handwrite `Skill(workflowprogram-orchestrate)`.

Docs MAY mention leaf entries as advanced explicit intents, but the first recommended path must be the orchestrator.

### 6. Validation Contract

Repository validation SHALL fail if:

- generated marketplace Markdown places an auto-generated comment before frontmatter
- `dist/plugin/skills/command-*` wrappers are present without an explicit allowlist
- active docs recommend non-namespaced `/workflowprogram-orchestrate` as the primary marketplace invocation
- active docs present `workflowprogram-develop` as the ordinary first choice instead of the orchestrator
- primary WorkflowProgram entry docs do not mention `workflow-entry.py run` or deterministic control-plane execution

### 7. Iterative Design Audit

Before implementation starts, the change must pass repeated logic review over these questions:

1. Does the entry taxonomy have a single ordinary user path?
2. Does any public command duplicate the leaf workflow implementation?
3. Does the generated dist layout match Claude Code discovery behavior?
4. Does the change preserve existing `develop` change-policy flow?
5. Do docs, validator, and build output enforce the same policy?

The audit converges when a complete pass finds no new problems.

## Decisions

- No new lifecycle entry such as `workflowprogram-change`.
- No new non-namespaced `/workflowprogram` command for this pass.
- Keep `workflowprogram-orchestrate` as the product-level router.
- Keep legacy commands for compatibility, but remove command wrapper skill duplication.
- Treat `workflowprogram-develop` as an advanced explicit leaf, not the recommended user entry.
