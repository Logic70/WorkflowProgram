<!-- AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY -->
<!-- Run: python tools/sync_plugin_assets.py -->

---
name: commit
description: 为当前变更生成结构化的 Conventional Commit 提交信息
version: 1.0.0
disable-model-invocation: true
---

分析当前变更并生成一条结构清晰的 Conventional Commit 提交信息。

## Step 1: 获取变更

运行 `git diff --cached --stat` 查看已暂存变更。
如果没有已暂存内容，则运行 `git diff --stat` 查看未暂存变更，并询问用户是否要全部暂存。

## Step 2: 分析变更

阅读完整 diff，理解：

- 改了什么
- 为什么改
- 影响范围在哪个模块或工作流资产

## Step 3: 生成提交信息

格式：

```text
type(scope): subject

Body: 解释为什么改，而不是重复描述改了什么。
```

常见类型：

- `feat`
- `fix`
- `refactor`
- `docs`
- `test`
- `chore`
- `perf`
- `style`
- `ci`
- `build`

## Step 4: 确认并提交

1. 展示生成的提交信息
2. 等待用户确认或修改
3. 使用确认后的内容执行 `git commit`

Target：`$ARGUMENTS`
