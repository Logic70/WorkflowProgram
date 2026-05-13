## Why

Target workflow publishing currently stages a Claude Code plugin package, but the package validation is too shallow. It can pass even when the installed plugin layout cannot resolve declared assets, prompt packages are omitted, runtime validators still check source-layout paths, or documentation references missing scripts.

The FreeSTRIDE publish failure exposed the pattern: target workflow source assets live under `.claude/`, `.workflowprogram/`, `config/`, and `templates/`, while the published plugin layout exposes `commands/`, `skills/`, and `agents/` at plugin root. Publishing must validate the installed shape, not just copied files.

## What Changes

- Package additional target workflow support assets referenced by spec and prompt files, including `.workflowprogram/loops/`, `config/`, and `templates/`.
- Rewrite generated package `.claude/settings.json` to match plugin-root layout paths.
- Add deterministic package validation gates for referenced local assets, missing prompt packages, stale `.claude/...` paths, missing Python dependency documentation, placeholder metadata, and cache artifacts.
- Add install/package dependency output when target runtime manifest declares Python packages.
- Extend publish tests to cover support asset packaging, package-layout validation, missing local references, and runtime validator compatibility.

## Impact

- Existing publish flows remain compatible, but packages with missing declared assets now fail before GitHub publish.
- Target workflows that intentionally reference local support files must either include those files or remove the references.
- FreeSTRIDE can be republished from an empty GitHub checkout and verified from the freshly published package instead of relying on residual repository files.
