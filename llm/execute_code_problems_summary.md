# execute_code 사용 시 발견된 문제점 종합

## 1. o3 관련 자료구조 문제
- **prepare_o3_context**: string 반환 → dict 반환 필요
- **get_o3_result**: result['data']['answer'] 구조 처리
- **에러 처리**: task['ok'] 체크 누락

## 2. Import 및 모듈 문제  
- **상대 경로 import**: `from ..module` 실패
- **모듈 재로드**: restart_json_repl 시 상태 유실
- **순환 참조**: 모듈 간 의존성 문제

## 3. 경로 처리 문제
- **작업 디렉토리**: 초기 경로가 프로젝트 외부
- **경로 구분자**: Windows에서 / vs \ 혼재
- **상대/절대 경로**: 일관성 없는 사용

## 4. 상태 관리 문제
- **전역 변수**: globals() 직접 접근
- **세션 유지**: REPL 재시작 시 변수 소실
- **백업 관리**: 누적되는 백업 폴더

## 5. 헬퍼 함수 일관성
- **반환값 타입**: dict vs 직접 값 혼재
- **에러 처리**: try-except vs if ok 패턴 혼재
- **API 표준화**: 일부 함수만 표준화됨

## 워크플로우 리팩토링 시 반영 사항

### 1. WorkflowManager 설계
```python
class WorkflowManager:
    def __init__(self, project_path='.'):
        self.project_path = os.path.abspath(project_path)
        self.ai_brain_path = os.path.join(self.project_path, '.ai-brain')
        self._ensure_directories()

    def _ensure_directories(self):
        """프로젝트 초기화 시 디렉토리 생성"""
        os.makedirs(self.ai_brain_path, exist_ok=True)
        os.makedirs(os.path.join(self.ai_brain_path, 'cache'), exist_ok=True)
```

### 2. 표준화된 반환값
```python
def load_workflow(self):
    """모든 메서드는 표준 dict 반환"""
    try:
        # 로직...
        return {'ok': True, 'data': workflow_data}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
```

### 3. 세션 상태 영속성
```python
def save_session_state(self, state_dict):
    """REPL 재시작 시에도 상태 유지"""
    state_file = os.path.join(self.ai_brain_path, 'session_state.json')
    with open(state_file, 'w') as f:
        json.dump(state_dict, f)
```

### 4. 절대 경로 사용
```python
def get_workflow_path(self):
    """항상 절대 경로 반환"""
    return os.path.abspath(
        os.path.join(self.ai_brain_path, 'workflow.json')
    )
```
