# WorkflowProgram-CN Plugin

这是 `WorkflowProgram-CN` 的 Claude Code 插件封装说明。

## 目录角色

- `.claude/`：源码真源
- `.claude-plugin/`：插件清单元数据
- `dist/plugin/`：仓库内 canonical 运行时载荷目录

## 受支持的加载与安装模型

主安装模型：

```bash
claude plugin marketplace add Logic70/WorkflowProgram
claude plugin install workflowprogram-cn@logic70-plugins
```

或在 Claude Code 会话内：

```text
/plugin marketplace add Logic70/WorkflowProgram
/plugin install workflowprogram-cn@logic70-plugins
/reload-plugins
```

Claude Code 加载插件后，会在 `SessionStart` 自动执行 Python runtime bootstrap。

说明：

- `dist/plugin/` 是仓库内 canonical marketplace 载荷目录
- `.claude/` 只作为源码真源，不直接作为插件运行目录
- `.claude-plugin/root/` 是会被展开到插件根目录的运行时资产真源
- Claude Code 运行时从 `PLUGIN_ROOT` 下的 `skills/`、`agents/`、`commands/`、`bin/`、`hooks/` 发现插件能力
- `dist/plugin/build-manifest.json` 记录本次构建的版本、commit 和文件摘要
- 宿主机需要 `Python 3.10+` 的 `python3`
- Python 依赖通过 `${CLAUDE_PLUGIN_DATA}/python/site-packages` 准备，不要求用户全局安装 `pyyaml`

开发与调试模型：

- Source Build：从源码仓构建 `dist/plugin/` 供本地调试使用

## 推荐主入口

安装后，普通用户优先使用唯一主入口：

- `/workflowprogram-cn:workflowprogram-orchestrate <需求>`
- `/workflowprogram-cn:workflowprogram-publish <target-root> --plugin-id <id> --repo <owner/repo-or-url>`

`workflowprogram-develop`、`workflowprogram-audit`、`workflowprogram-iterate`、`workflowprogram-validate` 是高级显式 intent 或内部路由目标。`workflowprogram-publish` 是独立发布环节，只用于把完整通过 develop 的目标 workflow 打包并发布成 marketplace plugin。旧 commands 仅作为兼容入口保留。

## 发布前准备

在调用 `/workflowprogram-cn:workflowprogram-publish` 前，用户需要先准备：

1. 一个已经完整通过 `workflowprogram-develop` 的目标 workflow。
2. 目标插件的 `plugin-id`、显示名和版本号。
3. 一个已经存在的 GitHub 发布仓库；当前 publish 流程不会自动创建仓库。
4. 已安装并登录的 `gh`，且对目标仓库有 push 权限。
5. 若要真实执行 push，而不是 `--dry-run`，还需要该仓库的本地 checkout 路径，供 `--repo-path` 使用。
6. 若要复用已有 marketplace，则 checkout 中还必须已有 `.claude-plugin/marketplace.json`，并选择 `--repo-mode existing_marketplace`。

最小入口：

```text
/workflowprogram-cn:workflowprogram-publish <target-root> --plugin-id <id> --repo <owner/repo-or-url>
```

复用已有 marketplace：

```text
/workflowprogram-cn:workflowprogram-publish <target-root> --plugin-id <id> --repo <owner/repo-or-url> --repo-mode existing_marketplace --repo-path <marketplace-checkout>
```

该模式会把插件规划到 `plugins/<plugin-id>/`，再合并已有 marketplace manifest；若更新同名插件，还必须显式允许更新并提升版本号。

真实 GitHub 写入仍要求显式审批；缺少认证、权限、仓库或本地 checkout 时，流程会返回 `BLOCKED` 并给出修复指引。

## 新增能力：S1 需求逻辑访谈

`workflowprogram-develop` 的 S1 会用七个 logic lenses 深挖需求，而不是只收集“输入/输出/边界场景”：

- `purpose`
- `object_model`
- `process_model`
- `decision_model`
- `evidence_model`
- `acceptance_model`
- `boundary_model`

运行时会生成 `RUN_ROOT/outputs/stages/question-backlog.json` 与 `RUN_ROOT/outputs/stages/requirement-logic-map.json`。`validate-workflow-draft.py` 会阻止缺少关键 lens、缺少 `REQ-* -> process/evidence/acceptance` 链接，或 L/XL 复杂度下只有泛问题的草案进入设计阶段。

## 目标工作流设计治理

完整通过 `workflowprogram-develop` 的目标 workflow 不只会写入 `.claude/` 资产，还会写入：

- `TARGET_ROOT/.workflowprogram/design/workflow-spec.yaml`：目标 workflow 的机器控制面和运行态地图。
- `TARGET_ROOT/.workflowprogram/design/workflow-view.md`：从 YAML 派生的只读概览。
- `TARGET_ROOT/.workflowprogram/design/workflow-maintenance.md`：从 YAML 派生的维护指导。
- `TARGET_ROOT/.workflowprogram/design/source/**`：目标 workflow 的设计源归档。

设计源归档使用 target-prefixed 命名，例如 `target-design-overview.md`、`target-design-detail.md`、`target-acceptance-tests.yaml`、`target-traceability-matrix.json`。这些文件解释“为什么这样设计”和“如何验证”，`workflow-spec.yaml` 只保存可执行、可校验的机器投影。

复杂、loop、工具重、逆向/安全或多下游节点还会使用 `target-node-designs/<node-id>.md` 作为单节点可执行设计契约。该文件必须符合 `workflow-spec-support/target-node-design-template.md`，并由 `validate-target-node-design.py` / S5 校验它与 `workflow_graph.nodes[*]` 的 owner、template、gate、input/output、loop policy 是否一致。

发布目标 workflow 时，`workflowprogram-publish` 会检查 develop/S5/design-review/managed/target-design-source 证据；publish 不负责临时补设计源，也不修复缺失的 traceability 或 acceptance tests。

## Python Runtime

- 插件在 `SessionStart` 通过 `${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap-python-runtime.py` 准备私有 Python 依赖。
- 插件内的 Python 主入口应通过 `workflowprogram-python` 调用，而不是裸 `python3`。
- 如需最小化排障，执行 `workflowprogram-doctor`。
- 如需清理插件 Python runtime、测试产物或目标项目旧 run，执行 `workflowprogram-clean`；默认 dry-run，删除必须显式传 `--apply`。
- 如果出现 `Unknown skill: workflowprogram-orchestrate`，先执行 `/reload-plugins` 或重启 `claude`，并使用 `/workflowprogram-cn:workflowprogram-orchestrate ...` 入口；不要让模型手写 `Skill(workflowprogram-orchestrate)`。
- 如果出现 `bin/workflowprogram-python: Permission denied`，说明安装缓存中的 launcher 缺少执行权限。更新并重新安装最新 marketplace 载荷；临时修复可执行 `chmod +x ~/.claude/plugins/cache/logic70-plugins/workflowprogram-cn/0.1.14/bin/workflowprogram-*`。

## 运行时模型

- 源码层 agent：`.claude/agents/`
- 插件运行时 agent：`dist/plugin/agents/`
- 插件运行时 skill：`dist/plugin/skills/`
- 插件 trace manifest：`dist/plugin/build-manifest.json`
- Python launcher：`dist/plugin/bin/workflowprogram-python`
- 安装 doctor：`dist/plugin/bin/workflowprogram-doctor`
- 清理维护命令：`dist/plugin/bin/workflowprogram-clean`
- 进展脚本：`dist/plugin/scripts/stage-progress.py`
- 路由脚本：`dist/plugin/scripts/route-intent.py`
- 规格校验脚本：`dist/plugin/scripts/validate-workflow-spec.py`
- 状态校验脚本：`dist/plugin/scripts/validate-run-state.py`
- 控制面 runner：`dist/plugin/scripts/workflow-runner.py`
- 目标项目最终工作流：`TARGET_ROOT/.claude/`

## 发现契约

WorkflowProgram 的运行时能力不是通过把文件放进用户 `~/.claude` 来被发现，而是通过：

1. WorkflowProgram 先被作为 plugin 加载
2. Claude Code 将 `dist/plugin/` 视为 `PLUGIN_ROOT`
3. Claude Code 从 `PLUGIN_ROOT` 中发现运行时 skills / agents / commands

因此，`~/.claude` 不是当前正式模型中的必需路径。

插件内部如需引用自身资源，应继续使用 `${CLAUDE_PLUGIN_ROOT}` 形式，避免绝对路径耦合。
