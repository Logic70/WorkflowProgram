---
name: workflowprogram-orchestrate
description: Route natural-language workflow requests for the current project to the correct WorkflowProgram entry skill; 为当前项目设计、审计、迭代、验证 workflow 时优先命中此入口
version: 1.0.0
---

作为 WorkflowProgram 的总控入口，负责把用户当前请求路由到正确的主能力。

## When To Use

- 用户希望为当前项目设计 Claude Code 工作流
- 用户希望审计当前项目中的 workflow 资产
- 用户希望根据 lessons 迭代当前 workflow
- 用户希望验证当前 workflow 是否符合结构约束

## Core Rules

- 当前工作对象是 `TARGET_ROOT`，即用户当前项目目录。
- 插件资产来自 `PLUGIN_ROOT`，应按只读资源处理。
- 不要把 `WorkflowProgram-CN` 仓库本身误当成默认目标项目。
- 不要把 `ship`、`preflight`、`hotfix` 这类仓库维护命令当成产品主入口。
- 这是当前唯一应承接自然语言自动触发的 `workflowprogram-*` 入口。
- 其他 `workflowprogram-develop/audit/iterate/validate` 仍应优先通过显式 slash 调用。
- 若请求不明确，只提出最小必要的一个澄清问题。

## Step 1: Resolve Context

1. 识别当前工作目录是否为 `TARGET_ROOT`。
2. 若用户显式给出路径，以该路径作为 `TARGET_ROOT`。
3. 明确本次操作是“设计 / 审计 / 迭代 / 验证”中的哪一类。

## Step 2: Route Request

按照以下规则路由：

- 设计新 workflow 或更新 workflow 架构 -> `workflowprogram-develop`
- 审计现有 workflow 结构与模式 -> `workflowprogram-audit`
- 基于 `lessons.md` 生成改进草案 -> `workflowprogram-iterate`
- 对 workflow 资产执行结构化校验 -> `workflowprogram-validate`

## Step 3: Hand-off Requirements

向目标主 skill 传递：

- `TARGET_ROOT`
- 用户原始需求
- 必要的约束或范围说明
- 当前已知的 `.claude/` 现状

## Output

输出应包含：

- 路由结论
- 目标主 skill 名称
- 若存在，最小缺失信息项
