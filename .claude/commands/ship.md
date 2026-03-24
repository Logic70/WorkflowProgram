---
name: ship
purpose: Review validate and prepare a commit for current workflow changes.
inputs: current git diff, optional scope
outputs: review summary, validation result, approved commit message, optional git commit
gates: stop-on-critical-review, stop-on-validation-failure, approve-before-commit
depends_on: review, test, commit, core-review-pipeline, core-validation-pipeline, core-reporting
writes_to: ./.git, ./lessons.md, ./validation-report.md
---

按顺序交付当前变更：先审查，再校验，最后准备提交。

## Usage

```text
/ship [<scope>]
```

## Stage 1: 预检查

**Goal**: 确认存在可交付的变更范围。

1. 运行 `git status`。
2. 确定 `$ARGUMENTS` 是否缩小交付范围。

**Verify**: 当前存在有效 diff。

**On failure**: 输出 `Nothing to ship.`。

## Stage 2: 审查

**Goal**: 获取安全、性能、风格和逻辑审查结果。

1. 获取 diff。
2. 并行运行四类审查。
3. 汇总为统一报告。

**Verify**: 四条审查链路都返回结果。

**On failure**: 记录审查失败。

**Gate**: 存在 critical 问题时必须暂停。

## Stage 3: 校验

**Goal**: 确认仓库结构与语义都通过检查。

1. 运行 `validate-workflow.ps1`。
2. 运行 `smoke-test-workflow.ps1`。

**Verify**: 两个脚本均成功退出。

**On failure**: 展示失败项并停止。

## Stage 4: 生成提交

**Goal**: 生成并确认提交信息。

1. 基于变更生成 Conventional Commit。
2. 让用户确认。
3. 获批后再提交。

**Verify**: 提交信息已批准，且提交成功。

**On failure**: 在 commit 前停止。

## Stage 5: 汇总

**Goal**: 输出可信的交付摘要。

1. 汇总审查结果。
2. 汇总校验结果。
3. 输出 commit 信息。

**Verify**: 摘要内容与实际执行结果一致。
