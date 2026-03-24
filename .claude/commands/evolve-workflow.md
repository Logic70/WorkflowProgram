---
name: evolve-workflow
purpose: Audit and improve a workflow repository using shared architecture rules.
inputs: target workflow path, optional fix or extraction flags
outputs: audit report, fix summary, constraint candidates, validation report
gates: stop-on-missing-target, approve-structural-changes, validate-after-fix
depends_on: workflow-audit, core-validation-pipeline, core-reporting
writes_to: ./validation-report.md, ./lessons.md, ./.claude/rules/constraints.md
---

通用工作流审计与演进命令。

## Usage

```text
/evolve-workflow [options] <workflow-path>
```

## Stage 1: 结构审计

**Goal**: 确认目标工作流满足基础目录和文件要求。

1. 检查根目录文件。
2. 检查 `.claude/` 目录结构。
3. 检查注册表与技能文件。

**Verify**: 结构问题已被完整列出。

**On failure**: 输出缺失项。

## Stage 2: 模式审计

**Goal**: 识别命令、技能、代理和规则的模式偏差。

1. 检查分阶段结构。
2. 检查 Goal / Verify。
3. 检查子代理是否自包含。

**Verify**: 模式偏差具备明确说明。

**On failure**: 标记无法解释的偏差。

## Stage 3: 演进分析

**Goal**: 从 lessons 中提炼可执行改进项。

1. 读取 `lessons.md`。
2. 提炼 recurring issue。
3. 生成规则或改进候选。

**Verify**: 改进候选可映射回 lessons 来源。

**On failure**: 输出原因。

## Stage 4: 修复与复验

**Goal**: 在启用 fix 时修复低风险问题并重新校验。

1. 自动修复格式和低风险结构问题。
2. 运行结构校验和烟雾测试。

**Verify**: 修复后通过校验。

**On failure**: 停止并报告未修复项。
