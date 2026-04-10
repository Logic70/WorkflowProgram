## ADDED Requirements

### Requirement: HighLevel SHALL define normative intent-to-stage flows
The HighLevel stage design SHALL define the normative stage chain for `develop`, `audit`, `iterate`, and `validate`. LowLevel MAY expand node-level execution details, but it MUST not be the only source for non-`develop` flow definitions.

#### Scenario: Audit flow is documented
- **WHEN** the HighLevel document describes supported workflow intents
- **THEN** it explicitly declares the `audit` stage flow instead of relying on LowLevel alone

#### Scenario: Iterate and validate flows are documented
- **WHEN** the HighLevel document describes supported workflow intents
- **THEN** it explicitly declares the `iterate` and `validate` stage flows instead of relying on LowLevel alone

### Requirement: `S1` SHALL apply only to the `develop` intent
The system SHALL treat `S1` as a `develop`-only stage unless a future requirement explicitly broadens that scope. Non-`develop` intent flows MUST bypass `S1`.

#### Scenario: Develop flow includes `S1`
- **WHEN** the routed intent is `develop`
- **THEN** the stage chain includes `S1` before design and generation stages

#### Scenario: Validate flow bypasses `S1`
- **WHEN** the routed intent is `validate`
- **THEN** the stage chain does not require `S1` before entering its validation path

### Requirement: Intent routing and flow validation SHALL stay aligned
Intent routing, stage flow documentation, and validation rules SHALL describe the same intent semantics. The routed entry skill, the documented intent chain, and any flow-oriented validation logic MUST agree on which stages are required or skippable for a given intent.

#### Scenario: Routed intent matches the documented chain
- **WHEN** the system routes a request to `workflowprogram-validate`
- **THEN** the documented `validate` flow and any flow validation rules agree that `S5` is required and `S1` is not

#### Scenario: Routed intent matches the develop chain
- **WHEN** the system routes a request to `workflowprogram-develop`
- **THEN** the documented `develop` flow and any flow validation rules agree that `S1`, `S3`, and `S4` are part of the main chain
