# Workflow Specification

## Workflow Identity

- 工作流名称：Fixture Host Generated Workflow
- 触发命令：/workflowprogram-develop
- 简要描述：由 fixture_host 生成的确定性规格草案。

## Trigger Model

- 调用方式：手动命令
- 触发细节：使用 `/workflowprogram-develop` 处理 `为当前项目设计一个最小 Claude Code workflow，至少包含 settings、一个 skill 和一个 rule 文件`。

## Inputs

- 必需输入：用户请求文本
- 可选输入：当前项目中的 workflow 资产
- 所需外部上下文：仓库中的设计文档与 constraints

## Outputs

- 主交付物：托管的 `.claude/` workflow 资产
- 次级产物：运行时验证报告和 lessons 增量
- 输出格式：Markdown、JSON、YAML

## Quality Gates

- 阻塞条件：审批未决、冲突、边界违规
- 必需验证：managed apply、spec schema、runtime judge
- 完成定义：目标资产与运行时验证结论一致

