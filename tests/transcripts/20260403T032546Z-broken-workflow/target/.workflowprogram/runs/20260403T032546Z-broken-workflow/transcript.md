# Runtime Smoke Transcript

- Run ID: `20260403T032546Z-broken-workflow`
- Fixture: `broken-workflow`
- Entry skill: `workflowprogram-validate`
- Result: `ENVIRONMENT-SKIP`

## Command

```bash
claude -p --plugin-dir /mnt/d/Code/WorkflowProgram-CN/dist/plugin --output-format json /workflowprogram-validate 验证当前项目中的 workflow 资产，并输出失败项、影响范围和修复优先级
```

## Stdout

```text
{"type":"result","subtype":"success","is_error":true,"duration_ms":246,"duration_api_ms":0,"num_turns":1,"result":"Not logged in · Please run /login","stop_reason":"stop_sequence","session_id":"3de66906-79f1-4e5c-b87e-f1a74f4ab7f9","total_cost_usd":0,"usage":{"input_tokens":0,"cache_creation_input_tokens":0,"cache_read_input_tokens":0,"output_tokens":0,"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":0,"ephemeral_5m_input_tokens":0},"inference_geo":"","iterations":[],"speed":"standard"},"modelUsage":{},"permission_denials":[],"terminal_reason":"completed","fast_mode_state":"off","uuid":"01123645-2bfb-4544-8ede-47d07d108a6d"}
```

## Stderr

```text
<empty>
```
