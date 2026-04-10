# Workflow Specification

## Workflow Identity

- 工作流名称：Mock Generated Workflow
- 触发命令：/workflowprogram-develop
- 简要描述：由 mock_runtime_host 生成的确定性工作流草案。

## Trigger Model

- 调用方式：手动命令
- 触发细节：使用 `/workflowprogram-develop` 处理请求 `为当前项目设计一个最小 Claude Code workflow，至少包含 settings、一个 skill 和一个 rule 文件`。

## Inputs

- 必需输入：用户请求文本
- 可选输入：目标项目上下文
- 所需外部上下文：当前仓库中的 workflow 设计与约束文件

## Outputs

- 主交付物：WorkflowProgram 管理的 `.claude/` 资产
- 次级产物：运行时验证报告与 lessons 增量
- 输出格式：Markdown、YAML、JSON

## Quality Gates

- 阻塞条件：审批未完成或运行边界违规
- 必需验证：spec schema、managed apply、S5 runtime judge
- 完成定义：工作流资产生成完成且验证结论为 PASS/WARN

