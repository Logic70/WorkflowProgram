## ADDED Requirements

### Requirement: Routing SHALL use a single natural-language entry and explicit leaf entries
The system SHALL treat `workflowprogram-orchestrate` as the only natural-language WorkflowProgram entry. Leaf capabilities `workflowprogram-develop`, `workflowprogram-audit`, `workflowprogram-iterate`, and `workflowprogram-validate` MUST remain explicit entries and MUST map one-to-one to supported intents.

#### Scenario: Natural-language request is routed
- **WHEN** a user makes a natural-language WorkflowProgram request
- **THEN** the system routes through `workflowprogram-orchestrate` and resolves exactly one supported intent

#### Scenario: Explicit slash entry is used
- **WHEN** a user invokes an explicit `workflowprogram-*` entry
- **THEN** the system uses the corresponding intent without reinterpreting it as another workflow intent

### Requirement: `S0` SHALL emit route evidence with target resolution
The system SHALL emit route evidence that records `intent`, `entry_skill`, `target_root`, and the routing confidence or rationale. `target_root` MUST be resolved to an absolute path and MUST exist before `S0` completes.

#### Scenario: Route evidence is persisted
- **WHEN** `S0` completes
- **THEN** `RUN_ROOT/outputs/stages/s0-route.json` exists and includes `intent`, `entry_skill`, and the resolved `target_root`

#### Scenario: Missing target path is materialized
- **WHEN** `S0` receives a valid path that does not yet exist
- **THEN** the system creates the directory before completing `S0` and records that outcome in routing or progress evidence

### Requirement: Strict routing SHALL block ambiguity
The system SHALL support a strict routing mode that blocks ambiguous requests instead of silently defaulting to a leaf flow.

#### Scenario: Ambiguous request under strict mode
- **WHEN** routing confidence is insufficient and strict mode is enabled
- **THEN** the request does not proceed to a leaf workflow entry until clarified
