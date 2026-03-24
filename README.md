# WorkflowProgram

WorkflowProgram 是一个可复用的 Claude Code 元工作流仓库。
它把命令、技能、专家 Agent、约束规则和验证脚本组合在一起，
用于设计、校验、交付、审计和持续演进其他工作流仓库。

## 这个仓库提供什么

- `.claude/commands/` 中的工作流命令
- `.claude/skills/` 中的可复用技能模板
- `.claude/agents/` 中的专家角色定义
- `.claude/rules/` 中的长期约束与规范
- `.claude/scripts/validate-workflow.ps1` 提供的仓库自检能力

这个仓库的主要产物是工作流资产本身，而不是业务 `src/` 代码。

## 快速开始

1. 打开工作区 `D:\Code\WorkflowProgram`
2. 先阅读 `CLAUDE.md`
3. 运行仓库校验：

```powershell
powershell -ExecutionPolicy Bypass -File .claude/scripts/validate-workflow.ps1
```

4. 根据需要调用命令：

```text
/develop 设计一个用于校验发布说明的工作流
/preflight
/ship
/evolve-workflow .
/iterate-workflow --dry-run .
```

## 命令清单

- `/develop <requirement>`
  根据需求设计工作流。
- `/ship [<scope>]`
  顺序执行审查、验证和提交准备。
- `/preflight [<scope>]`
  并行执行预检查，不会创建提交。
- `/hotfix [<description>]`
  运行热修复专用精简流程。
- `/evolve-workflow [options] <workflow-path>`
  审计并改进目标工作流仓库。
- `/iterate-workflow [--dry-run] [--apply] [<workflow-path>]`
  从 lessons 中生成并应用经过批准的改进草案。

## 技能清单

`settings.json` 中已注册的用户技能：

- `review`
- `test`
- `commit`
- `doc`
- `workflow-audit`

内部支持资产：

- `.claude/skills/develop/spec-template.md`

## 校验策略

仓库统一使用以下命令进行结构校验：

```powershell
powershell -ExecutionPolicy Bypass -File .claude/scripts/validate-workflow.ps1
```

它会检查：

- 根目录必需文件是否存在
- `.claude/settings.json` 是否为合法 JSON
- 命令和技能是否注册一致
- 命令文件是否具备 `Usage`、阶段、`Goal/Verify`
- 技能是否包含规范的 YAML frontmatter

## 目录结构

```text
WorkflowProgram/
|-- CLAUDE.md
|-- README.md
|-- lessons.md
|-- validation-report.md
`-- .claude/
    |-- agents/
    |-- commands/
    |-- rules/
    |-- scripts/
    |-- skills/
    |-- settings.json
    `-- settings.local.json
```

## 说明

- `.claude/settings.json` 是共享命令和技能的注册中心。
- `.claude/settings.local.json` 只应承载本机相关权限，不应进入共享流程设计依赖。
- `lessons.md` 是工作流演进契约的一部分，因为 `/iterate-workflow` 和 `/evolve-workflow` 都依赖它。
