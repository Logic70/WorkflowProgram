# Runtime Smoke Transcript

- Run ID: `20260403T032546Z-existing-workflow`
- Fixture: `existing-workflow`
- Entry skill: `workflowprogram-audit`
- Result: `ENVIRONMENT-SKIP`

## Command

```bash
claude -p --plugin-dir /mnt/d/Code/WorkflowProgram-CN/dist/plugin --output-format json /workflowprogram-audit 审计当前项目中的 workflow 结构，并输出结构问题、模式偏离和下一步建议
```

## Stdout

```text
{"type":"result","subtype":"success","is_error":true,"duration_ms":221,"duration_api_ms":0,"num_turns":1,"result":"Not logged in · Please run /login","stop_reason":"stop_sequence","session_id":"0e07cb0a-4767-469b-9424-a59fe5d6ce5f","total_cost_usd":0,"usage":{"input_tokens":0,"cache_creation_input_tokens":0,"cache_read_input_tokens":0,"output_tokens":0,"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":0,"ephemeral_5m_input_tokens":0},"inference_geo":"","iterations":[],"speed":"standard"},"modelUsage":{},"permission_denials":[],"terminal_reason":"completed","fast_mode_state":"off","uuid":"924689c5-e949-4e72-8295-ea6627efda33"}
```

## Stderr

```text
<empty>
```
