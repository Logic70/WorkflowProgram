<!-- AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY -->

# Workflow Specification

> **Note**: 本模板用于自然语言设计文档。
> 对于机器可读的编排配置，请使用 `yaml-spec-template.md`。
> 两者关系：`spec-template.md` → 人工审查 → `workflow-spec.yaml` → 生成 `workflow-view.md` / `workflow-lowlevel.md`。
> `workflow-spec.yaml` 是唯一机器语义真源；`workflow-view.md` 与 `workflow-lowlevel.md` 是派生报告，不得单独承载目标工作流执行规则。

## Workflow Identity

- 工作流名称：
- 触发命令：
- 简要描述：

## User Intent

- 用户诉求：
- 最终目的：
- 成功标准：

## Clarification Summary

- 澄清轮次：
- 已确认事项：
- 已消解歧义：

## Open Questions

- 阻塞未决问题：
- 可延后问题：
- 问题处理策略：

## Assumptions and Boundaries

- 当前假设：
- 外部依赖：
- 关键边界场景：
- 明确不做：

## Readback Confirmation

- 回读摘要：
- 用户确认状态：
- 最近修正：

## Problem Statement

- 需要自动化的流程是什么？
- 为什么现在需要这个工作流？

## Users and Stakeholders

- 主要使用者：
- 次要相关方：

## Trigger Model

- 调用方式：手动命令 / Hook / 混合
- 触发细节：

## Inputs

- 必需输入：
- 可选输入：
- 所需外部上下文：

## Outputs

- 主交付物：
- 次级产物：
- 输出格式：

## Quality Gates

- 阻塞条件：
- 必需验证：
- 完成定义：

## Roles and Expert Dimensions

- 角色 1：
- 角色 2：
- 角色 3：
- 需要补充的专业能力（skill / MCP / CLI）：
- 是否需要 capability discovery / host bootstrap 指引：
- 若使用领域能力画像（如 reverse engineering），默认能力包中哪些能力需要保留、移除或替换：
- 若领域画像提供默认 agent team，哪些角色/阶段分工需要保留、裁剪或关闭：
- 若存在 `project_local` bootstrap，需要生成哪些可复用配置 / wrapper / bootstrap 资产：
- 若存在 `host_global` bootstrap，WorkflowProgram 只生成 plan 与人工处理指引；哪些步骤必须由用户或外部安装流程完成：

## Pattern Selection Notes

- Sequential 需求：
- Fan-out 机会：
- Explore 需求：
- Event-Driven 需求：
- Test-Driven 循环：
- Specialized Agent 需求：
- RalphLoop 适用性：
- 是否需要某个目标节点持续迭代直到 verifier/test 通过：
- 循环目标来源（用户目标 / 模型分解子目标）：
- 若是模型子目标，父目标引用：
- 是否需要 TDD test-first 证据：

## Target Workflow Graph Readback

- WorkflowProgram 自身是否仍按 `S0..S6` 开发主链执行：
- 目标工作流是否需要非 `S1..S6` 的业务节点：
- 目标 workflow_graph 节点：
- 目标 workflow_graph 入口与转移：
- 每个 graph 节点的输入、输出、gate、owner：
- 需要 `loop_policy` 的 graph 节点：
- 每个 loop 节点的 `max_iterations`、反馈命令、停止条件、证据输出：
- 目标输出是否已映射到 `registry` 或 `test_contract.artifacts`：

## Extraction Decision

- 留在当前仓库还是抽取：
- 理由：

## File Plan

- 需要创建的文件：
- 需要修改的文件：

## Risks

- 已知风险：
- 假设条件：

## Acceptance Criteria

- [ ] 验收项 1
- [ ] 验收项 2
- [ ] 验收项 3
