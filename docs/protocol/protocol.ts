
// src/protocol.ts

interface ProtocolVersion {
  protocol: string;
  mcp_server?: string;
  python_repl?: string;
  ai_helpers?: string;
}

interface HandshakeRequest {
  type: 'handshake';
  client_version: ProtocolVersion;
  capabilities: string[];
  preferred_protocol: string;
}

interface HandshakeResponse {
  type: 'handshake_ack';
  server_version: ProtocolVersion;
  capabilities: string[];
  negotiated_protocol: string;
  session_id: string;
}

enum ErrorCode {
  PARSE_ERROR = -32700,
  INVALID_REQUEST = -32600,
  METHOD_NOT_FOUND = -32601,
  INVALID_PARAMS = -32602,
  INTERNAL_ERROR = -32603,

  // Custom errors
  VERSION_MISMATCH = -32001,
  CAPABILITY_NOT_SUPPORTED = -32002,
  HANDSHAKE_FAILED = -32003
}

class ProtocolManager {
  private version: ProtocolVersion = {
    protocol: '1.0.0',
    mcp_server: '4.2.0'
  };

  private sessionId?: string;
  private handshakeComplete = false;

  async performHandshake(replProcess: any): Promise<void> {
    const handshake: HandshakeRequest = {
      type: 'handshake',
      client_version: this.version,
      capabilities: ['execute_code', 'file_ops', 'git_ops', 'llm_ops'],
      preferred_protocol: '1.0.0'
    };

    const request = {
      jsonrpc: '2.0',
      method: 'initialize',
      params: handshake,
      id: 1
    };

    const response = await this.sendRequest(replProcess, request);

    if (response.error) {
      throw new Error(`Handshake failed: ${response.error.message}`);
    }

    this.sessionId = response.result.session_id;
    this.handshakeComplete = true;

    console.log(`Handshake complete. Session: ${this.sessionId}`);
  }
}
