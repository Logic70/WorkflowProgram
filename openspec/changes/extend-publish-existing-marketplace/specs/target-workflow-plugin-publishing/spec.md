## MODIFIED Requirements

### Requirement: Publish SHALL package a Claude Code marketplace plugin

The publish lifecycle SHALL stage a Claude Code marketplace-compatible plugin package for the target workflow before writing to a GitHub publishing checkout, and SHALL support either standalone marketplace packaging or reuse of an existing marketplace checkout.

#### Scenario: Existing marketplace packaging stages only plugin payload

- **GIVEN** the user selects `repo_mode=existing_marketplace`
- **WHEN** package creation runs
- **THEN** the package root contains the target plugin payload
- **AND** it does not replace the target checkout marketplace manifest
- **AND** marketplace catalog changes are handled through a separate merge plan

## ADDED Requirements

### Requirement: Publish SHALL reuse an existing marketplace safely

WorkflowProgram SHALL support publishing a generated target workflow into an existing Claude Code marketplace checkout without overwriting unrelated marketplace plugins.

#### Scenario: New plugin is appended to an existing marketplace

- **GIVEN** `repo_mode=existing_marketplace`
- **AND** `repo-path/.claude-plugin/marketplace.json` is valid
- **AND** no plugin entry exists for the requested plugin id
- **WHEN** marketplace merge planning runs
- **THEN** the merge preview appends exactly one new plugin entry
- **AND** the entry source points to `./plugins/<plugin-id>`

#### Scenario: Existing plugin update requires explicit approval and version increase

- **GIVEN** the existing marketplace already has a plugin entry for the requested plugin id
- **WHEN** the user has not set `--update-existing-entry`
- **THEN** publish returns a blocked conflict
- **WHEN** the user has set `--update-existing-entry` but the new version is not greater than the existing version
- **THEN** publish returns a blocked conflict

#### Scenario: Existing plugin source mismatch is blocked

- **GIVEN** the existing marketplace already has a plugin entry for the requested plugin id
- **AND** its source does not match `./plugins/<plugin-id>`
- **WHEN** publish plans an update
- **THEN** publish returns a blocked conflict
- **AND** it does not rewrite that source implicitly

### Requirement: Existing marketplace execution SHALL mutate only approved publishing checkout assets

WorkflowProgram SHALL apply existing-marketplace publication only to a clean local checkout after explicit approval.

#### Scenario: Dirty checkout blocks execution

- **GIVEN** `repo_mode=existing_marketplace`
- **AND** the publishing checkout has uncommitted changes
- **WHEN** GitHub publish execution is requested
- **THEN** publish returns `BLOCKED`
- **AND** `block_reason=existing_marketplace_checkout_dirty`

#### Scenario: Clean checkout receives plugin payload and merged manifest

- **GIVEN** package validation and marketplace merge validation passed
- **AND** GitHub execution is approved
- **AND** the publishing checkout is clean
- **WHEN** publish execution runs
- **THEN** the plugin payload is copied to `plugins/<plugin-id>/`
- **AND** the merged marketplace manifest is written to `.claude-plugin/marketplace.json`
- **AND** only those assets are staged for commit
