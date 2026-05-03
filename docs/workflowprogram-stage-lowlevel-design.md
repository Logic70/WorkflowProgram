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
| `host_capability_report` | 宿主能力探测结果 | `json` | `RUN_ROOT/outputs/stages/host-capability-report.json` |
| `team_plan` | Team fan-out 计划 | `json` | `RUN_ROOT/outputs/stages/team-plan.json` |
| `team_result` | Team 执行结果 | `json` | `RUN_ROOT/outputs/stages/team-results.json` |
| `team_join` | Team join 汇总 | `json` | `RUN_ROOT/outputs/stages/team-join-summary.json` |

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
- 条件性 `RUN_ROOT/outputs/stages/host-capability-report.json`
- 条件性 `RUN_ROOT/outputs/stages/host-bootstrap-plan.json`
- 条件性 `RUN_ROOT/outputs/stages/team-plan.json`
- 条件性 `RUN_ROOT/outputs/stages/team-results.json`
- 条件性 `RUN_ROOT/outputs/stages/team-join-summary.json`

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
- develop 主链若交付目标侧 runtime，`artifacts.deliverables` 必须包含 `.workflowprogram/runtime/runtime-manifest.json`
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

#### 2.5.5 `generated_runtime_contract`（目标工作流运行时契约）

`workflow-spec.yaml.generated_runtime_contract` 用于声明目标工作流自身交付的 deterministic runtime 包装层。当前模式固定为：

- `mode: shared-control-plane-wrapper`

必须字段：

- `runtime_root`
- `design_spec_path`
- `entry_script`
- `runner_script`
- `state_validator_script`
- `runtime_manifest`
- `run_root_dir`
- `mode`
- `runtime_capabilities`

固定约束：

1. `mode` 当前只能是 `shared-control-plane-wrapper`。
2. `runtime_capabilities` 必须是以下枚举的非空子集：
   - `state_transitions`
   - `run_state_validation`
   - `capability_discovery`
   - `host_capability_probe`
   - `team_orchestration`
3. `runtime_capabilities` 必须始终包含：
   - `state_transitions`
   - `run_state_validation`
4. 当声明 `capability_discovery.enabled=true` 时，`runtime_capabilities` 必须包含 `capability_discovery`。
5. 当声明 `host_capabilities` 时，`runtime_capabilities` 必须包含 `host_capability_probe`。
6. 当声明 `agent_team_contract.enabled=true` 时，`runtime_capabilities` 必须包含 `team_orchestration`。
7. 目标工作流 runtime 通过 wrapper 调共享控制面脚本，不复制一套独立 runner。

#### 2.5.5A `workflow_graph`（目标工作流业务图契约）

`workflow-spec.yaml.workflow_graph` 是可选 top-level section，用于描述生成后的目标工作流自己的业务节点、入口、转移、输出与 gate。它与 WorkflowProgram 自身的 `stages` / `intent_flows` 分层：

- `stages` / `intent_flows`：WorkflowProgram 开发、审计、迭代、验证控制面，仍按 `S0..S6` 归属证据。
- `workflow_graph`：目标工作流的业务执行图，不强制套用 `S1..S6`，可使用 `collect_input`、`reverse_binary`、`triage_findings` 等请求特定节点。
- `workflow-spec.yaml`：唯一机器语义真源。
- `workflow-spec.md`：需求澄清后的用户回读材料。
- `workflow-view.md` / `workflow-lowlevel.md`：从 YAML 派生的只读概览与维护说明，不得反向覆盖 graph 语义。

必须字段：

- `schema_version`
- `templates_used`
- `entrypoints`
- `nodes`
- `transitions`

节点必须声明：

- `id`
- `role`
- `template`
- `input_refs`
- `output_refs`
- `gate`
- `owner`

固定约束：

1. `entrypoints[*].name` 必须能解析到 `registry.commands` 或 `registry.skills`。
2. `transitions[*].from/to` 必须引用已声明节点或终止状态。
3. 所有节点必须能从至少一个 entrypoint 到达。
4. 目标资产类 `output_refs` 必须能回到 `registry` 或 `test_contract.artifacts`，避免生成未声明文件。
5. 修改目标工作流图时，只能先改 `workflow-spec.yaml.workflow_graph`，再重新生成 `workflow-view.md` 与 `workflow-lowlevel.md`。

#### 2.5.6 `capability_discovery`（能力发现与推荐契约）

`workflow-spec.yaml.capability_discovery` 是可选 top-level section，用于在 `host_capabilities` 最终定稿前，生成候选 `skill / MCP / CLI` 能力和结构化人工指引。

每项约束：

- `enabled` 必须存在
- `domains` 可选，但若存在必须是小写 slug 列表
- `include_local_installed` / `include_curated_profiles` / `infer_from_request` 只能是布尔值
- 若未提供 `domains`，则 `infer_from_request` 必须为 `true`
- `profile_overrides` 可选；若存在：
  - `exclude_capability_ids` 必须是小写 slug 列表
  - `replace_capabilities` 必须是列表；每项至少包含 `replaces / id / kind / name / probe`
  - `disable_team_default` 只能是布尔值
- 画像默认值只能产生推荐，不得覆盖用户显式声明的 `host_capabilities` 或 `agent_team_contract`

运行时规则：

1. `discover-host-capabilities.py` 负责把候选推荐写到 `RUN_ROOT/outputs/stages/host-capability-candidates.json`。
2. 同一脚本还必须写入 `RUN_ROOT/outputs/stages/host-bootstrap-instructions.md`，其中包含 `manual_steps`、`expected_outputs`、`recheck_hint`。
3. `capability_discovery` 只产生推荐和人工指引，不直接改动 `TARGET_ROOT`。
4. 若声明 `capability_discovery.enabled=true`，产品入口与目标侧 runtime 入口都必须先执行 discovery，再进入 host probe/bootstrap。
5. 领域画像输出必须在 discovery report 中保留：
   - `summary`
   - `suggested_host_capabilities`
   - `suggested_agent_team_contract`（若有）
   - `team_default_recommended`
   - `excluded_capability_ids`
   - `replaced_capability_ids`
6. 当前至少支持 `reverse_engineering` 画像；该画像可推荐逆向分析基础工具链，并可选推荐 triage / static / dynamic / review 四类 team 角色作为默认草案。

#### 2.5.7 `host_capabilities`（宿主能力契约）

`workflow-spec.yaml.host_capabilities` 是可选 top-level section，用于声明工作流依赖的宿主专业能力。

每项必须包含：

- `id`
- `kind`
- `name`
- `required`
- `probe`
- `approval_required`

其中：

- `kind` 只能是：`mcp_server | codex_skill | claude_skill | external_binary`
- `probe` 必须是结构化对象，不接受任意 shell string
- `bootstrap.scope` 只能是：`project_local | host_global | manual_only`
- `bootstrap.project_local_outputs` 只能落在 `TARGET_ROOT/.workflowprogram/bootstrap/**`
- `bootstrap.assets` 只允许在 `bootstrap.scope=project_local` 时声明，并且每个 asset 的 `path` 都必须落在 `TARGET_ROOT/.workflowprogram/bootstrap/**`
- `host_global` bootstrap 必须 `approval_required=true`

运行时规则：

1. `probe-host-capabilities.py` 负责把探测结果写到 `RUN_ROOT/outputs/stages/host-capability-report.json`。
2. 若存在缺口，同时必须写 `RUN_ROOT/outputs/stages/host-bootstrap-plan.json`。
3. `apply-host-bootstrap.py` 只允许自动执行 `project_local + approval_required=false` 的 bootstrap。
4. 若声明 `bootstrap.assets`，`apply-host-bootstrap.py` 必须按声明式格式真实生成配置 / wrapper / marker 文件，并把 materialized asset 与 re-check 结果写入 apply 证据和 target bootstrap manifest。
5. `host_global` 与 `manual_only` 只产生 plan 和待处理指引，WorkflowProgram 不自动执行宿主全局变更。
6. `manual_only` 永不自动执行，只产生 plan。
7. 只要存在 `required && status != ready`，最终 verdict 必须为 `FAIL`，且 `failure_kind=environment`，但 runner 仍需完整落证。
8. `generate-environment-remediation.py` 必须把当前 run 的 host readiness 与 `TARGET_ROOT/.workflowprogram/runs/*` 中的历史环境失败聚合为 `environment-remediation-report.json` 与 `environment-remediation-guide.md`。
9. remediation guide 必须显式包含 unresolved manual steps、expected outputs 与 re-check 指引，不能只保留 readiness failed。

#### 2.5.8 `agent_team_contract`（显式 Team 契约）

`workflow-spec.yaml.agent_team_contract` 是可选 top-level section，仅在 `enabled=true` 时生效。

必须字段：

- `enabled`
- `max_fan_out`
- `join_policy`
- `roles`
- `execution`

固定约束：

1. `max_fan_out <= 4`
2. 每个 role 必须包含：
   - `id`
   - `responsibility`
   - `ownership_stage_slots`
   - `output_patterns`
   - `required`
3. `ownership_stage_slots` 只能使用 `S1..S6`
4. `execution[*].role_ids` 数量不得超过 `max_fan_out`
5. `join_role` 必须引用已声明 role

运行时证据要求：

- `RUN_ROOT/outputs/stages/team-plan.json`
- `RUN_ROOT/outputs/stages/team-results.json`
- `RUN_ROOT/outputs/stages/team-join-summary.json`
- `events.jsonl` 至少包含：
  - `TeamFanOutStart`
  - `TeamRoleStarted`
  - `TeamRoleCompleted`
  - `TeamJoinCompleted`

执行策略：

- `fixture_host / command_adapter` 必须执行 full orchestration，并按契约生成 team evidence。
- `claude_cli` 第一版只校验证据与契约，不承诺强调度；缺结构化 team evidence 时只能降为 `WARN`，不得视作 clean PASS。

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

`stage-progress.py` 仍然是 `script_node`，但首选调用路径是 runner / control-plane helper 的内部封装；它保留 direct CLI 兼容用于调试，不作为模型主路径。

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
- `RUN_ROOT/outputs/stages/clarification-record.json`
- `RUN_ROOT/outputs/stages/open-questions.json`
- `RUN_ROOT/outputs/stages/assumption-log.md`
- `RUN_ROOT/outputs/stages/design-readiness-report.json`
- `RUN_ROOT/outputs/stages/clarification-challenge-report.json`
- `RUN_ROOT/outputs/stages/clarification-handoff.json`
- `RUN_ROOT/outputs/stages/clarification-evidence.json`
- 已消解歧义列表

### 准出目标

- 规格字段无 `TBD`
- 触发方式、输入输出、门禁、角色维度明确
- 规格文件落盘到约定路径

### 执行过程（封装级）

1. `clarify_requirement`（skill_node）
   - `workflowprogram-develop` 必须与用户进行多轮澄清。
   - 只有 `requirement-clarification-lead` 允许直接与用户对话；`scenario-extractor`、`assumption-auditor`、`constraint-reviewer` 只允许内部 challenge，不得直接触达用户。
   - 每轮只提出当前最关键的 1-3 个未决问题；若回答后仍存在会影响设计的歧义，则继续下一轮。
   - 只有当“用户诉求、最终目的、成功标准、触发方式、输入输出、质量门禁”均已明确时，才允许进入草案写入。
2. `draft_spec`（agent_node）
   - `requirement_analyst` 生成规格草案内容，必须把多轮对话收敛结果整理为 `User Intent`、`Clarification Summary`、`Open Questions`、`Assumptions and Boundaries`、`Readback Confirmation`。
3. `persist_spec`（script_node）
   - 套用 `spec-template.md`，写入 `RUN_ROOT/workflow-spec.md`。
4. `generate_clarification_package`（script_node）
   - 通过 `generate-clarification-package.py` 从 `workflow-spec.md` 派生 `clarification-record.json`、`open-questions.json`、`assumption-log.md`、`design-readiness-report.json`。
5. `generate_clarification_review`（script_node）
   - 通过 `generate-clarification-review.py` 生成 `clarification-challenge-report.json`、`clarification-handoff.json`、`clarification-evidence.json`。
   - `clarification-challenge-report.json` 必须记录内部 challenge roles 提出的补问建议与阻塞点。
   - `clarification-handoff.json` 必须为 `S2/S3` 生成确定性输入。
6. `spec_quality_check`（script_node）
   - 检查是否包含 `TBD/待补`、结构化澄清字段、有效 `澄清轮次` 与 `READY` 状态；失败则回到步骤 1。
7. `emit_stage_progress`（script_node）
   - 更新 S1 进展与里程碑，刷新 `user-progress.md`。

### 可验证检查

1. `RUN_ROOT/workflow-spec.md` 文件存在。
2. 文件不包含 `TBD` 或 `待补`。
3. 文件包含输入、输出、触发方式、质量门禁四个段落。
4. 文件必须包含 `User Intent` 与 `Clarification Summary` 两个段落。
5. 文件必须包含 `Open Questions`、`Assumptions and Boundaries`、`Readback Confirmation` 三个段落。
6. `Clarification Summary.澄清轮次` 必须是整数，且 `>= 2`。
7. `clarification-record.json`、`open-questions.json`、`assumption-log.md`、`design-readiness-report.json`、`clarification-challenge-report.json`、`clarification-handoff.json`、`clarification-evidence.json` 必须存在，且 `design-readiness-report.json.ready=true`、`clarification-handoff.json.ready=true`。
8. `clarification-challenge-report.json.review_roles[*].direct_user_contact` 必须全部为 `false`。
9. `clarification-evidence.json` 必须记录 `challenge_rounds >= 1`，并确认 `readback_confirmed=true`、`s2_handoff_ready=true`、`s3_handoff_ready=true`。
10. `milestones.jsonl` 至少包含 `clarify_requirement`、`persist_spec`、`generate_clarification_package`、`generate_clarification_review` 四个节点结果。

### 实现方案

- 主承载：`/develop` Stage 1、`workflowprogram-develop` Step 2
- 模板来源：`skills/workflow-spec-support/spec-template.md`
- 校验承载：`validate-workflow-draft.py`

### 承载文件

- [develop.md](/mnt/d/Code/WorkflowProgram-CN/.claude/commands/develop.md)
- [workflowprogram-develop/SKILL.md](/mnt/d/Code/WorkflowProgram-CN/.claude/skills/workflowprogram-develop/SKILL.md)
- [spec-template.md](/mnt/d/Code/WorkflowProgram-CN/.claude/skills/workflow-spec-support/spec-template.md)
- [validate-workflow-draft.py](/mnt/d/Code/WorkflowProgram-CN/.claude/scripts/validate-workflow-draft.py)

## S2 领域研究（Explore Context）

### 输入

- `workflow-spec.md`
- `clarification-record.json`
- `clarification-handoff.json.s2_inputs`
- 目标项目当前 `.claude/` 现状

### 输出

- 可复用资产列表
- 缺口与命名建议
- `RUN_ROOT/outputs/stages/s2-context-report.md`

### 准出目标

- 覆盖 `workflow-spec.md` 与 `clarification-handoff.json.s2_inputs` 指定范围
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
- `clarification-handoff.json.s3_inputs`
- S2 上下文结论

### 输出

- `RUN_ROOT/workflow-spec.yaml`（机器可读）
- `RUN_ROOT/workflow-view.md`（只读视图）
- `RUN_ROOT/workflow-lowlevel.md`（维护指导）
- `generated_runtime_contract`（内嵌于 `workflow-spec.yaml`）
- 可选 `capability_discovery`
- 可选 `host_capabilities`
- 可选 `agent_team_contract`
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
2. 顶层必须包含：`meta`、`stages`、`agent_refs`、`skills`、`registry`、`constraints`、`resource_limits`、`runtime_contract`、`test_contract`、`generated_runtime_contract`。
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
13. `generated_runtime_contract.mode` 必须是 `shared-control-plane-wrapper`。
14. 若声明 `capability_discovery`，则 `generated_runtime_contract.runtime_capabilities` 必须包含 `capability_discovery`。
15. 若声明 `host_capabilities`，则 `generated_runtime_contract.runtime_capabilities` 必须包含 `host_capability_probe`。
16. 若声明 `agent_team_contract.enabled=true`，则 `generated_runtime_contract.runtime_capabilities` 必须包含 `team_orchestration`。
17. 若声明 `workflow_graph`，validator 必须校验 graph entrypoints、nodes、transitions、templates_used、可达性与目标资产声明。

### 实现方案

- 主承载：`/develop` Stage 3
- YAML 模板来源：`yaml-spec-template.md`
- 视图渲染脚本：`generate-workflow-view.py`（确定性渲染，不依赖自由文本）
- 维护指导渲染脚本：`generate-workflow-lowlevel.py`
- 维护指导校验脚本：`${CLAUDE_PLUGIN_ROOT}/scripts/validate-workflow-lowlevel.py`
- 规格校验脚本：`${CLAUDE_PLUGIN_ROOT}/scripts/validate-workflow-spec.py`

### 承载文件

- [develop.md](/mnt/d/Code/WorkflowProgram-CN/.claude/commands/develop.md)
- [yaml-spec-template.md](/mnt/d/Code/WorkflowProgram-CN/.claude/skills/workflow-spec-support/yaml-spec-template.md)
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
- `RUN_ROOT/outputs/candidate/.workflowprogram/runtime/*`
- `managed-change-plan.json`
- `managed-change-result.json`
- `managed-change-summary.md`
- `managed-rollback-manifest.json`
- `managed-recover-instructions.md`
- 应用后的 `TARGET_ROOT/.claude/*`（无冲突时）
- 应用后的 `TARGET_ROOT/.workflowprogram/design/*`（无冲突时）
- 应用后的 `TARGET_ROOT/.workflowprogram/runtime/*`（无冲突时）

### 准出目标

- 所有候选文件可解释、可验证
- unmanaged/drifted 文件不被覆盖
- `managed-files.json` 与 apply 结果一致
- 冲突文件必须落盘到冲突目录
- 更新文件前必须保存 before snapshot，并在 `managed-rollback-manifest.json` 中记录安全回退条件
- 面向用户共享的 managed 报告必须包含 `schema_version`、`error_code`、`failure_kind`、`remediation` 并做 secret-like 脱敏

### 执行过程（封装级）

1. `generate_candidates`（script_node）
   - 按 `workflow-spec.yaml` 生成 `RUN_ROOT/outputs/candidate/.claude/*`，并同步准备 `RUN_ROOT/outputs/candidate/.workflowprogram/design/*` 与 `RUN_ROOT/outputs/candidate/.workflowprogram/runtime/*`。
2. `validate_generated_files`（skill_node）
   - 调 `validate-file` 检查关键候选文件格式与约束。
3. `plan_apply_managed_assets`（script_node）
   - 调 `managed-assets.py plan` 生成变更计划。
4. `apply_or_conflict`（script_node）
   - 无冲突执行 `apply-staged`；有冲突写入 `outputs/conflicts/` 并标记失败分类。
5. `product_entry_finalize`（script_node）
   - develop 主链必须通过 `${CLAUDE_PLUGIN_ROOT}/scripts/workflow-entry.py run --spec <RUN_ROOT>/workflow-spec.yaml --run-root <RUN_ROOT> --target-root <TARGET_ROOT> --entry-skill workflowprogram-develop --request "<原始需求>"` 驱动，而不是只在 skill 中罗列口头顺序。
   - 该脚本必须顺序调用 `validate-workflow-spec.py`、`generate-workflow-view.py`、`generate-workflow-lowlevel.py`、`generate-target-runtime.py`、`managed-assets.py`、`discover-host-capabilities.py`、`probe-host-capabilities.py`、`apply-host-bootstrap.py`（条件执行）、`generate-environment-remediation.py`、`workflow-runner.py`、`validate-run-state.py`，并写入 `outputs/stages/entry-orchestration-summary.json`。
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
3. `managed-rollback-manifest.json` 与 `managed-recover-instructions.md` 必须存在。
4. 若存在冲突，`RUN_ROOT/outputs/conflicts/` 必须存在且包含冲突文件副本。
5. `TARGET_ROOT/.workflowprogram/managed-files.json` 必须更新 `updated_at`。
6. `user-progress.md` 必须包含“已应用/冲突”摘要。
7. `RUN_ROOT/state.json` 必须存在且通过 `validate-run-state.py`。
8. `RUN_ROOT/outputs/stages/runner-summary.json` 必须存在。
8. `TARGET_ROOT/.workflowprogram/runtime/runtime-manifest.json` 必须存在，并通过 `${CLAUDE_PLUGIN_ROOT}/scripts/validate-generated-runtime.py` 校验。
9. 若声明 `host_capabilities`，则 `RUN_ROOT/outputs/stages/host-capability-report.json` 必须存在。
10. 若声明 `capability_discovery`，则 `RUN_ROOT/outputs/stages/host-capability-candidates.json` 与 `RUN_ROOT/outputs/stages/host-bootstrap-instructions.md` 必须存在。
11. 若声明 `host_capabilities`，则 `RUN_ROOT/outputs/stages/environment-remediation-report.json` 与 `RUN_ROOT/outputs/stages/environment-remediation-guide.md` 必须存在。

### 实现方案

- 主承载：`/develop` Stage 4、`workflowprogram-develop` Step 3
- 关键脚本：`workflow-entry.py`、`managed-assets.py`、`discover-host-capabilities.py`、`probe-host-capabilities.py`、`apply-host-bootstrap.py`、`generate-environment-remediation.py`、`workflow-runner.py`、`validate-run-state.py`

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
- 条件性 `RUN_ROOT/outputs/stages/host-capability-report.json`
- 条件性 `RUN_ROOT/outputs/stages/host-capability-probe.json`
- 条件性 `RUN_ROOT/outputs/stages/team-plan.json`
- 条件性 `RUN_ROOT/outputs/stages/team-results.json`
- 条件性 `RUN_ROOT/outputs/stages/team-join-summary.json`

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
   - 若声明 `capability_discovery`，则必须校验 `host-capability-candidates.json` 与 `host-bootstrap-instructions.md` 已生成，并且后者明确包含 `manual_steps`、`expected_outputs`、`recheck_hint`。
   - `validate / audit` 意图下若声明 `host_capabilities`，必须针对当前宿主执行实时 probe，而不是复用历史 develop 报告。
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
7. 若声明 `capability_discovery`，则 `host-capability-candidates.json` 与 `host-bootstrap-instructions.md` 必须被 S5 消费。
8. 若声明 `host_capabilities`，则 `host-capability-report.json` 必须被 S5 消费；required 缺失应判为 `FAIL/environment`，optional 缺失只记 `INFO`。
9. 若声明 `host_capabilities`，则 `environment-remediation-report.json` 与 `environment-remediation-guide.md` 也必须被 S5 消费；`validate/audit` 必须让 unresolved manual steps 对用户可见。
10. 若声明 `agent_team_contract.enabled=true`，则确定性 provider 缺 team evidence 必须 `FAIL`；`claude_cli` 缺结构化 team evidence 只能 `WARN`。

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
5. 当 `failure_kind=environment` 且存在 host capability 证据时，`environment-remediation-report.json` 必须存在。
6. 当 `environment-remediation-report.json.repeated_failure_count > 0` 时，`s6-lessons-delta.md` 必须至少包含一个 remediation / bootstrap / re-check 类候选项。

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

### 6.2 Marketplace 安装契约

当前正式安装路径是 marketplace。marketplace 元数据必须把插件源解析到 `dist/plugin/`，而不是仓库根目录。

首次启动时，插件必须在 `${CLAUDE_PLUGIN_DATA}/python/site-packages` 中准备私有 Python 依赖，并通过 `workflowprogram-python` 供所有插件脚本调用。

### 6.3 Marketplace 载荷验收检查

1. `dist/plugin/.claude-plugin/marketplace.json` 的 plugin source 使用 `git-subdir` 指向 `dist/plugin`。
2. `dist/plugin/hooks/hooks.json` 存在，且 `SessionStart` 会触发 Python runtime bootstrap。
3. `dist/plugin/bin/workflowprogram-python` 与 `dist/plugin/bin/workflowprogram-doctor` 存在。
4. `dist/plugin/requirements.lock.txt` 与 `dist/plugin/runtime-manifest.json` 存在。
5. 启动后可识别 `/workflowprogram-orchestrate` 入口。
