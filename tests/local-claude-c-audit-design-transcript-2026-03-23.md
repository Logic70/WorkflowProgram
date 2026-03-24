# Local Claude Transcript: C Audit Workflow Design

Date: 2026-03-23  
Source repository: `D:\Code\WorkflowProgram-CN`  
Local Claude session id: `f751b64f-5d0d-469f-b6d4-7b474a4a5b91`

## Initial prompt

```text
/develop 设计一个用于 C 语言代码审计的工作流。要求：输入为 git 链接或本地代码路径，输出为测试报告；支持 Level 1（非 AI 的常规自动化测试）和 Level 2（AI 驱动的安全测试）；支持常见嵌入式/IoT 安全问题检测；具备测试经验和工作流结构的自我迭代能力。当前先不要落盘文件，先做需求澄清。
```

## Claude clarification questions

1. Level 1 工具偏好？
   - A. 默认 `cppcheck + clang-tidy + flawfinder`
   - B. 完全自定义
   - C. 仅做规则框架

2. 嵌入式 / IoT 问题范围？
   - A. 只覆盖常见内存安全
   - B. 常见 CWE + 少量嵌入式规则
   - C. 常见 CWE + 较完整嵌入式 / IoT 专项

3. Level 2 深度？
   - A. 只做风险总结
   - B. 做深度安全分析并给修复建议
   - C. 直接尝试自动修复

4. 命令名方案？
   - A. `/c-audit <git-url|local-path> [--level1|--level2|--both]`
   - B. 使用更通用命名
   - C. 让 Claude 自定

5. 自我迭代如何触发？
   - A. 审计后自动起草 lessons，再走审批迭代
   - B. 手动触发
   - C. 自动直接写规则

## My answers

```text
1-A，但请把 Level 1 设计成可替换工具链，默认 cppcheck + clang-tidy + flawfinder。
2-C，主范围按 C 处理，但默认覆盖标准 CWE 子集 + 嵌入式 / IoT 常见问题：内存安全、边界检查、格式化字符串、整数溢出、竞态、volatile 与 ISR 误用、不安全加密 / RNG、硬编码凭据、危险调试接口、薄弱固件更新链。
3-B，并包含修复建议，但只做建议，不自动改代码。
4-A，命令名就用 /c-audit <git-url|local-path> [--level1|--level2|--both]。
5-A，允许自动起草 lessons 候选，再走 iterate-workflow 的审批流。
先输出 workflow-spec 草案和设计，不要写文件。
```

## Claude design summary

- 设计了一个 `C-Audit` 工作流，分为 6 个阶段：
  1. 准备
  2. Level 1 执行
  3. Level 1 解析
  4. Level 2 AI 分析
  5. 报告生成
  6. 经验沉淀
- Level 2 设计为 4 个专长分析维度：
  - dataflow
  - attack surface
  - embedded specific
  - crypto
- 输出同时包含 Markdown 报告和 JSON 报告。
- 设计了 `--learn` 选项，用于生成经验沉淀候选。

## Design defects discovered during follow-up

- 生成的仓库草案使用了 `.claude/commands/c-audit.json`，而不是 Markdown 命令文件。
- 生成的 `settings.json` 结构不符合当前 Claude 工作流仓的对象映射约定。
- 当目标目录位于当前工作区外部时，没有先声明写边界，后续出现大批量 write permission denials。

## Extracted lessons

- 设计阶段必须显式声明目标仓库是否仍为 Claude 兼容工作流仓。
- 若是 Claude 兼容仓，命令与技能格式要沿用现有约定，不能私自切换。
- 独立仓输出路径若不在当前工作区内，需要在生成前声明 `--add-dir` 或同等方案。
