## ADDED Requirements

### Requirement: The repository SHALL maintain a canonical runtime payload
The repository SHALL treat `dist/plugin/` as the canonical in-repo runtime payload and SHALL preserve the minimum plugin structure needed for installation and validation.

#### Scenario: Canonical payload structure exists
- **WHEN** a release candidate or local build is inspected
- **THEN** `dist/plugin/` contains the required runtime directories and plugin metadata

### Requirement: Release installation SHALL remain path-agnostic
The design SHALL support installing the plugin payload from any absolute path via `--plugin-dir`, as long as the extracted payload preserves the expected structure and manifest.

#### Scenario: Absolute plugin path works
- **WHEN** a user installs a released plugin payload into an arbitrary absolute directory
- **THEN** the design contract still maps that location into the expected `PLUGIN_ROOT` model
