# Runtime Smoke Transcript

- Run ID: `20260409T130911Z-invalid-entry`
- Fixture: `invalid-entry`
- Entry skill: `missing-workflowprogram-entry`
- Result: `FAIL`
- Contract source: `fixture_preset`
- Contract categories: `entry, failure`

## Command

```bash
claude -p --plugin-dir /mnt/d/Code/WorkflowProgram-CN/dist/plugin --output-format json /missing-workflowprogram-entry 验证非法入口时是否被正确拒绝
```

## Stdout

```text
{"type":"result","subtype":"success","is_error":false,"duration_ms":1121,"duration_api_ms":0,"num_turns":2,"result":"Unknown skill: missing-workflowprogram-entry","stop_reason":null,"session_id":"a76181bc-e7d9-425d-85fc-4aaba1d5c34d","total_cost_usd":0,"usage":{"input_tokens":0,"cache_creation_input_tokens":0,"cache_read_input_tokens":0,"output_tokens":0,"server_tool_use":{"web_search_requests":0,"web_fetch_requests":0},"service_tier":"standard","cache_creation":{"ephemeral_1h_input_tokens":0,"ephemeral_5m_input_tokens":0},"inference_geo":"","iterations":[],"speed":"standard"},"modelUsage":{},"permission_denials":[],"fast_mode_state":"off","uuid":"a3fac20f-d852-430c-9ea8-4205e5a8e773"}
```

## Stderr

```text
<empty>
```
