
## 📋 프로토콜 스키마 정의 및 구현 계획

### 🎯 목적
현재 시스템의 버전 불일치와 통신 불안정성을 해결하기 위한 표준 프로토콜 정의

### 🔍 현재 문제점
1. **버전 파편화**
   - MCP Server: 4.2.0
   - Python REPL: 7.1.0  
   - AI Helpers: 2.7.0
   - 서로 독립적으로 버전 관리되어 호환성 보장 불가

2. **프로토콜 부재**
   - 명확한 메시지 형식 없음
   - 에러 처리 일관성 부족
   - 타입 안정성 없음

3. **핸드셰이크 없음**
   - 연결 시 호환성 검증 불가
   - 기능 협상(capability negotiation) 불가
   - 세션 관리 부재

### 💡 해결 방안

#### 1. JSON-RPC 2.0 표준 채택
```json
{
  "jsonrpc": "2.0",
  "method": "execute_code",
  "params": {
    "code": "print('Hello')",
    "language": "python"
  },
  "id": 1,
  "metadata": {
    "timestamp": "2025-08-12T10:00:00Z",
    "session_id": "sess_001"
  }
}
```

#### 2. 3단계 핸드셰이크
1. **Client Hello** (MCP → REPL)
   - 클라이언트 버전 전송
   - 지원 기능 목록
   - 선호 프로토콜 버전

2. **Server Hello** (REPL → MCP)
   - 서버 버전 응답
   - 협상된 프로토콜 버전
   - 세션 ID 발급

3. **Ready** (양방향)
   - 핸드셰이크 완료 확인
   - 실제 통신 시작

#### 3. 버전 관리 체계
- **Semantic Versioning** (MAJOR.MINOR.PATCH)
- **호환성 매트릭스** 관리
- **Graceful Degradation** - 하위 버전 지원

### 📊 구현 단계

#### Phase 1: 프로토콜 정의 (완료) ✅
- JSON Schema 작성
- 에러 코드 체계 정의
- 핸드셰이크 시퀀스 설계

#### Phase 2: Python 구현 (진행 중) 🔄
1. protocol_handler.py 생성
2. json_repl_session.py 통합
3. 에러 핸들링 개선

#### Phase 3: TypeScript 구현 🔄
1. protocol.ts 생성
2. index.ts 통합
3. 타입 정의 강화

#### Phase 4: 테스트 및 검증 📝
1. 단위 테스트 작성
2. 통합 테스트
3. 하위 호환성 테스트

### 🚀 실제 적용 방법

#### 1. Python REPL 수정
```python
# json_repl_session.py 수정 필요 부분

class JSONREPLSession:
    def __init__(self):
        self.protocol_handler = ProtocolHandler()

    def handle_json_command(self, command_str):
        # 1. JSON 파싱
        request = json.loads(command_str)

        # 2. 핸드셰이크 체크
        if request.get('method') == 'initialize':
            return self.protocol_handler.handle_handshake(request)

        # 3. 요청 검증
        error = self.protocol_handler.validate_request(request)
        if error:
            return error

        # 4. 실제 처리
        return self.execute_method(request)
```

#### 2. TypeScript MCP 수정
```typescript
// index.ts 수정 필요 부분

class ExecuteCodeHandler {
    private protocol: ProtocolManager;

    async initialize() {
        this.protocol = new ProtocolManager();
        await this.protocol.performHandshake(this.replProcess);
    }

    async execute(request: any) {
        // 프로토콜 래핑
        const wrappedRequest = this.protocol.wrapRequest(request);
        const response = await this.sendToRepl(wrappedRequest);
        return this.protocol.unwrapResponse(response);
    }
}
```

### 📈 기대 효과

1. **안정성 향상**
   - 타입 안정성 보장
   - 명확한 에러 처리
   - 예측 가능한 동작

2. **호환성 개선**
   - 버전 간 호환성 보장
   - 점진적 업그레이드 가능
   - 기능 협상 지원

3. **디버깅 용이**
   - 표준화된 로깅
   - 명확한 에러 코드
   - 세션 추적 가능

4. **확장성**
   - 새 기능 추가 용이
   - 플러그인 시스템 가능
   - 다중 클라이언트 지원

### ⚠️ 주의사항

1. **기존 코드 호환성**
   - 레거시 모드 지원 필요
   - 점진적 마이그레이션

2. **성능 영향**
   - 핸드셰이크 오버헤드
   - JSON 검증 비용

3. **테스트 필요**
   - 모든 엣지 케이스 테스트
   - 스트레스 테스트
