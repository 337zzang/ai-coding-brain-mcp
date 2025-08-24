# MCP 서버 세션 격리 업데이트 가이드

## 📋 적용 방법

### 1. **MCP 서버 설정 수정**

`src/handlers.ts` 파일에서 execute_code 핸들러 수정:

```typescript
// src/handlers.ts 수정 예시
async function handleExecuteCode(params: any) {
    const { code, language } = params;
    
    // 요청에서 에이전트 정보 추출
    const agentId = params.agent_id || detectAgentFromContext();
    const sessionId = params.session_id;  // 재사용을 위한 세션 ID
    
    if (language === 'python') {
        // 개선된 격리 세션 사용
        const pythonScript = path.join(__dirname, '..', 'python', 'json_repl_session_isolated.py');
        
        // JSON-RPC 요청에 에이전트 정보 포함
        const request = {
            jsonrpc: '2.0',
            id: Date.now(),
            method: 'tools/execute',
            params: {
                code,
                agent_id: agentId,     // 추가
                session_id: sessionId   // 추가
            }
        };
        
        // ... 나머지 코드
    }
}

// 에이전트 감지 헬퍼 함수
function detectAgentFromContext(): string | undefined {
    // 현재 실행 컨텍스트에서 에이전트 정보 추출
    // 예: 호출 스택, 환경 변수, 또는 요청 헤더에서
    
    const callStack = new Error().stack;
    
    if (callStack?.includes('code-analyzer')) return 'code-analyzer';
    if (callStack?.includes('test-runner')) return 'test-runner';
    if (callStack?.includes('code-optimizer')) return 'code-optimizer';
    
    return undefined;  // 익명 세션 사용
}
```

### 2. **package.json 스크립트 업데이트**

```json
{
  "scripts": {
    "start": "node dist/index.js",
    "start:isolated": "REPL_MODE=isolated node dist/index.js",
    "test:isolation": "python python/test_session_isolation.py"
  }
}
```

### 3. **환경 변수 설정**

`.env` 파일 추가:

```bash
# REPL 세션 설정
REPL_MODE=isolated
REPL_MAX_SESSIONS=10
REPL_SESSION_TIMEOUT=3600
REPL_MEMORY_LIMIT=1000
```

### 4. **TypeScript 타입 정의 추가**

`src/types.ts`:

```typescript
export interface ExecuteCodeParams {
    code: string;
    language?: string;
    agent_id?: string;      // 에이전트 식별자
    session_id?: string;    // 세션 재사용 ID
}

export interface ExecuteCodeResult {
    success: boolean;
    stdout: string;
    stderr: string;
    session_id: string;     // 클라이언트가 재사용할 세션 ID
    agent_id?: string;
    memory_mb: number;
    execution_time_ms: number;
    // ... 기타 필드
}
```

## 🚀 즉시 적용 방법 (임시)

기존 코드를 수정하지 않고 즉시 적용하려면:

### 1. **심볼릭 링크 생성**

```bash
# Windows (관리자 권한 필요)
cd C:\Users\82106\Desktop\ai-coding-brain-mcp\python
ren json_repl_session.py json_repl_session_original.py
mklink json_repl_session.py json_repl_session_isolated.py

# Linux/Mac
cd /path/to/ai-coding-brain-mcp/python
mv json_repl_session.py json_repl_session_original.py
ln -s json_repl_session_isolated.py json_repl_session.py
```

### 2. **또는 직접 교체**

```bash
# 백업
cp json_repl_session.py json_repl_session.backup.py

# 교체
cp json_repl_session_isolated.py json_repl_session.py
```

## 📊 모니터링

### 세션 상태 확인 API

새로운 JSON-RPC 메소드 추가:

```typescript
// 세션 풀 메트릭 조회
{
    "jsonrpc": "2.0",
    "method": "tools/get_pool_metrics",
    "id": 1
}

// 응답
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "total_created": 5,
        "total_reused": 12,
        "total_expired": 1,
        "current_active": 4,
        "sessions": {
            "agent_code-analyzer": {
                "created_at": "2024-01-24T10:00:00",
                "last_accessed": "2024-01-24T10:05:00",
                "execution_count": 25
            }
            // ...
        }
    }
}
```

## ✅ 검증 방법

### 1. **단위 테스트 실행**

```bash
python python/test_session_isolation.py
```

### 2. **통합 테스트**

```bash
# MCP 서버 시작
npm run build
npm run start:isolated

# 다른 터미널에서 테스트
python -c "
import subprocess
import json

# 여러 에이전트 시뮬레이션
agents = ['code-analyzer', 'test-runner', 'code-optimizer']

for agent in agents:
    result = subprocess.run(
        ['node', 'dist/test-client.js', agent],
        capture_output=True,
        text=True
    )
    print(f'{agent}: {result.stdout}')
"
```

## 🎯 기대 효과

1. **충돌 방지**: 각 서브에이전트가 독립된 네임스페이스 사용
2. **성능 향상**: 세션 재사용으로 초기화 오버헤드 감소
3. **메모리 효율**: 에이전트별 메모리 제한 및 관리
4. **디버깅 용이**: 세션별 추적 및 메트릭 제공
5. **확장성**: 동시 실행 에이전트 수 증가 가능

## ⚠️ 주의사항

1. **하위 호환성**: 기존 코드와 호환되도록 agent_id가 없으면 익명 세션 사용
2. **메모리 관리**: 세션 수가 많아지면 메모리 사용량 증가 (모니터링 필요)
3. **정리 작업**: 주기적으로 만료된 세션 정리 (자동화됨)

## 📈 성능 비교

| 항목 | 기존 (단일 세션) | 개선 (격리 세션) |
|------|-----------------|-----------------|
| 동시 실행 가능 | 1개 | 10개+ |
| 변수 충돌 | 발생 | 없음 |
| 세션 초기화 | 매번 | 재사용 |
| 메모리 격리 | 없음 | 에이전트별 |
| 디버깅 | 어려움 | 세션별 추적 |

## 🔄 롤백 방법

문제 발생 시:

```bash
# Windows
cd C:\Users\82106\Desktop\ai-coding-brain-mcp\python
del json_repl_session.py
ren json_repl_session_original.py json_repl_session.py

# Linux/Mac
cd /path/to/ai-coding-brain-mcp/python
rm json_repl_session.py
mv json_repl_session_original.py json_repl_session.py
```

## 📞 지원

문제 발생 시:
- 로그 확인: `stderr` 출력에서 `[SessionPool]` 메시지 확인
- 메트릭 확인: `get_pool_metrics` 메소드로 상태 조회
- 세션 정리: 서버 재시작으로 모든 세션 초기화