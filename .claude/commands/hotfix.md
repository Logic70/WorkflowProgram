---
name: hotfix
purpose: Fast-track a hotfix with reduced review scope and strict safety gates.
inputs: current diff, optional hotfix description
outputs: security result, validation result, approved hotfix commit
gates: branch-must-not-be-main, stop-on-critical-security, stop-on-validation-failure, approve-before-commit
depends_on: test, commit, core-validation-pipeline, core-reporting
writes_to: ./.git, ./lessons.md, ./validation-report.md
---

用最小但必要的门禁处理热修复。

## Usage

```text
/hotfix [<description>]
```

## Stage 1: 分支检查

**Goal**: 确保当前不是直接在 `main` 上修复。

1. 读取当前分支。
2. 必要时切到 `hotfix/*`。

**Verify**: 当前位于非 `main` 的热修复分支。

**On failure**: 请求用户确认热修复描述。

## Stage 2: 安全检查

**Goal**: 快速确认 diff 中没有 critical 安全问题。

1. 仅运行安全检查。
2. 汇总结果。

**Verify**: 返回结构化安全结论。

**On failure**: 记录失败并停止。

**Gate**: 发现 critical 问题时必须停止。

## Stage 3: 校验

**Goal**: 确认热修复不破坏工作流结构。

1. 运行 `validate-workflow.ps1`。
2. 运行 `smoke-test-workflow.ps1`。

**Verify**: 两个脚本均通过。

**On failure**: 展示失败项。

## Stage 4: 快速提交

**Goal**: 生成并确认热修复提交。

1. 生成 `fix(scope): subject`。
2. 等待用户批准。
3. 获批后提交。

**Verify**: 提交信息获批且 commit 成功。

**On failure**: 在提交前停止。

## Stage 5: 汇总

**Goal**: 输出热修复状态摘要。

1. 输出分支名。
2. 输出安全和校验结果。
3. 输出 commit 信息。

**Verify**: 摘要与执行结果一致。
