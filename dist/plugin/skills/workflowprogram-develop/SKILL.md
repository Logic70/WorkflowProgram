<!-- AUTO-GENERATED FROM .claude/ - DO NOT EDIT DIRECTLY -->

---
name: workflowprogram-develop
description: Design or update Claude Code workflow assets for the current target project
version: 1.0.0
disable-model-invocation: true
---

面向 `TARGET_ROOT` 的工作流设计主入口。目标是在目标项目中设计或更新 `.claude/` 工作流资产，而不是修改插件源码仓。

## When To Use

- 为当前项目创建新的 Claude Code workflow
- 为现有项目补齐 `.claude/` 结构
- 重构已有 workflow 的技能、agents、rules 或 settings

## Core Rules

- 读取模板、规则和参考资产时，应从 `PLUGIN_ROOT` 读取。
- 不应直接把新文件静默写回 `TARGET_ROOT/.claude/`；应先生成候选产物，再通过 `${CLAUDE_PLUGIN_ROOT}/scripts/managed-assets.py` 决定是否应用。
- 若 `TARGET_ROOT` 已存在 `.claude/`，优先复用并增量修改。
- 必要时使用 `${CLAUDE_PLUGIN_ROOT}/skills/develop/spec-template.md` 作为规格模板来源。
- 不要把仓库维护命令包装进目标项目 workflow 设计。
- 若出现目标文件冲突，应把候选版本保留在 `RUN_ROOT/outputs/`，而不是覆盖用户资产。
- 对已应用文件，应维护 `TARGET_ROOT/.workflowprogram/managed-files.json`。
- 执行过程中必须通过 `${CLAUDE_PLUGIN_ROOT}/scripts/stage-progress.py` 写入进展与关键节点结果。
- `workflow-spec.md` 草案在进入 YAML 设计前必须通过 `${CLAUDE_PLUGIN_ROOT}/scripts/validate-workflow-draft.py` 的确定性质量门槛。
- S1 必须通过多轮用户对话澄清“用户诉求、最终目的、成功标准”；若这些信息仍不清楚，不得提前结束需求阶段。
- `workflow-spec.yaml` 产出后必须调用 `${CLAUDE_PLUGIN_ROOT}/scripts/validate-workflow-spec.py` 进行结构校验。
- `workflow-spec.yaml` 必须包含 `intent_flows`，明确 `develop / audit / iterate / validate` 的逻辑阶段流。
- `workflow-spec.yaml` 必须包含 `runtime_contract`，且至少声明：`write_boundaries`、`required_evidence`、`failure_kinds`、`environment_skip`。
- `workflow-spec.yaml` 必须包含 `test_contract`，且至少声明：`entry`、`boundary`、`flow`、`artifacts`、`failure`。
- develop 成功后，必须把 `workflow-spec.yaml`、`workflow-view.md`、`workflow-lowlevel.md` 持久化到 `TARGET_ROOT/.workflowprogram/design/`。
- `workflow-lowlevel.md` 仅用于维护与迭代指导，不得覆盖 `workflow-spec.yaml` 语义。
- `test_contract` 对执行字段必须使用 `runtime_contract.<field>` 固定引用语法，且不得复制 `runtime_contract` 同名字段。
- `test_contract.failure.implemented_now` 必须是 `runtime_contract.failure_kinds` 的子集，且不得反向改变 runner 的 verdict/failure_kind 语义。
- 生成链路完成后必须调用 `${CLAUDE_PLUGIN_ROOT}/scripts/workflow-runner.py` 进行程序化 stage 转移和状态落盘；runner 只负责控制面，不负责 S5 主判定。
- develop 主链的确定性脚本入口是 `${CLAUDE_PLUGIN_ROOT}/scripts/workflow-entry.py run`；它负责串起 spec 校验、视图生成、managed apply、runner 与 run-state 校验。
- S5 主判定必须由 `workflowprogram-validate` 承担，`runtime_smoke.py` 仅作为动态 harness 补证据。
- `RUN_ROOT/state.json` 必须通过 `${CLAUDE_PLUGIN_ROOT}/scripts/validate-run-state.py`，确保 `kind/producer/status` 枚举合规。

## Step 1: Resolve Target

1. 确认 `TARGET_ROOT`。
2. 检查 `TARGET_ROOT/.claude/` 是否已经存在。
3. 识别用户需求中的触发方式、输入、输出、角色与质量门禁。
4. 写入进展事件：`S1 StageStarted`。

## Step 2: Produce Workflow Spec

1. 用统一规格模板整理需求。
2. 每轮只提出当前最关键的 1-3 个未决问题，并根据用户回答继续追问，直到诉求、目的和成功标准清楚为止。
3. 在 `workflow-spec.md` 中显式整理 `User Intent` 与 `Clarification Summary`。
4. 形成工作流规格、模式选择和文件清单。
4. 写入进展事件：`S1 StageCheckpoint` 与 `S1 StageCompleted`。

## Step 3: Design Assets

先在 `RUN_ROOT/outputs/candidate/` 规划或生成候选资产，再决定是否应用到目标项目：

- `settings.json`
- `skills/`
- `agents/`
- `rules/`
- 必要时的 `commands/` 兼容层
- `.workflowprogram/design/{workflow-spec.yaml,workflow-view.md,workflow-lowlevel.md}`

生成候选资产后，使用以下流程：

1. 调用 `${CLAUDE_PLUGIN_ROOT}/scripts/workflow-entry.py run --spec <RUN_ROOT>/workflow-spec.yaml --run-root <RUN_ROOT> --target-root <TARGET_ROOT> --entry-skill workflowprogram-develop --request "<原始需求>" [--auto-approve|--approval-status approved]`
2. `workflow-entry.py` 必须按固定顺序调用：
   - `validate-workflow-spec.py`
   - `generate-workflow-view.py`
   - `generate-workflow-lowlevel.py`
   - `managed-assets.py plan`
   - `managed-assets.py apply-staged`
   - `workflow-runner.py run`
   - `validate-run-state.py`
3. 若 `managed-assets.py apply-staged` 报冲突，停止在 S4，保留 candidate 与 conflict 副本，不静默覆盖目标项目
4. 交由 `workflowprogram-validate` 形成 S5 主判定，并在可用时运行 `runtime_smoke.py` 补充动态证据
5. 读取 `RUN_ROOT/outputs/stages/entry-orchestration-summary.json` 作为产品入口编排摘要
6. 写入进展事件：`S4 StageStarted`、`S4 StageCheckpoint`、`S4 StageCompleted`

## Step 4: Verify Readiness

1. 检查命名是否一致。
2. 检查新增资产是否可被后续 `workflowprogram-validate` 验证。
3. 检查 `managed-files.json` 与本次应用结果是否一致。
4. 检查 `s5-validation-summary.json`、`validation-runtime-report.md` 与 `transcript.md` 的边界是否清晰。
5. 输出建议的下一步动作。
6. 更新 `RUN_ROOT/outputs/progress/user-progress.md`，向用户展示当前进展和历史关键节点结果。

## Output

输出应包含：

- 目标项目路径
- 设计摘要
- 计划新增或修改的 workflow 资产
- managed asset 计划或冲突摘要
- 当前阶段进展与关键节点历史结果摘要
- 建议执行的后续验证步骤
