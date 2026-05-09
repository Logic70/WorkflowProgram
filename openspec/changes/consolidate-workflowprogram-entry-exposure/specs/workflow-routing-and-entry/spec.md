## MODIFIED Requirements

### Requirement: Routing SHALL use a single natural-language entry and explicit leaf entries
The system SHALL treat `workflowprogram-orchestrate` as the only natural-language WorkflowProgram entry. The marketplace user-facing command recommendation SHALL be the namespaced orchestrator entry `/workflowprogram-cn:workflowprogram-orchestrate <request>`. Leaf capabilities `workflowprogram-develop`, `workflowprogram-audit`, `workflowprogram-iterate`, and `workflowprogram-validate` MUST remain one-to-one with supported intents, but documentation MUST present them as advanced explicit entries or internal route targets rather than the ordinary first path.

#### Scenario: Natural-language request is routed
- **WHEN** a user makes a natural-language WorkflowProgram request
- **THEN** the system routes through `workflowprogram-orchestrate`
- **AND** resolves exactly one supported intent before leaf execution

#### Scenario: Marketplace user invokes the primary command
- **WHEN** a user invokes `/workflowprogram-cn:workflowprogram-orchestrate <request>`
- **THEN** the command anchors execution to the orchestrator
- **AND** the orchestrator proceeds through deterministic route/context evidence and `workflow-entry.py run`

#### Scenario: Explicit leaf entry is used
- **WHEN** a user invokes an explicit `workflowprogram-*` leaf entry
- **THEN** the system uses the corresponding intent without reinterpreting it as another workflow intent
- **AND** records route evidence and route source in the run summary

### Requirement: Compatibility commands SHALL NOT create duplicate public skill surfaces
The system SHALL preserve legacy compatibility commands where needed, but marketplace distribution MUST NOT expose generated `command-*` wrapper skills unless they are explicitly allowlisted.

#### Scenario: Marketplace dist is generated
- **WHEN** `dist/plugin` is built
- **THEN** `dist/plugin/commands/*.md` may contain compatibility commands
- **AND** `dist/plugin/skills/command-*` is absent unless explicitly allowlisted

#### Scenario: Legacy command remains visible
- **WHEN** a legacy command such as `develop` is visible in Claude Code
- **THEN** its description and body identify it as compatibility-only
- **AND** point ordinary users to `/workflowprogram-cn:workflowprogram-orchestrate <request>`

### Requirement: Generated Markdown SHALL preserve discoverable frontmatter
Generated marketplace Markdown that contains YAML frontmatter SHALL keep that frontmatter at the start of the file so Claude Code can parse the intended description and invocation metadata.

#### Scenario: Skill Markdown is generated
- **WHEN** a `dist/plugin/skills/**/SKILL.md` file is generated with frontmatter
- **THEN** the first non-empty bytes of the file are `---`
- **AND** any auto-generated marker appears after the closing frontmatter or is omitted

#### Scenario: Command Markdown is generated
- **WHEN** a `dist/plugin/commands/*.md` file is generated with frontmatter
- **THEN** the first non-empty bytes of the file are `---`
- **AND** Claude Code does not display the auto-generated marker as the command description
