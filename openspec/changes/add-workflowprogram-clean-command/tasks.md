## 1. Design

- [x] 1.1 Define cleanup scopes, safety boundaries, and non-goals.
- [x] 1.2 Define CLI and report contracts.
- [x] 1.3 Define run-history retention rules.

## 2. Implementation

- [x] 2.1 Add `.claude/scripts/clean-workflowprogram.py`.
- [x] 2.2 Add `.claude-plugin/root/bin/workflowprogram-clean`.
- [x] 2.3 Update build output handling so `dist/plugin/bin/workflowprogram-clean` is executable.
- [x] 2.4 Update repository validation to require the new script and command.

## 3. Documentation

- [x] 3.1 Document the cleanup command in README.
- [x] 3.2 Document the cleanup command in plugin README.

## 4. Verification

- [x] 4.1 Add cleanup regression coverage.
- [x] 4.2 Rebuild `dist/plugin`.
- [x] 4.3 Run cleanup regression tests.
- [x] 4.4 Run repository validation.
