
## 핸드셰이크 시퀀스

### 1. 연결 시작 (MCP → REPL)
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "type": "handshake",
    "client_version": {
      "protocol": "1.0.0",
      "mcp_server": "4.2.0"
    },
    "capabilities": ["execute_code", "file_ops", "git_ops", "llm_ops"],
    "preferred_protocol": "1.0.0"
  },
  "id": 1
}
```

### 2. 핸드셰이크 응답 (REPL → MCP)
```json
{
  "jsonrpc": "2.0",
  "result": {
    "type": "handshake_ack",
    "server_version": {
      "protocol": "1.0.0",
      "python_repl": "7.1.0",
      "ai_helpers": "2.7.0"
    },
    "capabilities": ["execute_code", "file_ops", "git_ops", "llm_ops", "flow_ops"],
    "negotiated_protocol": "1.0.0",
    "session_id": "sess_20250812_001"
  },
  "id": 1
}
```

### 3. 호환성 검증
- 프로토콜 버전 일치 확인
- 필수 capabilities 확인
- 버전 호환성 매트릭스 체크
