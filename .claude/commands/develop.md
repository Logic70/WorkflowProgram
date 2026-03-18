Design a new workflow from a user's requirement. This command produces workflow FILES (commands, agents, skills, hooks, rules), NOT application code.

Follow each stage exactly. Every stage runs as a TDD loop: define goal → execute → verify → if failed, record to lessons.md, fix, retry.

## Stage 1: Understand the Need (Explore)

**Goal**: Produce a `workflow-spec.md` with zero ambiguities.

1. Parse $ARGUMENTS as the workflow requirement
2. Identify ambiguities and ask 3-5 clarifying questions covering:
   - What process should be automated? (trigger → steps → output)
   - What are the inputs and expected outputs?
   - What quality gates / stop conditions are needed?
   - How many roles / expert dimensions are involved?
   - Should it be manually triggered (/command) or auto-triggered (Hook)?
3. After user answers, write `workflow-spec.md` in the project root using the template from `.claude/skills/develop/spec-template.md`
4. **TDD verify**: Self-check — does every field in the spec have a concrete value (no TBD)? If not, ask follow-up questions and rewrite.

**On failure**: Record to `lessons.md`: what was ambiguous, what clarification was needed.

## Stage 2: Domain Research (Explore)

**Goal**: Produce a domain context report covering the spec's scope.

1. Launch an Explore subagent (read-only) to analyze:
   - Existing `.claude/` directory: current agents, skills, commands, hooks, rules
   - `CLAUDE.md`: project conventions, tech stack, commands
   - Project source code structure relevant to the workflow domain
2. Output a structured report: existing assets to reuse, gaps to fill, naming conventions
3. **TDD verify**: Does the report cover every domain mentioned in workflow-spec.md? If not, explore more.

**On failure**: Record to `lessons.md`: what context was missed.

## Stage 3: Pattern Selection & Workflow Design (Specialized Agent)

**Goal**: Produce a design document with pattern choices, agent roster, and file list.

Read `.claude/rules/constraints.md` for learned rules from past designs.

1. Analyze the workflow-spec.md against the six atomic patterns:
   - Sequential — steps with strict dependencies
   - Fan-out/Fan-in — independent parallel tasks, aggregate results
   - Explore — understand before acting
   - Event-Driven — Hook auto-triggers
   - Test-Driven — loop until goal met
   - Specialized Agent — split by expert dimension

2. Select which patterns to combine. Output a design document:
   - Flow diagram (ASCII art)
   - Agent roster: name, role, focus area, output format
   - Skill list: name, trigger, what it does
   - Hook list: trigger timing, matcher, action
   - File list: every file to create/modify
   - Each stage's TDD goal and verify condition

3. **TDD verify**: Does the design cover every requirement in workflow-spec.md? Are agent output formats unified? Is parallel agent count ≤ 4?

4. **GATE**: Show the design to user and WAIT for confirmation. Do NOT proceed until user approves.

**On failure**: Record to `lessons.md`: what design mistake was made.

## Stage 4: Generate Workflow Files (Sequential)

**Goal**: All files from the design's file list are created with correct format.

Generate files in this order (dependencies first):

1. **Agents** (`.claude/agents/*.md`):
   - Each agent: role + focus areas + output format + rules
   - Agent prompts must be self-contained (subagent context isolation)

2. **Skills** (`.claude/skills/*/SKILL.md`):
   - YAML frontmatter (name, description)
   - Step-by-step instructions with $ARGUMENTS support
   - If skill invokes agents, INLINE the full agent prompt (do NOT reference agent files)

3. **Commands** (`.claude/commands/*.md`):
   - Multi-stage workflow orchestration
   - Reference agents by description (inline prompts for subagent calls)
   - Define gates between stages

4. **Hooks** (update `.claude/settings.json`):
   - Merge new hooks with existing ones (don't overwrite)
   - PreToolUse for gates, PostToolUse for auto-triggers

5. **Rules** (update `.claude/rules/constraints.md`):
   - Add any domain-specific constraints identified during design

6. **Update CLAUDE.md** if the new workflow introduces new commands or conventions

7. **TDD verify per file**: After writing each file, verify:
   - Markdown files: proper structure, no broken references
   - JSON files: valid JSON, correct schema
   - Agent prompts: self-contained, no "read file X" instructions
   - Skills with agents: prompts are fully inlined

**On failure**: Record which file had what format issue → fix → re-verify.

## Stage 5: Workflow Validation (Test-Driven)

**Goal**: The generated workflow passes all validation checks.

Run the validation checklist:

- [ ] All files from design's file list exist
- [ ] `.claude/settings.json` is valid JSON
- [ ] No agent prompt references external files (subagent isolation rule)
- [ ] Commands reference correct agent names
- [ ] Parallel agent count per stage ≤ 4
- [ ] Every stage in commands has a clear TDD goal
- [ ] Skills have proper YAML frontmatter
- [ ] No duplicate agent/skill/command names with existing ones

If any check fails:
1. Record the issue in `lessons.md`
2. Fix the file
3. Re-run validation (max 3 rounds)

If 3 rounds still fail, STOP and report to user.

## Stage 6: Constraint Evolution

**Goal**: Extract reusable rules from this design session.

1. Review `lessons.md` for all entries from this /develop session
2. For each entry, ask: "Will this problem recur in future workflow designs?"
3. If yes, extract a rule in `ALWAYS/NEVER` format
4. Append to `.claude/rules/constraints.md` with source annotation:
   ```
   # Source: /develop "[workflow name]" — [date]
   ALWAYS [rule description]
   ```
5. Clean up: delete `workflow-spec.md` (it served its purpose, the workflow files are the deliverable)

## Final Output

Display a summary:
- Workflow name and trigger command
- Files created/modified (with paths)
- Pattern combination used
- Constraints learned (if any)
- Suggested next step: "Try running /[new-command] to test your new workflow"

Target: $ARGUMENTS (the workflow requirement description)
