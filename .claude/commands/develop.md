根据用户需求设计一个新工作流。这个命令生成的是工作流文件，
例如 commands、skills、agents、rules 与 settings 更新，而不是应用代码。

> Compatibility Note
>
> `/develop` 作为历史兼容入口保留。新的主入口应优先使用 `workflowprogram-develop`，它面向 `TARGET_ROOT` 设计或更新 workflow 资产。

## Usage

```text
/develop <requirement> [--auto-approve]
```

**参数：**
- `<requirement>`: 工作流需求描述（自然语言）
- `--auto-approve`: 自动批准模式，跳过人工确认门禁（用于 CI/CD）

**CI/CD 模式：**
设置环境变量 `CI=true` 或传入 `--auto-approve` 参数，所有设计门禁将自动放行。

**示例：**

```text
# 交互模式（默认）
/develop 设计一个用于审计 Markdown 链接有效性的工作流

# CI/CD 自动模式
/develop "设计一个用于审计 Markdown 链接有效性的工作流" --auto-approve
CI=true /develop "设计一个用于审计 Markdown 链接有效性的工作流"
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

**双轨设计输出（Dual-Track Output）**：

设计阶段产出两份互补的设计文档：

1. **`workflow-spec.yaml`** —— 机器可读的编排配置（源文件）
   - 包含：阶段定义、Agent 引用、转移条件、资源限额
   - 格式：结构化 YAML，支持 `max_retries`、`max_parallel` 等约束
   - 用途：Code Agent 执行时解析，强制执行状态转移
   - 可编辑：✅ 人工可编辑，AI 可生成

2. **`workflow-view.md`** —— 人类可读的只读视图（生成文件）
   - 包含：ASCII 流程图、设计决策说明、Agent 职责描述
   - 格式：自然语言 Markdown
   - 用途：人工审查、快速浏览、设计讨论
   - 可编辑：❌ 禁止直接编辑，从 YAML 单向生成

**单向瀑布生成原则**：
```
workflow-design.md（设计决策，人工审查）
         ↓
   提取转换
         ↓
workflow-spec.yaml（机器编排，单点真实）
         ↓
    生成渲染
         ↓
workflow-view.md（只读视图，人类查阅）
```

**编辑规则**：
- 如需修改设计 → 编辑 `workflow-spec.yaml`
- 重新生成视图 → 运行 `python tools/generate-view.py`
- 禁止直接编辑 `workflow-view.md`（会被覆盖）

**On failure**：把设计失误写入 `lessons.md`。

**Gate**：将设计展示给用户，得到批准后再进入生成阶段。

**自动批准模式**：若传入 `--auto-approve` 参数或环境变量 `CI=true` 存在，则跳过人工确认，打印确认信息后自动继续。

## Stage 4: 从 YAML 生成工作流文件 (Sequential + 即时校验)

**Goal**: 从 `workflow-spec.yaml` 生成所有工作流文件。

**复杂度级别**: 从 YAML 读取 `complexity` 字段，用于 Stage 5 Turn Count 配置

**写入约束**：

- 不要直接把新文件静默覆盖到 `TARGET_ROOT/.claude/`。
- 先把候选文件写入 `RUN_ROOT/outputs/candidate/.claude/`。
- 候选产物生成完成后，调用 `${CLAUDE_PLUGIN_ROOT}/scripts/managed-assets.py`：
  - `plan --target-root <TARGET_ROOT> --run-root <RUN_ROOT> --source-root <RUN_ROOT>/outputs/candidate/.claude`
  - 若无冲突，再执行 `apply-staged`
- 若返回冲突，必须把候选版本保留在 `RUN_ROOT/outputs/` 并向用户报告，不能静默覆盖用户资产。

**生成流程**：

1. 解析 `workflow-spec.yaml`
   - 读取 `meta` 段：target_platform, version
   - 读取 `stages` 段：阶段定义、Agent 引用、约束

2. 按 YAML 定义生成文件（每个文件生成后立即校验，最多3次）：

生成顺序（每个文件生成后立即校验，最多3次，失败则人工介入）：

1. `.claude/agents/*.md`
   - 从 YAML `agent_refs` 提取 Agent 定义
   - 生成后调用 `validate-file` skill 检查
   - 失败则修复，最多3次，仍失败则停止并人工介入

2. `.claude/skills/*/SKILL.md`
   - 从 YAML `skills` 段生成技能定义
   - 生成后调用 `validate-file` skill 检查
   - 失败则修复，最多3次，仍失败则停止并人工介入

3. `.claude/commands/*.md`
   - 从 YAML `stages` 生成命令 Stage 结构
   - 生成后调用 `validate-file` skill 检查
   - 失败则修复，最多3次，仍失败则停止并人工介入

4. `.claude/settings.json`
   - 从 YAML 生成命令和技能注册
   - 生成后调用 `validate-settings` skill 检查
   - 失败则修复，最多3次，仍失败则停止并人工介入

5. `.claude/rules/constraints.md`（如需要，从 YAML `constraints` 提取）
6. 生成 `workflow-view.md`（从 YAML 单向渲染，只读）
7. 更新 `CLAUDE.md`（如需要）

**Verify**: 设计文档中的每个文件都存在且通过 `validate-file` 检查。

**On failure**：单文件3次尝试失败后，停止并人工介入。

## Stage 5: 运行时验证 (Runtime Validation)

**Goal**: 验证工作流在实际执行时的行为是否符合设计。

**Step 1: 测试场景生成**

启动 `test-scenario-generator` 子代理：
1. 读取 `workflow-spec.md` 和设计文档
2. 为每个 Stage 生成标准覆盖测试场景：
   - Happy Path：正常输入
   - Edge Case：边界条件
   - Error Case：错误注入
3. 包含明确 Validation Points（自动判定命令 + 人工检查项）
4. 输出 `test-scenarios.md`

**Step 2: 异步执行验证**

启动 `workflow-verifier` 子代理：
1. 读取复杂度级别（S/M/L/XL）和 **Turn Count 限额**
2. 创建临时 worktree 作为沙盒环境
3. 在沙盒中启动独立 Claude Code 进程
4. 按 `test-scenarios.md` 输入命令，模拟用户执行
5. 轮询 `status.json` 检查进度，监控：
   - **Turn Count**: 累计交互轮数，超过限额强制终止
   - **Circuit Breaker**: 连续 `PostToolUseFailure` 报错计数
6. 达到限额、熔断条件或完成后终止进程

**资源控制配置（设计时指定）**：
- S (≤2 Stages): 50 turns
- M (3-5 Stages): 100 turns
- L (>5 Stages): 200 turns
- XL (复杂编排): 300 turns

**严格模式（可选）**：
设置 `STRICT_MODE=true` 启用更严格的资源限制：
- S: 20 turns / M: 50 turns / L: 100 turns / XL: 150 turns

严格模式用于：
- 强制优化 Agent 效率
- 避免粗放设计依赖轮数堆叠
- CI/CD 环境快速验证

**熔断机制**：
- 当同一 Agent 连续产生 **3 次 `PostToolUseFailure`** 报错，立即熔断终止
- 熔断时输出失败上下文和已执行的测试覆盖度

**Step 3: 生成验证报告**

输出 `validation-runtime-report.md`：
- 每个测试场景的详细结果（标准版 + 调试版）
- CRITICAL/WARNING 问题分类
- 失败时的日志片段和时间线

**反馈路径**：
- **PASS** → 进入 Stage 6
- **FAIL (设计缺陷)** → 回到 Stage 3
- **FAIL (实现缺陷)** → 回到 Stage 4

**最大循环**：10轮或问题收敛为0

**Verify**: 运行时验证报告无 CRITICAL 问题。

**On failure**：记录问题到 `lessons.md`，按缺陷类型反馈到 Stage 3 或 4，重新验证。

## Stage 6: 约束演进与流程闭环

**Goal**: 从本次设计会话中提炼可复用规则，完成流程闭环。

**前提**: Stage 5 运行时验证通过

1. 回顾本次 `/develop` 会话写入 `lessons.md` 的内容（只读取本次会话新增的记录）。
2. 判断问题是否会重复出现。
3. 对可复用问题提炼 `ALWAYS` 或 `NEVER` 规则，写入 `.claude/rules/constraints.md`。
4. 为规则标注来源命令和日期。
5. 当工作流文件成为正式交付物后，删除临时 `workflow-spec.md`。

**关于 Lessons 机制**:

- `lessons.md` 是**追加式日志**，用于记录失败经验和待提取的约束
- 每次新会话**不加载** `lessons.md` 的完整历史（避免上下文膨胀）
- 只读取本次会话新增的记录，或最新3条记录
- 长期约束沉淀到 `constraints.md`，新会话自动加载
- 使用 `/iterate-workflow` 定期将 `lessons.md` 中的约束批量提取到 `constraints.md`

**流程闭环说明**:

```
Stage 5 (运行时验证)
       │
       ├── PASS ──→ Stage 6 ──→ 完成
       │
       ├── FAIL (设计缺陷) ──→ Stage 3 (重新设计，需用户批准)
       │
       └── FAIL (实现缺陷) ──→ Stage 4 (重新生成)
              │
              └── 修复后 ──→ Stage 5 (重新验证)

最大循环: 10轮或问题收敛为0
```

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
