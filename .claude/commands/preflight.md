---
name: preflight
purpose: Run a parallel readiness check without creating a commit.
inputs: current branch diff, optional scope
outputs: preflight report, readiness verdict
gates: stop-on-empty-scope, stop-on-critical-security, stop-on-validation-failure
depends_on: review, test, doc, core-review-pipeline, core-validation-pipeline, core-reporting
writes_to: ./validation-report.md, ./lessons.md
---

在正式交付前执行并行预检查，不会创建提交。

## Usage

```text
/preflight [<scope>]
```

## Stage 1: 确定范围

**Goal**: 明确需要检查的 diff。

1. 解析 `$ARGUMENTS`。
2. 默认使用 `main...HEAD`。

**Verify**: 目标范围非空。

**On failure**: 输出 `Nothing to check.`。

## Stage 2: 并行检查

**Goal**: 并行运行安全、审查、文档和验证检查。

1. 启动安全检查。
2. 启动代码审查。
3. 启动文档检查。
4. 运行校验脚本。

**Verify**: 每一条检查链路都能产出可汇总结果。

**On failure**: 记录失败原因。

## Stage 3: 汇总报告

**Goal**: 产出统一的 READY / NOT READY 结论。

1. 按模块汇总发现数量。
2. 明确 critical、warning 和 doc gap。
3. 生成总 verdict。

**Verify**: 报告覆盖全部检查链路。

**On failure**: 指出缺失结果。
