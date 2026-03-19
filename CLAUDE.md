# Project Name

## Project Overview
<!-- TODO: 填写项目描述 -->
A brief description of what this project does.

## Tech Stack
<!-- TODO: 填写实际技术栈 -->
- Language: TBD
- Framework: TBD
- Database: TBD

## Architecture

本项目采用五层 Agentic 架构：

- **CLAUDE.md** — 项目级配置，每次会话自动加载
- **`.claude/rules/`** — 动态硬规则约束沉淀（如 `constraints.md`），自动进化并加载
- **`.claude/commands/`** — Workflow 编排（包含设计工作流的元工作流 `/develop` 以及 `/ship` 等）
- **`.claude/skills/`** — 可复用 Prompt 模板（`/review` `/test` `/commit` `/doc`）
- **`.claude/agents/`** — 专业 Agent 定义（增添了工作流设计/验证专家及安全/性能/风格/逻辑审查专家）
- **`.claude/settings.json`** — Hooks 事件驱动自动化

经验法则：**可测试的数据处理放代码层，LLM 编排放 commands/skills，专业角色放 agents，自动化触发放 hooks，工作流生产失败沉淀放 rules**。

## Code Style
<!-- TODO: 根据项目语言调整 -->
- Use type hints / type annotations on all function signatures
- Write clear, descriptive variable and function names
- Keep functions focused and under 50 lines when possible
- Add docstrings for all public functions and classes
- Import order: stdlib → third-party → local

## Project Structure
<!-- TODO: 填写实际项目结构 -->
```
src/
tests/
docs/
```

## Commands
<!-- TODO: 填写实际命令 -->
- Run: `TBD`
- Test: `TBD`
- Lint: `TBD`
- Build: `TBD`

## Rules
- NEVER commit directly to main branch
- NEVER hardcode secrets, API keys, or credentials in source code
- NEVER ignore error handling — always handle errors gracefully
- NEVER use `print()` for logging in production code
- NEVER leave TODO comments without a tracking issue
- Always write tests for new features before marking them complete
- Keep each module/file under 300 lines
- Run tests before every commit

## Testing Rules
- Test command: `TBD`
- All tests must pass before committing
- New features must include corresponding tests
- Test file naming: `test_<module>.py` or `<module>.test.ts` (adjust per stack)
