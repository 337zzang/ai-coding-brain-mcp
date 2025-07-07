"""
Comprehensive Integration Test Suite
워크플로우-컨텍스트-이벤트 시스템 전체 통합 테스트
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'python'))

import json
import tempfile
from datetime import datetime
from workflow.workflow_manager import WorkflowManager
from workflow.models import TaskStatus
from events.event_integration_adapter import get_event_adapter
from events.event_bus import get_event_bus
from events.event_types import EventTypes
from events.workflow_context_bridge import get_workflow_context_bridge
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegrationTestSuite:
    """통합 테스트 스위트"""

    def __init__(self):
        self.test_results = []
        self.event_bus = get_event_bus()
        self.bridge = get_workflow_context_bridge()
        self.adapter = get_event_adapter()
        self.captured_events = []

    def setup(self):
        """테스트 환경 설정"""
        # 이벤트 캡처 핸들러 등록
        event_types = [
            EventTypes.WORKFLOW_PLAN_CREATED,
            EventTypes.WORKFLOW_TASK_STARTED,
            EventTypes.WORKFLOW_TASK_COMPLETED,
            EventTypes.CONTEXT_UPDATED,
            EventTypes.FILE_ACCESSED,
            EventTypes.FILE_CREATED
        ]

        for event_type in event_types:
            self.event_bus.subscribe(event_type, self._capture_event)

        # 테스트용 임시 디렉토리
        self.test_dir = tempfile.mkdtemp()
        logger.info(f"Test directory: {self.test_dir}")

    def teardown(self):
        """테스트 환경 정리"""
        # 핸들러 제거
        self.event_bus.clear_handlers()

        # 임시 디렉토리 정리
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _capture_event(self, event):
        """이벤트 캡처"""
        self.captured_events.append({
            'type': event.type,
            'data': event.data,
            'timestamp': event.timestamp
        })

    def _assert(self, condition, message):
        """테스트 assertion"""
        if condition:
            self.test_results.append(('PASS', message))
            print(f"✅ {message}")
        else:
            self.test_results.append(('FAIL', message))
            print(f"❌ {message}")
            raise AssertionError(message)

    def test_workflow_lifecycle(self):
        """워크플로우 생명주기 테스트"""
        print("\n=== Test 1: 워크플로우 생명주기 ===")

        # WorkflowManager 통합
        wf_manager = WorkflowManager()
        self.adapter.integrate_workflow_manager(wf_manager)

        # 1. 계획 생성
        plan = wf_manager.create_plan("통합 테스트 계획", "전체 시스템 테스트")
        self._assert(plan is not None, "계획 생성 성공")

        # 이벤트 발행 확인
        plan_events = [e for e in self.captured_events 
                      if e['type'] == EventTypes.WORKFLOW_PLAN_CREATED]
        self._assert(len(plan_events) > 0, "PLAN_CREATED 이벤트 발행됨")

        # 2. 태스크 추가
        from workflow.models import Task
        tasks = [
            Task(title="데이터 수집", description="테스트 데이터 수집"),
            Task(title="데이터 처리", description="수집된 데이터 처리"),
            Task(title="결과 생성", description="처리 결과 문서화")
        ]
        plan.tasks.extend(tasks)
        wf_manager.save_data()

        self._assert(len(plan.tasks) == 3, "3개 태스크 추가됨")

        # 3. 태스크 실행
        for i, task in enumerate(plan.tasks):
            # 태스크 시작
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now().isoformat()

            # 이벤트 수동 발행 (실제로는 start_task 메서드 사용)
            from events.event_types import create_task_started_event
            start_event = create_task_started_event(task.id, task.title)
            self.event_bus.publish(start_event)

            # 브릿지가 현재 태스크 추적하는지 확인
            self._assert(
                self.bridge.current_task_id == task.id,
                f"브릿지가 태스크 {i+1} 추적 중"
            )

            # 태스크 완료
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now().isoformat()

            from events.event_types import create_task_completed_event
            complete_event = create_task_completed_event(
                task.id, task.title, f"태스크 {i+1} 완료"
            )
            self.event_bus.publish(complete_event)

        # 4. 전체 진행률 확인
        progress = plan.get_progress()
        self._assert(
            progress['percentage'] == 100.0,
            f"전체 진행률 100% (실제: {progress['percentage']}%)"
        )

    def test_file_task_correlation(self):
        """파일 작업과 태스크 연결 테스트"""
        print("\n=== Test 2: 파일-태스크 연결 ===")

        # 현재 태스크 설정
        test_task_id = "test_task_123"
        self.bridge.current_task_id = test_task_id

        # 파일 이벤트 발행
        from events.event_types import FileEvent
        file_event = FileEvent(
            EventTypes.FILE_CREATED,
            file_path="test_output.txt",
            operation="create"
        )
        self.event_bus.publish(file_event)

        # 컨텍스트 업데이트 이벤트 확인
        context_updates = [e for e in self.captured_events 
                          if e['type'] == EventTypes.CONTEXT_UPDATED 
                          and e['data'].get('update_type') == 'file_created']

        self._assert(len(context_updates) > 0, "파일 생성 시 컨텍스트 업데이트됨")

        if context_updates:
            update = context_updates[0]
            self._assert(
                update['data'].get('task_id') == test_task_id,
                f"파일 작업이 현재 태스크와 연결됨"
            )

    def test_event_history(self):
        """이벤트 히스토리 테스트"""
        print("\n=== Test 3: 이벤트 히스토리 ===")

        # 이벤트 히스토리 조회
        history = self.event_bus.get_history(limit=50)

        self._assert(
            len(history) > 0,
            f"이벤트 히스토리에 {len(history)}개 이벤트 기록됨"
        )

        # 이벤트 타입별 통계
        event_stats = {}
        for event in history:
            event_type = event.type
            event_stats[event_type] = event_stats.get(event_type, 0) + 1

        print("\n이벤트 타입별 통계:")
        for event_type, count in event_stats.items():
            print(f"  - {event_type}: {count}개")

    def test_error_handling(self):
        """에러 처리 테스트"""
        print("\n=== Test 4: 에러 처리 ===")

        # 에러를 발생시키는 핸들러
        def error_handler(event):
            raise ValueError("테스트 에러")

        # 정상 핸들러
        normal_called = []
        def normal_handler(event):
            normal_called.append(True)

        # 핸들러 등록
        self.event_bus.subscribe("error.test", error_handler)
        self.event_bus.subscribe("error.test", normal_handler)

        # 이벤트 발행
        from events.event_bus import Event
        self.event_bus.publish(Event(type="error.test"))

        # 하나의 핸들러가 실패해도 다른 핸들러는 실행됨
        self._assert(
            len(normal_called) > 0,
            "에러 핸들러가 실패해도 정상 핸들러는 실행됨"
        )

    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🧪 통합 테스트 스위트 시작\n")

        try:
            self.setup()

            # 각 테스트 실행
            self.test_workflow_lifecycle()
            self.test_file_task_correlation()
            self.test_event_history()
            self.test_error_handling()

            # 결과 요약
            print("\n=== 테스트 결과 요약 ===")
            passed = sum(1 for result, _ in self.test_results if result == 'PASS')
            failed = sum(1 for result, _ in self.test_results if result == 'FAIL')

            print(f"총 테스트: {len(self.test_results)}개")
            print(f"성공: {passed}개")
            print(f"실패: {failed}개")

            if failed == 0:
                print("\n✅ 모든 통합 테스트 통과!")
            else:
                print(f"\n❌ {failed}개 테스트 실패")

            return failed == 0

        finally:
            self.teardown()


if __name__ == "__main__":
    suite = IntegrationTestSuite()
    success = suite.run_all_tests()

    # 테스트 결과에 따른 종료 코드
    exit(0 if success else 1)
