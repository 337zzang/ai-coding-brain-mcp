"""
Workflow v3 테스트 - 데이터 모델
"""
import unittest
from datetime import datetime, timezone
import sys
from pathlib import Path

# 경로 추가
sys.path.append(str(Path(__file__).parent.parent.parent))

from python.workflow.v3.models import (
    Task, WorkflowPlan, WorkflowEvent, WorkflowState,
    TaskStatus, PlanStatus, EventType
)


class TestTask(unittest.TestCase):
    """Task 모델 테스트"""
    
    def test_task_creation(self):
        """태스크 생성 테스트"""
        task = Task(title="테스트 태스크", description="설명")
        
        self.assertEqual(task.title, "테스트 태스크")
        self.assertEqual(task.description, "설명")
        self.assertEqual(task.status, TaskStatus.TODO)
        self.assertIsNotNone(task.id)
        self.assertIsInstance(task.created_at, datetime)
        
    def test_task_validation(self):
        """태스크 검증 테스트"""
        # 빈 제목으로 생성 시도
        with self.assertRaises(ValueError):
            Task(title="", description="설명")
            
        # 공백만 있는 제목
        with self.assertRaises(ValueError):
            Task(title="   ", description="설명")
            
    def test_task_completion(self):
        """태스크 완료 테스트"""
        task = Task(title="테스트 태스크")
        
        # 시작
        task.start()
        self.assertEqual(task.status, TaskStatus.IN_PROGRESS)
        self.assertIsNotNone(task.started_at)
        
        # 완료
        task.complete("완료 메모")
        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertIsNotNone(task.completed_at)
        self.assertIsNotNone(task.duration)
        self.assertIn("완료 메모", task.notes[0])
        
    def test_task_serialization(self):
        """태스크 직렬화 테스트"""
        task = Task(title="테스트 태스크", description="설명")
        
        # to_dict
        data = task.to_dict()
        self.assertEqual(data['title'], "테스트 태스크")
        self.assertEqual(data['status'], 'todo')
        
        # from_dict
        task2 = Task.from_dict(data)
        self.assertEqual(task.id, task2.id)
        self.assertEqual(task.title, task2.title)


class TestWorkflowPlan(unittest.TestCase):
    """WorkflowPlan 모델 테스트"""
    
    def test_plan_creation(self):
        """플랜 생성 테스트"""
        plan = WorkflowPlan(name="테스트 플랜", description="설명")
        
        self.assertEqual(plan.name, "테스트 플랜")
        self.assertEqual(plan.status, PlanStatus.DRAFT)
        self.assertEqual(len(plan.tasks), 0)
        
    def test_plan_validation(self):
        """플랜 검증 테스트"""
        with self.assertRaises(ValueError):
            WorkflowPlan(name="")
            
    def test_plan_task_management(self):
        """플랜의 태스크 관리 테스트"""
        plan = WorkflowPlan(name="테스트 플랜")
        
        # 태스크 추가
        task1 = Task(title="태스크 1")
        task2 = Task(title="태스크 2")
        plan.tasks.extend([task1, task2])
        
        # 현재 태스크 확인
        current = plan.get_current_task()
        self.assertEqual(current.title, "태스크 1")
        
        # 첫 번째 태스크 완료
        task1.complete()
        current = plan.get_current_task()
        self.assertEqual(current.title, "태스크 2")
        
        # 모든 태스크 완료
        task2.complete()
        plan.complete()
        self.assertEqual(plan.status, PlanStatus.COMPLETED)
        self.assertIsNotNone(plan.completed_at)
        
    def test_plan_stats(self):
        """플랜 통계 테스트"""
        plan = WorkflowPlan(name="테스트 플랜")
        
        # 태스크 추가
        for i in range(3):
            task = Task(title=f"태스크 {i+1}")
            if i < 2:  # 2개만 완료
                task.start()
                task.complete()
            plan.tasks.append(task)
            
        plan._update_stats()
        
        self.assertEqual(plan.stats['total_tasks'], 3)
        self.assertEqual(plan.stats['completed_tasks'], 2)
        self.assertAlmostEqual(plan.stats['completion_rate'], 2/3)


class TestWorkflowEvent(unittest.TestCase):
    """WorkflowEvent 모델 테스트"""
    
    def test_event_creation(self):
        """이벤트 생성 테스트"""
        event = WorkflowEvent(
            type=EventType.TASK_ADDED,
            plan_id="plan123",
            task_id="task456",
            details={'title': '새 태스크'}
        )
        
        self.assertEqual(event.type, EventType.TASK_ADDED)
        self.assertEqual(event.plan_id, "plan123")
        self.assertEqual(event.task_id, "task456")
        self.assertIsInstance(event.timestamp, datetime)
        
    def test_event_serialization(self):
        """이벤트 직렬화 테스트"""
        event = WorkflowEvent(
            type=EventType.PLAN_CREATED,
            plan_id="plan123",
            details={'name': '테스트 플랜'}
        )
        
        # to_dict
        data = event.to_dict()
        self.assertEqual(data['type'], 'plan_created')
        self.assertEqual(data['plan_id'], 'plan123')
        
        # from_dict
        event2 = WorkflowEvent.from_dict(data)
        self.assertEqual(event.id, event2.id)
        self.assertEqual(event.type, event2.type)


class TestWorkflowState(unittest.TestCase):
    """WorkflowState 모델 테스트"""
    
    def test_state_creation(self):
        """상태 생성 테스트"""
        state = WorkflowState()
        
        self.assertIsNone(state.current_plan)
        self.assertEqual(len(state.events), 0)
        self.assertEqual(state.version, "3.0.0")
        
    def test_state_with_plan(self):
        """플랜이 있는 상태 테스트"""
        state = WorkflowState()
        plan = WorkflowPlan(name="테스트 플랜")
        state.current_plan = plan
        
        # 이벤트 추가
        event = WorkflowEvent(
            type=EventType.PLAN_CREATED,
            plan_id=plan.id,
            details={'name': plan.name}
        )
        state.add_event(event)
        
        self.assertEqual(len(state.events), 1)
        self.assertIsNotNone(state.last_saved)
        
    def test_plan_history(self):
        """플랜 히스토리 추출 테스트"""
        state = WorkflowState()
        
        # 플랜 1 이벤트
        state.add_event(WorkflowEvent(
            type=EventType.PLAN_CREATED,
            plan_id="plan1",
            details={'name': '플랜 1'}
        ))
        state.add_event(WorkflowEvent(
            type=EventType.PLAN_ARCHIVED,
            plan_id="plan1",
            details={'name': '플랜 1'}
        ))
        
        # 플랜 2 이벤트
        state.add_event(WorkflowEvent(
            type=EventType.PLAN_CREATED,
            plan_id="plan2",
            details={'name': '플랜 2'}
        ))
        
        history = state.get_plan_history()
        self.assertEqual(len(history), 2)
        
        # 플랜 1은 아카이브됨
        plan1 = next(p for p in history if p['id'] == 'plan1')
        self.assertEqual(plan1['status'], 'archived')
        
        # 플랜 2는 활성
        plan2 = next(p for p in history if p['id'] == 'plan2')
        self.assertEqual(plan2['status'], 'active')


if __name__ == '__main__':
    unittest.main()
