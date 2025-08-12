"""
LLM Facade 완성 코드
__init__.py에 추가할 Facade 구조
"""

# ============ LLM Facade 네임스페이스 ============

class LLMFacade:
    """LLM 모듈 Facade 패턴"""
    
    def __init__(self, parent):
        self.parent = parent
        
    # 비동기 실행
    def ask_async(self, question, context=None, reasoning_effort="medium"):
        """O3 비동기 실행 (병렬 처리 권장)"""
        from .llm import ask_o3_async
        return ask_o3_async(question, context, reasoning_effort)
    
    def ask_practical(self, question, context=None):
        """O3 동기 실행 (즉시 결과)"""
        from .llm import ask_o3_practical
        return ask_o3_practical(question, context)
    
    # 작업 관리
    def get_result(self, task_id):
        """비동기 작업 결과 가져오기"""
        from .llm import get_o3_result
        return get_o3_result(task_id)
    
    def check_status(self, task_id):
        """작업 상태 확인"""
        from .llm import check_o3_status
        return check_o3_status(task_id)
    
    def show_progress(self):
        """전체 작업 진행 상황"""
        from .llm import show_o3_progress
        return show_o3_progress()
    
    # Context Builder
    def create_context(self):
        """O3 Context Builder 생성"""
        from .llm import O3ContextBuilder
        return O3ContextBuilder()
    
    # 작업 정리
    def cleanup_old_tasks(self, days=7):
        """오래된 작업 정리"""
        from .llm import cleanup_old_o3_tasks
        return cleanup_old_o3_tasks(days)
    
    def get_task_statistics(self):
        """작업 통계 조회"""
        from .llm import get_o3_task_statistics
        return get_o3_task_statistics()
    
    def archive_completed_tasks(self):
        """완료 작업 아카이브"""
        from .llm import archive_completed_o3_tasks
        return archive_completed_o3_tasks()
    
    def clear_completed(self):
        """완료 작업 정리"""
        from .llm import clear_completed_o3_tasks
        return clear_completed_o3_tasks()

# ============ O3 별칭 (동일 기능) ============

class O3Facade(LLMFacade):
    """O3 별칭 - LLMFacade와 동일"""
    pass

# ============ __init__.py에 추가할 코드 ============

def init_llm_facade():
    """__init__.py에서 호출할 초기화 함수"""
    
    # Facade 인스턴스 생성
    llm = LLMFacade(None)
    o3 = O3Facade(None)
    
    # 기존 함수들 (하위 호환성)
    from .llm import (
        ask_o3_async,
        ask_o3_practical,
        get_o3_result,
        check_o3_status,
        show_o3_progress,
        O3ContextBuilder,
        cleanup_old_o3_tasks,
        get_o3_task_statistics,
        archive_completed_o3_tasks,
        clear_completed_o3_tasks
    )
    
    return {
        # Facade 네임스페이스
        'llm': llm,
        'o3': o3,
        
        # 기존 함수 (하위 호환)
        'ask_o3_async': ask_o3_async,
        'ask_o3_practical': ask_o3_practical,
        'get_o3_result': get_o3_result,
        'check_o3_status': check_o3_status,
        'show_o3_progress': show_o3_progress,
        'O3ContextBuilder': O3ContextBuilder,
        'cleanup_old_o3_tasks': cleanup_old_o3_tasks,
        'get_o3_task_statistics': get_o3_task_statistics,
        'archive_completed_o3_tasks': archive_completed_o3_tasks,
        'clear_completed_o3_tasks': clear_completed_o3_tasks
    }

# ============ 사용 예시 ============

"""
사용법:

1. __init__.py에 추가:
```python
# LLM Facade 초기화
from .llm_facade_complete import init_llm_facade
llm_exports = init_llm_facade()

# 네임스페이스 추가
llm = llm_exports['llm']
o3 = llm_exports['o3']

# 기존 함수 export (하위 호환)
ask_o3_async = llm_exports['ask_o3_async']
# ... 나머지 함수들
```

2. 사용자 코드:
```python
import ai_helpers_new as h

# Facade 스타일 (권장)
task_id = h.llm.ask_async("복잡한 질문", reasoning_effort="high")['data']
result = h.llm.get_result(task_id)

# O3 별칭
task_id = h.o3.ask_async("질문")['data']
result = h.o3.get_result(task_id)

# 기존 스타일 (하위 호환)
task_id = h.ask_o3_async("질문")['data']
result = h.get_o3_result(task_id)
```
"""
