<!-- AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY -->

---
name: workflowprogram-develop
description: Design or update Claude Code workflow assets for the current target project
version: 1.0.0
disable-model-invocation: true
---

面向 `TARGET_ROOT` 的工作流设计主入口。目标是在目标项目中设计或更新 `.claude/` 工作流资产，而不是修改插件源码仓。

## When To Use

- 为当前项目创建新的 Claude Code workflow
- 为现有项目补齐 `.claude/` 结构
- 重构已有 workflow 的技能、agents、rules 或 settings

## Core Rules

- 读取模板、规则和参考资产时，应从 `PLUGIN_ROOT` 读取。
- 不应直接把新文件静默写回 `TARGET_ROOT/.claude/`；应先生成候选产物，再通过 `${CLAUDE_PLUGIN_ROOT}/scripts/managed-assets.py` 决定是否应用。
- 若 `TARGET_ROOT` 已存在 `.claude/`，优先复用并增量修改。
- 必要时使用 `${CLAUDE_PLUGIN_ROOT}/skills/develop/spec-template.md` 作为规格模板来源。
- 不要把仓库维护命令包装进目标项目 workflow 设计。
- 若出现目标文件冲突，应把候选版本保留在 `RUN_ROOT/outputs/`，而不是覆盖用户资产。
- 对已应用文件，应维护 `TARGET_ROOT/.workflowprogram/managed-files.json`。

## Step 1: Resolve Target

1. 确认 `TARGET_ROOT`。
2. 检查 `TARGET_ROOT/.claude/` 是否已经存在。
3. 识别用户需求中的触发方式、输入、输出、角色与质量门禁。

## Step 2: Produce Workflow Spec

1. 用统一规格模板整理需求。
2. 若关键信息缺失，只提出最小必要问题。
3. 形成工作流规格、模式选择和文件清单。

## Step 3: Design Assets

先在 `RUN_ROOT/outputs/candidate/.claude/` 规划或生成候选资产，再决定是否应用到 `TARGET_ROOT/.claude/`：

- `settings.json`
- `skills/`
- `agents/`
- `rules/`
- 必要时的 `commands/` 兼容层

生成候选资产后，使用以下流程：

1. 调用 `${CLAUDE_PLUGIN_ROOT}/scripts/managed-assets.py plan --target-root <TARGET_ROOT> --run-root <RUN_ROOT> --source-root <RUN_ROOT>/outputs/candidate/.claude`
2. 若无冲突，再调用 `apply-staged`
3. 若存在冲突，只输出候选版本与冲突摘要，不静默覆盖目标项目

## Step 4: Verify Readiness

1. 检查命名是否一致。
2. 检查新增资产是否可被后续 `workflowprogram-validate` 验证。
3. 检查 `managed-files.json` 与本次应用结果是否一致。
4. 输出建议的下一步动作。

## Output

输出应包含：

- 目标项目路径
- 设计摘要
- 计划新增或修改的 workflow 资产
- managed asset 计划或冲突摘要
- 建议执行的后续验证步骤
