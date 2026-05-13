## Design

### 1. Installed Package Shape Is The Validation Source

Publishing has two filesystem shapes:

- source target workflow shape: `.claude/commands`, `.claude/skills`, `.claude/agents`;
- installed plugin shape: `commands`, `skills`, `agents`.

All package validation must use the installed plugin shape. When a target workflow source file or spec references `.claude/skills/foo/SKILL.md`, the publish package validator resolves it to `skills/foo/SKILL.md` inside `package-root`.

### 2. Support Asset Discovery

The package builder copies explicit public assets and runtime assets as before, then includes support assets needed by the workflow:

- `.workflowprogram/design/**`;
- `.workflowprogram/runtime/**`;
- `.workflowprogram/loops/**`;
- `config/**`;
- `templates/**`;
- other local file references discovered from workflow spec and prompt assets when they start with an approved support prefix.

The builder excludes non-source cache and transient artifacts:

- `__pycache__/`;
- `*.pyc`;
- `.pytest_cache/`;
- `.git/`;
- `.DS_Store`;
- editor backups.

### 3. Settings Rewrite

If source `TARGET_ROOT/.claude/settings.json` exists, the package builder writes a package-local `.claude/settings.json` with path values rewritten:

- `.claude/commands/x.md` -> `commands/x.md`;
- `.claude/skills/x/SKILL.md` -> `skills/x/SKILL.md`;
- `.claude/agents/x.md` -> `agents/x.md`.

Validation fails if any rewritten setting path does not exist in package-root.

### 4. Local Reference Validation

The package validator extracts local file references from:

- `.workflowprogram/design/workflow-spec.yaml`;
- `commands/**/*.md`;
- `skills/**/SKILL.md`;
- `agents/**/*.md`;
- `CLAUDE.md`;
- `.workflowprogram/design/**/*.md`.

References beginning with these prefixes must resolve in package-root:

- `.claude/`;
- `.workflowprogram/`;
- `config/`;
- `templates/`;
- `schemas/`;
- `assets/`;
- `data/`;
- `scripts/`;
- `requirements.txt`.

Runtime output paths such as `outputs/**` are not publish package assets and are ignored.

### 5. Runtime Validator Compatibility

If the staged package contains `.workflowprogram/runtime/validate-run-state.py` with a `--spec` interface, validation runs it against the staged package:

```text
python3 .workflowprogram/runtime/validate-run-state.py --spec .workflowprogram/design/workflow-spec.yaml --target-root <package-root>
```

This catches target runtime wrappers that still expect source-layout `.claude/...` files after publishing.

Generated WorkflowProgram shared-control-plane wrappers that expose only `--state` continue to be validated by manifest and wrapper-marker checks, not by this compatibility mode.

### 6. Dependency Documentation

If `.workflowprogram/runtime/runtime-manifest.json` declares `dependencies.packages`, the package builder writes `requirements.txt` at package root and the package README includes explicit Python dependency installation guidance. Validation fails if packages are declared but no requirements file or README mention exists.

### 7. GitHub Clean Republish Verification

The end-to-end verification for FreeSTRIDE uses a clean publish repository checkout:

1. remove existing tracked repository content;
2. commit the empty baseline when needed;
3. run `workflowprogram-publish` to create a fresh `dist/plugin`;
4. verify the fresh checkout contains all declared package assets;
5. run package validation and a target report-render smoke from the freshly published package.

### Iterative Design Audit

#### Round 1: Path Shape Conflict

Finding: The original package validation accepted source-layout settings and target validators even though the installed plugin used root `commands/skills/agents`.

Resolution: Add package-layout path rewriting and package-root setting validation.

Status: closed.

#### Round 2: Asset Reference Drift

Finding: Copying only `.claude/`, design, and runtime misses valid support assets such as templates, config scripts, and loop prompt packages.

Resolution: Add support asset discovery and local reference validation.

Status: closed.

#### Round 3: Over-Packaging Risk

Finding: Copying whole target repositories could leak app source or transient outputs.

Resolution: Use allowlisted support prefixes and cache exclusions; do not copy `src/`, `.git/`, or `outputs/` unless a later explicit publish asset contract permits it.

Status: closed.

#### Round 4: Dependency Blind Spot

Finding: A package can include runnable scripts but omit dependency instructions, causing first-use failures.

Resolution: Derive requirements from target runtime manifest and validate README/requirements coverage.

Status: closed.

#### Round 5: Residual Repository False Positives

Finding: Verifying publish against a repository with old files can hide missing files in the new package.

Resolution: Use a clean republish verification path and inspect the fresh `dist/plugin` from GitHub.

Status: closed.
