# Workflow Specification

## Workflow Identity

- 工作流名称：
- 触发命令：
- 简要描述：

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
- 必须验证：
- 完成定义：

## Roles and Expert Dimensions

- 角色 1：
- 角色 2：
- 角色 3：
- 角色 4（如需要）：

## Pattern Selection Notes

- Sequential 需求：
- Fan-out 机会：
- Explore 需求：
- Event-Driven 需求：
- Test-Driven 循环：
- Specialized Agent 需求：

## Target Repository Conventions

- 留在当前仓库还是抽取独立仓：
- 若为 Claude 工作流仓：
  - `.claude/settings.json` 注册格式：
  - 用户命令文件格式：
  - 用户技能文件格式：
- 若与默认格式不同，差异是什么：

## Extraction Boundary

- 目标输出路径：
- 是否在当前 Claude 工作区内：
- 若不在，所需额外目录授权方式（例如 `--add-dir`）：

## File Plan

- 需要创建的文件：
- 需要修改的文件：

## Toolchain Dependencies

- 必需工具：
- 可选工具：
- 安装方式：
- 不可用时的降级策略：

## Security Scope (如适用)

- 覆盖的 CWE 子集：
- 嵌入式/IoT 专项检查：
- 数据流/污点分析能力：

## Risks

- 已知风险：
- 假设条件：

## Acceptance Criteria

- [ ] 验收项 1
- [ ] 验收项 2
- [ ] 验收项 3
- [ ] 若为独立工作流仓，命令可被本地 Claude 正确识别
