# Workflow Specification Template
# Code Agent 编排专用格式

meta:
  name: example-workflow
  version: "1.0.0"
  target_platform: claude_code
  source_design: workflow-design.md
  complexity: M  # S/M/L/XL - 用于 Stage 5 Turn Count 配置

# 阶段定义
stages:
  - id: explore
    name: 需求探索
    pattern: Explore
    agent_ref: requirement_analyst
    input: $ARGUMENTS
    output: workflow-spec.md
    gate: user_approval
    max_retries: 3
    on_approve: design
    on_reject: abort

  - id: design
    name: 工作流设计
    pattern: Specialized
    agent_ref: workflow_designer
    input: workflow-spec.md
    output: workflow-design.md
    gate: user_approval
    auto_approve_cond: "--auto-approve or CI=true"
    max_retries: 3
    on_approve: generate
    on_reject: explore

  - id: generate
    name: 文件生成
    pattern: Sequential
    steps:
      - action: generate_agents
        from_yaml: agents
      - action: generate_skills
        from_yaml: skills
      - action: generate_commands
        from_yaml: commands
      - action: update_settings
        from_yaml: registry
    output: |
      .claude/agents/*.md
      .claude/skills/*/SKILL.md
      .claude/commands/*.md
      .claude/settings.json

  - id: validate
    name: 运行时验证
    pattern: Test-Driven
    agent_ref: workflow_verifier
    input: test-scenarios.md
    resources:
      max_turn_count: 100  # M 复杂度默认 100 turns
      circuit_breaker:
        trigger: PostToolUseFailure
        threshold: 3
    max_retries: 3
    feedback:
      on_fail_design: design  # 设计缺陷 → 回到 Stage 3
      on_fail_impl: generate  # 实现缺陷 → 回到 Stage 4

  - id: learn
    name: 约束演进
    pattern: Sequential
    actions:
      - extract_lessons
      - update_constraints
    output: .claude/rules/constraints.md

# Agent 引用列表（指向 .claude/agents/*.md）
agent_refs:
  - requirement_analyst
  - workflow_designer
  - workflow_verifier
  - security-reviewer
  - performance-reviewer
  - style-reviewer
  - logic-reviewer

# 技能引用列表
skills:
  - name: validate-file
    internal: true
  - name: validate-settings
    internal: true

# 命令注册表
registry:
  commands:
    - name: example
      file: .claude/commands/example.md
  skills:
    - name: example-skill
      file: .claude/skills/example/SKILL.md

# 约束规则（将写入 constraints.md）
constraints:
  always:
    - "为用户可见命令保留 ## Usage 段"
    - "将命令组织为编号阶段，提供 Goal 与 Verify"
    - "子代理提示词内联，不依赖外部文件"
  never:
    - "在单个 fan-out 阶段中超过 4 个并行代理"
    - "让子代理运行时依赖外部 agent 文件"
    - "在未经验证的情况下声明工作流创建完成"

# 资源限额配置
resource_limits:
  max_parallel_agents: 4
  max_retries_per_stage: 3
  max_validation_loops: 10
