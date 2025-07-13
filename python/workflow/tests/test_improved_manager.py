"""
Improved Workflow Manager Tests
==============================
개선된 워크플로우 매니저 테스트
"""

import unittest
import os
import json
import tempfile
import shutil
from datetime import datetime
from ..improved_manager import ImprovedWorkflowManager
from ..models import TaskStatus, PlanStatus


class TestImprovedWorkflowManager(unittest.TestCase):
    """ImprovedWorkflowManager 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        # 임시 디렉토리 생성
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.test_dir)
        
        # memory 디렉토리 생성
        os.makedirs("memory", exist_ok=True)
        
        # 테스트용 매니저 생성
        self.manager = ImprovedWorkflowManager("test_project")
    
    def tearDown(self):
        """테스트 환경 정리"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.test_dir)
    
    def test_create_plan(self):
        """플랜 생성 테스트"""
        plan_id = self.manager.create_plan("테스트 플랜", "설명")
        
        self.assertIsNotNone(plan_id)
        self.assertEqual(self.manager.data["active_plan_id"], plan_id)
        self.assertEqual(len(self.manager.data["plans"]), 1)
        
        plan = self.manager.data["plans"][0]
        self.assertEqual(plan["name"], "테스트 플랜")
        self.assertEqual(plan["description"], "설명")
        self.assertEqual(plan["status"], PlanStatus.DRAFT.value)
    
    def test_add_task(self):
        """태스크 추가 테스트"""
        plan_id = self.manager.create_plan("테스트 플랜")
        task_id = self.manager.add_task("태스크 1", "설명 1")
        
        self.assertIsNotNone(task_id)
        
        plan = self.manager._get_plan(plan_id)
        self.assertEqual(len(plan["tasks"]), 1)
        
        task = plan["tasks"][0]
        self.assertEqual(task["title"], "태스크 1")
        self.assertEqual(task["description"], "설명 1")
        self.assertEqual(task["status"], TaskStatus.TODO.value)
    
    def test_start_task(self):
        """태스크 시작 테스트"""
        plan_id = self.manager.create_plan("테스트 플랜")
        task_id = self.manager.add_task("태스크 1")
        
        result = self.manager.start_task(task_id)
        self.assertTrue(result)
        
        task = self.manager._find_task(task_id)
        self.assertEqual(task["status"], TaskStatus.IN_PROGRESS.value)
        self.assertIsNotNone(task["started_at"])
    
    def test_complete_task(self):
        """태스크 완료 테스트"""
        plan_id = self.manager.create_plan("테스트 플랜")
        task_id = self.manager.add_task("태스크 1")
        
        self.manager.start_task(task_id)
        result = self.manager.complete_task(task_id, "완료 메모")
        self.assertTrue(result)
        
        task = self.manager._find_task(task_id)
        self.assertEqual(task["status"], TaskStatus.COMPLETED.value)
        self.assertIsNotNone(task["completed_at"])
        self.assertIn("[완료] 완료 메모", task["notes"])
    
    def test_get_status(self):
        """상태 조회 테스트"""
        # 플랜 없을 때
        status = self.manager.get_status()
        self.assertEqual(status["status"], "idle")
        self.assertIsNone(status["plan_id"])
        
        # 플랜 생성 후
        plan_id = self.manager.create_plan("테스트 플랜")
        self.manager.add_task("태스크 1")
        self.manager.add_task("태스크 2")
        
        status = self.manager.get_status()
        self.assertEqual(status["status"], "active")
        self.assertEqual(status["plan_id"], plan_id)
        self.assertEqual(status["plan_name"], "테스트 플랜")
        self.assertEqual(status["total_tasks"], 2)
        self.assertEqual(status["progress"], 0.0)
    
    def test_process_command(self):
        """명령 처리 테스트"""
        # /start 명령
        result = self.manager.process_command("/start 새 프로젝트")
        self.assertTrue(result["success"])
        self.assertIn("plan_id", result)
        
        # /task 명령
        result = self.manager.process_command("/task 첫 번째 태스크")
        self.assertTrue(result["success"])
        self.assertIn("task_id", result)
        
        # /list 명령
        result = self.manager.process_command("/list")
        self.assertTrue(result["success"])
        self.assertEqual(len(result["tasks"]), 1)
        
        # /status 명령
        result = self.manager.process_command("/status")
        self.assertTrue(result["success"])
        self.assertIn("status", result)
        
        # /focus 명령
        result = self.manager.process_command("/focus 1")
        self.assertTrue(result["success"])
        
        # /complete 명령
        result = self.manager.process_command("/complete 작업 완료")
        self.assertTrue(result["success"])
    
    def test_plan_auto_completion(self):
        """플랜 자동 완료 테스트"""
        plan_id = self.manager.create_plan("테스트 플랜")
        task1_id = self.manager.add_task("태스크 1")
        task2_id = self.manager.add_task("태스크 2")
        
        # 모든 태스크 완료
        self.manager.complete_task(task1_id)
        self.manager.complete_task(task2_id)
        
        # 플랜 상태 확인
        plan = self.manager._get_plan(plan_id)
        self.assertEqual(plan["status"], PlanStatus.COMPLETED.value)
        self.assertIsNotNone(plan["completed_at"])
    
    def test_progress_calculation(self):
        """진행률 계산 테스트"""
        plan_id = self.manager.create_plan("테스트 플랜")
        task1_id = self.manager.add_task("태스크 1")
        task2_id = self.manager.add_task("태스크 2")
        task3_id = self.manager.add_task("태스크 3")
        
        # 초기 진행률
        status = self.manager.get_status()
        self.assertEqual(status["progress"], 0.0)
        
        # 1개 완료 (33.33%)
        self.manager.complete_task(task1_id)
        status = self.manager.get_status()
        self.assertAlmostEqual(status["progress"], 33.33, places=1)
        
        # 2개 완료 (66.67%)
        self.manager.complete_task(task2_id)
        status = self.manager.get_status()
        self.assertAlmostEqual(status["progress"], 66.67, places=1)
        
        # 3개 완료 (100%)
        self.manager.complete_task(task3_id)
        status = self.manager.get_status()
        self.assertEqual(status["progress"], 100.0)
    
    def test_event_logging(self):
        """이벤트 로깅 테스트"""
        plan_id = self.manager.create_plan("테스트 플랜")
        task_id = self.manager.add_task("태스크 1")
        
        # 이벤트 확인
        events = self.manager.data["events"]
        self.assertGreaterEqual(len(events), 2)
        
        # 플랜 생성 이벤트
        plan_event = events[0]
        self.assertEqual(plan_event["type"], "plan_created")
        self.assertEqual(plan_event["entity_id"], plan_id)
        
        # 태스크 추가 이벤트
        task_event = events[1]
        self.assertEqual(task_event["type"], "task_added")
        self.assertEqual(task_event["entity_id"], task_id)
    
    def test_persistence(self):
        """데이터 영속성 테스트"""
        plan_id = self.manager.create_plan("테스트 플랜")
        task_id = self.manager.add_task("태스크 1")
        
        # 새 매니저 인스턴스 생성
        new_manager = ImprovedWorkflowManager("test_project")
        
        # 데이터 확인
        self.assertEqual(new_manager.data["active_plan_id"], plan_id)
        self.assertEqual(len(new_manager.data["plans"]), 1)
        
        plan = new_manager._get_plan(plan_id)
        self.assertEqual(plan["name"], "테스트 플랜")
        self.assertEqual(len(plan["tasks"]), 1)


if __name__ == "__main__":
    unittest.main()