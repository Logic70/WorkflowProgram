# WorkflowProgram Stage High-Level 设计

## 1. 目的与范围

本文档定义 WorkflowProgram 在目标项目中的高层运行逻辑，覆盖：

- 用户界面使用流程（自然语言与 slash）
- 按 Stage 划分的运行逻辑
- 输入、最终输出与项目结构
- 质量要求

本文基于当前实现（`workflowprogram-*` skills、`/develop`、`managed-assets.py`、`RUN_ROOT` 证据模型）编写。  
若与历史文档冲突，以本文和本次讨论形成的新方案为准。

## 2. 设计基线与冲突收敛

### 2.1 基线

- 入口能力由 `workflowprogram-*` skills 承载。
- 自然语言自动触发仅开放 `workflowprogram-orchestrate`。
- 目标项目写入采用 staged candidate + managed apply 流程。
- 运行证据统一写入 `TARGET_ROOT/.workflowprogram/runs/<run-id>/`。

### 2.2 冲突收敛决策

- 决策 D1：优先使用现有 Claude Code 能力边界，不引入脱离现状的独立工作流引擎。
- 决策 D2：`workflow-spec.yaml` 作为流程控制面（control plane）与设计单点真实源。
- 决策 D3：`state` 分为 `values` 与 `artifacts` 两类；文件内容落盘，`state` 仅追踪文件引用与状态。
- 决策 D4：skill/agent 负责节点执行，跨节点轮转由 spec 约束，不由单一大提示词临场决定。
- 决策 D5：所有目标项目写入必须经过 managed asset 链路，禁止静默覆盖。

## 3. 项目结构（高层）

```text
WorkflowProgram-CN/
├── .claude/                 # 源码真源（skills/agents/rules/scripts/settings）
├── .claude-plugin/          # 插件元数据
├── tools/                   # 构建、验证、smoke
├── dist/plugin/             # 仓库内 canonical 运行时载荷目录
├── docs/                    # 设计文档
└── tests/                   # fixtures 与验证证据

TARGET_ROOT/
├── .claude/                 # 最终交付工作流资产
└── .workflowprogram/
    ├── managed-files.json   # managed 文件清单
    └── runs/<run-id>/       # 本次运行证据
```

### 3.1 安装与分发模型（可执行）

`dist/plugin/` 不是“唯一可能安装位置”，而是“仓库内唯一 canonical 运行时载荷目录”。  
用户安装时可以把同构载荷放到任意绝对路径，再通过 `--plugin-dir` 指向该路径。

| 通道 | 载荷来源 | 安装步骤 | 当前状态 |
|---|---|---|---|
| Source Build | 本仓库 `dist/plugin/` | `python3 tools/build_plugin.py` -> `claude --plugin-dir <repo>/dist/plugin` | 受支持 |
| GitHub Release Package | Release 附件中的 `plugin/` 目录 | 下载并解压 -> 校验 `build-manifest.json` -> `claude --plugin-dir <extract>/plugin` | 受支持（当发布包提供时） |
| Marketplace / `/plugin install` | 平台安装器 | 安装后由平台决定目录，仍应可映射到 `PLUGIN_ROOT` 模型 | 未定案 |

### 3.2 GitHub 安装步骤（用户视角）

1. 从 GitHub Release 下载 `workflowprogram-plugin-<version>.tar.gz`（或 zip）。
2. 解压后确认存在 `plugin/skills`、`plugin/agents`、`plugin/commands`、`plugin/.claude-plugin`、`plugin/build-manifest.json`。
3. 在目标项目目录启动：
   `claude --plugin-dir /abs/path/to/plugin`
4. 在会话中执行 `/workflowprogram-orchestrate ...` 或其他 `workflowprogram-*` 入口。

## 4. 用户界面使用流程

### 4.1 入口方式

- 自然语言入口：`workflowprogram-orchestrate`
- 显式入口（slash）：`/workflowprogram-orchestrate`、`/workflowprogram-develop`、`/workflowprogram-audit`、`/workflowprogram-iterate`、`/workflowprogram-validate`

### 4.2 使用过程

1. 用户在目标项目目录发起请求（自然语言或 slash）。
2. `workflowprogram-orchestrate` 识别意图：`develop | audit | iterate | validate`。
3. 系统解析 `TARGET_ROOT`，加载 `PLUGIN_ROOT` 资产。
4. 按意图进入对应 Stage 流程。
5. 产出目标项目资产与运行证据。

### 4.3 输入与最终输出

输入（最小）：

- 用户需求文本
- 目标项目路径（隐式当前目录或显式路径）
- 可选约束（质量门禁、触发方式、是否自动审批）

最终输出（交付层）：

- `TARGET_ROOT/.claude/` 资产（`settings.json`、`skills/`、`agents/`、`rules/`、可选 `commands/`）
- `TARGET_ROOT/.workflowprogram/managed-files.json`
- `RUN_ROOT` 证据（`context.json`、`state.json`、`events.jsonl`、`transcript.md`、`validation-runtime-report.md`、`outputs/`）
- 进展可视化资产（`outputs/progress/current-progress.json`、`outputs/progress/milestones.jsonl`、`outputs/progress/user-progress.md`）

## 5. Stage 运行逻辑（High-Level）

### S0 路由阶段（Route）

- 目标：确定意图与目标项目上下文。
- 入口：`workflowprogram-orchestrate`
- 输出：路由结果与 hand-off 上下文。

### S1 需求澄清阶段（Explore Requirement）

- 目标：把自然语言需求收敛为无歧义规格。
- 输出：`workflow-spec.md`（人类可读规格草案）。

### S2 领域研究阶段（Explore Context）

- 目标：识别目标项目可复用资产、缺口和命名约定。
- 输出：结构化研究结论（供设计阶段使用）。

### S3 结构设计阶段（Design）

- 目标：确定模式组合、节点职责、文件清单与门禁。
- 输出：
  - `workflow-spec.yaml`（机器可读控制面）
  - `workflow-view.md`（只读视图）

### S4 资产生成与受控写入阶段（Generate + Managed Apply）

- 目标：先生成候选，再受控应用到目标项目。
- 输出：
  - `RUN_ROOT/outputs/candidate/.claude/*`
  - `managed-change-plan/result/summary`
  - 应用后的 `TARGET_ROOT/.claude/*`（无冲突场景）

### S5 验证阶段（Validate）

- 目标：形成 workflow 级统一校验结论与运行证据。
- 输出：`PASS | WARN | FAIL | ENVIRONMENT-SKIP` 结论与证据链。

### S6 闭环阶段（Lessons & Constraints）

- 目标：将失败经验、冲突与可复用约束沉淀。
- 输出：`lessons.md` 增量、约束候选、下一轮改进建议。

### 5A. Stage 可验证验收矩阵

| Stage | 可验证准出条件 | 最小证据 |
|---|---|---|
| S0 | `intent` 属于 4 个枚举且 `target_root` 可解析为绝对路径 | `RUN_ROOT/outputs/stages/s0-route.json` |
| S1 | `workflow-spec.md` 存在且不含 `TBD` | `RUN_ROOT/workflow-spec.md` |
| S2 | 上下文报告包含“可复用资产/缺口/命名建议”三段 | `RUN_ROOT/outputs/stages/s2-context-report.md` |
| S3 | `workflow-spec.yaml` 可解析且关键键存在；`workflow-view.md` 已生成 | `RUN_ROOT/workflow-spec.yaml`、`RUN_ROOT/workflow-view.md` |
| S4 | candidate 目录存在；managed plan/result 存在；冲突不覆盖目标文件 | `RUN_ROOT/outputs/candidate/.claude/`、`managed-change-plan/result` |
| S5 | 产生 workflow 级结论，且证据链文件齐全 | `validation-runtime-report.md`、`state.json`、`events.jsonl` |
| S6 | 输出 lessons 增量与约束候选，关联本次 `run-id` | `RUN_ROOT/outputs/stages/s6-lessons-delta.md` |

## 6. Quality 要求

### 6.1 一致性要求

- 所有 Stage 必须声明输入、输出、准出目标和失败反馈路径。
- `workflow-spec.yaml` 字段命名、枚举和状态机转移必须一致。
- 文档中的 `TARGET_ROOT / RUN_ROOT / PLUGIN_ROOT` 含义必须统一。

### 6.2 可靠性要求

- 目标项目资产写入必须先 candidate 后 apply。
- unmanaged 或 drifted 文件不得静默覆盖。
- 每次执行必须产生可追踪证据，且可定位失败阶段。
- 每个 Stage 必须输出进展事件并可回溯关键节点结果。

### 6.3 可维护性要求

- 叶子 skill 只负责节点执行，不承担全流程调度职责。
- 规则与校验脚本必须与真实注册状态同步。
- 设计变更必须同步更新 high-level 与 low-level 文档。

### 6.4 可验证性要求

- 结构校验：`validate-workflow.py/.ps1`
- 运行烟测：`runtime_smoke.py`
- 变更证据：`managed-change-*`、`events.jsonl`、`state.json`

## 7. 与现有实现的关系

- 本设计不推翻现有 `workflowprogram-*` skill 体系。
- 本设计把 `workflow-spec.yaml` 升级为流程控制面，但仍通过现有 skill/agent/script 实现执行。
- 本设计不引入强依赖的新外部运行时；先以当前能力闭环，再渐进增强自动化调度。
