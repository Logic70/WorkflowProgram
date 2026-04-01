# Session State Bus

轻量级状态总线，用于工作流执行期间的数据传递、检查点创建和调试。

## 用途

- **Agent 间数据共享**: 将前一 Stage 的数据写入总线，后一 Stage 读取
- **检查点恢复**: 在长流程中创建检查点，支持断点续传
- **调试追踪**: 查看 Stage 历史、当前状态、性能指标
- **防丢失**: 结构化存储，避免 LLM 上下文遗忘导致数据丢失

## 使用方式

### 初始化会话

```bash
python3 .claude/scripts/state-bus.py init --command "/develop news-workflow" --max-turns 100
```

### Stage 执行流程

```bash
# 1. 进入 Stage
python3 .claude/scripts/state-bus.py transition --stage explore

# 2. 写入数据到总线
python3 .claude/scripts/state-bus.py write --stage explore --key requirements --value "创建新闻收集工作流"
python3 .claude/scripts/state-bus.py write --stage explore --key complexity --value "M"

# 3. 创建检查点（关键节点）
python3 .claude/scripts/state-bus.py checkpoint --stage explore

# 4. 进入下一 Stage
python3 .claude/scripts/state-bus.py transition --stage design

# 5. 读取前一 Stage 数据
python3 .claude/scripts/state-bus.py read --stage explore --key requirements
```

### 调试命令

```bash
# 查看当前状态
python3 .claude/scripts/state-bus.py status

# 查看 Stage 历史
python3 .claude/scripts/state-bus.py history

# 查看所有检查点
python3 .claude/scripts/state-bus.py checkpoints

# 恢复到检查点
python3 .claude/scripts/state-bus.py restore explore-20-143022
```

## 数据结构

```json
{
  "meta": {
    "session_id": "uuid",
    "command": "/develop xxx",
    "status": "running",
    "created_at": "2026-04-01T10:00:00"
  },
  "state": {
    "current_stage": "design",
    "stage_history": ["explore"],
    "turn_count": 25,
    "max_turns": 100
  },
  "data_bus": {
    "explore": {
      "requirements": "创建新闻收集工作流",
      "complexity": "M"
    },
    "design": {
      "patterns": ["Sequential", "Fan-out"]
    }
  },
  "checkpoints": [
    {
      "id": "explore-20-143022",
      "stage": "explore",
      "turn": 20,
      "file": ".claude/checkpoints/explore-20-143022.json"
    }
  ],
  "debug": {
    "performance": {
      "tokens_input": 12000,
      "tokens_output": 8000,
      "api_calls": 15
    }
  }
}
```

## 集成到 Commands

在 `develop.md` 中使用：

```markdown
## Stage 1: 需求探索

**执行前**:
```bash
python3 .claude/scripts/state-bus.py transition --stage explore
```

**执行中**:
1. 分析需求
2. 写入总线:
   ```bash
   python3 .claude/scripts/state-bus.py write --stage explore --key requirements "$ARGUMENTS"
   python3 .claude/scripts/state-bus.py write --stage explore --key output_file "workflow-spec.md"
   ```
3. 创建检查点:
   ```bash
   python3 .claude/scripts/state-bus.py checkpoint --stage explore
   ```

**执行后**:
```bash
python3 .claude/scripts/state-bus.py status
```
```

## 优势

| 特性 | 说明 |
|------|------|
| 防丢失 | 结构化存储，不依赖 LLM 上下文 |
| 可调试 | 检查点机制支持断点续传 |
| 可追踪 | Stage 历史和性能指标 |
| 轻量级 | 纯 JSON + Python，无外部依赖 |
