## Iterative Design Review

### Review Scope

This review checks whether the proposed entry exposure consolidation introduces contradictions with current WorkflowProgram behavior, change-policy execution, marketplace installation, or Claude Code discovery.

### Round 1: Entry Surface

Findings:

- The current installed plugin exposes multiple similar entries: `develop`, `command-develop`, `workflowprogram-develop`, and `workflowprogram-orchestrate`.
- This conflicts with the desired user model of one ordinary entry plus advanced leaf entries.

Resolution:

- The design defines `/workflowprogram-cn:workflowprogram-orchestrate <request>` as the ordinary explicit command.
- `workflowprogram-orchestrate` remains the only natural-language entry.
- Leaf skills are retained as advanced explicit entries and route targets.

Status: closed.

### Round 2: Command / Skill Responsibility

Findings:

- Existing compatibility command docs duplicate lifecycle instructions.
- Generated `command-*` wrapper skills make commands look like additional skills and can be surfaced to users.

Resolution:

- The design requires public commands to act as stable anchors and not duplicate independent lifecycle behavior.
- The implementation plan removes generated `skills/command-*` wrappers by default.
- Legacy commands remain compatibility-only.

Status: closed.

### Round 3: Marketplace Discovery

Findings:

- Generated dist Markdown currently places `<!-- AUTO-GENERATED ... -->` before YAML frontmatter.
- Claude Code can display that marker as the command/skill description.

Resolution:

- The design requires frontmatter to be the first bytes of generated Markdown when frontmatter exists.
- The auto-generated marker must move after frontmatter or be omitted.
- Validation will reject frontmatter-blocking comments.

Status: closed.

### Round 4: Change-Policy Compatibility

Findings:

- The proposal must not create a new modification lifecycle or bypass `workflowprogram-develop`.
- Existing controlled evolution relies on `route-intent.json`, `change-context.json`, `change-policy.json`, `impact-analysis.json`, and `workflow-entry.py run`.

Resolution:

- The design explicitly does not add `workflowprogram-change`.
- Modification requests still route to `workflowprogram-develop`.
- Public entries must converge on `workflow-entry.py run`, preserving existing change-policy gates.

Status: closed.

### Round 5: Documentation Consistency

Findings:

- Active docs currently mention non-namespaced `/workflowprogram-orchestrate`.
- Some tutorials present `/workflowprogram-develop` as the ordinary starting point.

Resolution:

- The implementation plan updates README, plugin README, HighLevel, LowLevel, and tutorials to recommend `/workflowprogram-cn:workflowprogram-orchestrate <request>`.
- Leaf entries may still be documented as advanced explicit entries.

Status: closed.

### Round 6: Residual Conflict Scan

Checks:

- Single ordinary user path exists.
- No new non-namespaced `/workflowprogram` command is proposed.
- No new `workflowprogram-change` lifecycle is proposed.
- Frontmatter rule is explicit.
- Command wrapper removal is explicit.
- `workflow-entry.py run` remains the deterministic control-plane path.
- Existing change-policy flow remains in `develop`.

Result:

No new design problems found.

### Round 7: Pre-Implementation Flow Review

Checks:

- `workflow-entry.py` already maps `workflowprogram-orchestrate` through route evidence and maps modification requests to `workflowprogram-develop`.
- Existing change-policy validation remains inside the develop branch and is not replaced by this entry exposure change.
- The implementation must update validator expectations before rebuilding dist, otherwise the old command-wrapper requirement will block the new build.

Result:

No new blocking design problems found. Implementation must change build and validation together.

### Round 8: Verification Closure Review

Checks:

- Frontmatter repair can be verified statically by checking generated command / skill files start with `---` when they have frontmatter.
- Command wrapper removal can be verified statically by asserting `dist/plugin/skills/command-*` is absent.
- Documentation drift can be verified by searching active user docs for the namespaced orchestrator command.
- Runtime change-policy behavior is preserved because public entries still converge on `workflow-entry.py run`.

Result:

No new blocking design problems found. Implementation can begin.
