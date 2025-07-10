"""
EventBus 통합 테스트
===================

WorkflowManager와 EventBus의 통합을 검증하는 테스트 케이스입니다.
"""

import unittest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.workflow.v3.manager import WorkflowManager
from python.workflow.v3.event_bus import event_bus
from python.workflow.v3.event_types import EventType


class TestEventBusIntegration(unittest.TestCase):
    """EventBus 통합 테스트"""

    def setUp(self):
        """테스트 초기화"""
        self.received_events = []
        self.test_handler = lambda event: self.received_events.append(event)

        # 이벤트 핸들러 등록
        self.event_types = [
            EventType.PLAN_CREATED,
            EventType.PLAN_STARTED,
            EventType.TASK_ADDED,
            EventType.TASK_COMPLETED,
            EventType.PLAN_COMPLETED
        ]

        for event_type in self.event_types:
            event_bus.subscribe(event_type.value, self.test_handler)

        # EventBus 시작
        event_bus.start()

        # WorkflowManager 생성
        self.wf = WorkflowManager("test_project")

    def tearDown(self):
        """테스트 정리"""
        # 핸들러 제거
        for event_type in self.event_types:
            event_bus.unsubscribe(event_type.value, self.test_handler)

        # cleanup
        if hasattr(self.wf, 'cleanup'):
            self.wf.cleanup()

    def test_plan_creation_events(self):
        """플랜 생성 시 이벤트 발행 테스트"""
        # 플랜 생성
        plan = self.wf.start_plan("테스트 플랜", "테스트 설명")

        # 이벤트 확인
        self.assertEqual(len(self.received_events), 2)
        self.assertEqual(self.received_events[0].type, EventType.PLAN_CREATED.value)
        self.assertEqual(self.received_events[1].type, EventType.PLAN_STARTED.value)

        # 플랜 정보 확인
        self.assertEqual(self.received_events[0].payload['plan_name'], "테스트 플랜")

    def test_task_lifecycle_events(self):
        """태스크 생명주기 이벤트 테스트"""
        # 플랜 생성
        plan = self.wf.start_plan("태스크 테스트")
        self.received_events.clear()  # 플랜 이벤트 제거

        # 태스크 추가
        task = self.wf.add_task("테스트 태스크")
        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0].type, EventType.TASK_ADDED.value)

        # 태스크 완료
        self.wf.complete_task(task.id)
        self.assertEqual(len(self.received_events), 2)
        self.assertEqual(self.received_events[1].type, EventType.TASK_COMPLETED.value)

    def test_plan_completion_event(self):
        """플랜 완료 이벤트 테스트"""
        # 플랜과 태스크 생성
        plan = self.wf.start_plan("완료 테스트")
        task = self.wf.add_task("유일한 태스크")
        self.received_events.clear()

        # 태스크 완료 (플랜도 완료됨)
        self.wf.complete_task(task.id)

        # 이벤트 확인
        event_types = [e.type for e in self.received_events]
        self.assertIn(EventType.TASK_COMPLETED.value, event_types)
        self.assertIn(EventType.PLAN_COMPLETED.value, event_types)

    def test_event_payload_integrity(self):
        """이벤트 페이로드 무결성 테스트"""
        # 플랜 생성
        plan_name = "페이로드 테스트"
        plan_desc = "상세 설명"
        plan = self.wf.start_plan(plan_name, plan_desc)

        # 페이로드 확인
        created_event = self.received_events[0]
        self.assertEqual(created_event.payload['plan_name'], plan_name)
        self.assertEqual(created_event.payload['plan_id'], plan.id)
        self.assertEqual(created_event.payload['project_name'], "test_project")

    def test_multiple_subscribers(self):
        """다중 구독자 테스트"""
        # 추가 구독자
        extra_events = []
        extra_handler = lambda e: extra_events.append(e)

        event_bus.subscribe(EventType.PLAN_CREATED.value, extra_handler)

        # 플랜 생성
        self.wf.start_plan("다중 구독 테스트")

        # 두 핸들러 모두 이벤트 수신 확인
        self.assertTrue(len(self.received_events) > 0)
        self.assertTrue(len(extra_events) > 0)

        # 정리
        event_bus.unsubscribe(EventType.PLAN_CREATED.value, extra_handler)


if __name__ == '__main__':
    unittest.main()
