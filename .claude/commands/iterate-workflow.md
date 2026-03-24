---
name: iterate-workflow
purpose: Draft and apply workflow improvements from lessons with explicit approval.
inputs: target workflow path, lessons.md, optional dry-run or apply flags
outputs: draft changes, approval list, applied updates, refreshed validation result
gates: stop-on-missing-lessons, approve-structural-changes, validate-after-apply
depends_on: workflow-audit, core-validation-pipeline, core-reporting
writes_to: ./lessons.md, ./validation-report.md, ./.claude/rules/constraints.md, ./.claude/commands, ./.claude/skills, ./.claude/settings.json
---

基于 lessons 对工作流进行审批式自我迭代。

## Usage

```text
/iterate-workflow [--dry-run] [--apply] [<workflow-path>]
```

## Stage 1: 分析 lessons

**Goal**: 找出高价值、可执行的改进机会。

1. 读取 `lessons.md`。
2. 将问题归类为格式、结构、模式、代理、规则问题。

**Verify**: 问题已完成归类。

**On failure**: 提示先积累 lessons。

## Stage 2: 生成草案

**Goal**: 为每个问题生成带原因和影响说明的提案。

1. 产出 diff 预览。
2. 标明自动修复项和需审批项。

**Verify**: 每个提案都包含目标文件、理由和预期效果。

**On failure**: 保留已生成草案并说明缺口。

## Stage 3: 审批展示

**Goal**: 让用户逐项理解并批准结构性变更。

1. 展示摘要。
2. 展示 diff。
3. 等待用户决定。

**Verify**: 用户可以逐项批准或拒绝。

**On failure**: 保留最关键的提案。

## Stage 4: 应用批准项

**Goal**: 只落盘用户明确批准的修改。

1. 自动应用低风险格式修复。
2. 对结构性项仅应用批准内容。

**Verify**: 未批准的结构性变更不会被应用。

**On failure**: 停止后续落盘。

## Stage 5: 重新校验

**Goal**: 确认应用后的工作流仍通过全部检查。

1. 运行 `validate-workflow.ps1`。
2. 运行 `smoke-test-workflow.ps1`。

**Verify**: 变更后依然通过全部脚本。

**On failure**: 输出阻塞项并回退到草案说明层。
