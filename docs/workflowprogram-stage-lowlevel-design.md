# WorkflowProgram Stage Low-Level 设计

## 1. 设计目标

本文档给出各 Stage 的详细设计，包含：

- 输入、输出、准出目标
- 执行过程
- 实现方案
- 承载文件

本文遵循高层设计：[workflowprogram-stage-highlevel-design.md](/mnt/d/Code/WorkflowProgram-CN/docs/workflowprogram-stage-highlevel-design.md)。

## 2. 控制对象定义（State + Artifact）

### 2.1 State.values 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `request_id` | string | 本次请求唯一标识 |
| `intent` | enum | 请求意图（见 2.1.1） |
| `target_root` | string | 目标项目绝对路径 |
| `plugin_root` | string | 插件加载根路径 |
| `run_root` | string | 本次运行证据根路径 |
| `approval_status` | enum | 审批状态（见 2.1.1） |
| `stage_status` | enum | 阶段状态（见 2.1.1） |
| `validation_verdict` | enum | 验证结论（见 2.1.1） |
| `failure_kind` | enum | 失败分类（见 2.1.1） |
| `next_action` | string | 下一步动作建议 |

### 2.1.1 State.values 枚举说明

`intent` 枚举：

| 枚举值 | 中文说明 |
|---|---|
| `develop` | 进入工作流设计与生成主链 |
| `audit` | 进入工作流审计链 |
| `iterate` | 进入基于 lessons 的迭代提案链 |
| `validate` | 进入工作流验证链 |

`approval_status` 枚举：

| 枚举值 | 中文说明 |
|---|---|
| `pending` | 等待用户审批 |
| `approved` | 用户已批准 |
| `rejected` | 用户拒绝，需回退或终止 |
| `auto-approved` | 由 CI 或参数自动放行 |

`stage_status` 枚举：

| 枚举值 | 中文说明 |
|---|---|
| `running` | 阶段执行中 |
| `blocked` | 阶段被 gate 或依赖阻塞 |
| `failed` | 阶段执行失败 |
| `done` | 阶段完成 |

`validation_verdict` 枚举：

| 枚举值 | 中文说明 |
|---|---|
| `PASS` | 验证通过 |
| `WARN` | 存在告警但不阻断 |
| `FAIL` | 存在阻断问题 |
| `ENVIRONMENT-SKIP` | 因环境条件不满足而跳过 |

`failure_kind` 枚举：

| 枚举值 | 中文说明 |
|---|---|
| `none` | 无失败 |
| `design` | 设计问题导致失败 |
| `implementation` | 实现问题导致失败 |
| `environment` | 环境问题导致失败或跳过 |
| `conflict` | 目标文件冲突导致失败 |

### 2.2 State.artifacts 字段

Artifact 使用固定结构：

| 字段 | 类型 | 约束 |
|---|---|---|
| `id` | string | 全局唯一（建议 `<stage>.<name>`） |
| `kind` | enum | 资产类型（见 2.3） |
| `root` | enum | 资产根路径（见 2.2.1） |
| `path` | string | 相对 `root` 的路径，不允许绝对路径 |
| `producer` | enum | 生产阶段（见 2.2.1） |
| `format` | enum | 文件格式（见 2.2.1） |
| `lifecycle` | enum | 生命周期（见 2.2.1） |
| `status` | enum | 资产状态（见 2.2.1） |
| `managed` | bool | 仅 `TARGET_ROOT` 下资产允许 `true` |
| `sha256` | string? | 文件摘要，可选 |

### 2.2.1 Artifact 枚举说明

`root` 枚举：

| 枚举值 | 中文说明 |
|---|---|
| `PLUGIN_ROOT` | 插件运行时载荷目录 |
| `TARGET_ROOT` | 目标项目目录 |
| `RUN_ROOT` | 本次运行证据目录 |
| `TEMP_ROOT` | 临时目录（可清理） |

`producer` 枚举（Stage ID）：

| 枚举值 | 中文说明 |
|---|---|
| `S0` | 路由阶段 |
| `S1` | 需求澄清阶段 |
| `S2` | 领域研究阶段 |
| `S3` | 结构设计阶段 |
| `S4` | 生成与受控写入阶段 |
| `S5` | 验证阶段 |
| `S6` | 闭环阶段 |

`format` 枚举：

| 枚举值 | 中文说明 |
|---|---|
| `md` | Markdown 文档 |
| `yaml` | YAML 配置 |
| `json` | JSON 对象文件 |
| `jsonl` | JSON Lines 事件流文件 |
| `txt` | 纯文本文件 |
| `dir` | 目录类型资产 |

`lifecycle` 枚举：

| 枚举值 | 中文说明 |
|---|---|
| `ephemeral` | 临时产物，可在流程结束后清理 |
| `evidence` | 运行证据，需保留用于追溯 |
| `deliverable` | 交付物，面向目标项目长期保留 |
| `cache` | 缓存产物，可重建 |

`status` 枚举：

| 枚举值 | 中文说明 |
|---|---|
| `planned` | 已规划未生成 |
| `generated` | 已生成待验证 |
| `validated` | 已通过结构或格式验证 |
| `applied` | 已应用到目标位置 |
| `conflict` | 检测到冲突，未应用 |
| `archived` | 已归档，不再参与当前执行 |

### 2.3 `kind` 枚举

| `kind` | 中文指代 | 典型格式 | 典型路径示例 |
|---|---|---|---|
| `spec` | 工作流规格文件 | `md` / `yaml` | `RUN_ROOT/workflow-spec.md`、`RUN_ROOT/workflow-spec.yaml` |
| `view` | 规格渲染视图 | `md` | `RUN_ROOT/workflow-view.md` |
| `agent` | Agent 定义文件 | `md` | `TARGET_ROOT/.claude/agents/security-reviewer.md` |
| `skill` | Skill 定义文件 | `md` | `TARGET_ROOT/.claude/skills/workflowprogram-develop/SKILL.md` |
| `command` | Command 定义文件 | `md` | `TARGET_ROOT/.claude/commands/develop.md` |
| `rule` | 规则或约束文件 | `md` | `TARGET_ROOT/.claude/rules/constraints.md` |
| `settings` | 注册与配置文件 | `json` | `TARGET_ROOT/.claude/settings.json` |
| `report` | 报告类输出 | `md` / `json` | `RUN_ROOT/validation-runtime-report.md` |
| `test_scenario` | 测试场景定义 | `md` | `RUN_ROOT/outputs/test-scenarios.md` |
| `transcript` | 运行转录 | `md` | `RUN_ROOT/transcript.md` |
| `event_log` | 事件日志流 | `jsonl` | `RUN_ROOT/events.jsonl` |
| `state_snapshot` | 状态快照 | `json` | `RUN_ROOT/state.json` |
| `candidate_asset` | 待应用候选资产 | `dir` | `RUN_ROOT/outputs/candidate/.claude/` |
| `managed_manifest` | managed 资产清单 | `json` | `TARGET_ROOT/.workflowprogram/managed-files.json` |
| `managed_plan` | managed 变更计划 | `json` | `RUN_ROOT/outputs/managed-change-plan.json` |
| `managed_result` | managed 应用结果 | `json` | `RUN_ROOT/outputs/managed-change-result.json` |
| `build_manifest` | 插件构建追踪清单 | `json` | `PLUGIN_ROOT/build-manifest.json` |

### 2.4 状态转移约束

- `planned -> generated -> validated -> applied`
- 冲突路径：`generated -> conflict -> archived`
- 禁止跨级跳转（如 `planned -> applied`）。

### 2.5 Stage 证据路径约定

为保证每个 Stage 可验证，约定以下最小证据路径：

- `RUN_ROOT/outputs/stages/s0-route.json`
- `RUN_ROOT/workflow-spec.md`
- `RUN_ROOT/outputs/stages/s2-context-report.md`
- `RUN_ROOT/workflow-spec.yaml`
- `RUN_ROOT/workflow-view.md`
- `RUN_ROOT/outputs/stages/s3-design-summary.json`
- `RUN_ROOT/outputs/candidate/.claude/`
- `RUN_ROOT/outputs/managed-change-plan.json`
- `RUN_ROOT/outputs/managed-change-result.json`
- `RUN_ROOT/outputs/stages/s5-validation-summary.json`
- `RUN_ROOT/outputs/stages/s6-lessons-delta.md`

### 2.6 原子能力规划与质量要求

WorkflowProgram 自身必须按原子能力组织，每个 Stage 必须可拆分为最小执行单元（Node）：

- `skill_node`：由某个 `SKILL.md` 承载的执行单元
- `agent_node`：由某个 agent 提示词承载的分析单元
- `script_node`：由脚本承载的确定性执行单元
- `gate_node`：人工或自动审批单元

每个 Node 必须满足：

1. 输入字段确定（引用 `state.values` 或 `state.artifacts`）。
2. 输出字段确定（至少一个可机读输出）。
3. 失败路径确定（回退、重试或终止）。
4. 证据落盘确定（写入 `RUN_ROOT`）。

### 2.7 运行中进展与历史节点结果契约

除中间状态和日志外，运行时必须向用户持续输出“当前进展 + 历史关键节点结果”。  
约定最小进展资产：

- `RUN_ROOT/outputs/progress/current-progress.json`
- `RUN_ROOT/outputs/progress/milestones.jsonl`
- `RUN_ROOT/outputs/progress/user-progress.md`

`current-progress.json` 最小字段：

- `run_id`
- `current_stage`
- `current_node`
- `percent`
- `updated_at`
- `last_verdict`

`milestones.jsonl` 最小字段：

- `ts`
- `stage`
- `node`
- `status`
- `result`
- `artifact_refs`

`user-progress.md` 最小内容：

- 当前阶段与完成度
- 最近 3 个关键节点结果
- 当前阻塞点（如有）
- 建议下一步

### 2.8 用户播报规则

每个 Stage 至少触发三次播报：

1. `StageStarted`：进入阶段时
2. `StageCheckpoint`：关键 Node 完成时
3. `StageCompleted`：阶段完成时

播报内容必须来自 `current-progress.json` 与 `milestones.jsonl`，不得仅依赖自由文本。

## 3. Stage 详细设计

### 3.1 Stage 封装矩阵（可直接指导生成）

| Stage | 原子 Node | 承载类型 | 默认承载对象 |
|---|---|---|---|
| S0 | `route_intent` | `skill_node` | `workflowprogram-orchestrate` |
| S0 | `emit_route_milestone` | `script_node` | 进展记录脚本（progress writer） |
| S1 | `clarify_requirement` | `skill_node` | `workflowprogram-develop` |
| S1 | `draft_spec` | `agent_node` | `requirement_analyst`（或等效子代理） |
| S1 | `persist_spec` | `script_node` | 模板渲染与写盘逻辑 |
| S2 | `scan_target_assets` | `skill_node` | `workflow-audit` |
| S2 | `build_context_report` | `agent_node` | `workflow_designer` / explore 子代理 |
| S3 | `design_workflow` | `agent_node` | `workflow-designer` |
| S3 | `render_yaml_and_view` | `script_node` | spec/view 生成脚本 |
| S3 | `approval_gate` | `gate_node` | 用户审批或 CI 自动审批 |
| S4 | `generate_candidates` | `script_node` | 生成器链（agents/skills/commands/settings） |
| S4 | `validate_generated_files` | `skill_node` | `validate-file` |
| S4 | `plan_apply_managed_assets` | `script_node` | `managed-assets.py` |
| S5 | `workflow_validation` | `skill_node` | `workflowprogram-validate` |
| S5 | `runtime_smoke_optional` | `script_node` | `tools/runtime_smoke.py` |
| S5 | `publish_validation_summary` | `script_node` | 汇总写盘逻辑 |
| S6 | `extract_lessons` | `skill_node` | `workflowprogram-iterate` |
| S6 | `propose_constraints` | `agent_node` | 规则提炼子代理 |
| S6 | `publish_lessons_delta` | `script_node` | lessons 增量写盘逻辑 |

## S0 路由（workflowprogram-orchestrate）

### 输入

- 用户请求文本
- 当前目录或显式目标路径

### 输出

- `intent`
- `target_root`
- 最小 hand-off 参数集合
- `RUN_ROOT/outputs/stages/s0-route.json`

### 准出目标

- 明确单一意图（`develop/audit/iterate/validate`）
- 明确 `target_root`
- 生成路由证据文件

### 执行过程（封装级）

1. `route_intent`（skill_node）
   - 调用 `workflowprogram-orchestrate` 解析请求语义、路径上下文与意图。
2. `normalize_target`（script_node）
   - 规范化并校验 `target_root` 绝对路径。
3. `persist_route_result`（script_node）
   - 写入 `RUN_ROOT/outputs/stages/s0-route.json`。
4. `emit_route_milestone`（script_node）
   - 追加 `milestones.jsonl`，更新 `current-progress.json`。
5. `notify_user`（script_node）
   - 写入/更新 `user-progress.md`，输出“已路由到哪个主流程”。

### 可验证检查

1. `intent` 必须属于 `develop|audit|iterate|validate`。
2. `target_root` 必须是绝对路径，且目录存在。
3. `s0-route.json` 必须包含 `intent`、`target_root`、`entry_skill` 字段。
4. 进展资产 `current-progress.json` 与 `milestones.jsonl` 必须包含 S0 记录。

### 实现方案

- 主承载：`workflowprogram-orchestrate`
- 自然语言入口只开放此 skill，叶子 skill 使用显式 slash。

### 承载文件

- [workflowprogram-orchestrate/SKILL.md](/mnt/d/Code/WorkflowProgram-CN/.claude/skills/workflowprogram-orchestrate/SKILL.md)
- [.claude/settings.json](/mnt/d/Code/WorkflowProgram-CN/.claude/settings.json)

## S1 需求澄清（Explore Requirement）

### 输入

- `intent=develop`
- 用户需求与约束

### 输出

- `RUN_ROOT/workflow-spec.md`（规格草案）
- 已消解歧义列表

### 准出目标

- 规格字段无 `TBD`
- 触发方式、输入输出、门禁、角色维度明确
- 规格文件落盘到约定路径

### 执行过程（封装级）

1. `clarify_requirement`（skill_node）
   - `workflowprogram-develop` 提最小必要澄清问题并归档答案。
2. `draft_spec`（agent_node）
   - `requirement_analyst` 生成规格草案内容。
3. `persist_spec`（script_node）
   - 套用 `spec-template.md`，写入 `RUN_ROOT/workflow-spec.md`。
4. `spec_quality_check`（script_node）
   - 检查是否包含 `TBD/待补`，失败则回到步骤 1。
5. `emit_stage_progress`（script_node）
   - 更新 S1 进展与里程碑，刷新 `user-progress.md`。

### 可验证检查

1. `RUN_ROOT/workflow-spec.md` 文件存在。
2. 文件不包含 `TBD` 或 `待补`。
3. 文件包含输入、输出、触发方式、质量门禁四个段落。
4. `milestones.jsonl` 至少包含 `clarify_requirement` 和 `persist_spec` 两个节点结果。

### 实现方案

- 主承载：`/develop` Stage 1、`workflowprogram-develop` Step 2
- 模板来源：`skills/develop/spec-template.md`

### 承载文件

- [develop.md](/mnt/d/Code/WorkflowProgram-CN/.claude/commands/develop.md)
- [workflowprogram-develop/SKILL.md](/mnt/d/Code/WorkflowProgram-CN/.claude/skills/workflowprogram-develop/SKILL.md)
- [spec-template.md](/mnt/d/Code/WorkflowProgram-CN/.claude/skills/develop/spec-template.md)

## S2 领域研究（Explore Context）

### 输入

- `workflow-spec.md`
- 目标项目当前 `.claude/` 现状

### 输出

- 可复用资产列表
- 缺口与命名建议
- `RUN_ROOT/outputs/stages/s2-context-report.md`

### 准出目标

- 覆盖 `workflow-spec.md` 指定范围
- 列出可复用与需新建项
- 结构化上下文报告落盘

### 执行过程（封装级）

1. `scan_target_assets`（skill_node）
   - 使用 `workflow-audit` 盘点 `TARGET_ROOT/.claude/` 资产。
2. `diff_with_plugin_assets`（script_node）
   - 对比 `PLUGIN_ROOT` 模板能力与目标现状。
3. `build_context_report`（agent_node）
   - 生成上下文报告（可复用资产、缺口、命名建议）。
4. `persist_context_report`（script_node）
   - 写入 `RUN_ROOT/outputs/stages/s2-context-report.md`。
5. `emit_stage_progress`（script_node）
   - 记录 S2 关键节点结果并更新用户进展。

### 可验证检查

1. `s2-context-report.md` 文件存在。
2. 文件包含 `可复用资产`、`缺口`、`命名建议` 三段。
3. 报告明确引用的目标路径位于 `TARGET_ROOT`。
4. `milestones.jsonl` 中 S2 节点至少有一条 `status=ok` 的上下文报告记录。

### 实现方案

- 主承载：`/develop` Stage 2
- 可调用底层审计技能辅助。

### 承载文件

- [develop.md](/mnt/d/Code/WorkflowProgram-CN/.claude/commands/develop.md)
- [workflow-audit/SKILL.md](/mnt/d/Code/WorkflowProgram-CN/.claude/skills/workflow-audit/SKILL.md)

## S3 结构设计（Design）

### 输入

- `workflow-spec.md`
- S2 上下文结论

### 输出

- `RUN_ROOT/workflow-spec.yaml`（机器可读）
- `RUN_ROOT/workflow-view.md`（只读视图）
- 资产生成清单
- `RUN_ROOT/outputs/stages/s3-design-summary.json`

### 准出目标

- 覆盖阶段定义、节点职责、转移路径、资源约束
- 用户 gate 通过（或自动批准）
- YAML 可解析且关键字段齐全

### 执行过程（封装级）

1. `design_workflow`（agent_node）
   - `workflow-designer` 生成阶段结构、节点职责、约束策略。
2. `render_yaml_and_view`（script_node）
   - 产出 `RUN_ROOT/workflow-spec.yaml` 和 `RUN_ROOT/workflow-view.md`。
3. `persist_design_summary`（script_node）
   - 写入 `RUN_ROOT/outputs/stages/s3-design-summary.json`。
4. `approval_gate`（gate_node）
   - 用户审批或 CI 自动批准。
5. `emit_stage_progress`（script_node）
   - 记录 S3 关键节点和审批结果，更新用户进展。

### 可验证检查

1. `workflow-spec.yaml` 可被 YAML 解析。
2. 顶层必须包含：`meta`、`stages`、`agent_refs`、`skills`、`registry`、`constraints`、`resource_limits`。
3. `s3-design-summary.json` 必须记录 `approval_status` 与 `complexity`。
4. `workflow-view.md` 必须存在且标注来源 `workflow-spec.yaml`。
5. `approval_status` 必须写入 `current-progress.json`。

### 实现方案

- 主承载：`/develop` Stage 3
- YAML 模板来源：`yaml-spec-template.md`

### 承载文件

- [develop.md](/mnt/d/Code/WorkflowProgram-CN/.claude/commands/develop.md)
- [yaml-spec-template.md](/mnt/d/Code/WorkflowProgram-CN/.claude/skills/develop/yaml-spec-template.md)

## S4 生成与受控写入（Generate + Managed Apply）

### 输入

- `workflow-spec.yaml`
- `target_root`
- `run_root`

### 输出

- `RUN_ROOT/outputs/candidate/.claude/*`
- `managed-change-plan.json`
- `managed-change-result.json`
- `managed-change-summary.md`
- 应用后的 `TARGET_ROOT/.claude/*`（无冲突时）

### 准出目标

- 所有候选文件可解释、可验证
- unmanaged/drifted 文件不被覆盖
- `managed-files.json` 与 apply 结果一致
- 冲突文件必须落盘到冲突目录

### 执行过程（封装级）

1. `generate_candidates`（script_node）
   - 按 `workflow-spec.yaml` 生成 `RUN_ROOT/outputs/candidate/.claude/*`。
2. `validate_generated_files`（skill_node）
   - 调 `validate-file` 检查关键候选文件格式与约束。
3. `plan_apply_managed_assets`（script_node）
   - 调 `managed-assets.py plan` 生成变更计划。
4. `apply_or_conflict`（script_node）
   - 无冲突执行 `apply-staged`；有冲突写入 `outputs/conflicts/` 并标记失败分类。
5. `persist_apply_summary`（script_node）
   - 写入 managed plan/result/summary 与更新 `managed-files.json`。
6. `emit_stage_progress`（script_node）
   - 记录 S4 关键节点结果并更新用户进展。

### 可验证检查

1. `RUN_ROOT/outputs/candidate/.claude/` 必须存在。
2. `managed-change-plan.json` 与 `managed-change-result.json` 必须存在。
3. 若存在冲突，`RUN_ROOT/outputs/conflicts/` 必须存在且包含冲突文件副本。
4. `TARGET_ROOT/.workflowprogram/managed-files.json` 必须更新 `updated_at`。
5. `user-progress.md` 必须包含“已应用/冲突”摘要。

### 实现方案

- 主承载：`/develop` Stage 4、`workflowprogram-develop` Step 3
- 关键脚本：`managed-assets.py`

### 承载文件

- [develop.md](/mnt/d/Code/WorkflowProgram-CN/.claude/commands/develop.md)
- [workflowprogram-develop/SKILL.md](/mnt/d/Code/WorkflowProgram-CN/.claude/skills/workflowprogram-develop/SKILL.md)
- [managed-assets.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/managed-assets.py)

## S5 验证（Validate）

### 输入

- 目标项目 `.claude/` 资产
- S4 产出证据

### 输出

- workflow 级结论：`PASS/WARN/FAIL/ENVIRONMENT-SKIP`
- 运行态报告或结构化验证报告
- `RUN_ROOT/outputs/stages/s5-validation-summary.json`

### 准出目标

- 关键资产覆盖完成
- 注册、命名、结构、格式无阻断性问题
- 证据链完整可追溯
- 验证结论和失败分类可机读

### 执行过程（封装级）

1. `workflow_validation`（skill_node）
   - 调 `workflowprogram-validate` 形成 workflow 级校验结论。
2. `critical_file_checks`（skill_node）
   - 调 `validate-file` 检查关键文件与注册一致性。
3. `runtime_smoke_optional`（script_node）
   - 按需执行 `tools/runtime_smoke.py` 采集动态证据。
4. `publish_validation_summary`（script_node）
   - 写入 `RUN_ROOT/outputs/stages/s5-validation-summary.json`。
5. `emit_stage_progress`（script_node）
   - 更新进展、里程碑与用户可见结论。

### 可验证检查

1. `s5-validation-summary.json` 必须包含 `verdict`、`failure_kind`、`checked_files`。
2. 若 verdict=`ENVIRONMENT-SKIP`，必须包含 `environment_reason`。
3. `RUN_ROOT/state.json` 与 `validation-runtime-report.md` 结论必须一致。
4. `milestones.jsonl` 必须记录至少一个关键检查节点结果。

### 实现方案

- 主承载：`workflowprogram-validate`
- 工具承载：`validate-workflow.py/.ps1`、`runtime_smoke.py`

### 承载文件

- [workflowprogram-validate/SKILL.md](/mnt/d/Code/WorkflowProgram-CN/.claude/skills/workflowprogram-validate/SKILL.md)
- [validate-workflow.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/validate-workflow.py)
- [validate-workflow.ps1](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/validate-workflow.ps1)
- [runtime_smoke.py](/mnt/d/Code/WorkflowProgram-CN/tools/runtime_smoke.py)
- [phase-03-step-02-runtime-evidence-spec.md](/mnt/d/Code/WorkflowProgram-CN/docs/phase-03-step-02-runtime-evidence-spec.md)

## S6 闭环（Lessons & Constraints）

### 输入

- S5 验证结论（若本轮包含验证阶段）
- 失败或冲突证据

### 输出

- lessons 增量
- 规则候选或约束更新建议
- 下一轮迭代建议
- `RUN_ROOT/outputs/stages/s6-lessons-delta.md`

### 准出目标

- 失败经验可复用、可检索
- 约束演进建议与证据关联
- 产出包含本次 `run_id`

### 执行过程（封装级）

1. `extract_lessons`（skill_node）
   - 调 `workflowprogram-iterate` 或等效逻辑提炼经验项。
2. `propose_constraints`（agent_node）
   - 形成规则候选与影响范围说明。
3. `publish_lessons_delta`（script_node）
   - 写入 `RUN_ROOT/outputs/stages/s6-lessons-delta.md`。
4. `update_lessons_registry`（script_node）
   - 将可落地项追加到 `lessons.md`。
5. `emit_stage_progress`（script_node）
   - 输出最终阶段总结与关键节点历史回顾。

### 可验证检查

1. `s6-lessons-delta.md` 必须存在。
2. 产出必须包含 `run_id` 与 `failure_kind`。
3. 至少包含一条可执行约束候选或显式声明“无新增约束”。
4. `user-progress.md` 必须包含“历史关键节点结果”汇总段落。

### 实现方案

- 主承载：`/develop` Stage 6
- 辅助承载：`workflowprogram-iterate`

### 承载文件

- [develop.md](/mnt/d/Code/WorkflowProgram-CN/.claude/commands/develop.md)
- [workflowprogram-iterate/SKILL.md](/mnt/d/Code/WorkflowProgram-CN/.claude/skills/workflowprogram-iterate/SKILL.md)
- [lessons.md](/mnt/d/Code/WorkflowProgram-CN/lessons.md)
- [constraints.md](/mnt/d/Code/WorkflowProgram-CN/.claude/rules/constraints.md)

## 4. 意图到 Stage 的映射

| 意图 | Stage 流程 |
|---|---|
| `develop` | `S0 -> S1 -> S2 -> S3 -> S4 -> S5 -> S6` |
| `audit` | `S0 -> S5(审计模式) -> S6` |
| `iterate` | `S0 -> S6(提案模式) -> S5(可选)` |
| `validate` | `S0 -> S5 -> S6(可选)` |

## 5. 实施约束

- 不新增脱离 Claude Code 的独立运行时依赖。
- 先用现有 skill/agent/script 实现 Stage 执行，再渐进增强自动调度。
- 所有新字段必须先写入规范文档，再进入模板与脚本实现。

## 6. 安装与分发 Low-Level 契约

### 6.1 Canonical 载荷定义

- 仓库内 canonical 载荷目录：`dist/plugin/`
- 载荷最小结构：
  - `skills/`
  - `agents/`
  - `commands/`
  - `rules/`
  - `scripts/`
  - `.claude-plugin/`
  - `build-manifest.json`

### 6.2 GitHub Release 安装契约

当以 GitHub 发布包分发时，发布包必须解压为如下结构：

```text
workflowprogram-plugin-<version>/
└── plugin/
    ├── skills/
    ├── agents/
    ├── commands/
    ├── rules/
    ├── scripts/
    ├── .claude-plugin/
    └── build-manifest.json
```

用户安装命令：

```bash
claude --plugin-dir /abs/path/to/workflowprogram-plugin-<version>/plugin
```

### 6.3 发布包验收检查

1. `build-manifest.json.plugin_version` 与 release tag 一致。
2. `build-manifest.json.files[]` 中的路径在发布包中全部可找到。
3. 启动后可识别 `/workflowprogram-orchestrate` 入口。
