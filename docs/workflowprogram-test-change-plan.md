# WorkflowProgram 测试变更计划总表

> 依据本轮历史讨论整理。目标是把“已落地变更、部分完成项、待继续项”收敛成一份可持续更新的索引表。

| ID | 变更目标 | 状态 | 变更内容索引 | 说明 |
|---|---|---|---|---|
| C1 | 收口测试契约模型，明确 `runtime_contract` 与 `test_contract` 分层 | 已完成 | `docs/workflowprogram-stage-highlevel-design.md`<br>`docs/workflowprogram-stage-lowlevel-design.md`<br>`README.md` | 已统一执行约束与测试判定边界；`test_contract` 采用 `runtime_contract.<field>` 固定引用语法，`implemented_now` 仅表示覆盖度。 |
| C2 | 将测试规划补充到 HighLevel / LowLevel / consistency-check | 已完成 | `docs/workflowprogram-stage-highlevel-design.md`<br>`docs/workflowprogram-stage-lowlevel-design.md`<br>`docs/workflowprogram-stage-consistency-check.md` | 已把入口 / 边界 / 流程 / 产物 / 失败五类契约写入设计文档，并确认当前无显式冲突。 |
| C3 | 同步主入口文档和模板，避免设计与执行入口口径不一致 | 已完成 | `.claude/commands/develop.md`<br>`.claude/skills/workflowprogram-develop/SKILL.md`<br>`.claude/skills/develop/yaml-spec-template.md` | `/develop`、`workflowprogram-develop`、YAML 模板现在都明确要求 `runtime_contract + test_contract`，并统一到显式 `stage_slot: S1..S6` 六阶段模型。 |
| C4 | 将 `test_contract` 纳入规格校验与视图生成 | 已完成 | `.claude/scripts/validate-workflow-spec.py`<br>`tools/generate-view.py` | 规格校验器已检查字段结构、引用存在、禁止复制声明、`implemented_now` 子集关系，并强制 `stage_slot` 完整性与顺序；视图生成器已渲染 `Test Contract (Judgment Only)`。 |
| C5 | 将运行时硬约束工程化到控制面 runner | 已完成 | `.claude/scripts/workflow-runner.py`<br>`.claude/scripts/runtime_host.py` | runner 已执行写入边界、环境 skip、失败类别枚举、最小证据集校验；运行宿主已抽象为 `claude_cli / fixture_host / command_adapter`。 |
| C6 | 将仓库级静态校验升级到“当前生效设计真源” | 已完成 | `.claude/scripts/validate-workflow.py`<br>`.claude/scripts/validate-workflow.ps1`<br>`docs/phase-07-implementation-plan.md` | Python 版已校验 active docs、dist 关键载荷、build-manifest sha256、source/dist 构建一致性与 command wrapper；PowerShell 规则已同步，当前阶段以非 Windows 路径为主。 |
| C7 | 让 S5 / smoke 输出开始消费 `test_contract` 判定来源 | 已完成 | `.claude/skills/workflowprogram-validate/SKILL.md`<br>`.claude/scripts/workflow-s5-judge.py`<br>`tools/runtime_smoke.py` | `workflowprogram-validate` 已收口为 S5 主 judge；`runtime_smoke.py` 复用 judge 并输出 `contract_source`、`contract_categories`、`validation-runtime-report.md` 与 `outputs/stages/s5-validation-summary.json`。judge 现已校验入口一致性、流程核心证据、route/runner 语义、deliverable 变更、冲突候选副本和异常路径摘要一致性。 |
| C8 | 固化基础动态测试的最小场景集 | 已完成 | `tests/spec-fixtures/valid-minimal.yaml`<br>`tests/spec-fixtures/invalid-entry.yaml`<br>`tests/spec-fixtures/write-boundary-violation.yaml`<br>`tests/spec-fixtures/environment-skip.yaml`<br>`tools/mock_runtime_host.py` | spec fixture 已固定到显式 `stage_slot` 六阶段模型；`command_adapter + mock_runtime_host` 已补齐非 Claude provider 的真实 PASS/FAIL smoke 路径，`empty-project / existing-workflow / broken-workflow / invalid-entry / missing-args / external-write / managed-conflict` 均可稳定复验。 |
| C9 | 沉淀阶段性计划与验证记录 | 已完成 | `docs/phase-07-implementation-plan.md`<br>`validation-report.md` | 当前已形成“目标、步骤、验证矩阵、阶段结果”三层记录。 |
| C10 | 清理历史文档，区分真源与追溯材料 | 已完成 | `docs/workflowprogram-design-status.md`<br>`docs/phase-*.md` | 已通过文档状态索引和历史文档顶部状态说明区分 active/supporting/historical；archive 全量物理清理仍可后续单独执行，但不再影响真源判定。 |
| C11 | 完成动态测试体系闭环 | 已完成 | `tools/runtime_smoke.py`<br>`.claude/scripts/workflow-s5-judge.py`<br>`.claude/scripts/runtime_host.py`<br>`tools/mock_runtime_host.py` | 当前已具备 provider-agnostic 的 smoke/judge 闭环：非 Claude provider 可稳定跑 PASS 与固定负例，S5 判定覆盖 `entry / boundary / flow / artifacts / failure` 五类契约，并能在异常路径保持 summary 与最终 verdict 一致。 |
| C12 | 完成平台侧补验证 | 暂缓 | `powershell.exe -ExecutionPolicy Bypass -File .claude/scripts/validate-workflow.ps1` | 当前范围暂不考虑 Windows 平台；Python 校验器、runner 和 smoke 已完成非 Windows 复验。 |
| C13 | 将 S1/S6 质量门槛与真实宿主 smoke 标准化 | 已完成 | `.claude/scripts/validate-workflow-draft.py`<br>`.claude/scripts/validate-lessons-delta.py`<br>`tools/runtime_smoke_matrix.py`<br>`tools/runtime_smoke.py` | `workflow-spec.md` 与 `s6-lessons-delta.md` 已有确定性 validator；`runtime_smoke` 会在 skip/error 路径补齐最小 progress 证据；`runtime_smoke_matrix.py` 已统一 `command_adapter / fixture_host / claude_cli` 的复验入口。 |
| C14 | 收口产品入口确定性编排与能力矩阵校验 | 已完成 | `.claude/scripts/workflow-entry.py`<br>`docs/workflowprogram-capability-matrix.json`<br>`docs/workflowprogram-design-status.md`<br>`.claude/scripts/validate-workflow.py` | develop 主链已有单一脚本入口串起 `validate-workflow-spec -> generate-view -> managed-assets -> workflow-runner -> validate-run-state`，仓库级 validator 也会按 capability matrix 与文档状态索引检查 HighLevel / LowLevel / 模板 / 脚本同步性。 |

## 当前判断

| 维度 | 结论 | 备注 |
|---|---|---|
| 静态设计与实现收口 | 已完成 | HighLevel / LowLevel / 主入口 / 模板 / 校验器 / runner / dist 发布链已对齐到显式 `stage_slot: S1..S6`，S5 主 judge 与动态 harness 的边界已收口。 |
| 运行时硬约束执行 | 已完成 | `runtime_contract` 已程序化生效。 |
| 基础动态测试能力 | 已完成 | 已具备 provider-agnostic 的 PASS/FAIL smoke、固定负例矩阵、S5 judge 摘要与契约分项报告。 |
| S1 / S6 质量门槛 | 已完成 | `workflow-spec.md` 与 `s6-lessons-delta.md` 已从提示词要求升级为确定性校验规则。 |
| 历史文档治理 | 已完成 | 已新增 `workflowprogram-design-status.md` 标记活文档/支持文档/历史文档边界，并在关键历史设计文档顶部补充状态说明。 |

## 建议优先级

| 优先级 | 下一步 | 目的 |
|---|---|---|
| P1 | 强化 route-intent 语义测试 | 当前 deterministic wrapper、capability matrix、历史文档治理已收口；后续如需继续提升，可补 declarative 路由夹具与负例。 |
| P2 | Windows / PowerShell 原生复验 | 当前范围外，可按需补做。 |

当前 capability matrix 已纳入仓库级静态校验，任何对 HighLevel / LowLevel / 模板 / validator / 入口脚本的漂移都应先在 `docs/workflowprogram-capability-matrix.json` 中收口。
