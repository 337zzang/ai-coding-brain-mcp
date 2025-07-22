
# Flow 시스템 코드 개선 최종 설계서

## 🎯 문제 진단 결과

### 근본 원인
1. **Lazy Initialization 문제**: Proxy가 처음 호출될 때만 초기화됨
2. **Context 불일치**: 새 세션에서 이전 context가 반영되지 않음
3. **자동화 미작동**: Task 상태 전환 로직이 구현되지 않음

## 🛠️ Task별 실행 계획

### Task 1: Proxy 초기화 개선
**목표**: 세션 시작 시 자동으로 프로젝트 연결

**상세 설계**:
```python
# __init__.py 수정
# 모듈 임포트 시 자동 초기화 추가
def _auto_init_proxy():
    """모듈 로드 시 자동으로 현재 프로젝트 초기화"""
    try:
        proxy = get_workflow_proxy()
        if proxy._current is None:
            # 현재 디렉토리 기준으로 초기화
            proxy.switch()
            print(f"✅ FlowManagerUnified 자동 초기화 완료")
    except Exception:
        pass  # 조용히 실패

# 모듈 로드 시 실행
_auto_init_proxy()
```

### Task 2: wf 함수 강화
**목표**: 첫 호출 시에도 정상 작동

**상세 설계**:
```python
def wf(command: str, verbose: bool = False) -> Dict[str, Any]:
    """개선된 워크플로우 명령 실행"""
    try:
        proxy = get_workflow_proxy()

        # 초기화 확인 및 자동 복구
        if proxy._current is None:
            proxy.switch()

        manager = proxy.current()
        # ... 나머지 로직
```

### Task 3: Task 상태 전환 자동화
**목표**: planning → in_progress → reviewing → completed 자동화

**상세 설계**:
```python
class FlowManagerUnified:
    def update_task_status(self, task_id: str, new_status: str):
        """상태 전환 시 자동화 트리거"""
        task = self._find_task(task_id)
        old_status = task.get('status')

        # 상태 업데이트
        task['status'] = new_status

        # 상태별 자동 동작
        if new_status == 'planning':
            self._trigger_planning_template(task)
        elif new_status == 'reviewing':
            self._trigger_review_report(task)
        elif old_status == 'reviewing' and new_status == 'completed':
            self._finalize_task(task)
```

### Task 4: 세션 복구 메커니즘
**목표**: 세션이 끊겨도 자동 복구

**상세 설계**:
```python
class _WorkflowProxy:
    def current(self) -> FlowManagerUnified:
        """개선된 current 메서드"""
        if self._current is None:
            # 자동 복구 시도
            self._restore_session()
        return self._current

    def _restore_session(self):
        """세션 복구 로직"""
        # 1. 현재 프로젝트 감지
        # 2. 이전 상태 로드
        # 3. Context 복원
```

## ⚠️ 위험 요소 및 대응 계획
| 위험 요소 | 발생 가능성 | 영향도 | 대응 방안 |
|----------|------------|-------|-----------|
| 기존 세션 충돌 | 낮음 | 높음 | 버전 체크 추가 |
| 자동 초기화 실패 | 중간 | 중간 | Fallback 메커니즘 |
| 상태 전환 오류 | 낮음 | 높음 | 롤백 기능 구현 |

## 🧪 테스트 계획
1. 새 세션에서 wf 첫 호출 테스트
2. Task 상태 전환 자동화 테스트
3. 세션 복구 시나리오 테스트
4. 동시성 테스트 (여러 프로젝트)

## ❓ 확인 필요 사항
1. 이 설계가 문제를 충분히 해결하나요?
2. 추가로 고려해야 할 edge case가 있나요?
3. 성능 영향은 어떻게 될까요?

**✅ 이 계획대로 진행해도 될까요?**
