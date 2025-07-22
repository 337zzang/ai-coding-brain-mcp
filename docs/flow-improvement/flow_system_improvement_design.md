
# Flow 시스템 코드 개선 설계서

## 🎯 핵심 문제점 및 해결 방안

### 1. Proxy 초기화 문제

**문제점:**
- _WorkflowProxy가 싱글톤이지만 세션 시작 시 자동 초기화 안됨
- current()가 None 상태에서 switch()를 호출하지만 실패

**원인 분석:**
```python
# flow_proxy.py의 current() 메서드
def current(self) -> FlowManagerUnified:
    if self._current is None:
        self.switch()  # project_root=None으로 호출됨
    return self._current

# switch() 메서드
def switch(self, project_root: Optional[str] = None) -> FlowManagerUnified:
    if project_root:
        root = os.path.abspath(project_root)
    else:
        root = _detect_project_root()  # 이 함수가 제대로 작동하는지?
```

**해결 방안:**
1. __init__.py에서 모듈 임포트 시 자동 초기화
2. _detect_project_root() 함수 개선
3. 세션 복구 메커니즘 추가

### 2. Context 연결 끊김

**문제점:**
- FlowManagerUnified는 정상 작동하지만 Proxy를 통한 접근 실패
- wf 명령어가 빈 context 반환

**해결 방안:**
1. wf 함수에 초기화 체크 추가
2. 자동 복구 메커니즘 구현

### 3. Task 상태 전환 자동화 미작동

**문제점:**
- planning → in_progress 자동 전환 안됨
- reviewing → completed 자동 전환 안됨

**해결 방안:**
1. 상태 전환 트리거 추가
2. 이벤트 기반 아키텍처 도입
