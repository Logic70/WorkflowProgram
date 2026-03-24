---
name: develop
purpose: Design a workflow from requirements and turn it into workflow assets.
inputs: requirement description, user clarifications, target runtime conventions, output directory (optional)
outputs: workflow-spec.md, design summary, workflow files, rule updates
gates: clarify-before-spec, approve-design-before-generation, validate-before-finish
depends_on: workflow-spec-support, workflow-audit, core-validation-pipeline, core-reporting
writes_to: $OUTPUT_DIR/workflow-spec.md, $OUTPUT_DIR/.claude/agents, $OUTPUT_DIR/.claude/skills, $OUTPUT_DIR/.claude/commands, $OUTPUT_DIR/.claude/settings.json, $OUTPUT_DIR/.claude/rules/constraints.md, $OUTPUT_DIR/CLAUDE.md, $OUTPUT_DIR/lessons.md
---

根据用户需求设计一个新工作流。产物是工作流资产，而不是业务应用代码。

支持两种运行模式：
- **本地模式**（默认）：在当前仓库内创建工作流资产。`$OUTPUT_DIR` = `.`
- **跨路径模式**：通过 `--output-dir` 指定目标路径，在该路径下创建独立工作流仓。当作为用户级 Skill 被调用时，`$OUTPUT_DIR` 由调用方传入。

## Usage

```text
/develop <requirement> [--output-dir <path>]
```

## Stage 1: 理解需求
**Goal**: 确定运行模式和输出路径，产出无歧义的 `workflow-spec.md`。
1. 解析 `$ARGUMENTS`。若指定了 `--output-dir`，设置 `$OUTPUT_DIR` 为该绝对路径；否则 `$OUTPUT_DIR` = 当前工作目录。
2. 若 `$OUTPUT_DIR` 不存在，创建它。
3. 围绕输入、输出、触发方式、质量门禁、角色分工和运行环境提出澄清问题。
4. 明确这是”当前仓内演进”还是”抽取到新目录的独立工作流”。
5. 基于 `.claude/skills/develop/spec-template.md` 生成 `$OUTPUT_DIR/workflow-spec.md`。
**Verify**: `workflow-spec.md` 不包含未解释的空白项、`TBD` 或未声明的运行边界。`$OUTPUT_DIR` 路径已确认可写。
**On failure**: 把缺失信息记录到 `lessons.md`。

## Stage 2: 研究上下文
**Goal**: 识别可复用资产、目标格式和实现边界。
1. 审阅 WorkflowProgram-CN 的 `.claude/` 结构、`CLAUDE.md`、规则和契约。这些是**设计参考**，不是复制目标。
2. 若目标是抽取新仓库，确认目标仓是否仍遵循 Claude 命令/技能约定。
3. 若 `$OUTPUT_DIR` 与 WorkflowProgram-CN 不同（跨路径模式），确认对 `$OUTPUT_DIR` 的写权限已就绪。
**Verify**: 简报覆盖需求中的关键范围、目标目录与运行约束。
**On failure**: 记录遗漏的上下文或权限边界。

## Stage 3: 设计工作流
**Goal**: 产出结构化设计方案。
1. 结合原子模式给出阶段流、Skill 清单、Agent 维度、验证方式和输出格式。
2. 明确命令注册格式、文件布局和报告产物。
3. 若工作流依赖外部工具链（静态分析器、编译器等），明确列出每个工具的用途、安装方式和不可用时的降级策略。
4. 若抽取独立仓库，默认沿用 Claude 兼容格式：
   - `.claude/settings.json` 使用对象映射注册。
   - 用户命令位于 `.claude/commands/*.md`。
   - 用户技能位于 `.claude/skills/*/SKILL.md`。
**Verify**: 设计覆盖所有需求，且单阶段并行代理不超过 4 个。
**On failure**: 记录设计缺口。
**Gate**: 必须先获得用户批准设计，再进入文件生成。

## Stage 4: 生成工作流资产
**Goal**: 在 `$OUTPUT_DIR` 下按设计生成完整文件集。
1. 所有文件写入 `$OUTPUT_DIR`（不是 WorkflowProgram-CN 目录）。
2. 先生成规则、模板和脚本，再生成 commands、skills、agents、settings。
3. 对独立工作流仓，优先生成”可运行、可验证”的最小闭环。
4. 生成 `$OUTPUT_DIR/CLAUDE.md`、`$OUTPUT_DIR/README.md`、`$OUTPUT_DIR/.gitignore` 等仓库基础文件。
**Verify**: 设计清单中的文件都存在于 `$OUTPUT_DIR`，格式与目标仓约定一致。
**On failure**: 修复后重新验证，不保留错误格式的占位文件。

## Stage 5: 仓库校验
**Goal**: 确保新工作流通过结构和烟雾测试。
1. 若 `$OUTPUT_DIR` 内包含 `validate-workflow.ps1`，运行它。
2. 若 `$OUTPUT_DIR` == WorkflowProgram-CN，同时运行 `smoke-test-workflow.ps1`。
3. 若产出独立工作流仓且尚无验证脚本，为 `$OUTPUT_DIR` 补一份仓库内验证脚本。
4. 对 WorkflowProgram-CN 本身运行 `validate-workflow.ps1` 确认元仓未被破坏。
**Verify**: 所有验证都通过，并且关键命令可被 Claude 识别。
**On failure**: 停止交付并报告阻塞项。

## Stage 6: 约束沉淀
**Goal**: 把可复用经验提炼成规则。
1. 回看本次设计、生成和本地 Claude 测试的偏差。
2. 将 recurring issue 写入 WorkflowProgram-CN 的 `.claude/rules/constraints.md`（不是目标仓的）。
3. 将真实问答与决策沉淀到 WorkflowProgram-CN 的 `lessons.md` 或测试记录中。
4. 若目标仓有自己的 `constraints.md`，将仅与目标仓相关的规则写入其中。
**Verify**: 需要沉淀的经验已经转成规则或记录。
**On failure**: 保留草稿并说明原因。
