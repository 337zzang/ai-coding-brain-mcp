
# LLM/O3 Facade 네임스페이스 구현
class LLMNamespace:
    """LLM/O3 함수들을 위한 Facade 네임스페이스"""

    def __init__(self):
        # llm 모듈 import
        from . import llm as llm_module
        self._module = llm_module

    # O3 관련 메서드들
    def ask(self, question: str, context: str = None, reasoning_effort: str = 'high'):
        """O3에게 질문 (동기)"""
        return self._module.ask_o3(question, context, reasoning_effort)

    def ask_async(self, question: str, context: str = None, reasoning_effort: str = 'high'):
        """O3에게 질문 (비동기)"""
        return self._module.ask_o3_async(question, context, reasoning_effort)

    def ask_practical(self, question: str):
        """O3에게 실용적인 질문"""
        return self._module.ask_o3_practical(question)

    def get_result(self, task_id: str):
        """O3 작업 결과 가져오기"""
        return self._module.get_o3_result(task_id)

    def check_status(self, task_id: str):
        """O3 작업 상태 확인"""
        return self._module.check_o3_status(task_id)

    def show_progress(self):
        """O3 작업 진행 상황 표시"""
        return self._module.show_o3_progress()

    def clear_completed(self):
        """완료된 O3 작업 정리"""
        return self._module.clear_completed_tasks()

    # Context Builder
    def create_context(self):
        """O3 Context Builder 생성"""
        from .llm import O3ContextBuilder
        return O3ContextBuilder()

# 네임스페이스 인스턴스 생성
llm = LLMNamespace()
o3 = llm  # o3는 llm의 별칭
