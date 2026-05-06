<!-- AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY -->

---
name: workflowprogram-release
description: Release WorkflowProgram plugin changes by bumping plugin metadata, rebuilding dist, validating, committing, and pushing
version: 1.0.0
disable-model-invocation: true
---

面向 WorkflowProgram 插件源码仓的发布维护入口。用于在用户明确要求发布或 bump 插件版本时，执行版本号更新、dist 重建、验证、git 提交和推送。

## When To Use

- 用户要求发布 WorkflowProgram 插件新版本
- 用户要求 bump plugin version
- 用户要求让 Claude Code marketplace 用户能感知插件更新
- 已有功能变更完成，需要把 `dist/plugin` 与 `.claude-plugin` 元数据同步

## Core Rules

- 当前工作目录必须是 WorkflowProgram 插件源码仓。
- 只修改插件发布相关文件，除非用户明确要求补功能或修验证失败。
- 版本真源是 `.claude-plugin/plugin.json` 和 `.claude-plugin/marketplace.json`；`dist/plugin/**` 必须通过 `python3 tools/build_plugin.py` 生成，不要手改 dist。
- 默认执行 patch bump，例如 `0.1.1 -> 0.1.2`；如果 `$ARGUMENTS` 显式给出版本号，则使用该版本。
- 不要纳入无关未跟踪文件，例如临时 Office 文件、实验脚本、其他工作树目录。
- 发布前必须验证版本一致性：源 plugin metadata、marketplace metadata、dist plugin metadata、dist marketplace metadata、`dist/plugin/build-manifest.json` 必须相同。
- 发布前至少运行 `python3 .claude/scripts/validate-workflow.py` 和 `git diff --check`。
- 若用户要求更强验证，额外运行 runtime smoke matrix。
- 只有验证通过后才能提交并推送 `main`。

## Step 1: Inspect State

1. 运行 `git status --short --untracked-files=all`。
2. 运行 `git branch --show-current`，确认当前分支；默认应在 `main`。
3. 读取当前版本：
   - `.claude-plugin/plugin.json`
   - `.claude-plugin/marketplace.json`
4. 如果两个源版本不一致，先停止并报告需要人工确认。

## Step 2: Resolve Next Version

1. 如果 `$ARGUMENTS` 包含明确版本号，例如 `0.1.2`，使用该版本。
2. 否则执行 patch bump：
   - `MAJOR.MINOR.PATCH -> MAJOR.MINOR.(PATCH+1)`
3. 确认版本号符合语义版本格式：`^[0-9]+\.[0-9]+\.[0-9]+$`。

## Step 3: Update Source Metadata

修改：

- `.claude-plugin/plugin.json` 的 `version`
- `.claude-plugin/marketplace.json` 中对应 plugin 的 `version`
- `.claude-plugin/README.md` 中安装缓存路径示例里的版本号（如果存在）

不要直接修改 `dist/plugin/**`。

## Step 4: Rebuild Dist

运行：

```bash
python3 tools/build_plugin.py
```

确认输出中显示目标版本，例如：

```text
Plugin: workflowprogram-cn@<version>
```

## Step 5: Validate Version Consistency

运行一个最小 JSON 检查，确认以下路径版本完全一致：

- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `dist/plugin/.claude-plugin/plugin.json`
- `dist/plugin/.claude-plugin/marketplace.json`
- `dist/plugin/build-manifest.json`

如果版本不一致，停止并修复后重新构建。

## Step 6: Validate Release

必须运行：

```bash
python3 .claude/scripts/validate-workflow.py
git diff --check
```

如果本次发布伴随 runtime 行为变更，还要运行：

```bash
python3 dist/plugin/scripts/bootstrap-python-runtime.py --plugin-root dist/plugin --plugin-data dist/plugin/.plugin-data --json
python3 tools/runtime_smoke_matrix.py --provider-command 'python3 tools/mock_runtime_host.py' --timeout 60 --json
```

## Step 7: Commit

1. 只暂存发布相关文件：
   - `.claude-plugin/README.md`
   - `.claude-plugin/marketplace.json`
   - `.claude-plugin/plugin.json`
   - `dist/plugin/.claude-plugin/README.md`
   - `dist/plugin/.claude-plugin/marketplace.json`
   - `dist/plugin/.claude-plugin/plugin.json`
   - `dist/plugin/build-manifest.json`
2. 不暂存无关未跟踪文件。
3. 提交信息格式：

```text
Bump plugin version to <version>
```

## Step 8: Push And Report

1. 运行 `git push origin main`。
2. 运行：

```bash
git rev-parse HEAD
git rev-parse origin/main
git status -sb --untracked-files=all
```

3. 向用户报告：
   - 新版本号
   - commit hash
   - 是否已推送到 `origin/main`
   - 剩余未跟踪文件（如有）
