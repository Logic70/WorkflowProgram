根据用户需求设计一个新工作流。这个命令生成的是工作流文件，
例如 commands、skills、agents、rules 与 settings 更新，而不是应用代码。

## Usage

```text
/develop <requirement>
```

示例：

```text
/develop 设计一个用于审计 Markdown 链接有效性的工作流
```

整个过程遵循 TDD 风格循环：定义目标 -> 执行 -> 验证 -> 失败则记录到
`lessons.md` -> 修复 -> 重试。

## Stage 1: 理解需求 (Explore)

**Goal**: 生成一个没有歧义的 `workflow-spec.md`。

1. 将 `$ARGUMENTS` 解析为工作流需求。
2. 识别歧义点，并围绕以下维度向用户提出 3-5 个澄清问题：
   - 需要自动化的流程是什么？（触发 -> 步骤 -> 输出）
   - 输入和输出分别是什么？
   - 有哪些质量门禁或停止条件？
   - 涉及多少种角色或专家维度？
   - 应由手动命令触发，还是由 hook 自动触发？
3. 用户回答后，使用 `.claude/skills/develop/spec-template.md` 在仓库根目录生成 `workflow-spec.md`。
4. **Verify**: 规格中的每个字段都有明确值，且不再包含 `TBD`。

**On failure**：把歧义点和所需补充信息记录到 `lessons.md`。

## Stage 2: 领域研究 (Explore)

**Goal**: 生成覆盖规格范围的领域上下文报告。

1. 启动只读 Explore 子代理，分析：
   - 现有 `.claude/` 资产：agents、skills、commands、settings、rules
   - `CLAUDE.md` 中的项目约定、校验方式和命名规则
   - 与目标工作流领域相关的项目结构
2. 输出结构化报告，列出可复用资产、缺口和命名建议。
3. **Verify**: 报告覆盖 `workflow-spec.md` 中提到的所有领域范围。

**On failure**：把遗漏的上下文记录到 `lessons.md`。

## Stage 3: 模式选择与工作流设计 (Specialized Agent)

**Goal**: 生成包含模式组合、Agent 编制和文件清单的设计文档。

设计前先阅读 `.claude/rules/constraints.md`。

### 工作流抽取决策框架

在真正生成文件前，先判断这个工作流是否应被抽取成独立仓库。

**ALWAYS extract when：**

- 该工作流强依赖某种语言、框架或工具链
- 其他团队或项目也可能独立复用它
- 它需要独立演进和发布节奏
- 它与当前仓库技术栈明显不同

**NEVER extract when：**

- 它只服务于本仓库
- 它高度依赖当前仓库约定或本地配置
- 它还在高频变化期
- 它本质上是通用能力，应留在当前仓库

**If extracting：**

1. 先在当前仓库中生成草稿
2. 向用户展示设计
3. 批准后复制到 `../{name}-workflow/`
4. 再清理当前仓库中的临时副本

随后，基于六种原子模式分析需求：

- Sequential
- Fan-out/Fan-in
- Explore
- Event-Driven
- Test-Driven
- Specialized Agent

设计文档至少包括：

- ASCII 流程图
- Agent 清单：名称、职责、关注点、输出格式、约束
- Skill 清单：触发方式与职责
- Hook 清单：只有确实需要 hooks 时才添加
- 文件清单：要创建或修改的每个文件
- 每一阶段的 TDD 目标和验证条件

**Verify**: 设计覆盖全部需求，统一并行输出格式，并且并行代理数不超过 4 个。

**On failure**：把设计失误写入 `lessons.md`。

**Gate**：将设计展示给用户，得到批准后再进入生成阶段。

## Stage 4: 生成工作流文件 (Sequential)

**Goal**: 设计文档中的文件全部生成且格式正确。

生成顺序：

1. `.claude/agents/*.md`
2. `.claude/skills/*/SKILL.md`
3. `.claude/commands/*.md`
4. `.claude/settings.json`
5. `.claude/rules/constraints.md`
6. 如有必要，更新 `CLAUDE.md`

逐文件检查：

- Markdown 标题结构稳定、引用不破损
- JSON 可解析
- Agent 提示词自包含
- 会调用子代理的 Skill 内联完整提示词

**Verify**: 设计文档中的每个文件都存在且通过格式检查。

**On failure**：把问题记录到 `lessons.md`，修复后重新验证。

## Stage 5: 工作流校验 (Test-Driven)

**Goal**: 生成后的工作流通过仓库校验。

校验清单：

- [ ] 设计文档中的全部文件存在
- [ ] `.claude/settings.json` 是合法 JSON
- [ ] 没有子代理在运行时依赖外部 agent 文件
- [ ] 命令引用的 agent 名称或内联提示词有效
- [ ] 单阶段并行代理数不超过 4
- [ ] 每个阶段都有清晰的 `Goal` 与 `Verify`
- [ ] Skills 具备合法 YAML frontmatter
- [ ] 没有引入重复的 command、skill 或 agent 名称

若校验失败：

1. 记录到 `lessons.md`
2. 修复文件
3. 重新校验，最多 3 轮

**Verify**: 校验通过，或在 3 轮失败后给出明确阻塞报告。

**On failure**：停止并向用户说明阻塞点。

## Stage 6: 约束演进

**Goal**: 从本次设计会话中提炼可复用规则。

1. 回顾本次 `/develop` 会话写入 `lessons.md` 的内容。
2. 判断问题是否会重复出现。
3. 对可复用问题提炼 `ALWAYS` 或 `NEVER` 规则，写入 `.claude/rules/constraints.md`。
4. 为规则标注来源命令和日期。
5. 当工作流文件成为正式交付物后，删除临时 `workflow-spec.md`。

**Verify**: 可复用经验已经沉淀为规则，临时草稿已清理。

**On failure**：保留临时文件并向用户解释原因。

## Final Output

输出以下内容：

- 工作流名称与触发命令
- 创建或修改的文件
- 使用的模式组合
- 新增的约束
- 下一步建议

Target：`$ARGUMENTS`
