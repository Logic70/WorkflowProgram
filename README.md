# WorkflowProgram-CN

> 面向 Claude Code 生态的元工作流仓库

WorkflowProgram-CN 不是业务应用模板，也不是一组零散 prompt。
它的目标是帮助你为目标项目设计、交付、审计、验证和迭代一套可运行的 `.claude/` 工作流资产，并把这套过程产品化为：

- 可执行的 `workflow-spec.yaml`
- 可阅读的 `workflow-view.md`
- 可维护的 `workflow-lowlevel.md`
- 可验证的运行证据、状态与判定链

如果你希望先理解设计哲学，再动手使用，建议先看：

- [WorkflowProgram 101 章节版](docs/workflowprogram-101/index.md)
- [WorkflowProgram 101 单页版](docs/workflowprogram-101.md)
- [WorkflowProgram 流程图文档](docs/workflowprogram-flow-slides/workflowprogram_overview.pptx)

---

## 安装步骤

### 1. 环境准备

建议准备以下环境：

- `Python 3.10+`
- `Claude Code CLI`
- `git`

用于本仓库维护的可选环境：

- `Node.js 20+`
  - 仅在需要重新生成 PPT 文档时使用

### 2. 克隆与校验仓库

```bash
git clone https://github.com/Logic70/WorkflowProgram-CN.git
cd WorkflowProgram-CN

# macOS / Linux
python3 .claude/scripts/validate-workflow.py

# Windows
powershell -ExecutionPolicy Bypass -File .claude/scripts/validate-workflow.ps1
```

### 3. 构建插件运行时载荷

```bash
python3 tools/build_plugin.py
```

构建完成后，Claude Code 真正消费的是：

- `dist/plugin/`

而不是源码层 `.claude/`。

### 4. 以 plugin-dir 方式启动 Claude Code

```bash
claude --plugin-dir /abs/path/to/WorkflowProgram-CN/dist/plugin
```

当前稳定支持的安装/发现方式是：

1. Source Build 通道
   先运行 `python3 tools/build_plugin.py`，再使用 `--plugin-dir dist/plugin`

2. Release Package 通道
   解压 release 附件中的 `plugin/` 目录，再使用 `--plugin-dir /abs/path/to/plugin`

当前**不建议**把 `dist/plugin/` 直接复制到用户 `~/.claude` 作为正式安装契约。

---

## 设计哲学与概念

### 1. 它产出的不是应用代码，而是工作流产品

WorkflowProgram-CN 产出的重点是：

- `.claude/commands/*.md`
- `.claude/skills/*/SKILL.md`
- `.claude/agents/*.md`
- `.claude/rules/constraints.md`
- `.claude/settings.json`

也就是“让 Code Agent 能工作”的工作流资产，而不是业务系统源码。

### 2. 三根目录必须分清

| 位置 | 含义 | 作用 |
|------|------|------|
| `PLUGIN_ROOT` | 插件运行时模板与脚本来源 | WorkflowProgram 自己的能力仓 |
| `TARGET_ROOT` | 目标项目目录 | 最终交付 `.claude/` 资产的地方 |
| `RUN_ROOT` | 单次运行工作目录 | 记录 spec、视图、状态、事件、验证证据 |

这三个根目录分离，是为了避免：

- 把插件仓误当目标项目改写
- 把中间态直接覆盖进目标资产
- 让调试证据和交付物混在一起

### 3. 三类设计产物分层

当前设计真源已经收口为：

- `workflow-spec.yaml`
  - 机器可执行真源
- `workflow-view.md`
  - 只读概览视图
- `workflow-lowlevel.md`
  - 维护/迭代指导文档，不允许覆盖 YAML 语义

其中：

- 改执行语义，先改 `workflow-spec.yaml`
- 改视图与维护说明，通过生成脚本重算

### 4. 阶段模型固定为 `S0..S6`

当前运行与验证口径围绕以下阶段展开：

- `S0` 路由与目标准备
- `S1` 需求澄清
- `S2` 上下文研究
- `S3` YAML 设计与审批
- `S4` 受控写入与控制面执行
- `S5` workflow 级验证判定
- `S6` lessons / constraints 回流

不是所有 intent 都会跑完整 `S1..S6`，而是由 `workflow-spec.yaml.intent_flows` 决定：

- `develop -> S1,S2,S3,S4,S5,S6`
- `audit -> S5,S6`
- `iterate -> S6`
- `validate -> S5`

### 5. AI 与 Python 分工明确

WorkflowProgram 的设计理念不是“全部让模型自由发挥”，而是：

- AI 负责：
  - 理解需求
  - 设计方案
  - 生成候选 workflow 资产
- Python 脚本负责：
  - 意图路由
  - spec 校验
  - 受控写入
  - 状态落盘
  - 运行证据归集
  - workflow 级判定

所以它是一条“AI 设计 + Python 控制面 + S5 judge”的产品化链路。

---

## 快速使用

### 推荐入口

当前推荐直接使用 `workflowprogram-*` 主入口：

```text
/workflowprogram-orchestrate "为当前项目设计一个 Claude Code 工作流"
```

如果你已经明确知道要做什么，也可以直接调用叶子入口：

```text
/workflowprogram-develop "为当前项目创建一个新闻采集与摘要工作流"
/workflowprogram-audit /path/to/existing-project
/workflowprogram-validate /path/to/existing-project
/workflowprogram-iterate /path/to/existing-project
```

历史兼容入口仍保留：

- `/develop`
- `/evolve-workflow`
- `/iterate-workflow`

但当前产品主路径优先采用 `workflowprogram-*`。

### 一次典型的 develop 使用方式

```text
/workflowprogram-develop "为当前项目创建一个每日收集科技新闻并生成摘要的工作流"
```

执行后你通常会看到这些结果：

- `RUN_ROOT/workflow-spec.yaml`
- `RUN_ROOT/workflow-view.md`
- `RUN_ROOT/workflow-lowlevel.md`
- `RUN_ROOT/outputs/candidate/.claude/`
- `TARGET_ROOT/.workflowprogram/design/`
  - 持久化后的 `workflow-spec.yaml / workflow-view.md / workflow-lowlevel.md`

### 自动审批模式

当你在 CI 或非交互场景使用时，可以启用自动审批：

```text
/workflowprogram-develop "需求描述" --auto-approve
CI=true /workflowprogram-develop "需求描述"
```

显式人工批准也支持记录：

- `approved`
- `auto-approved`

两者不会混为一种状态。

---

## 文件结构

### 仓库结构

```text
WorkflowProgram-CN/
├── .claude/
│   ├── commands/                  # 源码层命令定义
│   ├── skills/                    # 源码层技能定义
│   ├── agents/                    # 源码层 agent 定义
│   ├── rules/                     # 源码层规则
│   ├── scripts/                   # 源码层脚本
│   └── settings.json              # 源码层注册表
├── .claude-plugin/                # 插件清单元数据
├── dist/plugin/                   # 构建后的 canonical 运行时载荷
├── docs/                          # 设计文档、教程、流程图、实现计划
├── openspec/                      # OpenSpec 需求拆解与审计产物
├── tests/                         # spec fixtures、smoke fixtures、transcripts
├── tools/                         # 构建、smoke、矩阵验证工具
├── CLAUDE.md                      # 仓库级协作说明
├── lessons.md                     # 追加式经验日志
├── validation-report.md           # 校验与实现进展记录
└── README.md
```

### 目标项目侧结构

在一次典型执行后，`TARGET_ROOT` 下会出现两类资产：

```text
TARGET_ROOT/
├── .claude/                                   # 最终交付给目标项目的 workflow 资产
└── .workflowprogram/
    ├── managed-files.json                     # 托管文件清单
    ├── design/
    │   ├── workflow-spec.yaml                 # 持久化设计真源
    │   ├── workflow-view.md                   # 持久化只读视图
    │   └── workflow-lowlevel.md               # 持久化维护指导
    └── runs/<run-id>/
        ├── context.json
        ├── state.json
        ├── events.jsonl
        ├── transcript.md
        ├── validation-runtime-report.md
        └── outputs/
            ├── candidate/
            ├── progress/
            ├── stages/
            └── ...
```

### 关键文件说明

| 文件/目录 | 作用 |
|-----------|------|
| `.claude/settings.json` | 命令与 skill 的注册中心 |
| `workflow-spec.yaml` | 机器可执行的 workflow 真源 |
| `workflow-view.md` | 从 YAML 渲染的人类可读概览 |
| `workflow-lowlevel.md` | 维护/迭代指导 |
| `managed-files.json` | 目标侧受控文件清单 |
| `state.json` / `events.jsonl` | 控制面状态与事件证据 |
| `user-progress.md` | 面向用户的当前进展与关键节点摘要 |

---

## 运行过程

### 1. 入口与路由

自然语言请求优先进入：

- `workflowprogram-orchestrate`

再由：

- `route-intent.py`

把请求确定性地路由到：

- `workflowprogram-develop`
- `workflowprogram-audit`
- `workflowprogram-iterate`
- `workflowprogram-validate`

显式 `/develop` 或 `workflowprogram-develop` 不会再“跳回” `orchestrate`；
但 `workflow-entry.py` 仍会再次调用 `route-intent.py` 保留路由证据，并在 strict 模式下检查入口与请求是否冲突。

### 2. develop 主链如何执行

当前 develop 主链已经固定为确定性脚本链：

```text
workflow-entry.py run
  -> validate-workflow-spec.py
  -> generate-workflow-view.py
  -> generate-workflow-lowlevel.py
  -> managed-assets.py plan/apply-staged
  -> workflow-runner.py run
  -> validate-run-state.py
  -> workflowprogram-validate / workflow-s5-judge.py
```

其中：

- `workflow-entry.py`
  - 把 prompt/skill 层说明桥接到真实脚本链
- `managed-assets.py`
  - 托管 `candidate -> TARGET_ROOT` 的安全应用
- `workflow-runner.py`
  - 控制面 runner，只负责 stage 转移、状态落盘、最小证据和边界语义
- `workflowprogram-validate + workflow-s5-judge.py`
  - 负责 workflow 级 S5 主判定

### 3. 为什么不是直接写目标项目

当前不会直接静默写入 `TARGET_ROOT/.claude/`，而是先走：

1. `RUN_ROOT/outputs/candidate/`
2. `managed-assets.py plan`
3. `managed-assets.py apply-staged`

如果发现冲突：

- 停在 `S4`
- 保留 candidate 与 conflict 副本
- 不覆盖用户资产

### 4. 进展与证据如何落盘

当前已标准化三类进展产物：

- `RUN_ROOT/outputs/progress/current-progress.json`
- `RUN_ROOT/outputs/progress/milestones.jsonl`
- `RUN_ROOT/outputs/progress/user-progress.md`

统一更新脚本：

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/stage-progress.py update ...
```

当前也已标准化控制面与运行证据：

- `context.json`
- `state.json`
- `events.jsonl`
- `transcript.md`
- `validation-runtime-report.md`
- `outputs/stages/s5-validation-summary.json`
- `outputs/stages/s6-lessons-delta.md`

### 5. 运行宿主与 smoke

当前运行宿主已经抽象为：

- `claude_cli`
- `fixture_host`
- `command_adapter`

对应脚本：

- `.claude/scripts/runtime_host.py`
- `tools/runtime_smoke.py`
- `tools/runtime_smoke_matrix.py`

这意味着：

- 正式主路径仍是 Claude Code CLI
- 测试与验证可以通过 fixture 或 adapter 做确定性回归

---

## 维护说明

### 1. 哪些文档是当前真源

优先阅读：

- [workflowprogram-stage-highlevel-design.md](docs/workflowprogram-stage-highlevel-design.md)
- [workflowprogram-stage-lowlevel-design.md](docs/workflowprogram-stage-lowlevel-design.md)
- [workflowprogram-stage-consistency-check.md](docs/workflowprogram-stage-consistency-check.md)

文档真源索引见：

- [workflowprogram-design-status.md](docs/workflowprogram-design-status.md)

能力对齐矩阵见：

- [workflowprogram-capability-matrix.json](docs/workflowprogram-capability-matrix.json)

### 2. 修改 workflow 的正确姿势

修改执行语义时，优先顺序是：

1. 修改 `workflow-spec.yaml`
2. 重新生成 `workflow-view.md`
3. 重新生成 `workflow-lowlevel.md`
4. 重新执行 validator / runner / smoke

不要只改：

- `workflow-view.md`
- `workflow-lowlevel.md`
- README 文字描述

来试图改变真实执行语义。

### 3. 仓库级验证命令

```bash
# 仓库静态校验
python3 .claude/scripts/validate-workflow.py

# 插件构建
python3 tools/build_plugin.py

# spec 结构校验
python3 .claude/scripts/validate-workflow-spec.py --spec <workflow-spec.yaml>

# lowlevel 派生校验
python3 .claude/scripts/validate-workflow-lowlevel.py \
  --spec <workflow-spec.yaml> \
  --lowlevel <workflow-lowlevel.md>

# runner 状态校验
python3 .claude/scripts/validate-run-state.py --state <RUN_ROOT>/state.json

# lessons 产物校验
python3 .claude/scripts/validate-lessons-delta.py --run-root <RUN_ROOT>
```

### 4. 运行期验证命令

```bash
# 单条 smoke
python3 tools/runtime_smoke.py --fixture empty-project

# 统一矩阵复验
python3 tools/runtime_smoke_matrix.py --json
```

### 5. 经验沉淀机制

WorkflowProgram 当前采用三层经验管理：

- `lessons.md`
  - 追加式失败经验日志
- `.claude/rules/constraints.md`
  - 提炼后的长期规则
- `RUN_ROOT/outputs/stages/s6-lessons-delta.md`
  - 单次运行提炼出来的 lessons 增量

当前 `S6` 还会要求：

- `user-progress.md` 必须包含“历史关键节点结果”
- `s6-lessons-delta.md` 必须和当前 `run_id`、`failure_kind` 关联

### 6. 文档与教程维护

当前仓库已经有三套面向不同读者的文档：

- `README.md`
  - 面向首次接触的使用者
- `docs/workflowprogram-101/`
  - 面向想理解设计哲学和架构的人
- `docs/workflowprogram-flow-slides/`
  - 面向需要图文讲解和演示的人

如果你更新了执行主链、设计资产或验证边界，通常应同步更新这三处中的至少一处。

### 7. 本地 Git 仓维护流程

推荐按下面的顺序维护本地仓库：

1. 先新建或切到一个单一目的分支，只做一类改动。
2. 优先修改真源文件，再修改派生产物。
3. 改完后先跑静态校验，再跑构建，再跑运行期验证。
4. 只提交和这次目标直接相关的文件，不把临时 transcript、锁文件、无关脏改动一起提交。

具体建议：

- 如果你修改了 `.claude/scripts/`、`.claude/skills/`、`.claude/commands/` 或设计文档，优先把这些文件视为真源。
- `dist/plugin/`、`workflow-view.md`、`workflow-lowlevel.md`、PPT、报告类文件属于派生产物；只有在真源变化后才重建，不建议手工长期维护。
- 修改 `workflow-spec.yaml` 语义后，至少应重新生成 `workflow-view.md`、`workflow-lowlevel.md`，并复跑 validator。
- 修改运行主链、证据模型、judge、宿主适配时，除了静态校验，还应补跑 `runtime_smoke.py` 或 `runtime_smoke_matrix.py`。
- 修改 `README.md`、`docs/workflowprogram-101/`、`docs/workflowprogram-flow-slides/` 时，应检查文档口径是否仍与 HighLevel、LowLevel 和实际脚本一致。

一套可执行的本地维护命令顺序如下：

```bash
# 1. 查看当前分支和工作区，确认不会误带无关改动
git status --short

# 2. 修改真源文件
#    例如 .claude/scripts/、.claude/skills/、docs/ 里的设计文档

# 3. 重新生成派生产物
python3 .claude/scripts/generate-workflow-view.py \
  --spec <workflow-spec.yaml> \
  --output <workflow-view.md>
python3 .claude/scripts/generate-workflow-lowlevel.py \
  --spec <workflow-spec.yaml> \
  --output <workflow-lowlevel.md>
python3 tools/build_plugin.py

# 4. 跑静态校验
python3 .claude/scripts/validate-workflow.py
python3 .claude/scripts/validate-workflow-spec.py --spec <workflow-spec.yaml>
python3 .claude/scripts/validate-workflow-lowlevel.py \
  --spec <workflow-spec.yaml> \
  --lowlevel <workflow-lowlevel.md>
git diff --check

# 5. 需要时再跑运行期验证
python3 tools/runtime_smoke.py --fixture empty-project
python3 tools/runtime_smoke_matrix.py --json

# 6. 只暂存本次需要提交的文件
git add <files...>
git commit -m "<scope>: <summary>"
git push origin <branch>
```

提交时的范围控制建议：

- 单次提交尽量只覆盖一个主题，例如“收口 S5 judge”或“刷新 README 和教程”。
- 如果仓库已经有其他未完成脏改动，用 `git add <files...>` 精确暂存，不要直接 `git add .`。
- `tests/transcripts/`、PowerPoint 的 `~$*.pptx` 锁文件、运行期临时目录通常不应提交。
- 如果这次修改了 `dist/plugin/`，要确保对应真源文件也在同一个提交里；不要只提交 dist 结果。

---

## 相关文档

- [WorkflowProgram 101 章节版](docs/workflowprogram-101/index.md)
- [WorkflowProgram 流程图文档](docs/workflowprogram-flow-slides/workflowprogram_overview.pptx)
- [文档状态索引](docs/workflowprogram-design-status.md)
- [能力矩阵](docs/workflowprogram-capability-matrix.json)
- [验证进展报告](validation-report.md)

---

## 许可证

MIT
