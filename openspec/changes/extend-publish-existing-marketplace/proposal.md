## Why

`workflowprogram-publish` currently packages every generated target workflow as a standalone marketplace payload. That works for one-off publishing, but it prevents users from maintaining a durable shared marketplace that hosts multiple WorkflowProgram-generated workflow plugins.

The publish lifecycle should support reusing an existing marketplace repository without weakening the current standalone publish path or silently overwriting existing plugin entries.

## What Changes

- Add `repo_mode=existing_marketplace` to the target workflow publish lifecycle.
- Preserve current `current_repo` and `export_repo` behavior.
- Package the target plugin into `plugins/<plugin-id>/` when reusing an existing marketplace checkout.
- Merge the plugin entry into an existing `.claude-plugin/marketplace.json` instead of generating a replacement marketplace manifest.
- Block unsafe updates when plugin ids, source paths, versions, marketplace names, or Git checkout state conflict.
- Add publish evidence, docs, fixtures, and smoke cases for append, update, and blocked/failure paths.

## What Stays The Same

- Publish remains an independent lifecycle after `workflowprogram-develop`.
- Publish does not modify target workflow semantic design.
- GitHub writes remain approval-gated and use the user's local `gh` / `git` environment.
- Standalone marketplace publishing remains supported.
