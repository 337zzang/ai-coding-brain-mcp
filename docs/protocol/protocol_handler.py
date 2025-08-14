
# python/protocol_handler.py

import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import IntEnum

class ErrorCode(IntEnum):
    """표준 에러 코드"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # 커스텀 에러 코드
    VERSION_MISMATCH = -32001
    CAPABILITY_NOT_SUPPORTED = -32002
    HANDSHAKE_FAILED = -32003

@dataclass
class ProtocolVersion:
    """프로토콜 버전 관리"""
    protocol: str = "1.0.0"
    mcp_server: Optional[str] = None
    python_repl: str = "7.1.0"
    ai_helpers: str = "2.7.0"

    def is_compatible(self, client_version: str) -> bool:
        """버전 호환성 체크"""
        # Major 버전만 체크 (1.x.x는 모두 호환)
        return self.protocol.split('.')[0] == client_version.split('.')[0]

class ProtocolHandler:
    """JSON-RPC 프로토콜 핸들러"""

    def __init__(self):
        self.version = ProtocolVersion()
        self.session_id = None
        self.capabilities = [
            "execute_code",
            "file_ops", 
            "git_ops",
            "llm_ops",
            "flow_ops",
            "search_ops"
        ]
        self.handshake_complete = False

    def handle_handshake(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """핸드셰이크 처리"""
        params = request.get('params', {})
        client_version = params.get('client_version', {})

        # 버전 호환성 체크
        if not self.version.is_compatible(client_version.get('protocol', '')):
            return self.error_response(
                request['id'],
                ErrorCode.VERSION_MISMATCH,
                f"Protocol version mismatch. Server: {self.version.protocol}"
            )

        # 세션 ID 생성
        import datetime
        self.session_id = f"sess_{datetime.datetime.now():%Y%m%d_%H%M%S}"

        # 핸드셰이크 응답
        self.handshake_complete = True
        return {
            "jsonrpc": "2.0",
            "result": {
                "type": "handshake_ack",
                "server_version": {
                    "protocol": self.version.protocol,
                    "python_repl": self.version.python_repl,
                    "ai_helpers": self.version.ai_helpers
                },
                "capabilities": self.capabilities,
                "negotiated_protocol": self.version.protocol,
                "session_id": self.session_id
            },
            "id": request['id']
        }

    def validate_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """요청 검증"""
        # JSON-RPC 2.0 검증
        if request.get('jsonrpc') != '2.0':
            return self.error_response(
                request.get('id'),
                ErrorCode.INVALID_REQUEST,
                "Invalid JSON-RPC version"
            )

        # 핸드셰이크 체크 (initialize 제외)
        if not self.handshake_complete and request.get('method') != 'initialize':
            return self.error_response(
                request.get('id'),
                ErrorCode.HANDSHAKE_FAILED,
                "Handshake required before method calls"
            )

        return None  # 검증 통과

    def error_response(self, id: Any, code: int, message: str, data: Any = None) -> Dict:
        """에러 응답 생성"""
        error = {
            "code": code,
            "message": message
        }
        if data:
            error["data"] = data

        return {
            "jsonrpc": "2.0",
            "error": error,
            "id": id
        }
