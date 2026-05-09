## 1. Design And Planning

- [x] 1.1 Audit current command, skill, dist, and docs exposure.
- [x] 1.2 Define the final entry taxonomy: primary command, natural-language skill, leaf skills, compatibility commands, internal support.
- [x] 1.3 Define frontmatter and command-wrapper distribution rules.
- [x] 1.4 Define validation and documentation acceptance criteria.
- [x] 1.5 Run repeated design self-review until no new issues are found.

## 2. Build Output Changes

- [x] 2.1 Update `tools/build_plugin.py` so generated Markdown frontmatter remains at the first line when present.
- [x] 2.2 Stop generating `dist/plugin/skills/command-*` wrappers by default, or introduce an explicit empty allowlist.
- [x] 2.3 Rebuild `dist/plugin/` and verify `build-manifest.json` reflects removed wrapper assets.
- [x] 2.4 Ensure generated command files keep valid command frontmatter and useful descriptions.

## 3. Command And Skill Guidance

- [x] 3.1 Update `workflowprogram-orchestrate` so it clearly states that public execution must enter `workflow-entry.py run`.
- [x] 3.2 Update legacy command docs (`develop`, `evolve-workflow`, `iterate-workflow`, etc.) to describe themselves as compatibility dispatchers and point to `/workflowprogram-cn:workflowprogram-orchestrate`.
- [x] 3.3 Reduce duplicated lifecycle instructions in compatibility command docs where practical, or explicitly mark copied sections as reference-only.
- [x] 3.4 Update `workflowprogram-develop/audit/iterate/validate` wording so leaf skills are advanced explicit entries or route targets, not the ordinary first path.

## 4. Documentation Updates

- [x] 4.1 Update `README.md` and `README.en.md` to recommend `/workflowprogram-cn:workflowprogram-orchestrate <request>`.
- [x] 4.2 Update `.claude-plugin/README.md` with namespaced marketplace invocation and the refined entry taxonomy.
- [x] 4.3 Update HighLevel and LowLevel design docs to align with the primary orchestrator entry and compatibility command policy.
- [x] 4.4 Update tutorial docs that currently show `/workflowprogram-develop` as the ordinary starting point.

## 5. Validation And Tests

- [x] 5.1 Extend `.claude/scripts/validate-workflow.py` to reject frontmatter-blocking generated comments.
- [x] 5.2 Extend validation to reject unapproved `dist/plugin/skills/command-*` wrappers.
- [x] 5.3 Extend validation to check active docs recommend the namespaced orchestrator command.
- [x] 5.4 Add or update bootstrap/plugin exposure tests to catch misleading descriptions such as `AUTO-GENERATED`.
- [x] 5.5 Run `python3 .claude/scripts/validate-workflow.py`.
- [x] 5.6 Run relevant runtime smoke matrix or targeted plugin bootstrap tests.
- [x] 5.7 Run `openspec validate consolidate-workflowprogram-entry-exposure --strict`.

## 6. Release Follow-up

- [ ] 6.1 Bump plugin version after implementation.
- [ ] 6.2 Rebuild dist and verify installed marketplace cache shows the corrected entry list/descriptions.
- [ ] 6.3 Commit with a message that names entry exposure consolidation.
- [ ] 6.4 Push to GitHub when tests pass.
