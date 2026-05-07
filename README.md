# WorkflowProgram-CN

[中文](README.md) | [English](README.en.md)

面向 Claude Code 工作区的**元工作流引擎**。它不提供业务代码，而是帮你把 workflow 做成可交付、可验证、可迭代的产品。

## 它解决什么问题

大多数 Claude Code workflow 最初都是"一个 SKILL.md + 几个 agent + 手工改 settings.json"。这样做能跑，但很快会遇到：

- 文档和实际行为脱节，没有统一真源
- 步骤顺序靠模型记忆，容易跳步漏步
- 目标项目被直接覆盖，冲突无法恢复
- 失败后无法分层定位，也没有结构化证据
- 经验留在聊天记录里，下次还是从零开始

WorkflowProgram 用四层设计系统性地回应这些问题：**真源** / **控制面** / **验证层** / **闭环层**。

## 安装

**前置要求**：宿主机存在 `Python 3.10+` 的 `python3`。

主安装路径是 Claude Code marketplace：

```bash
claude plugin marketplace add Logic70/WorkflowProgram
claude plugin install workflowprogram-cn@logic70-plugins
```

如果你已经在 Claude Code 交互界面里，也可以执行：

```text
/plugin marketplace add Logic70/WorkflowProgram
/plugin install workflowprogram-cn@logic70-plugins
/reload-plugins
```

安装完成后：

1. 重新启动 `claude`，或在会话内执行 `/reload-plugins`
2. 首次启动会在 `${CLAUDE_PLUGIN_DATA}/python/site-packages` 自动准备插件私有 Python 依赖
3. 如需最小化排障，执行 `workflowprogram-doctor`

排障：

- 如果出现 `Unknown skill: workflowprogram-orchestrate`，通常是当前 Claude 会话还没重新加载插件。执行 `/reload-plugins` 或重启 `claude`，然后用 `/workflowprogram-orchestrate ...` 入口，不要让模型手写 `Skill(workflowprogram-orchestrate)`。
- 如果出现 `bin/workflowprogram-python: Permission denied`，说明安装缓存里的 launcher 没有执行权限。更新到最新 marketplace 载荷后重新安装；临时修复可执行 `chmod +x ~/.claude/plugins/cache/logic70-plugins/workflowprogram-cn/0.1.0/bin/workflowprogram-*`。

开发和调试仍可使用源码构建 `dist/plugin/`，但那不再是面向最终用户的主安装模型。

## 使用

在你的目标项目目录中启动 Claude Code：

```bash
cd your-project
claude
```

然后用自然语言描述你的需求：

```
"为当前项目设计一个 code review workflow"
"审计当前项目的 workflow 结构"
"验证当前项目的 workflow 资产"
```

`workflowprogram-orchestrate` 会自动路由到正确的入口技能。你也可以直接调用：

| 入口 | 用途 |
|------|------|
| `workflowprogram-develop` | 从需求到交付的完整设计流程 |
| `workflowprogram-audit` | 审计已有 workflow 的结构和模式 |
| `workflowprogram-validate` | 对 workflow 资产做一次验证判定 |
| `workflowprogram-iterate` | 从 lessons 中提炼改进建议 |

## 核心概念

### 三根目录

| 目录 | 角色 | 说明 |
|------|------|------|
| `PLUGIN_ROOT` | 能力来源 | WorkflowProgram 的 skills、脚本、模板（`dist/plugin/`）。只读。 |
| `TARGET_ROOT` | 交付目标 | 用户的项目根目录。最终的 `.claude/` 资产写在这里。只通过 managed apply 写入。 |
| `RUN_ROOT` | 运行证据 | 单次运行的隔离空间（`TARGET_ROOT/.workflowprogram/runs/<run-id>/`）。 |

### 阶段模型 S0..S6

| 阶段 | 职责 |
|------|------|
| S0 | 路由：识别用户意图，准备目标环境 |
| S1 | 需求澄清：多轮对话确保规格无歧义 |
| S2 | 上下文研究：分析目标项目现有结构 |
| S3 | 设计与审批：生成 `workflow-spec.yaml`，用户审批后才进入下一步 |
| S4 | 受控写入：候选资产生成 &rarr; managed apply &rarr; runner 执行 |
| S5 | 验证判定：S5 judge 消费 test_contract 给出 verdict |
| S6 | 经验回流：提炼 lessons 和约束候选 |

所有入口都会先经过 `S0` 路由；`workflow-spec.yaml.intent_flows` 继续定义 `S1-S6` 的逻辑阶段需求。当前默认模板中：`develop` 走 `S1-S6`，`audit` 走 `S5-S6`，`validate` 走 `S5`（可选 `S6`），`iterate` 走 `S6`（可选 `S5`）。

### S1 需求逻辑访谈

`develop` 的 S1 不再只是泛泛澄清输入输出，而是按七个 logic lenses 追问需求逻辑：

- `purpose`：为什么要做，成功信号是什么
- `object_model`：读取、转换、分类、产出的对象是什么
- `process_model`：目标工作流需要哪些业务步骤或节点
- `decision_model`：哪些分支、策略、阈值或人工确认会改变执行
- `evidence_model`：什么证据能证明中间产物和最终结论可信
- `acceptance_model`：哪些正向、负向、歧义场景能验收
- `boundary_model`：何时停止、降级、延后或明确不做

S1 会生成 `question-backlog.json` 和 `requirement-logic-map.json`。前者记录每个追问为什么会影响设计，后者把 `REQ-*` 链接到 process/evidence/acceptance 等逻辑元素。对 `L/XL` 复杂度请求，只问“还有哪些边界场景”这类泛问题会被 `validate-workflow-draft.py` 拦截，不能进入设计阶段。

### AI 和 Python 的分工

- **AI**：理解需求、补充设计、在每个节点内生成候选资产。
- **Python**：`workflow-entry.py` 串联固定脚本链，负责 spec/view/lowlevel/runtime 渲染、受控写入、能力探测与环境修复；`workflow-runner.py` 控制状态转移；`workflow-s5-judge.py` 给出判定。

编排顺序由程序决定，不由模型"记住"。

### 目标侧 runtime 与扩展能力

- develop 成功后，除了 `.claude/` 资产，还会持久化 `TARGET_ROOT/.workflowprogram/design/{workflow-spec.yaml,workflow-view.md,workflow-lowlevel.md}`。
- 目标项目还会获得自己的 deterministic runtime 包装层：`TARGET_ROOT/.workflowprogram/runtime/{workflow-entry.py,workflow-runner.py,validate-run-state.py,runtime-manifest.json}`。
- 若 workflow 声明 `capability_discovery`，入口会先生成候选 `skill / MCP / CLI` 推荐与人工指引，再进入后续探测。
- 若 workflow 声明 `host_capabilities`，入口与 S5 会消费 `host-capability-report.json`、`environment-remediation-report.json`、`environment-remediation-guide.md`。
- 若 workflow 声明 `agent_team_contract`，S5 还会校验 `team-plan.json`、`team-results.json`、`team-join-summary.json` 等 Team 证据。

### 受控写入

AI 不直接写目标项目。而是：

1. 候选资产写到 `RUN_ROOT/outputs/candidate/`
2. `managed-assets.py plan` 生成变更计划
3. `managed-assets.py apply-staged` 执行受控写入
4. 冲突时保留副本，不静默覆盖

### 三层验证

| 层 | 职责 | 关键文件 |
|----|------|---------|
| Runner | 控制面硬约束（边界、证据、值域） | `state.json`, `events.jsonl` |
| S5 Judge | workflow 级 verdict（消费 test_contract） | `s5-validation-summary.json`, `validation-runtime-report.md` |
| Runtime Smoke | 动态端到端 harness | `tools/runtime_smoke.py` |

### 经验闭环

- `lessons.md`：追加式日志，记录失败经验和待提炼约束
- `constraints.md`：长期 ALWAYS/NEVER 规则，新会话只加载这个文件
- `s6-lessons-delta.md`：单次运行增量，由 `validate-lessons-delta.py` 校验

## 项目结构

```
WorkflowProgram-CN/
├── CLAUDE.md                    # 项目协作说明
├── README.md
├── lessons.md                   # 经验日志
├── .claude/
│   ├── settings.json            # 命令与技能注册表
│   ├── commands/                # 6 个源码命令入口
│   ├── skills/                  # 12 个技能（含 5 个主产品技能）
│   ├── agents/                  # 8 个专家 agent 定义
│   ├── rules/constraints.md     # 长期约束规则
│   └── scripts/                 # 确定性脚本链、校验器与共享库
├── .claude-plugin/              # 插件元数据与 plugin root 真源
├── dist/plugin/                 # 构建产物（canonical marketplace payload）
├── docs/                        # 设计文档、教程、实现计划
├── tests/                       # fixtures、expectations、transcripts
└── tools/                       # 构建、烟雾测试、mock host
```

## 开发与验证

```bash
# 仓库结构校验
python .claude/scripts/validate-workflow.py

# spec / lowlevel / generated runtime 校验
python .claude/scripts/validate-workflow-spec.py --spec <workflow-spec.yaml>
python .claude/scripts/validate-workflow-lowlevel.py --spec <workflow-spec.yaml> --lowlevel <workflow-lowlevel.md>
python .claude/scripts/validate-generated-runtime.py --spec <workflow-spec.yaml> --runtime-root <target-runtime-root>

# 烟雾测试（单场景）
python tools/runtime_smoke.py --fixture empty-project --runtime-provider fixture_host

# 烟雾测试（完整矩阵，含 capability / host / team 场景）
python tools/runtime_smoke_matrix.py

# 重新构建插件
python tools/build_plugin.py
```

## 教程

- [HTML 版教程](docs/workflowprogram-101-html/index.html) -- 可视化、循序渐进
- [HTML Tutorial (English)](docs/workflowprogram-101-html/index.en.html)
- [单页版 Markdown](docs/workflowprogram-101.md) -- 快速扫一遍全貌
- [Single-page Markdown (English)](docs/workflowprogram-101.en.md)
- [章节版 Markdown](docs/workflowprogram-101/index.md) -- 逐章深入
- [Chapter Guide (English)](docs/workflowprogram-101-en/index.md)

## 许可

MIT
