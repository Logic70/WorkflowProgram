---
name: workflowprogram-orchestrate
description: Route natural-language workflow requests for the current project to the correct WorkflowProgram entry skill; 为当前项目设计、审计、迭代、验证 workflow 时优先命中此入口
version: 1.0.0
---

作为 WorkflowProgram 的总控入口，负责把用户当前请求路由到正确的主能力。

## When To Use

- 用户希望为当前项目设计 Claude Code 工作流
- 用户希望审计当前项目中的 workflow 资产
- 用户希望根据 lessons 迭代当前 workflow
- 用户希望验证当前 workflow 是否符合结构约束

## Core Rules

- 当前工作对象是 `TARGET_ROOT`，即用户当前项目目录。
- 插件资产来自 `PLUGIN_ROOT`，应按只读资源处理。
- 不要把 `WorkflowProgram-CN` 仓库本身误当成默认目标项目。
- 不要把 `ship`、`preflight`、`hotfix` 这类仓库维护命令当成产品主入口。
- 这是当前唯一应承接自然语言自动触发的 `workflowprogram-*` 入口。
- 显式用户入口优先使用 `/workflowprogram-cn:workflowprogram-orchestrate <需求>`。
- 其他 `workflowprogram-develop/audit/iterate/validate` 是高级显式 leaf 或内部路由目标，不是普通首选入口。
- 若请求不明确，只提出最小必要的一个澄清问题。
- 路由前应优先调用 `workflowprogram-python ${CLAUDE_PLUGIN_ROOT}/scripts/route-intent.py --request "<用户请求>" --target-root <TARGET_ROOT> --json`。
- 路由结果必须写入 `RUN_ROOT/outputs/stages/route-intent.json`；随后调用 `${CLAUDE_PLUGIN_ROOT}/scripts/resolve-change-context.py` 写入 `RUN_ROOT/outputs/stages/change-context.json`。
- 若 `change-context.json.change_policy_required=true`，必须把该证据交给 `workflowprogram-develop`，不得直接当作普通新建 workflow 处理。
- 当路由结果进入叶子入口后，确定性脚本链必须通过 `${CLAUDE_PLUGIN_ROOT}/scripts/workflow-entry.py run` 驱动，而不是只靠口头步骤串联或读取 prompt 文件后手工修改。
- 当 `WORKFLOWPROGRAM_STRICT_ROUTE=1` 或显式 strict 模式开启时，若路由歧义则必须先澄清，不得直接分发到叶子 skill。

## Step 1: Resolve Context

1. 识别当前工作目录是否为 `TARGET_ROOT`。
2. 若用户显式给出路径，以该路径作为 `TARGET_ROOT`。
3. 通过 `route-intent.py --out <RUN_ROOT>/outputs/stages/route-intent.json` 得到意图、置信度和 `request_kind`。
4. 通过 `resolve-change-context.py --route <RUN_ROOT>/outputs/stages/route-intent.json --out <RUN_ROOT>/outputs/stages/change-context.json` 判断目标是空项目、已有托管 workflow、已有非托管 workflow 还是 partial workflow。
5. 明确本次操作是“设计 / 审计 / 迭代 / 验证”中的哪一类，以及是否需要 change policy。

## Step 2: Route Request

按照以下规则路由：

- 设计新 workflow 或更新 workflow 架构 -> `workflowprogram-develop`
- 审计现有 workflow 结构与模式 -> `workflowprogram-audit`
- 基于 `lessons.md` 生成改进草案 -> `workflowprogram-iterate`
- 对 workflow 资产执行结构化校验 -> `workflowprogram-validate`

## Step 3: Hand-off Requirements

向目标主 skill 传递：

- `TARGET_ROOT`
- 用户原始需求
- `RUN_ROOT/outputs/stages/route-intent.json`
- `RUN_ROOT/outputs/stages/change-context.json`
- 必要的约束或范围说明
- 当前已知的 `.claude/` 现状

## Output

输出应包含：

- 路由结论
- 目标主 skill 名称
- 若存在，最小缺失信息项
