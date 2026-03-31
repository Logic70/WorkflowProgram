# WorkflowProgram-CN Plugin

这是 `WorkflowProgram-CN` 的 Claude Code 插件封装版本。

## 插件目录

- `.claude-plugin/plugin.json`：插件清单
- `commands/`：用户可直接调用的插件命令
- `skills/`：插件技能
- `agents/`：插件代理定义
- `rules/`：插件内规则资产
- `scripts/`：插件内部脚本
- `tools/sync_plugin_assets.py`：从 `.claude/` 同步生成插件运行目录

## 本地开发验证

```bash
python3 tools/sync_plugin_assets.py
claude --plugin-dir /mnt/d/Code/WorkflowProgram-CN
```

## 说明

- 源资产继续保留在 `.claude/` 下，便于仓库本身作为工作流项目使用。
- 插件运行目录是根级 `commands/skills/agents/rules/scripts`，由同步脚本生成。
- 插件命令内部使用 `${CLAUDE_PLUGIN_ROOT}` 引用插件自身资源，避免硬编码绝对路径。
