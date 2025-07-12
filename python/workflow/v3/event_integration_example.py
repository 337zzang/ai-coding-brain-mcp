"""
표준화된 이벤트 처리 예제

WorkflowManager에서 사용할 수 있는 개선된 이벤트 처리 패턴을 보여줍니다.
"""
from python.workflow.v3.event_helpers import create_event_publisher
from python.workflow.v3.listener_manager import ListenerManager
from python.workflow.v3.listeners import (
    ErrorHandlerListener,
    ContextUpdateListener
)
from python.workflow.v3.events import GitAutoCommitListener
from python.workflow.v3.event_bus import EventBus


class ImprovedWorkflowManager:
    """개선된 이벤트 처리를 사용하는 WorkflowManager 예제"""

    def __init__(self, context_integration, helpers):
        # 기존 초기화 코드...

        # EventBus 초기화
        self.event_bus = EventBus()
        self.event_bus.start()

        # ListenerManager 초기화
        self.listener_manager = ListenerManager(self.event_bus)

        # 리스너 등록
        self._register_listeners(context_integration, helpers)

        # EventPublisher 생성
        self.events = create_event_publisher(self._add_event)

    def _register_listeners(self, context_integration, helpers):
        """모든 리스너 등록"""

        # 1. ContextUpdateListener - 컨텍스트 자동 업데이트
        context_listener = ContextUpdateListener(context_integration)
        self.listener_manager.register_listener("context_updater", context_listener)

        # 2. ErrorHandlerListener - 에러 처리
        error_listener = ErrorHandlerListener(self, retry_limit=3)
        self.listener_manager.register_listener("error_handler", error_listener)

        # 3. GitAutoCommitListener - Git 자동 커밋
        git_listener = GitAutoCommitListener(helpers)
        self.listener_manager.register_listener("git_auto_commit", git_listener)

        # 추가 리스너들은 여기에...

    def create_plan(self, name: str, description: str = ""):
        """플랜 생성 - 개선된 이벤트 처리"""
        # 핵심 로직
        plan = self._create_plan_object(name, description)
        self.state.add_plan(plan)

        # 이벤트 발행 (한 줄로 간단하게!)
        self.events.plan_lifecycle(plan, 'created')
        self.events.plan_lifecycle(plan, 'started')

        # 수동 처리 제거됨 - 모든 부가 작업은 리스너가 처리
        # ❌ self.context_integration.record_event(...)
        # ❌ if self.auto_commit: self.git_commit(...)

        return plan

    def complete_task(self, task_id: str, note: str = ""):
        """태스크 완료 - 개선된 이벤트 처리"""
        # 핵심 로직
        task = self.state.get_task(task_id)
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now()

        # 이벤트 발행
        self.events.task_lifecycle(
            self.state.current_plan.id, 
            task, 
            'completed',
            note=note,
            duration=self._calculate_duration(task)
        )

        # 플랜 완료 체크
        if self._is_plan_completed():
            self.events.plan_lifecycle(
                self.state.current_plan,
                'completed',
                total_tasks=len(self.state.current_plan.tasks),
                duration=self._calculate_plan_duration()
            )

        return task

    def handle_task_failure(self, task_id: str, error: str):
        """태스크 실패 - 개선된 이벤트 처리"""
        task = self.state.get_task(task_id)

        # 이벤트 발행만 하면 ErrorHandlerListener가 알아서 처리
        self.events.task_lifecycle(
            self.state.current_plan.id,
            task,
            'failed',
            error=error
        )

        # 재시도, 플랜 일시정지 등은 ErrorHandlerListener가 처리

    def get_event_metrics(self):
        """이벤트 처리 메트릭 조회"""
        return self.listener_manager.get_metrics()
