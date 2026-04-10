# WorkflowProgram-CN

> **面向 Claude Code 生态的元工作流仓库**

WorkflowProgram-CN 是一个用于设计、交付、审计和迭代**可嵌入 Claude Code 的业务工作流仓库**的元工作流工具。

它不提供业务应用源码，而是提供一组可复用的命令、技能、Agent 定义、约束规则和校验脚本，帮助你用结构化的方式创建可自动化的工作流程。

---

## 产品定位

**聚焦 Code Agent 领域**

WorkflowProgram-CN 专为 Claude Code、OpenCode 等 AI 编程助手生态设计，产出物是符合 `.claude/` 结构规范的**工作流仓库**，而非通用的 CI/CD 模板。

**典型产出示例**：[daily-news-workflow](https://github.com/Logic70/-daily-news-workflow) —— 一个包含标准 `.claude/` 结构、可被 WorkflowProgram-CN 审计和演进的新闻收集工作流。

---

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone https://github.com/Logic70/WorkflowProgram-CN.git
cd WorkflowProgram-CN

# 验证仓库结构
# Windows:
powershell -ExecutionPolicy Bypass -File .claude/scripts/validate-workflow.ps1
# macOS/Linux:
python3 .claude/scripts/validate-workflow.py
```

### 2. 三分钟上手

```bash
# 构建并以 plugin-dir 方式加载
python3 tools/build_plugin.py
claude --plugin-dir /mnt/d/Code/WorkflowProgram-CN/dist/plugin
```

```text
# 推荐：先让总控 skill 识别目标
/workflowprogram-orchestrate "为当前项目设计一个 Claude Code 工作流"

# 显式主入口
/workflowprogram-develop "创建一个用于每日收集科技新闻的工作流"
/workflowprogram-audit /path/to/existing-workflow
/workflowprogram-validate /path/to/existing-workflow
```

## 入门教程

如果你想先理解这套仓库背后的设计哲学，再动手跑命令，先看这套教程：

- [WorkflowProgram 101 章节版](docs/workflowprogram-101/index.md)
- [WorkflowProgram 101 单页版](docs/workflowprogram-101.md)

---

## 核心能力

### 1. 工作流设计（workflowprogram-develop）

面向 `TARGET_ROOT` 的主入口，用于为目标项目设计或更新 `.claude/` workflow 资产：

```text
/workflowprogram-develop "创建一个用于每日收集科技新闻并生成摘要的工作流"
```

**阶段**：
1. 需求分析 → 2. 规格定义 → 3. 架构设计 → 4. 资产生成 → 5. workflow 验证建议

### 2. 工作流编排与验证（workflowprogram-orchestrate, workflowprogram-validate）

| 入口 | 用途 |
|------|------|
| `workflowprogram-orchestrate` | 识别自然语言需求并路由到正确主 skill |
| `workflowprogram-validate` | 对目标项目中的 workflow 资产执行结构化验证 |

### 3. 工作流演进（workflowprogram-audit, workflowprogram-iterate）

| 入口 | 用途 |
|------|------|
| `workflowprogram-audit` | 审计目标工作流，识别结构问题和模式偏离 |
| `workflowprogram-iterate` | 从 lessons.md 生成改进草案 |

### 4. 仓库维护兼容命令（/ship, /preflight, /hotfix）

| 命令 | 用途 |
|------|------|
| `/ship [<scope>]` | 顺序执行审查、校验和提交准备 |
| `/preflight [<scope>]` | 并行预检查，不创建提交 |
| `/hotfix [<description>]` | 热修复精简流程 |

---

## 架构设计

WorkflowProgram-CN 采用分层结构，将不同类型的资产分离：

```
WorkflowProgram-CN/
├── .claude/
│   ├── commands/          # 源码层命令定义
│   ├── skills/            # 源码层技能定义
│   ├── agents/            # 源码层 agent 定义
│   ├── rules/             # 源码层规则
│   ├── scripts/           # 源码层脚本
│   └── settings.json      # 源码层注册表
├── .claude-plugin/        # 插件清单元数据
├── dist/plugin/           # 仓库内 canonical 运行时载荷目录
├── tests/                 # fixture、expectation、transcript 与 runtime 证据
├── tools/                 # 构建与 runtime smoke 工具
├── docs/                  # 设计、phase 计划与归档文档
├── CLAUDE.md              # 开发者说明
├── README.md              # 本文件
├── lessons.md             # 经验日志（失败记录、待提取约束）
└── validation-report.md   # 校验报告
```

### 资产分层原则

| 位置 | 用途 | 经验法则 |
|------|------|----------|
| `.claude/` | 源码真源 | 只在这里维护命令、技能、agent、规则和脚本 |
| `dist/plugin/` | canonical 运行时载荷 | Claude Code 插件运行时消费的载荷目录（仓库内） |
| `TARGET_ROOT/.claude/` | 目标项目最终交付 | 插件执行后写入目标项目的工作流资产 |
| `TARGET_ROOT/.workflowprogram/managed-files.json` | managed 资产清单 | 记录哪些目标文件可由 WorkflowProgram 安全更新 |
| `TARGET_ROOT/.workflowprogram/runs/<run-id>/` | 运行证据 | 记录 context、state、events、transcript 和 runtime report |

---

## 推荐入口（Skills-First）

当前推荐直接使用 `workflowprogram-*` skills 作为主入口：

- `/workflowprogram-orchestrate`：总控入口，负责将自然语言请求路由到正确主能力
- `/workflowprogram-develop`：为 `TARGET_ROOT` 设计或更新 workflow 资产
- `/workflowprogram-audit`：审计目标项目中的 workflow 资产
- `/workflowprogram-iterate`：基于 lessons 生成 workflow 改进草案
- `/workflowprogram-validate`：对目标项目中的 workflow 资产执行结构化验证

旧 `/develop`、`/evolve-workflow`、`/iterate-workflow` 继续保留为兼容 slash 入口；用户级主入口统一采用 `workflowprogram-*` skills。
当前方案下，只有 `workflowprogram-orchestrate` 允许承接自然语言自动触发；其余 4 个叶子 skill 仍以显式 slash 调用为主。

## 兼容命令清单

### 工作流设计
- `/develop <requirement> [--auto-approve]` —— 根据需求设计新工作流

### 交付流水线
- `/ship [<scope>] [--auto-approve]` —— 审查、校验、提交
- `/preflight [<scope>]` —— 并行预检查
- `/hotfix [<description>]` —— 热修复流程

### 工作流演进
- `/evolve-workflow [options] <path>` —— 审计目标工作流
- `/iterate-workflow [--dry-run] [--apply] [<path>]` —— 从经验迭代改进

---

## Plugin 运行时模型

当前设计明确区分三层：

- 源码层：`.claude/*`
  - 仓库内部开发真源
- 安装产物层：`dist/plugin/*`
  - 插件运行时实际消费的目录
- 目标项目层：`TARGET_ROOT/.claude/`
  - WorkflowProgram 执行后写入目标项目的最终工作流资产

其中 agent 采用双层模型：

- 源码定义：`.claude/agents/`
- 运行时暴露：`dist/plugin/agents/`

## 插件发现与调用契约

Claude Code 识别 WorkflowProgram 的前提，不是用户 `~/.claude` 下存在这些文件，而是 **WorkflowProgram 先被作为 plugin 加载**。

当前受支持的发现模型是：

1. 使用 `python3 tools/build_plugin.py` 生成 `dist/plugin/`
2. 使用 `claude --plugin-dir /abs/path/to/dist/plugin` 启动 Claude Code
3. Claude Code 从 `dist/plugin/skills/`、`dist/plugin/agents/`、`dist/plugin/commands/` 发现运行时资产

因此：

- `.claude/` 是源码真源
- `dist/plugin/` 是 Claude Code 真正消费的运行时目录
- `TARGET_ROOT/.claude/` 才是 WorkflowProgram 写给目标项目的最终工作流

当前唯一受支持的显式调用语法是 slash 入口：

- `/workflowprogram-orchestrate`
- `/workflowprogram-develop`
- `/workflowprogram-audit`
- `/workflowprogram-iterate`
- `/workflowprogram-validate`

纯自然语言触发可以作为易用性增强，但不是发布验证的唯一契约。
当前自然语言优化策略是：**只让 `workflowprogram-orchestrate` 承接自然语言自动触发**，再由它路由到叶子 skill，避免多个叶子 skill 互相竞争。
为降低歧义，当前实现提供确定性路由脚本：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/route-intent.py --request "<user request>" --target-root <TARGET_ROOT> --json
```

当设置 `WORKFLOWPROGRAM_STRICT_ROUTE=1`（或 `--strict`）时，歧义请求会被程序硬阻断并要求先澄清。

## 目标项目资产更新契约

WorkflowProgram 不应把新资产直接静默覆盖到 `TARGET_ROOT/.claude/`。

当前受支持的最小流程是：

1. 先在 `RUN_ROOT/outputs/candidate/.claude/` 生成候选文件
2. 调用 `${CLAUDE_PLUGIN_ROOT}/scripts/managed-assets.py plan`
3. 若无冲突，再调用 `apply-staged`
4. 若有冲突，把候选版本保留在 `RUN_ROOT/outputs/conflicts/`

应用成功后，工具会维护：

- `TARGET_ROOT/.workflowprogram/managed-files.json`
- `RUN_ROOT/outputs/managed-change-plan.json`
- `RUN_ROOT/outputs/managed-change-result.json`

## 构建产物可追溯性

每次执行 `python3 tools/build_plugin.py` 后，`dist/plugin/` 下都应生成：

- `build-manifest.json`

它至少记录：

- `plugin_name`
- `plugin_version`
- `generated_at`
- `source_commit`
- `source_dirty`
- 每个构建文件的 `path` 与 `sha256`

---

## 动态验证

Phase 3 已引入最小运行时 smoke harness：

- 开发期结构验证：`python3 .claude/scripts/validate-workflow.py`
- 插件构建：`python3 tools/build_plugin.py`
- 运行时 smoke：`python3 tools/runtime_smoke.py --fixture empty-project`

当前环境下，如果 Claude CLI 未登录，运行时 smoke 会返回 `ENVIRONMENT-SKIP`，同时仍会创建 `RUN_ROOT` 和完整证据文件。

## 运行进展可视化

Phase 6 起，建议在 Stage 执行中统一写入进展资产：

- `RUN_ROOT/outputs/progress/current-progress.json`
- `RUN_ROOT/outputs/progress/milestones.jsonl`
- `RUN_ROOT/outputs/progress/user-progress.md`

统一脚本入口：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/stage-progress.py update ...
```

## 控制面执行与状态校验

当前实现已提供程序化 runner 与状态校验：

```bash
# 1) 校验 workflow-spec 结构
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-workflow-spec.py --spec <RUN_ROOT>/workflow-spec.yaml

# 2) 执行程序化 stage 转移（控制面）
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/workflow-runner.py run --spec <RUN_ROOT>/workflow-spec.yaml --run-root <RUN_ROOT> --target-root <TARGET_ROOT> [--auto-approve]

# 3) 校验 state/artifacts 枚举约束
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-run-state.py --state <RUN_ROOT>/state.json
```

`validate-run-state.py` 会强制检查 `kind/root/producer/status` 等枚举，避免仅靠提示词约定。

`validate-workflow-spec.py` 还会强制 `workflow-spec.yaml` 同时声明 `runtime_contract` 与 `test_contract`：

- `runtime_contract`：执行期硬约束
  - `write_boundaries`：允许写入路径边界
  - `required_evidence`：最小运行证据集
  - `failure_kinds`：失败类别枚举
  - `environment_skip`：环境 skip 条件

- `test_contract`：基础运行测试判定
  - `entry`：主入口、入口类型、必需参数、缺参与非法入口 verdict
  - `boundary`：引用写入边界，并补充 managed 覆盖/冲突/外部写入策略
  - `flow`：required/skippable stages、失败回流、verdict 终止条件
  - `artifacts`：关键交付物、关键证据引用、可缺失非关键输出
  - `failure`：失败枚举引用、环境 skip 引用、`implemented_now` 覆盖度声明

其中：

- `test_contract` 对执行字段必须使用 `runtime_contract.<field>` 固定引用语法
- `test_contract` 不得复制 `runtime_contract` 同名字段
- `test_contract.failure.implemented_now` 必须是 `runtime_contract.failure_kinds` 的子集，且不得反向改变 runner 语义

## 安装与验证路径

当前文档定义两条受支持安装通道，它们共享同一运行时载荷结构：

- Source Build 通道：
  - 使用 `python3 tools/build_plugin.py` 生成 `dist/plugin/`
  - 使用 `claude --plugin-dir /mnt/d/Code/WorkflowProgram-CN/dist/plugin` 做发现与运行验证

- GitHub Release Package 通道：
  - 下载并解压 release 附件 `workflowprogram-plugin-<version>.tar.gz`（或 zip）
  - 确认解压目录包含 `plugin/build-manifest.json`
  - 使用 `claude --plugin-dir /abs/path/to/<extracted>/plugin` 启动

以下路径当前**不属于受支持稳态模型**：

- 将 `dist/plugin/` 复制到用户 `~/.claude`
- 在未完成实测前，直接把 marketplace 或 `/plugin install` 视为正式安装契约

仓库中的 `tools/install_dev.sh` 和 `tools/quick_install.sh` 仅保留为实验性开发辅助脚本，不作为发布路径。


## 详细使用指南

### CI/CD 自动模式

所有设计门禁支持自动批准：

```text
# 方式1: 命令行参数
/develop "需求描述" --auto-approve
/ship --auto-approve

# 方式2: 环境变量
CI=true /develop "需求描述"
```

### 严格资源模式

设置 `STRICT_MODE=true` 启用更严格的 Turn Count 限制：
- S: 20 turns / M: 50 turns / L: 100 turns / XL: 150 turns

用于强制优化 Agent 效率和 CI/CD 快速验证。

---

## 技能清单

### 辅助/复用技能
- `/review` —— 代码审查
- `/test` —— 测试执行
- `/commit` —— 提交准备
- `/doc` —— 文档生成
- `/workflow-audit` —— 工作流审计

### 内部支持资产
- `.claude/skills/develop/spec-template.md` —— /develop 规格模板

---

## 工作流产出示例

### daily-news-workflow

一个由 WorkflowProgram-CN 生成的典型工作流仓库：

**功能**：每日自动收集科技新闻，翻译为中文，部署到 GitHub Pages

**结构**：
```
daily-news-workflow/
├── .claude/               # 工作流标记（可被 WorkflowProgram-CN 演进）
│   ├── commands/          # 命令设计文档（展示阶段结构，非自动加载）
│   ├── skills/            # 技能定义
│   └── settings.json      # 工作流元数据
├── .github/workflows/     # GitHub Actions 自动化
├── scripts/               # Python 收集器
├── docs/                  # 输出目录（GitHub Pages）
└── README.md
```

**演进能力**：
- 在 WorkflowProgram-CN 中运行 `/evolve-workflow /path/to/daily-news-workflow`
- 审计结构问题、从 lessons.md 提取约束、生成改进方案
- `.claude/` 中的命令定义是**设计文档**，用于演进，不会自动加载为 Claude Code 的 `/` 命令

---

## 经验沉淀机制

WorkflowProgram-CN 使用三层机制管理知识：

```
┌─────────────────────────────────────────────┐
│  constraints.md  ← 长期记忆（AI 上下文加载）  │
│  - 精简的 ALWAYS/NEVER 规则                  │
│  - 从 lessons 定期提取                       │
└─────────────────────────────────────────────┘
                        ▲
                        │ 定期提取
┌─────────────────────────────────────────────┐
│  lessons.md  ← 短期日志（只追加）            │
│  - 失败经验、Constraints To Extract         │
│  - 由 /develop 等命令在失败时写入            │
└─────────────────────────────────────────────┘
                        ▲
                        │ 会话内读写
┌─────────────────────────────────────────────┐
│  session-findings.md  ← 临时缓存（可选）     │
│  - 当前会话的上下文                          │
│  - 会话结束可归档或删除                      │
└─────────────────────────────────────────────┘
```

---

## 校验策略

所有共享工作流变更交付前必须通过仓库校验：

```bash
# Windows
powershell -ExecutionPolicy Bypass -File .claude/scripts/validate-workflow.ps1

# macOS/Linux
python3 .claude/scripts/validate-workflow.py
```

**校验内容**：
- 根目录与源码层必需文件（README.md, CLAUDE.md, lessons.md, .claude/rules/constraints.md）
- `.claude/settings.json` JSON 合法性
- 命令/技能注册一致性
- 命令文件规范性（Usage、阶段、Goal/Verify）
- 技能 YAML frontmatter 完整性

---

## Plugin 构建与本地验证

WorkflowProgram-CN 通过 `tools/build_plugin.py` 生成正式插件产物：

```bash
python3 tools/build_plugin.py
claude --plugin-dir /mnt/d/Code/WorkflowProgram-CN/dist/plugin
```

Plugin 清单位于 `.claude-plugin/plugin.json`，运行时实际消费目录为 `dist/plugin/`。

---

## 关键约束

| 规则 | 说明 |
|------|------|
| **产出物标准** | 所有工作流产出必须包含 `.claude/` 结构，可被 Code Agent 识别 |
| **上下文管理** | 新会话只加载 `constraints.md`，避免 lessons.md 膨胀 |
| **子代理内联** | 只要可以内联提示词，就不依赖外部 agent 文件 |
| **并行限制** | 单次 fan-out 不超过 4 个并行代理 |
| **本地配置隔离** | `.claude/settings.local.json` 不进入共享流程依赖 |

---

## 许可证

MIT
