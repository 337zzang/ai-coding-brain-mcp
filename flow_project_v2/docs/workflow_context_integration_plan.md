
## 📋 워크플로우-컨텍스트 통합 최종 계획 (o3 분석 기반)

### 🔍 o3 분석 핵심 인사이트

1. **MCP 환경 특성**
   - 세션이 짧고 휘발성 (idle timeout 수~수십 초)
   - 상태 저장은 외부 저장소 필요
   - → ✅ **task 완료 시점 저장이 적절** (5분 자동저장 제거)

2. **통합 아키텍처**
   - Decorator 패턴이 최적 (기존 코드 최소 변경)
   - WorkflowManager를 래핑하여 Context 기능 추가
   - → ✅ **ContextWorkflowManager(WorkflowManager 래퍼)**

3. **명령어 체계**
   - 기존 패턴 유지: /대상 동작
   - → ✅ **새 명령어**: /context show, /session save, /history list

4. **이벤트 기반 저장**
   - 필수: TaskCompleted, TaskFailed
   - 보조: ManualSave, GracefulShutdown
   - → ✅ **이벤트 훅 시스템 구현**

5. **호환성 전략**
   - 환경 변수로 Context 기능 토글
   - → ✅ **CONTEXT_SYSTEM=on/off**

### 🏗️ 구현 아키텍처

```python
# 1. Decorator 패턴으로 WorkflowManager 래핑
class ContextWorkflowManager:
    def __init__(self, workflow_manager, enable_context=True):
        self.wm = workflow_manager
        self.context_enabled = enable_context
        if enable_context:
            self.context_mgr = ContextManager()
            self.session_mgr = SessionManager(self.context_mgr)
            self.summarizer = ContextSummarizer(self.context_mgr)

    def add_task(self, name, **kwargs):
        result = self.wm.add_task(name, **kwargs)
        if self.context_enabled and result['ok']:
            # Context 추적
            self._track_task_creation(result['data'])
        return result

    def complete_task(self, task_id, summary=''):
        result = self.wm.complete_task(task_id, summary)
        if self.context_enabled and result['ok']:
            # 완료 시점 저장
            self._save_on_completion(task_id, summary)
        return result
```

### 📝 확장될 명령어

**기존 명령어** (100% 호환)
- /help, /status, /task add/list, /start, /complete

**추가 명령어** (Context 활성화 시)
- /context - 현재 컨텍스트 요약 (기본: brief)
- /context show [brief|detailed|ai] - 형식 지정
- /session save [name] - 수동 세션 저장
- /session list - 저장된 세션 목록
- /session restore [id] - 세션 복원
- /history [n] - 최근 n개 히스토리
- /stats - 통계 보기

### 🔧 구현 단계

1. **ContextWorkflowManager 구현** (30분)
   - Decorator 패턴으로 기존 WorkflowManager 래핑
   - 환경 변수 기반 활성화/비활성화

2. **이벤트 훅 시스템** (20분)
   - task 완료/실패 시점 자동 저장
   - 수동 저장 명령어

3. **명령어 핸들러 확장** (20분)
   - wf_command에 새 명령어 추가
   - Context 비활성화 시 "기능 꺼짐" 메시지

4. **테스트 및 문서화** (30분)
   - 기존 기능 호환성 테스트
   - 새 기능 통합 테스트

### ⚡ 주요 변경사항

1. **자동저장 제거**: 5분 타이머 방식 → task 완료 시점 저장
2. **선택적 활성화**: CONTEXT_SYSTEM 환경변수로 on/off
3. **비침습적 통합**: 기존 WorkflowManager 코드 변경 최소화

### 📊 예상 효과

- **성능**: 불필요한 주기적 저장 제거로 리소스 절약
- **안정성**: 작업 완료 시점에만 저장하여 일관성 보장
- **호환성**: 기존 사용자는 변화 없이 사용 가능
- **확장성**: 새로운 Context 기능 점진적 도입 가능
