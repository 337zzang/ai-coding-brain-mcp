# AI Coding Brain MCP - 명령어 관리 시스템

## 📋 명령어 관리 프로세스

### 1. 아키텍처 구조

```
사용자 입력
    ↓
wf() 함수 (python/workflow_wrapper.py)
    ↓
FlowManagerUnified (python/ai_helpers_new/flow_manager_unified.py)
    ↓
FlowCommandRouter (python/ai_helpers_new/flow_command_router.py)
    ↓
각 핸들러 메서드 실행
```

### 2. 주요 모듈

| 모듈명 | 파일 경로 | 역할 |
|--------|-----------|------|
| workflow_wrapper | python/workflow_wrapper.py | 명령어 진입점 (wf 함수) |
| FlowManagerUnified | python/ai_helpers_new/flow_manager_unified.py | 통합 매니저, 라우터 관리 |
| FlowCommandRouter | python/ai_helpers_new/flow_command_router.py | 명령어 파싱 및 라우팅 |
| FlowManager | python/ai_helpers_new/flow_manager.py | 실제 Flow/Plan/Task 데이터 관리 |
| LegacyFlowAdapter | python/ai_helpers_new/legacy_flow_adapter.py | 이전 버전 호환성 |

### 3. 명령어 처리 흐름

1. **명령어 입력**: `wf("/flow ai-coding-brain-mcp")`
2. **workflow_wrapper.wf()**: 
   - FlowManagerUnified 인스턴스 가져오기
   - manager._router.route() 호출
3. **FlowCommandRouter.route()**:
   - 명령어 파싱 ("/flow" + ["ai-coding-brain-mcp"])
   - command_map에서 핸들러 찾기
   - handle_flow() 메서드 호출
4. **handle_flow()**:
   - Flow 전환: manager.switch_project()
   - Plan 목록 표시: handle_flow_status()
5. **결과 반환**: Flow 전환 메시지 + Plan 목록

## 📌 전체 명령어 리스트

### 메인 명령어

| 명령어 | 핸들러 메서드 | 설명 |
|--------|---------------|------|
| `/flow` | handle_flow | Flow 관련 작업 (전환, 상태) |
| `/flows` | handle_flows | Flow 목록 표시 |
| `/f` | handle_flow | /flow 단축키 |
| `/fs` | handle_flows | /flows 단축키 |
| `/task` | handle_task | Task 관련 작업 |
| `/task_list` | handle_task_list | Task 목록 표시 |
| `/project` | handle_flow | /flow 리다이렉트 |
| `/projects` | handle_flows | /flows 리다이렉트 |
| `/fp` | handle_flow | 기존 fp 명령 호환 |
| `/plans` | handle_plans | Plan 목록 표시 |
| `/plan` | handle_plans | /plans 리다이렉트 |
| `/start` | handle_start | Task 시작 (상태 → in_progress) |
| `/complete` | handle_complete | Task 완료 (상태 → completed) |
| `/status` | handle_status | Task 또는 Flow 상태 확인 |
| `/tasks` | handle_tasks | 특정 Plan의 Task 목록 |

### Flow 서브 명령어

| 명령어 | 핸들러 메서드 | 설명 |
|--------|---------------|------|
| `/flow create [name]` | handle_flow_create | 새 Flow 생성 |
| `/flow list` | handle_flow_list | Flow 목록 표시 |
| `/flow status` | handle_flow_status | 현재 Flow의 Plan 목록 표시 |
| `/flow delete [name]` | handle_flow_delete | Flow 삭제 |
| `/flow archive [name]` | handle_flow_archive | Flow 아카이브 |
| `/flow restore [name]` | handle_flow_restore | 아카이브된 Flow 복원 |

### 특수 명령어

| 명령어 | 설명 |
|--------|------|
| `/flow [name]` | 특정 Flow로 전환 + Plan 목록 표시 |
| `/flow -` | 이전 Flow로 전환 |
| `[숫자]` | Plan 선택 (예: `2` = 2번 Plan 선택) |
| `Plan [숫자] 선택` | Plan 선택 대체 형식 |

## 🔧 명령어 추가/수정 방법

### 1. 새 명령어 추가

1. FlowCommandRouter의 __init__ 메서드에서 command_map에 추가:
```python
self.command_map = {
    'new_command': self.handle_new_command,
    # ...
}
```

2. 핸들러 메서드 구현:
```python
def handle_new_command(self, args: List[str]) -> Dict[str, Any]:
    # 명령어 처리 로직
    return {'ok': True, 'data': '결과'}
```

### 2. 서브 명령어 추가

Flow 관련 서브 명령어의 경우:
```python
self.flow_subcommands = {
    'new_sub': self.handle_flow_new_sub,
    # ...
}
```

## 📝 주요 변경 이력

- **v30.0**: /flow 명령어 개선 - Flow 전환 시 Plan 목록 자동 표시
- **v31.0**: Context System 통합

## 🔍 디버깅 팁

1. 명령어 처리 과정 추적:
   - workflow_wrapper.py의 wf() 함수에 로깅 추가
   - FlowCommandRouter.route()에 명령어 파싱 로그

2. 핸들러 오류 확인:
   - 각 handle_* 메서드의 반환값 확인
   - {'ok': False, 'error': '...'} 형식 준수

3. 데이터 흐름 확인:
   - .ai-brain/flows.json 파일 직접 확인
   - FlowManager의 데이터 구조 검증
