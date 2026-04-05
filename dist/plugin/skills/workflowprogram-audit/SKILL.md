<!-- AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY -->

---
name: workflowprogram-audit
description: Audit workflow assets in the current target project and report structural or pattern issues
version: 1.0.0
disable-model-invocation: true
---

面向 `TARGET_ROOT` 的工作流审计主入口。负责审计目标项目中已有的 workflow 资产，而不是审计插件源码仓本身。

## When To Use

- 检查当前项目的 `.claude/` 结构是否完整
- 识别 workflow 模式、命名或约束偏离
- 输出结构化审计报告和改进建议

## Core Rules

- 当前审计对象是 `TARGET_ROOT` 或其指定子路径。
- 优先使用 `workflow-audit` 作为底层检查清单。
- 对关键文件可按需调用 `validate-file`。
- 审计输出必须区分结构问题、模式问题和质量问题。

## Step 1: Resolve Audit Scope

1. 确认 `TARGET_ROOT` 和审计范围。
2. 找出目标 workflow 根目录。
3. 检查核心资产是否存在：`CLAUDE.md`、`README.md`、`lessons.md`、`.claude/`。

## Step 2: Run Audit

1. 使用 `workflow-audit` 清单检查结构和模式。
2. 必要时对 `settings.json`、关键 skill、agent、command 文件做 `validate-file` 验证。
3. 记录严重度和影响范围。

## Step 3: Summarize Findings

按以下维度汇总：

- 结构缺失
- 模式偏离
- 可维护性问题
- 建议优先级

## Output

输出应包含：

- 审计目标路径
- Findings 列表
- 严重度分类
- 建议的修复和后续动作
