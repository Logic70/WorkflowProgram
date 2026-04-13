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

### 2.1.2 职责边界与阶段模型

为消除阶段模型与实现边界的漂移，统一约定三层职责：

| 层级 | 责任 | 典型产物 |
|---|---|---|
| runner | 控制面状态转移、边界校验、状态落盘与最小运行证据校验 | `context.json`、`state.json`、`events.jsonl`、`outputs/stages/runner-summary.json` |
| workflowprogram-validate | S5 主 judge，消费 `test_contract`，形成 workflow 级 verdict | `validation-runtime-report.md`、`outputs/stages/s5-validation-summary.json` |
| runtime_smoke | 动态 harness，补充真实执行和环境相关证据 | `transcript.md`、`validation-runtime-report.md`、`outputs/stages/s5-validation-summary.json` |

逻辑阶段与执行阶段的关系如下：

- 逻辑模型仍按 `S0..S6` 统一描述职责归属。
- runner 只负责控制面：状态转移、边界校验、状态落盘与最小运行证据校验。
- `workflow-spec.yaml.stages` 可保持为执行链列表，runner 只按执行链推进，不承担 S5 judge 语义。
- `workflow-spec.yaml.intent_flows` 负责把 `develop/audit/iterate/validate` 映射到逻辑阶段流；runner 至少必须执行当前意图的 `required_stage_slots`。
- `learn` 阶段负责 S6 闭环，不负责替代 S5 判定。

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

为保证每个 Stage 可验证，约定以下设计态证据路径（按场景可裁剪）：

- `RUN_ROOT/outputs/stages/s0-route.json`
- `RUN_ROOT/workflow-spec.md`
- `RUN_ROOT/outputs/stages/s2-context-report.md`
- `RUN_ROOT/workflow-spec.yaml`
- `RUN_ROOT/workflow-view.md`
- `RUN_ROOT/workflow-lowlevel.md`
- `RUN_ROOT/outputs/stages/s3-design-summary.json`
- `RUN_ROOT/outputs/candidate/.claude/`
- `RUN_ROOT/outputs/candidate/.workflowprogram/design/`
- `RUN_ROOT/outputs/managed-change-plan.json`
- `RUN_ROOT/outputs/managed-change-result.json`
- `RUN_ROOT/outputs/stages/s5-validation-summary.json`
- `RUN_ROOT/outputs/stages/s6-lessons-delta.md`

#### 2.5.1 `runtime_contract.required_evidence`（运行态硬约束）

为支撑完整运行测试，`workflow-spec.yaml.runtime_contract.required_evidence` 必须至少包含：

- `context.json`
- `state.json`
- `events.jsonl`
- `outputs/progress/current-progress.json`
- `outputs/progress/milestones.jsonl`
- `outputs/progress/user-progress.md`
- `outputs/stages/s0-route.json`
- `outputs/stages/runner-summary.json`

`workflow-runner.py` 在结束前必须逐项检查上述文件是否存在，缺失即失败。

#### 2.5.2 `runtime_contract.write_boundaries`（写入边界硬约束）

`workflow-spec.yaml.runtime_contract.write_boundaries` 必须声明：

- `target_root_allow`
- `run_root_allow`
- `temp_root_allow`
- `deny`

Runner 在生成每个 artifact 前必须先做边界匹配；命中 `deny` 或不在 allow 列表即失败。

#### 2.5.3 `runtime_contract.failure_kinds` 与 `environment_skip`

- `failure_kinds`：运行结论中的 `failure_kind` 必须来自此枚举。
- `environment_skip`：每个条目必须具备 `code/check/message`，命中后 runner 输出 `ENVIRONMENT-SKIP`，并写入 `skip_reasons` 证据。

#### 2.5.4 `test_contract`（基础运行测试判定契约）

`workflow-spec.yaml.test_contract` 不参与 runner 的执行期状态转移；它的职责是为基础运行测试提供稳定的判定输入。

固定分段：

- `entry`
- `boundary`
- `flow`
- `artifacts`
- `failure`

##### 2.5.4.1 `test_contract.entry`

必须声明：

- `main_entry`
  - 必须能解析到 `registry.commands` 或 `registry.skills` 中的真实入口
- `entry_type`
  - 枚举：`slash_command | natural_language | hybrid`
- `required_args`
  - 必需输入参数列表
- `missing_arg_verdict`
  - 缺参时预期 verdict，必须来自 `PASS/WARN/FAIL/ENVIRONMENT-SKIP`
- `invalid_entry_verdict`
  - 非法入口时预期 verdict，必须来自 `PASS/WARN/FAIL/ENVIRONMENT-SKIP`

##### 2.5.4.2 `test_contract.boundary` 与 `artifacts`

为避免配置漂移，`test_contract` 对执行期硬约束必须采用固定引用语法：

```yaml
ref: runtime_contract.<field>
```

当前允许的固定写法：

- `test_contract.boundary.write_boundaries_ref: runtime_contract.write_boundaries`
- `test_contract.artifacts.evidence_ref: runtime_contract.required_evidence`
- `test_contract.failure.failure_kinds_ref: runtime_contract.failure_kinds`
- `test_contract.failure.environment_skip_ref: runtime_contract.environment_skip`

校验器必须同时检查：

1. 引用语法可解析
2. 引用目标真实存在
3. `test_contract` 中不存在同名复制声明（例如再次声明 `write_boundaries`、`required_evidence`、`failure_kinds`、`environment_skip`）

此外：

- `boundary` 必须补充 `managed_overwrite_policy`、`conflict_expectation`、`external_write_policy`
- `artifacts.deliverables` 必须声明关键交付物
- develop 主链若包含 `S4`，`artifacts.deliverables` 必须包含 `.workflowprogram/managed-files.json`
- `artifacts.optional_outputs` 可声明允许缺失的非关键输出

##### 2.5.4.3 `test_contract.flow`

必须声明：

- `required_stages`
  - 必须发生的阶段，必须是已声明 `stage.id` 的子集
- `skippable_stages`
  - 允许跳过的阶段，必须是已声明 `stage.id` 的子集
- `failure_recovery`
  - 失败类别到回流阶段的映射；键必须来自 `runtime_contract.failure_kinds`，值必须是已声明 `stage.id`
- `terminal_conditions`
  - `PASS/WARN/FAIL/ENVIRONMENT-SKIP -> stage_status` 的终止状态映射

##### 2.5.4.4 `test_contract.failure`

必须声明：

- `failure_kinds_ref`
- `environment_skip_ref`
- `implemented_now`

其中：

- `implemented_now` 必须是 `runtime_contract.failure_kinds` 的子集
- `implemented_now` 只表达“当前实现覆盖度”，不得反向改变 runner 的 `verdict` 或 `failure_kind`
- 当 `runtime_contract.failure_kinds` 已声明但 `implemented_now` 尚未覆盖全部枚举时，视为测试覆盖度缺口，而不是执行契约缺口

#### 2.5.5 验证证据归属

S5 相关证据不归 runner 独占，应由主 judge 与 smoke harness 共同写入：

- `validation-runtime-report.md`
- `outputs/stages/s5-validation-summary.json`
- `transcript.md`

其中：

- `workflowprogram-validate` 负责生成判定结论与 summary。
- `runtime_smoke.py` 负责在 Claude 可用时补充真实执行证据。
- runner 仅负责保留控制面证据，不负责 S5 结果解释。
- `state.json` 与 `events.jsonl` 的字段定义以 [phase-03-step-02-runtime-evidence-spec.md](/mnt/d/Code/WorkflowProgram-CN/docs/phase-03-step-02-runtime-evidence-spec.md) 为准；本节只定义其在 Stage 契约中的归属与引用方式。

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

建议统一调用：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/stage-progress.py update ...
```

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
| S0 | `route_intent_hard_check` | `script_node` | `${CLAUDE_PLUGIN_ROOT}/scripts/route-intent.py` |
| S0 | `emit_route_milestone` | `script_node` | `${CLAUDE_PLUGIN_ROOT}/scripts/stage-progress.py` |
| S1 | `clarify_requirement` | `skill_node` | `workflowprogram-develop` |
| S1 | `draft_spec` | `agent_node` | `requirement_analyst`（或等效子代理） |
| S1 | `persist_spec` | `script_node` | 模板渲染与写盘逻辑 |
| S2 | `scan_target_assets` | `skill_node` | `workflow-audit` |
| S2 | `build_context_report` | `agent_node` | `workflow_designer` / explore 子代理 |
| S3 | `design_workflow` | `agent_node` | `workflow-designer` |
| S3 | `render_yaml_and_view` | `script_node` | spec/view 生成脚本 |
| S3 | `validate_yaml_contract` | `script_node` | `${CLAUDE_PLUGIN_ROOT}/scripts/validate-workflow-spec.py` |
| S3 | `approval_gate` | `gate_node` | 用户审批或 CI 自动审批 |
| S4 | `generate_candidates` | `script_node` | 生成器链（agents/skills/commands/settings） |
| S4 | `validate_generated_files` | `skill_node` | `validate-file` |
| S4 | `plan_apply_managed_assets` | `script_node` | `managed-assets.py` |
| S4 | `product_entry_finalize` | `script_node` | `${CLAUDE_PLUGIN_ROOT}/scripts/workflow-entry.py` |
| S4 | `run_transition_control_plane` | `script_node` | `${CLAUDE_PLUGIN_ROOT}/scripts/workflow-runner.py` |
| S4 | `validate_state_artifacts` | `script_node` | `${CLAUDE_PLUGIN_ROOT}/scripts/validate-run-state.py` |
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
- 若 `target_root` 不存在则先创建目录
- 生成路由证据文件

### 执行过程（封装级）

1. `route_intent`（skill_node）
   - 调用 `workflowprogram-orchestrate` 解析请求语义、路径上下文与意图。
2. `route_intent_hard_check`（script_node）
   - 调用 `${CLAUDE_PLUGIN_ROOT}/scripts/route-intent.py` 进行确定性路由校验；strict 模式下歧义必须阻断。
3. `normalize_target`（script_node）
   - 规范化 `target_root` 绝对路径；若目录不存在则创建，并记录“已存在/本阶段创建”的结果。
4. `persist_route_result`（script_node）
   - 写入 `RUN_ROOT/outputs/stages/s0-route.json`。
5. `emit_route_milestone`（script_node）
   - 追加 `milestones.jsonl`，更新 `current-progress.json`。
6. `notify_user`（script_node）
   - 写入/更新 `user-progress.md`，输出“已路由到哪个主流程”。

### 可验证检查

1. `intent` 必须属于 `develop|audit|iterate|validate`。
2. `target_root` 必须是绝对路径，且目录存在。
3. `s0-route.json` 必须包含 `intent`、`target_root`、`entry_skill` 字段。
4. `s0-route.json` 必须包含 `target_root_preexisting` 与 `target_root_created` 字段。
5. 进展资产 `current-progress.json` 与 `milestones.jsonl` 必须包含 S0 记录。

### 实现方案

- 主承载：`workflowprogram-orchestrate`
- 自然语言入口只开放此 skill，叶子 skill 使用显式 slash。
- 通过 `route-intent.py` 提供确定性路由能力；strict 模式下启用硬性阻断。

### 承载文件

- [workflowprogram-orchestrate/SKILL.md](/mnt/d/Code/WorkflowProgram-CN/.claude/skills/workflowprogram-orchestrate/SKILL.md)
- [.claude/settings.json](/mnt/d/Code/WorkflowProgram-CN/.claude/settings.json)
- [route-intent.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/route-intent.py)

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
   - `workflowprogram-develop` 必须与用户进行多轮澄清。
   - 每轮只提出当前最关键的 1-3 个未决问题；若回答后仍存在会影响设计的歧义，则继续下一轮。
   - 只有当“用户诉求、最终目的、成功标准、触发方式、输入输出、质量门禁”均已明确时，才允许进入草案写入。
2. `draft_spec`（agent_node）
   - `requirement_analyst` 生成规格草案内容，必须把多轮对话收敛结果整理为 `User Intent` 与 `Clarification Summary`。
3. `persist_spec`（script_node）
   - 套用 `spec-template.md`，写入 `RUN_ROOT/workflow-spec.md`。
4. `spec_quality_check`（script_node）
   - 检查是否包含 `TBD/待补`、`User Intent`、`Clarification Summary` 与有效 `澄清轮次`；失败则回到步骤 1。
5. `emit_stage_progress`（script_node）
   - 更新 S1 进展与里程碑，刷新 `user-progress.md`。

### 可验证检查

1. `RUN_ROOT/workflow-spec.md` 文件存在。
2. 文件不包含 `TBD` 或 `待补`。
3. 文件包含输入、输出、触发方式、质量门禁四个段落。
4. 文件必须包含 `User Intent` 与 `Clarification Summary` 两个段落。
5. `Clarification Summary.澄清轮次` 必须是整数，且 `>= 2`。
6. `milestones.jsonl` 至少包含 `clarify_requirement` 和 `persist_spec` 两个节点结果。

### 实现方案

- 主承载：`/develop` Stage 1、`workflowprogram-develop` Step 2
- 模板来源：`skills/develop/spec-template.md`
- 校验承载：`validate-workflow-draft.py`

### 承载文件

- [develop.md](/mnt/d/Code/WorkflowProgram-CN/.claude/commands/develop.md)
- [workflowprogram-develop/SKILL.md](/mnt/d/Code/WorkflowProgram-CN/.claude/skills/workflowprogram-develop/SKILL.md)
- [spec-template.md](/mnt/d/Code/WorkflowProgram-CN/.claude/skills/develop/spec-template.md)
- [validate-workflow-draft.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/validate-workflow-draft.py)

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
- `RUN_ROOT/workflow-lowlevel.md`（维护指导）
- 资产生成清单
- `RUN_ROOT/outputs/stages/s3-design-summary.json`

### 准出目标

- 覆盖阶段定义、节点职责、转移路径、资源约束
- 覆盖执行契约（`runtime_contract`）与基础运行测试契约（`test_contract`）
- 用户 gate 通过（或自动批准）
- YAML 可解析且关键字段齐全

### 执行过程（封装级）

1. `design_workflow`（agent_node）
   - `workflow-designer` 生成阶段结构、节点职责、约束策略。
2. `render_yaml_and_view`（script_node）
   - 先产出 `RUN_ROOT/workflow-spec.yaml`。
   - 再调用 `python ${CLAUDE_PLUGIN_ROOT}/scripts/generate-workflow-view.py --spec <RUN_ROOT>/workflow-spec.yaml --out <RUN_ROOT>/workflow-view.md` 生成只读视图。
   - 再调用 `python ${CLAUDE_PLUGIN_ROOT}/scripts/generate-workflow-lowlevel.py --spec <RUN_ROOT>/workflow-spec.yaml --out <RUN_ROOT>/workflow-lowlevel.md` 生成维护指导文档。
3. `validate_yaml_contract`（script_node）
   - 调用 `${CLAUDE_PLUGIN_ROOT}/scripts/validate-workflow-spec.py --spec <RUN_ROOT>/workflow-spec.yaml`，同时校验 `runtime_contract` 与 `test_contract`；失败则回退到设计步骤。
4. `persist_design_summary`（script_node）
   - 写入 `RUN_ROOT/outputs/stages/s3-design-summary.json`。
5. `approval_gate`（gate_node）
   - 用户审批或 CI 自动批准；人工批准与自动批准必须分别记录为 `approved` 和 `auto-approved`。
6. `emit_stage_progress`（script_node）
   - 记录 S3 关键节点和审批结果，更新用户进展。

### 可验证检查

1. `workflow-spec.yaml` 可被 YAML 解析。
2. 顶层必须包含：`meta`、`stages`、`agent_refs`、`skills`、`registry`、`constraints`、`resource_limits`、`runtime_contract`、`test_contract`。
3. `runtime_contract` 必须包含：`write_boundaries`、`required_evidence`、`failure_kinds`、`environment_skip`。
4. `test_contract` 必须包含：`entry`、`boundary`、`flow`、`artifacts`、`failure`。
5. `test_contract` 中所有 `*_ref` 字段必须采用 `runtime_contract.<field>` 固定语法，且目标字段存在。
6. `test_contract.failure.implemented_now` 必须是 `runtime_contract.failure_kinds` 的子集。
7. `s3-design-summary.json` 必须记录 `approval_status` 与 `complexity`。
8. `workflow-view.md` 必须存在且标注来源 `workflow-spec.yaml`。
9. `workflow-lowlevel.md` 必须存在，并通过 `${CLAUDE_PLUGIN_ROOT}/scripts/validate-workflow-lowlevel.py --spec <workflow-spec.yaml> --lowlevel <workflow-lowlevel.md>` 的确定性校验。
10. `approval_status` 必须写入 `current-progress.json`。
11. `validate-workflow-spec.py` 必须返回 `PASS`。
12. 若存在 `user_approval` gate，则未经批准不得进入 S4。

### 实现方案

- 主承载：`/develop` Stage 3
- YAML 模板来源：`yaml-spec-template.md`
- 视图渲染脚本：`generate-workflow-view.py`（确定性渲染，不依赖自由文本）
- 维护指导渲染脚本：`generate-workflow-lowlevel.py`
- 维护指导校验脚本：`${CLAUDE_PLUGIN_ROOT}/scripts/validate-workflow-lowlevel.py`
- 规格校验脚本：`${CLAUDE_PLUGIN_ROOT}/scripts/validate-workflow-spec.py`

### 承载文件

- [develop.md](/mnt/d/Code/WorkflowProgram-CN/.claude/commands/develop.md)
- [yaml-spec-template.md](/mnt/d/Code/WorkflowProgram-CN/.claude/skills/develop/yaml-spec-template.md)
- [generate-workflow-view.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/generate-workflow-view.py)
- [generate-workflow-lowlevel.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/generate-workflow-lowlevel.py)
- [validate-workflow-lowlevel.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/validate-workflow-lowlevel.py)
- [validate-workflow-spec.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/validate-workflow-spec.py)

## S4 生成与受控写入（Generate + Managed Apply）

### 输入

- `workflow-spec.yaml`
- `target_root`
- `run_root`

### 输出

- `RUN_ROOT/outputs/candidate/.claude/*`
- `RUN_ROOT/outputs/candidate/.workflowprogram/design/*`
- `managed-change-plan.json`
- `managed-change-result.json`
- `managed-change-summary.md`
- 应用后的 `TARGET_ROOT/.claude/*`（无冲突时）
- 应用后的 `TARGET_ROOT/.workflowprogram/design/*`（无冲突时）

### 准出目标

- 所有候选文件可解释、可验证
- unmanaged/drifted 文件不被覆盖
- `managed-files.json` 与 apply 结果一致
- 冲突文件必须落盘到冲突目录

### 执行过程（封装级）

1. `generate_candidates`（script_node）
   - 按 `workflow-spec.yaml` 生成 `RUN_ROOT/outputs/candidate/.claude/*`，并同步准备 `RUN_ROOT/outputs/candidate/.workflowprogram/design/*`。
2. `validate_generated_files`（skill_node）
   - 调 `validate-file` 检查关键候选文件格式与约束。
3. `plan_apply_managed_assets`（script_node）
   - 调 `managed-assets.py plan` 生成变更计划。
4. `apply_or_conflict`（script_node）
   - 无冲突执行 `apply-staged`；有冲突写入 `outputs/conflicts/` 并标记失败分类。
5. `product_entry_finalize`（script_node）
   - develop 主链必须通过 `${CLAUDE_PLUGIN_ROOT}/scripts/workflow-entry.py run --spec <RUN_ROOT>/workflow-spec.yaml --run-root <RUN_ROOT> --target-root <TARGET_ROOT> --entry-skill workflowprogram-develop --request "<原始需求>"` 驱动，而不是只在 skill 中罗列口头顺序。
   - 该脚本必须顺序调用 `validate-workflow-spec.py`、`generate-workflow-view.py`、`generate-workflow-lowlevel.py`、`managed-assets.py`、`workflow-runner.py`、`validate-run-state.py`，并写入 `outputs/stages/entry-orchestration-summary.json`。
6. `run_transition_control_plane`（script_node）
   - 调 `${CLAUDE_PLUGIN_ROOT}/scripts/workflow-runner.py run --spec <RUN_ROOT>/workflow-spec.yaml --run-root <RUN_ROOT> --target-root <TARGET_ROOT>`，由程序执行状态转移并产出 `state.json` / `events.jsonl`。
7. `validate_state_artifacts`（script_node）
   - 调 `${CLAUDE_PLUGIN_ROOT}/scripts/validate-run-state.py --state <RUN_ROOT>/state.json`，强制检查 `kind/producer/status` 枚举。
8. `persist_apply_summary`（script_node）
   - 写入 managed plan/result/summary 与更新 `managed-files.json`。
9. `emit_stage_progress`（script_node）
   - 记录 S4 关键节点结果并更新用户进展。

### 可验证检查

1. `RUN_ROOT/outputs/candidate/.claude/` 与 `RUN_ROOT/outputs/candidate/.workflowprogram/design/` 必须存在。
2. `managed-change-plan.json` 与 `managed-change-result.json` 必须存在。
3. 若存在冲突，`RUN_ROOT/outputs/conflicts/` 必须存在且包含冲突文件副本。
4. `TARGET_ROOT/.workflowprogram/managed-files.json` 必须更新 `updated_at`。
5. `user-progress.md` 必须包含“已应用/冲突”摘要。
6. `RUN_ROOT/state.json` 必须存在且通过 `validate-run-state.py`。
7. `RUN_ROOT/outputs/stages/runner-summary.json` 必须存在。

### 实现方案

- 主承载：`/develop` Stage 4、`workflowprogram-develop` Step 3
- 关键脚本：`workflow-entry.py`、`managed-assets.py`、`workflow-runner.py`、`validate-run-state.py`

### 承载文件

- [develop.md](/mnt/d/Code/WorkflowProgram-CN/.claude/commands/develop.md)
- [workflowprogram-develop/SKILL.md](/mnt/d/Code/WorkflowProgram-CN/.claude/skills/workflowprogram-develop/SKILL.md)
- [workflow-entry.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/workflow-entry.py)
- [managed-assets.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/managed-assets.py)
- [workflow-runner.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/workflow-runner.py)
- [validate-run-state.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/validate-run-state.py)

## S5 验证（Validate）

### 输入

- 目标项目 `.claude/` 资产
- S4 产出证据
- `workflow-spec.yaml.test_contract`

### 输出

- workflow 级结论：`PASS/WARN/FAIL/ENVIRONMENT-SKIP`
- 运行态报告或结构化验证报告
- `RUN_ROOT/outputs/stages/s5-validation-summary.json`
- `RUN_ROOT/transcript.md`
- `RUN_ROOT/validation-runtime-report.md`

### 准出目标

- 关键资产覆盖完成
- 注册、命名、结构、格式无阻断性问题
- 证据链完整可追溯
- 验证结论和失败分类可机读
- 基础运行测试的入口/边界/流程/产物/失败五类判定均有对应检查来源

### 执行过程（封装级）

1. `workflow_validation`（skill_node）
   - 调 `workflowprogram-validate` 形成 workflow 级校验结论；它是 S5 主 judge。
2. `critical_file_checks`（skill_node）
   - 调 `validate-file` 检查关键文件与注册一致性。
3. `runtime_smoke_optional`（script_node）
   - 按需执行 `tools/runtime_smoke.py` 或等效 harness 采集动态证据。
   - 动态验证目标应优先从 `test_contract` 派生；其中执行期边界、skip 与失败枚举仍以 `runtime_contract` 为准。
   - `runtime_smoke.py` 是动态 harness，不是 S5 主 judge。
4. `publish_validation_summary`（script_node）
   - 写入 `RUN_ROOT/outputs/stages/s5-validation-summary.json`。
5. `emit_stage_progress`（script_node）
   - 更新进展、里程碑与用户可见结论。

### 可验证检查

1. `s5-validation-summary.json` 必须包含 `verdict`、`failure_kind`、`checked_files`。
2. 若 verdict=`ENVIRONMENT-SKIP`，必须包含 `environment_reason`。
3. `RUN_ROOT/state.json` 与 `validation-runtime-report.md` 结论必须一致。
4. `milestones.jsonl` 必须记录至少一个关键检查节点结果。
5. 当存在 `test_contract` 时，验证总结必须能够解释其判定目标来源于哪一类契约（入口/边界/流程/产物/失败），即使当前执行器尚未覆盖全部枚举。
6. `validation-runtime-report.md`、`transcript.md` 和 `s5-validation-summary.json` 的责任归属必须清晰区分。

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
- 校验承载：`validate-lessons-delta.py`

### 承载文件

- [develop.md](/mnt/d/Code/WorkflowProgram-CN/.claude/commands/develop.md)
- [workflowprogram-iterate/SKILL.md](/mnt/d/Code/WorkflowProgram-CN/.claude/skills/workflowprogram-iterate/SKILL.md)
- [lessons.md](/mnt/d/Code/WorkflowProgram-CN/lessons.md)
- [constraints.md](/mnt/d/Code/WorkflowProgram-CN/.claude/rules/constraints.md)
- [validate-lessons-delta.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/validate-lessons-delta.py)

## 4. 意图到 Stage 的映射

| 意图 | Stage 流程 |
|---|---|
| `develop` | `S0 -> S1 -> S2 -> S3 -> S4 -> S5 -> S6` |
| `audit` | `S0 -> S5(审计模式) -> S6` |
| `iterate` | `S0 -> S6(提案模式) -> S5(可选)` |
| `validate` | `S0 -> S5 -> S6(可选)` |

## 5. 实施约束

- 不新增脱离 Claude Code 的独立运行时依赖。
- 使用 `workflow-runner.py` 作为统一控制面，执行程序化 Stage 转移与证据落盘。
- 所有新字段必须先写入规范文档，再进入模板与脚本实现。
- Runner 采用“程序控制面 + AI 节点执行”分层：程序负责状态转移、I/O 约束与证据落盘；AI 负责节点语义生成。
- 对 `kind/producer/status` 的枚举约束必须通过 `validate-run-state.py` 强制校验，不得仅依赖提示词约定。

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
