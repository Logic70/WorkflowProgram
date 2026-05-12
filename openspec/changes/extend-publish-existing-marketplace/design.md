## Design

### 1. Goal

Allow `workflowprogram-publish` to append or update a generated target workflow plugin inside an already existing Claude Code marketplace repository.

The optimization must preserve the current standalone flow. Existing users who rely on an exported single-plugin marketplace must see no behavioral change unless they explicitly choose `repo_mode=existing_marketplace`.

### 2. Public Publish Mode

Extend the existing repository mode enum:

- `current_repo`
- `export_repo`
- `existing_marketplace`

`existing_marketplace` requires:

- `--repo-path <local-marketplace-checkout>`
- an existing `repo-path/.claude-plugin/marketplace.json`
- optional `--marketplace-name <name>` that must match the manifest when provided
- optional `--update-existing-entry` for explicit same-plugin updates

The existing standalone modes continue to stage a self-contained package-root marketplace payload as they do today.

### 3. Existing Marketplace Layout

When `repo_mode=existing_marketplace`, the publish flow uses this checkout layout:

```text
repo-path/
├── .claude-plugin/
│   └── marketplace.json
└── plugins/
    └── <plugin-id>/
        ├── .claude-plugin/plugin.json
        ├── .claude-plugin/workflowprogram-publish.json
        ├── commands/
        ├── skills/
        └── .workflowprogram/
```

The marketplace entry source is fixed to:

```json
{
  "name": "<plugin-id>",
  "source": "./plugins/<plugin-id>"
}
```

V1 does not support arbitrary plugin paths or cross-repository plugin source rewrites.

### 4. Marketplace Merge Rules

Add a deterministic `merge-target-marketplace.py` script.

Inputs:

- `package-root`
- `run-root`
- `repo-path`
- `plugin-id`
- `version`
- optional `marketplace-name`
- optional `update-existing-entry`

Behavior:

1. Parse `repo-path/.claude-plugin/marketplace.json`.
2. Resolve the authoritative marketplace name from the manifest.
3. If `--marketplace-name` is provided and does not match, return `BLOCKED/conflict`.
4. Find any existing plugin entry with the same plugin id.
5. If no existing entry exists, append a new entry that points to `./plugins/<plugin-id>`.
6. If an entry exists:
   - require `--update-existing-entry`;
   - require the existing source to already point at `./plugins/<plugin-id>`;
   - require the new package version to be greater than the current catalog/plugin version;
   - otherwise return `BLOCKED/conflict`.
7. Write merge preview and plan into publish evidence. The script does not mutate the checkout.

### 5. GitHub Checkout Apply Rules

`github-publish-target-plugin.py` remains the only script that mutates a Git checkout.

For `existing_marketplace`:

- require `repo-path`
- require the checkout to be git-clean before execution
- copy the package payload into `repo-path/plugins/<plugin-id>/`
- write the merged marketplace manifest to `repo-path/.claude-plugin/marketplace.json`
- stage only the plugin directory and marketplace manifest
- commit, tag, and push only after approval

Dry-run still produces plans and PASS/BLOCKED evidence without checkout writes.

### 6. Validation

`validate-target-plugin-package.py` keeps validating the staged plugin payload.

Add marketplace-level evidence validation:

- `marketplace-resolution.json`
- `marketplace-merge-plan.json`
- `marketplace-manifest-preview.json`
- `marketplace-validation-report.json`

The report checks:

- manifest exists and parses;
- marketplace name resolution;
- append/update/block decision;
- source path shape;
- duplicate plugin id handling;
- version bump handling for updates.

### 7. Install Instructions

`install-instructions.md` must distinguish:

- standalone marketplace install flow;
- existing marketplace append/update flow.

For existing marketplaces, use the resolved marketplace name and repository in install/update instructions. Do not invent a new marketplace name when a manifest already declares one.

### 8. Conflict Taxonomy

Use stable blocked reasons:

- `existing_marketplace_repo_path_required`
- `existing_marketplace_manifest_missing`
- `existing_marketplace_manifest_invalid`
- `marketplace_name_mismatch`
- `existing_marketplace_checkout_dirty`
- `marketplace_plugin_exists`
- `marketplace_source_mismatch`
- `marketplace_version_not_bumped`

These remain publish-layer reasons; they must not be reclassified as target workflow design failures.

### 9. Review Closure

#### Round 1

- Finding: Do not refactor away the existing standalone mode.
- Resolution: Add `existing_marketplace` as a new `repo_mode` only.

#### Round 2

- Finding: Reusing a marketplace is unsafe if plugin path and catalog merge are not fixed.
- Resolution: Standardize `plugins/<plugin-id>/` and `./plugins/<plugin-id>` catalog sources.

#### Round 3

- Finding: Existing plugin updates need explicit conflict/version gates.
- Resolution: Require `--update-existing-entry`, stable source reuse, and version increase.

#### Round 4

- Finding: No new actionable design issue remained after lifecycle, information-flow, compatibility, and testability review.
- Resolution: Proceed to implementation.
