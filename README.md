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

```text
# 设计一个新工作流
/develop "创建一个用于每日收集科技新闻的工作流"

# 审计现有工作流
/evolve-workflow /path/to/existing-workflow

# 交付当前变更
/preflight  # 预检查
/ship        # 正式交付
```

---

## 核心能力

### 1. 工作流设计（/develop）

从需求到完整工作流仓库的端到端设计：

```text
/develop "创建一个用于每日收集科技新闻并生成摘要的工作流"
```

**阶段**：
1. 需求分析 → 2. 规格定义 → 3. 架构设计 → 4. 代码生成 → 5. 验证交付

### 2. 交付流水线（/ship, /preflight, /hotfix）

| 命令 | 用途 |
|------|------|
| `/ship [<scope>]` | 顺序执行审查、校验和提交准备 |
| `/preflight [<scope>]` | 并行预检查，不创建提交 |
| `/hotfix [<description>]` | 热修复精简流程 |

### 3. 工作流演进（/evolve-workflow, /iterate-workflow）

| 命令 | 用途 |
|------|------|
| `/evolve-workflow <path>` | 审计目标工作流，识别结构问题 |
| `/iterate-workflow [--apply] <path>` | 从 lessons.md 生成改进方案 |

---

## 架构设计

WorkflowProgram-CN 采用分层结构，将不同类型的资产分离：

```
WorkflowProgram-CN/
├── .claude/
│   ├── commands/          # 用户可见命令（/develop, /ship 等）
│   ├── skills/            # 可复用技能模板
│   ├── agents/            # 专家角色定义
│   ├── rules/             # 长期约束与规范
│   ├── scripts/           # 可执行校验脚本
│   └── settings.json      # 命令/技能注册中心
│
├── commands/              # 根级命令（Plugin 模式兼容）
├── skills/                # 根级技能（Plugin 模式兼容）
├── agents/                # 根级 Agent（Plugin 模式兼容）
├── rules/                 # 根级规则（Plugin 模式兼容）
├── scripts/               # 根级脚本（Plugin 模式兼容）
│
├── CLAUDE.md              # 项目说明（Claude Code 优先读取）
├── README.md              # 本文件
├── lessons.md             # 经验日志（失败记录、待提取约束）
└── validation-report.md   # 校验报告
```

### 资产分层原则

| 位置 | 用途 | 经验法则 |
|------|------|----------|
| `scripts/` | 可确定、可复验的检查 | 能自动化的校验放脚本 |
| `commands/`, `skills/` | 流程编排 | 用户交互和流程控制 |
| `agents/` | 角色职责 | AI 子代理的提示词定义 |
| `rules/` | 长期约束 | 沉淀为 ALWAYS/NEVER 规则 |

---

## 命令清单

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

### 用户可用技能
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
- 根目录必需文件（README.md, CLAUDE.md, lessons.md, constraints.md）
- `.claude/settings.json` JSON 合法性
- 命令/技能注册一致性
- 命令文件规范性（Usage、阶段、Goal/Verify）
- 技能 YAML frontmatter 完整性

---

## Plugin 模式（可选）

WorkflowProgram-CN 同时支持作为 Claude Code Plugin 加载：

```bash
# 同步根级资产
python3 tools/sync_plugin_assets.py

# 以 Plugin 模式启动
claude --plugin-dir /mnt/d/Code/WorkflowProgram-CN
```

Plugin 清单位于 `.claude-plugin/plugin.json`

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
