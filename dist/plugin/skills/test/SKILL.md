<!-- AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY -->

---
name: test
description: Run validation or tests for current changes
version: 1.0.0
disable-model-invocation: true
---

运行与当前变更相关的测试或验证命令，并在失败时分析原因。

## Step 1: 识别变更文件

运行 `git diff --name-only $ARGUMENTS` 列出变更文件。
如果 `$ARGUMENTS` 为空，则默认使用未暂存变更。

## Step 2: 查找关联测试

针对每个变更文件查找可能的测试文件：

- 同目录下的 `test_<name>.*`
- 同目录下的 `<name>.test.*`
- 同目录下的 `<name>_test.*`
- `tests/` 或 `__tests__/` 中的对应文件

## Step 3: 运行测试或验证

- 如果存在明确关联测试，则优先运行关联测试
- 如果找不到，则回退到项目在 `CLAUDE.md` 中定义的完整测试命令
- 允许透传额外参数

## Step 4: 分析结果

如果全部通过：

- 报告通过情况与测试数量

如果有失败：

- 展示失败输出
- 分析根因
- 给出可执行修复建议
