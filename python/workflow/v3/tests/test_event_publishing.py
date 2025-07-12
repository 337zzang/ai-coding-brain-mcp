"""
이벤트 발행 시스템 테스트
========================

WorkflowManager와 EventBus의 이벤트 발행/구독 기능을 테스트합니다.
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 테스트 대상 모듈 import
import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from python.workflow.v3.manager import WorkflowManager
from python.workflow.v3.event_bus import event_bus, Event
from python.workflow.v3.event_types import EventType
from python.workflow.v3.task_context_manager import TaskContextManager
from python.workflow.v3.task_context_handlers import TaskContextEventHandlers


class TestEventPublishing(unittest.TestCase):
    """이벤트 발행 시스템 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        # 임시 디렉토리 생성
        self.temp_dir = tempfile.mkdtemp()
        self.memory_dir = Path(self.temp_dir) / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # 테스트용 프로젝트 이름
        self.project_name = "test_project"
        
        # 이벤트 수집을 위한 리스트
        self.captured_events: List[Event] = []
        
        # 이벤트 캡처 핸들러 등록
        self._register_event_capture()
        
        # WorkflowManager 인스턴스 캐시 초기화
        WorkflowManager.clear_instance()
    
    def tearDown(self):
        """테스트 환경 정리"""
        # 임시 디렉토리 삭제
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # WorkflowManager 캐시 정리
        WorkflowManager.clear_instance()
        
        # 이벤트 버스 초기화
        event_bus._subscribers.clear()
        
    def _register_event_capture(self):
        """모든 이벤트를 캡처하는 핸들러 등록"""
        def capture_event(event: Event):
            self.captured_events.append(event)
            print(f"📨 Captured event: {event.type}")
        
        # 모든 이벤트 타입에 대해 캡처 핸들러 등록
        for event_type in EventType:
            event_bus.subscribe(event_type, capture_event)
    
    def test_event_bus_basic(self):
        """EventBus 기본 기능 테스트"""
        print("\n🧪 Test: EventBus 기본 기능")
        
        # 테스트 이벤트 발행
        test_event = Event(
            type=EventType.SYSTEM_INFO,
            data={"message": "Test event"}
        )
        
        event_bus.publish(test_event)
        
        # 이벤트가 캡처되었는지 확인
        self.assertEqual(len(self.captured_events), 1)
        self.assertEqual(self.captured_events[0].type, EventType.SYSTEM_INFO)
        self.assertEqual(self.captured_events[0].data["message"], "Test event")
        
        print(f"✅ EventBus published and captured 1 event")
    
    def test_workflow_manager_events(self):
        """WorkflowManager의 이벤트 발행 테스트"""
        print("\n🧪 Test: WorkflowManager 이벤트 발행")
        
        # 테스트용 WorkflowManager 생성
        wm = WorkflowManager(self.project_name)
        
        # 플랜 생성
        plan = wm.start_plan("Test Plan", "Test Description")
        
        # 이벤트 확인
        plan_events = [e for e in self.captured_events if e.type in [EventType.PLAN_CREATED, EventType.PLAN_STARTED]]
        self.assertEqual(len(plan_events), 2)
        
        # PLAN_CREATED 이벤트 확인
        created_event = next(e for e in plan_events if e.type == EventType.PLAN_CREATED)
        self.assertEqual(created_event.data.get("name"), "Test Plan")
        
        # 태스크 추가
        task = wm.add_task("Test Task", "Task Description")
        
        # TASK_ADDED 이벤트 확인
        task_events = [e for e in self.captured_events if e.type == EventType.TASK_ADDED]
        self.assertEqual(len(task_events), 1)
        self.assertEqual(task_events[0].data.get("title"), "Test Task")
        
        print(f"✅ WorkflowManager published {len(self.captured_events)} events")
    
    def test_task_context_integration(self):
        """TaskContextManager 통합 테스트"""
        print("\n🧪 Test: TaskContextManager 통합")
        
        # TaskContextManager 생성
        tcm = TaskContextManager(str(self.memory_dir))
        handlers = TaskContextEventHandlers(tcm)
        handlers.register_all(event_bus)
        
        # WorkflowManager 생성 및 플랜 시작
        wm = WorkflowManager(self.project_name)
        plan = wm.start_plan("Integration Test", "Testing TCM integration")
        
        # task_context.json 파일 확인
        context_file = self.memory_dir / "task_context.json"
        self.assertTrue(context_file.exists())
        
        # 컨텍스트 파일 내용 확인
        with open(context_file, 'r', encoding='utf-8') as f:
            context_data = json.load(f)
        
        # 플랜이 기록되었는지 확인
        self.assertIn(plan.id, context_data.get("plans", {}))
        self.assertEqual(context_data["current_plan"], plan.id)
        
        print(f"✅ TaskContextManager recorded plan: {plan.name}")
    
    def test_event_chain(self):
        """전체 이벤트 체인 테스트"""
        print("\n🧪 Test: 전체 이벤트 체인")
        
        # TaskContextManager 설정
        tcm = TaskContextManager(str(self.memory_dir))
        handlers = TaskContextEventHandlers(tcm)
        handlers.register_all(event_bus)
        
        # WorkflowManager로 전체 플로우 실행
        wm = WorkflowManager(self.project_name)
        
        # 1. 플랜 생성
        plan = wm.start_plan("Complete Flow Test", "Testing complete event flow")
        
        # 2. 태스크 추가
        task1 = wm.add_task("First Task", "Do something")
        task2 = wm.add_task("Second Task", "Do something else")
        
        # 3. 첫 번째 태스크 시작 (수동으로 이벤트 발행)
        from python.workflow.v3.events import EventBuilder
        start_event = EventBuilder.task_started(plan.id, task1)
        wm._add_event(start_event)
        
        # 4. 태스크 완료
        wm.complete_task(task1.id, "Task completed successfully")
        
        # 이벤트 수 확인
        print(f"\n📊 Total events captured: {len(self.captured_events)}")
        
        # 이벤트 타입별 집계
        event_types = {}
        for event in self.captured_events:
            event_types[event.type] = event_types.get(event.type, 0) + 1
        
        print("\n📈 Event type breakdown:")
        for event_type, count in event_types.items():
            print(f"  - {event_type}: {count}")
        
        # 기본 이벤트들이 발행되었는지 확인
        self.assertIn(EventType.PLAN_CREATED, event_types)
        self.assertIn(EventType.PLAN_STARTED, event_types)
        self.assertIn(EventType.TASK_ADDED, event_types)
        self.assertIn(EventType.TASK_COMPLETED, event_types)
        
        # TaskContext 파일 최종 상태 확인
        context_file = self.memory_dir / "task_context.json"
        with open(context_file, 'r', encoding='utf-8') as f:
            final_context = json.load(f)
        
        # 태스크가 완료 상태로 기록되었는지 확인
        task_context = final_context["tasks"].get(task1.id)
        self.assertIsNotNone(task_context)
        self.assertEqual(task_context["status"], "completed")
        
        print("\n✅ Complete event chain test passed!")


def run_tests():
    """테스트 실행"""
    # 테스트 suite 생성
    suite = unittest.TestLoader().loadTestsFromTestCase(TestEventPublishing)
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # 직접 실행 시
    success = run_tests()
    exit(0 if success else 1)
