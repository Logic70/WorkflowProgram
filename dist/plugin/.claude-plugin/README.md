# WorkflowProgram-CN Plugin

这是 `WorkflowProgram-CN` 的 Claude Code 插件封装说明。

## 目录角色

- `.claude/`：源码真源
- `.claude-plugin/`：插件清单元数据
- `dist/plugin/`：正式安装产物

## 受支持的安装 / 本地验证模型

```bash
python3 tools/build_plugin.py
claude --plugin-dir /mnt/d/Code/WorkflowProgram-CN/dist/plugin
```

说明：

- 当前唯一受支持的安装 / 验证路径是 `plugin-dir`
- 本地开发与验证统一以 `dist/plugin/` 为对象
- `.claude/` 只作为源码真源，不直接作为插件运行目录
- Claude Code 运行时从 `dist/plugin/skills/`、`dist/plugin/agents/`、`dist/plugin/commands/` 发现插件能力
- `dist/plugin/build-manifest.json` 记录本次构建的版本、commit 和文件摘要

## 推荐主入口

安装后，优先使用以下 slash skills-first 入口：

- `/workflowprogram-orchestrate`
- `/workflowprogram-develop`
- `/workflowprogram-audit`
- `/workflowprogram-iterate`
- `/workflowprogram-validate`

旧 commands 仅作为兼容入口保留。

## 正式安装

正式发布安装仍属于后续待定事项。

在 marketplace 或 `/plugin install` 的行为完成实测定案前，本文档不把它们视为受支持稳态契约。

`tools/install_dev.sh` 和 `tools/quick_install.sh` 只应被视为实验性开发辅助路径；它们不代表正式插件生命周期模型。

## 运行时模型

- 源码层 agent：`.claude/agents/`
- 插件运行时 agent：`dist/plugin/agents/`
- 插件运行时 skill：`dist/plugin/skills/`
- 插件 trace manifest：`dist/plugin/build-manifest.json`
- 目标项目最终工作流：`TARGET_ROOT/.claude/`

## 发现契约

WorkflowProgram 的运行时能力不是通过把文件放进用户 `~/.claude` 来被发现，而是通过：

1. WorkflowProgram 先被作为 plugin 加载
2. Claude Code 将 `dist/plugin/` 视为 `PLUGIN_ROOT`
3. Claude Code 从 `PLUGIN_ROOT` 中发现运行时 skills / agents / commands

因此，`~/.claude` 不是当前正式模型中的必需路径。

插件内部如需引用自身资源，应继续使用 `${CLAUDE_PLUGIN_ROOT}` 形式，避免绝对路径耦合。
