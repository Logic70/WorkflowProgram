## Summary

Consolidate WorkflowProgram's user-facing entry surface so explicit command usage, natural-language skill routing, and deterministic control-plane execution all converge on the same path.

The current installed plugin exposes too many similar entries (`develop`, `command-develop`, `workflowprogram-develop`, `workflowprogram-orchestrate`), and generated marketplace assets place the auto-generated comment before Markdown frontmatter. In Claude Code this causes descriptions to render as `<!-- AUTO-GENERATED ... -->` and increases the chance that the model falls back to reading prompt files instead of entering the controlled runtime path.

## Motivation

The target behavior is:

- Users can explicitly invoke one stable, namespaced slash entry: `/workflowprogram-cn:workflowprogram-orchestrate <request>`.
- Natural-language requests still match `workflowprogram-orchestrate` through its skill description.
- Leaf entries (`workflowprogram-develop/audit/iterate/validate`) remain available only as advanced explicit intents or internal route targets, not as the main recommendation.
- Legacy commands such as `develop` remain compatibility-only and must not create duplicate public skill-like surfaces such as `command-develop`.
- Every public WorkflowProgram entry must drive the deterministic `workflow-entry.py run` chain rather than relying on long prompt instructions.

## Scope

This change affects:

- marketplace dist generation in `tools/build_plugin.py`
- repository validation in `.claude/scripts/validate-workflow.py`
- source command/skill guidance under `.claude/`
- active product docs and installation docs
- runtime smoke / bootstrap checks that assert plugin exposure and frontmatter quality

This change does not introduce a new lifecycle intent and does not replace `workflowprogram-develop`. Existing change-policy behavior remains inside `develop`.

## Out of Scope

- Replacing Claude Code plugin namespace behavior.
- Removing backwards-compatible legacy commands in the first implementation pass.
- Changing the target workflow S1-S6 lifecycle or generated workflow runtime contract.
