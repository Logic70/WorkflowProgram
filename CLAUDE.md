# WorkflowProgram-CN

## 项目概述

WorkflowProgram-CN 是一个面向 Claude Code 风格工作区的元工作流仓库。
它不提供业务应用源码，而是提供一组可复用的命令、技能、Agent、
规则和校验脚本，用来设计、交付、审计和迭代其他工作流仓库。

## 技术栈

- 文档与配置：Markdown、JSON
- 自动化与校验：PowerShell
- 运行环境：Claude Code 工作区命令体系
- 数据库：无

## 架构说明

本仓库采用分层工作流结构：

- `CLAUDE.md`
  项目级说明，进入工作区时优先读取。
- `.claude/settings.json`
  用户可见命令与技能的共享注册表。
- `.claude/settings.local.json`
  本机权限与本地覆盖配置，不应作为共享工作流逻辑依赖。
- `.claude/commands/`
  工作流编排入口，如 `/develop`、`/ship`、`/evolve-workflow`。
- `.claude/skills/`
  可复用技能模板，如审查、测试、文档和工作流审计。
- `.claude/agents/`
  专家角色定义，用于设计或内联子代理提示词。
- `.claude/rules/`
  持久化约束与演进规则。
- `.claude/scripts/`
  可执行校验脚本，使仓库能够被自动验证。

经验法则：
可确定、可复验的检查放到脚本里；
流程编排放到 commands 和 skills；
角色职责放到 agents；
长期有效的约束沉淀到 rules。

## 核心能力

- `/develop`
  根据需求设计一个新工作流，产出的是工作流文件，不是应用代码。
- `/ship`
  以顺序流水线执行审查、校验和提交准备。
- `/preflight`
  在正式交付前运行更快的并行就绪检查，不会提交代码。
- `/hotfix`
  以精简流程快速处理热修复，但仍保留关键安全与校验门禁。
- `/evolve-workflow`
  审计目标工作流仓库，识别结构和模式问题，并可从 lessons 中抽取约束。
- `/iterate-workflow`
  从 `lessons.md` 生成改进草案，展示 diff，待批准后再应用。

## 项目结构

```text
WorkflowProgram-CN/
|-- CLAUDE.md
|-- README.md
|-- lessons.md
|-- validation-report.md
`-- .claude/
    |-- settings.json
    |-- settings.local.json
    |-- agents/
    |-- commands/
    |-- rules/
    |-- scripts/
    `-- skills/
```

## Commands

工作流入口命令：

- `/develop <requirement>`
  根据需求设计新工作流，并按阶段完成规格、设计、生成与校验。
- `/ship [<scope>]`
  顺序执行审查、验证与提交准备。
- `/preflight [<scope>]`
  执行并行化的预检查与就绪性汇总。
- `/hotfix [<description>]`
  执行热修复专用精简流程。
- `/evolve-workflow [options] <workflow-path>`
  审计并演进目标工作流仓库。
- `/iterate-workflow [--dry-run] [--apply] [<workflow-path>]`
  从经验沉淀中生成审批优先的工作流改进草案。

## Skills

用户可直接使用的技能：

- `/review`
- `/test`
- `/commit`
- `/doc`
- `/workflow-audit`

内部支持资产：

- `.claude/skills/develop/spec-template.md`
  `/develop` 生成 `workflow-spec.md` 时使用的规格模板。

## Development Commands

- Run：在 Claude Code 中打开本仓库后直接调用上述命令
- Test：`powershell -ExecutionPolicy Bypass -File .claude/scripts/validate-workflow.ps1`
- Lint：`powershell -ExecutionPolicy Bypass -File .claude/scripts/validate-workflow.ps1`
- Build：`N/A`

## 规则

- NEVER 直接在 `main` 分支上提交。
- ALWAYS 保持 `.claude/settings.json` 与实际对外命令、技能同步。
- ALWAYS 保持 `README.md`、`lessons.md` 和 `.claude/rules/constraints.md` 存在。
- ALWAYS 在命令或技能中为可独立运行的子代理内联完整提示词。
- NEVER 让子代理在运行时依赖外部 agent 文件。
- NEVER 在单次 fan-out 阶段中超过 4 个并行代理。
- ALWAYS 把可复用的失败经验和流程教训记录到 `lessons.md`。
- ALWAYS 若未来增加 hooks，保持其轻量、同步、可解释。

## Testing Rules

- 测试命令：`powershell -ExecutionPolicy Bypass -File .claude/scripts/validate-workflow.ps1`
- 共享工作流变更在交付前必须通过全部仓库校验。
- 新增用户可见命令或技能时，必须同步更新 `README.md`、`CLAUDE.md` 和 `.claude/settings.json`。
- 可复用的长期约束应写入 `.claude/rules/constraints.md`。
