# WorkflowProgram Constraints

来源：2026-03-20 仓库基线整理。

## 仓库不变量

- ALWAYS 保持 `README.md`、`CLAUDE.md`、`lessons.md` 和 `.claude/rules/constraints.md` 存在。
- ALWAYS 保持 `.claude/settings.json` 与对外命令、技能的真实状态同步。
- ALWAYS 在示例路径中优先使用仓库内相对路径，除非工作流明确需要外部目标路径。
- NEVER 把 `.claude/settings.local.json` 当作共享工作流逻辑的一部分。

## 命令设计

- ALWAYS 为用户可见命令保留 `## Usage` 段。
- ALWAYS 将用户可见命令组织为编号阶段，并为阶段提供 `Goal` 与 `Verify`。
- ALWAYS 将可复用的失败经验或上下文缺口记录到 `lessons.md`。
- NEVER 在单个 fan-out 阶段中超过 4 个并行代理。
- NEVER 让子代理运行时依赖外部 agent 文件，只要可以内联提示词就必须内联。

## 技能与 Agent 设计

- ALWAYS 为每个 `SKILL.md` 提供 `name`、`description`、`version` frontmatter。
- ALWAYS 为审查类和校验类 Agent 明确输出格式。
- NEVER 漏掉任何被命令直接引用的支持资产。

## 校验

- ALWAYS 在仓库结构或注册规则变更后同步维护 `.claude/scripts/validate-workflow.ps1`。
- ALWAYS 在交付共享工作流变更前执行仓库校验。
- NEVER 在未说明原因和运行成本前引入重量级共享 hooks。
