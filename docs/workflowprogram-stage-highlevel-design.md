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
- 自然语言自动触发策略仅开放 `workflowprogram-orchestrate`，并通过 `route-intent.py` 提供确定性路由（strict 模式可硬阻断歧义）。
- 主产品入口的确定性脚本链为 `workflow-entry.py -> managed-assets.py -> workflow-runner.py -> validate-run-state.py`；叶子 skill 不应只靠提示词顺序隐式串联这些脚本。
- 目标项目写入采用 staged candidate + managed apply 流程。
- 运行证据统一写入 `TARGET_ROOT/.workflowprogram/runs/<run-id>/`。

### 2.2 冲突收敛决策

- 决策 D1：优先使用现有 Claude Code 能力边界，不引入脱离现状的独立工作流引擎。
- 决策 D2：`workflow-spec.yaml` 作为流程控制面（control plane）与设计单点真实源。
- 决策 D3：`state` 分为 `values` 与 `artifacts` 两类；文件内容落盘，`state` 仅追踪文件引用与状态。
- 决策 D4：skill/agent 负责节点执行，跨节点轮转由 spec 约束，不由单一大提示词临场决定。
- 决策 D5：所有目标项目写入必须经过 managed asset 链路，禁止静默覆盖。
- 决策 D6：Runner 采用“程序控制面 + AI 节点执行”分层；程序负责状态转移与约束检查，AI 负责节点语义工作。
- 决策 D7：`workflow-spec.yaml` 同时承载 `runtime_contract` 与 `test_contract`；前者定义执行期硬约束，后者定义基础运行测试的判定语义。
- 决策 D8：`test_contract` 只能通过 `runtime_contract.<field>` 引用执行约束，禁止复制或削弱 runner 已声明的执行语义。
- 决策 D9：逻辑阶段模型与执行阶段列表分离。`S0..S6` 用于统一描述职责与证据归属，具体执行链可由 `workflow-spec.yaml.stages` 承载；其中 `workflowprogram-validate` 负责 S5 判定，`runtime_smoke.py` 负责补充运行态证据，`learn` 负责 S6 闭环。
- 决策 D10：`workflow-spec.yaml.intent_flows` 作为“意图到逻辑阶段流”的机器可读真源；`test_contract.flow` 默认表达 `develop` 主链，其他意图流由 `intent_flows` 解释。

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

### 4.2A 意图到 Stage 流程

- `develop`: `S0 -> S1 -> S2 -> S3 -> S4 -> S5 -> S6`
- `audit`: `S0 -> S5(审计模式) -> S6`
- `iterate`: `S0 -> S6(提案模式) -> S5(可选)`
- `validate`: `S0 -> S5 -> S6(可选)`

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
- 规范要求：
  - `target_root` 必须解析为绝对路径。
  - `S0` 准出前 `target_root` 必须已存在；若路径不存在，系统必须先创建目录并记录该结果。
  - 路由证据必须记录 `intent`、`entry_skill`、`target_root` 与“目录原本已存在/本阶段创建”的事实。

### S1 需求澄清阶段（Explore Requirement）

- 目标：通过持续多轮对话把自然语言需求收敛为无歧义规格，明确用户诉求、最终目的与成功标准。
- 输出：`workflow-spec.md`（人类可读规格草案）。
- 适用范围：仅适用于 `develop` 主链；`audit / iterate / validate` 不进入 S1，除非后续设计显式扩展。
- 规范要求：
  - S1 不得只做单轮问答后立即结束；只要仍存在会影响设计的歧义，就必须继续向用户追问。
  - 每轮只聚焦当前最高优先级的未决问题，直到“用户诉求 / 最终目的 / 成功标准 / 触发方式 / 输入输出 / 质量门禁”全部明确。
  - `workflow-spec.md` 必须包含 `User Intent` 与 `Clarification Summary`，用于记录澄清收敛结果。

### S2 领域研究阶段（Explore Context）

- 目标：识别目标项目可复用资产、缺口和命名约定。
- 输出：结构化研究结论（供设计阶段使用）。

### S3 结构设计阶段（Design）

- 目标：确定模式组合、节点职责、文件清单与门禁。
- 输出：
  - `workflow-spec.yaml`（机器可读控制面）
  - `runtime_contract`（内嵌于 `workflow-spec.yaml`，定义写入边界、证据集、失败枚举、环境 skip）
- `test_contract`（内嵌于 `workflow-spec.yaml`，定义入口/边界/流程/产物/失败五类基础测试判定）
  - 其中 `test_contract.flow` 默认表达 `develop` 主链；非 `develop` 流转由 `intent_flows` 约束
  - `workflow-view.md`（只读视图）
  - `workflow-lowlevel.md`（维护与迭代指导；不得覆盖 YAML 语义）
- 规范要求：
  - `develop` 主链必须在 S3 完成后经过审批 gate，方可进入 S4。
  - 审批记录必须区分 `approved`（人工批准）与 `auto-approved`（CI 或参数自动放行）。

### S4 资产生成与受控写入阶段（Generate + Managed Apply）

- 目标：先生成候选，再受控应用到目标项目。
- 输出：
  - `RUN_ROOT/outputs/candidate/.claude/*`
  - `RUN_ROOT/outputs/candidate/.workflowprogram/design/*`
  - `managed-change-plan/result/summary`
  - `TARGET_ROOT/.workflowprogram/managed-files.json`
  - 应用后的 `TARGET_ROOT/.claude/*`（无冲突场景）
  - 应用后的 `TARGET_ROOT/.workflowprogram/design/{workflow-spec.yaml,workflow-view.md,workflow-lowlevel.md}`（无冲突场景）

### S5 验证阶段（Validate）

- 目标：形成 workflow 级统一校验结论与运行证据。
- 目标补充：基础运行测试必须覆盖 `entry / boundary / flow / artifacts / failure` 五类契约；执行期语义以 `runtime_contract` 为准，判定语义以 `test_contract` 为准。
- 主承载：`workflowprogram-validate`
- 辅助证据：`runtime_smoke.py`
- 输出：`PASS | WARN | FAIL | ENVIRONMENT-SKIP` 结论与证据链，至少包含 `validation-runtime-report.md` 与 `outputs/stages/s5-validation-summary.json`。
- 证据归属：
  - `context.json`、`state.json`、`events.jsonl` 属于运行态/控制面证据，由 runner 负责保留。
  - `validation-runtime-report.md` 与 `outputs/stages/s5-validation-summary.json` 属于 S5 判定产物。
  - `transcript.md` 属于动态运行证据，由 `runtime_smoke.py` 或等效 harness 补充，供 S5 消费。

### S6 闭环阶段（Lessons & Constraints）

- 目标：将失败经验、冲突与可复用约束沉淀。
- 输出：`lessons.md` 增量、约束候选、下一轮改进建议。

### 5A. Stage 可验证验收矩阵

| Stage | 可验证准出条件 | 最小证据 |
|---|---|---|
| S0 | `intent` 属于 4 个枚举，`target_root` 为绝对路径且目录已存在（不存在时已创建） | `RUN_ROOT/outputs/stages/s0-route.json` |
| S1 | `workflow-spec.md` 存在、不含 `TBD/待补`，包含 `User Intent` 与 `Clarification Summary`，且保留触发方式/输入/输出/质量门禁四段；`澄清轮次 >= 2` | `RUN_ROOT/workflow-spec.md` |
| S2 | 上下文报告包含“可复用资产/缺口/命名建议”三段 | `RUN_ROOT/outputs/stages/s2-context-report.md` |
| S3 | `workflow-spec.yaml` 可解析且关键键存在（含 `runtime_contract` 与 `test_contract`）；`workflow-view.md` 与 `workflow-lowlevel.md` 已生成，且 `workflow-lowlevel.md` 可由 `workflow-spec.yaml` 确定性重算；审批状态已记录且未绕过 gate | `RUN_ROOT/workflow-spec.yaml`、`RUN_ROOT/workflow-view.md`、`RUN_ROOT/workflow-lowlevel.md`、`outputs/stages/s3-design-summary.json` |
| S4 | candidate 目录存在；managed plan/result 存在；`TARGET_ROOT/.workflowprogram/managed-files.json` 已写入且带 `updated_at`；目标侧设计包已持久化；冲突不覆盖目标文件 | `RUN_ROOT/outputs/candidate/.claude/`、`RUN_ROOT/outputs/candidate/.workflowprogram/design/`、`managed-change-plan/result`、`TARGET_ROOT/.workflowprogram/managed-files.json` |
| S5 | 产生 workflow 级结论，且证据链文件齐全 | `validation-runtime-report.md`、`outputs/stages/s5-validation-summary.json` |
| S6 | 输出 lessons 增量与约束候选，关联本次 `run-id` 与 `failure_kind`，且 `user-progress.md` 含“历史关键节点结果” | `RUN_ROOT/outputs/stages/s6-lessons-delta.md` |

### 5B. 基础运行测试契约

为避免把测试规则散落在自由文本中，`workflow-spec.yaml` 必须显式声明：

- `runtime_contract`
  - 执行期硬约束：写入边界、最小证据集、失败类别枚举、环境 skip 条件
- `test_contract`
  - 基础运行测试判定：`entry / boundary / flow / artifacts / failure`

统一原则：

- `runtime_contract` 决定 runner 可以做什么、必须保留什么、如何降级。
- `test_contract` 决定基础测试应检查什么、哪些结果算通过或失败。
- `workflowprogram-validate` 是 `test_contract` 的主消费方，`runtime_smoke.py` 是补充烟测与证据采集工具。
- `test_contract` 对执行字段只允许引用，不允许复制同名内容。
- `test_contract.failure.implemented_now` 仅表达“当前实现覆盖度”，不得反向改变 runner 的 `verdict` 或 `failure_kind` 语义。

## 5C. 产品入口编排

- `workflowprogram-orchestrate` 负责意图路由，不负责替代控制面脚本链。
- `workflowprogram-develop` 的确定性脚本入口是 `${CLAUDE_PLUGIN_ROOT}/scripts/workflow-entry.py run`。
- `workflow-entry.py` 必须按固定顺序执行：
  - `validate-workflow-spec.py`
  - `generate-workflow-view.py`
  - `generate-workflow-lowlevel.py`
  - `managed-assets.py plan/apply-staged`
  - `workflow-runner.py run`
  - `validate-run-state.py`
- 编排结果必须落盘到 `RUN_ROOT/outputs/stages/entry-orchestration-summary.json`。

基础运行测试的统一场景骨架至少包含：

- 标准成功场景
- 非法入口场景
- 边界/冲突场景
- 流程阻断场景
- 环境不足场景

每个具体工作流可在 `test_contract` 中进一步裁剪判定目标，但不得绕开上述五类契约。

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
- 统一 runner 负责状态转移与 enum 约束落盘，避免仅靠自然语言约定驱动流程。
- develop 主链必须通过 `workflow-entry.py` 串起 spec/view/managed-assets/runner/state 校验，而不是由 skill 自由决定脚本顺序。

### 6.4 可验证性要求

- 结构校验：`validate-workflow.py/.ps1`
- 运行烟测：`runtime_smoke.py`
- 变更证据：`managed-change-*`、`events.jsonl`、`state.json`
- spec 契约校验：`validate-workflow-spec.py` 同时校验 `runtime_contract` 与 `test_contract`
- 判定边界：runner 只执行 `runtime_contract`；`test_contract` 由 validator、验证技能或外部 harness 消费

## 7. 与现有实现的关系

- 本设计不推翻现有 `workflowprogram-*` skill 体系。
- 本设计把 `workflow-spec.yaml` 升级为流程控制面，但仍通过现有 skill/agent/script 实现执行。
- 本设计不引入强依赖的新外部运行时；先以当前能力闭环，再渐进增强自动化调度。
- 当前 runner 已以脚本化控制面落地（`workflow-runner.py` + `validate-workflow-spec.py` + `validate-run-state.py`），并与 `managed-assets.py`、`stage-progress.py`、`generate-workflow-view.py` 组成闭环。
- 当前 develop 产品入口已通过 `workflow-entry.py` 收口为确定性脚本编排。
- 当前 S5 验证链路由 `workflowprogram-validate`、`runtime_smoke.py` 和 `s5-validation-summary.json` 构成，不由 runner 单独承担。
