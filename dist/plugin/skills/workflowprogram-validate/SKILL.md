<!-- AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY -->

---
name: workflowprogram-validate
description: Validate workflow assets in the current target project at workflow scope
version: 1.0.0
disable-model-invocation: true
---

面向 `TARGET_ROOT` 的 workflow 级验证主入口。负责对目标项目中的 workflow 资产执行统一校验，不等同于仓库维护命令 `/preflight`。

## When To Use

- 验证当前项目的 `.claude/` 资产是否齐全
- 在生成或修改 workflow 后做结构化校验
- 为后续审计或交付提供统一验证结论

## Core Rules

- 当前验证对象是 `TARGET_ROOT/.claude/`，不是插件源码仓。
- `preflight` 面向当前仓库 diff；本 skill 面向目标项目 workflow 资产。
- 单文件检查优先复用 `validate-file`；workflow 级结论由本 skill 汇总输出。
- 若项目已有专门 workflow 验证命令，可作为补充信息纳入结果。

## Step 1: Resolve Validation Scope

1. 确认 `TARGET_ROOT` 和待验证的 workflow 根路径。
2. 列出关键目标：`settings.json`、`skills/`、`agents/`、`rules/`、必要时的 `commands/`。
3. 判断是全量验证还是指定范围验证。

## Step 2: Run Checks

1. 对关键文件调用 `validate-file`。
2. 汇总目录级存在性、注册一致性和文件格式状态。
3. 如有必要，补充调用 `test` 运行项目定义的 workflow 校验命令。

## Step 3: Produce Verdict

输出统一结论：

- PASS
- WARN
- FAIL

并说明：

- 失败项
- 影响范围
- 修复优先级

## Output

输出应包含：

- 验证目标路径
- 覆盖范围
- 总体结论
- 失败或警告清单
