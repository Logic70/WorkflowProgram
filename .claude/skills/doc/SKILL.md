---
name: doc
description: Generate or update documentation for changed code
disable-model-invocation: true
---

Generate or update documentation for $ARGUMENTS (default: current changes).

## Step 1: Identify scope

If $ARGUMENTS specifies a file or module, document that.
Otherwise, run `git diff --name-only` to find changed files.

## Step 2: Analyze what needs documentation

For each changed file, check:
- [ ] All public functions/classes have docstrings
- [ ] Docstrings match current implementation (not outdated)
- [ ] Complex logic has inline comments explaining WHY
- [ ] README mentions new public APIs or features
- [ ] CHANGELOG has an entry for user-facing changes (if CHANGELOG exists)

## Step 3: Generate documentation

For missing docstrings:
- Generate Google-style / JSDoc-style docstrings (match project convention)
- Include: description, parameters, return value, exceptions/errors, usage example

For README updates:
- Add new features/APIs to the appropriate section
- Update examples if the API changed

For CHANGELOG:
- Add entry under "Unreleased" section
- Categorize as: Added / Changed / Fixed / Removed

## Step 4: Apply changes

Show the proposed documentation changes and wait for user confirmation before applying.

Output: list of documentation updates made, organized by file.
