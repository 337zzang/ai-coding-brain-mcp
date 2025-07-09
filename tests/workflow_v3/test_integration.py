"""
Workflow v3 통합 테스트
"""
import unittest
import tempfile
import shutil
import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from python.workflow.v3.manager import WorkflowManager
from python.workflow.v3.parser import CommandParser
from python.workflow.v3.models import TaskStatus, PlanStatus
from python.workflow.v3.storage import FileStorage


class TestWorkflowIntegration(unittest.TestCase):
    """워크플로우 통합 테스트"""
    
    def setUp(self):
        """테스트 환경 설정"""
        # 임시 디렉토리 생성
        self.test_dir = tempfile.mkdtemp()
        self.storage = FileStorage(self.test_dir)
        self.manager = WorkflowManager(storage=self.storage)
        self.parser = CommandParser()
        
    def tearDown(self):
        """테스트 환경 정리"""
        shutil.rmtree(self.test_dir)
        
    def execute_command(self, command_str):
        """명령어 실행 헬퍼"""
        parsed = self.parser.parse(command_str)
        return self.manager.execute(parsed)
        
    def test_complete_workflow_cycle(self):
        """전체 워크플로우 사이클 테스트"""
        # 1. 플랜 생성
        result = self.execute_command("/start 테스트 프로젝트 | 통합 테스트용 프로젝트")
        self.assertTrue(result['success'])
        self.assertEqual(result['plan']['name'], "테스트 프로젝트")
        self.assertEqual(result['plan']['description'], "통합 테스트용 프로젝트")
        
        # 2. 태스크 추가
        tasks = [
            "/task 요구사항 분석",
            "/task 시스템 설계 | 아키텍처 설계",
            "/task 구현",
            "/task 테스트"
        ]
        
        for cmd in tasks:
            result = self.execute_command(cmd)
            self.assertTrue(result['success'])
            
        # 3. 상태 확인
        result = self.execute_command("/status")
        self.assertTrue(result['success'])
        self.assertEqual(result['total_tasks'], 4)
        self.assertEqual(result['completed_tasks'], 0)
        
        # 4. 첫 번째 태스크 시작
        result = self.execute_command("/focus 1")
        self.assertTrue(result['success'])
        self.assertEqual(result['task']['title'], "요구사항 분석")
        
        # 5. 태스크 완료
        result = self.execute_command("/next 요구사항 분석 완료!")
        self.assertTrue(result['success'])
        self.assertEqual(result['completed_task']['status'], 'completed')
        self.assertEqual(result['next_task']['title'], "시스템 설계")
        
        # 6. 나머지 태스크 완료
        for i in range(3):
            result = self.execute_command(f"/next 태스크 {i+2} 완료!")
            self.assertTrue(result['success'])
            
        # 7. 플랜 완료 확인
        state = self.manager.get_state()
        self.assertEqual(state.current_plan.status, PlanStatus.COMPLETED)
        
    def test_alias_commands(self):
        """별칭 명령어 테스트"""
        # 플랜 생성 (/s = /start)
        result = self.execute_command("/s 별칭 테스트")
        self.assertTrue(result['success'])
        
        # 태스크 추가 (/t = /task)
        result = self.execute_command("/t 태스크 1")
        self.assertTrue(result['success'])
        
        # 포커스 (/f = /focus)
        result = self.execute_command("/f 1")
        self.assertTrue(result['success'])
        
        # 다음 진행 (/n = /next)
        result = self.execute_command("/n 완료!")
        self.assertTrue(result['success'])
        
    def test_legacy_command_compatibility(self):
        """레거시 명령어 호환성 테스트"""
        # 플랜 생성
        self.execute_command("/start 레거시 테스트")
        self.execute_command("/task 태스크 1")
        
        # /done -> /next
        result = self.execute_command("/done 레거시 완료 명령")
        self.assertTrue(result['success'])
        
        # /history -> /status history
        result = self.execute_command("/history")
        self.assertTrue(result['success'])
        self.assertIn('history', result)
        
    def test_error_handling(self):
        """에러 처리 테스트"""
        # 플랜 없이 태스크 추가 시도
        result = self.execute_command("/task 태스크")
        self.assertFalse(result['success'])
        self.assertIn("error", result)
        
        # 잘못된 태스크 번호로 focus
        self.execute_command("/start 에러 테스트")
        result = self.execute_command("/focus 999")
        self.assertFalse(result['success'])
        
    def test_persistence(self):
        """데이터 영속성 테스트"""
        # 플랜 생성 및 태스크 추가
        self.execute_command("/start 영속성 테스트")
        self.execute_command("/task 태스크 1")
        self.execute_command("/task 태스크 2")
        
        # 매니저 재생성 (저장된 데이터 로드)
        manager2 = WorkflowManager(storage=self.storage)
        state = manager2.get_state()
        
        # 데이터 확인
        self.assertIsNotNone(state.current_plan)
        self.assertEqual(state.current_plan.name, "영속성 테스트")
        self.assertEqual(len(state.current_plan.tasks), 2)
        
    def test_build_command(self):
        """문서화 명령어 테스트"""
        # 플랜 생성 및 태스크 추가
        self.execute_command("/start 문서화 테스트")
        self.execute_command("/task 태스크 1")
        self.execute_command("/next 완료!")
        
        # 빌드 명령
        result = self.execute_command("/build")
        self.assertTrue(result['success'])
        self.assertIn('content', result)
        
        # 리뷰 빌드
        result = self.execute_command("/build review")
        self.assertTrue(result['success'])
        self.assertIn('review', result['content'].lower())
        
    def test_plan_list_command(self):
        """플랜 목록 명령어 테스트"""
        # 여러 플랜 생성
        self.execute_command("/start 플랜 1")
        self.execute_command("/next")  # 플랜 완료를 위해
        
        self.execute_command("/start 플랜 2")
        
        # 플랜 목록 조회
        result = self.execute_command("/plan list")
        self.assertTrue(result['success'])
        self.assertGreaterEqual(len(result['plans']), 2)
        
    def test_status_history_command(self):
        """히스토리 조회 테스트"""
        # 이벤트 생성
        self.execute_command("/start 히스토리 테스트")
        self.execute_command("/task 태스크 1")
        self.execute_command("/next 완료!")
        
        # 히스토리 조회
        result = self.execute_command("/status history")
        self.assertTrue(result['success'])
        self.assertGreater(len(result['history']), 0)
        
        # 이벤트 타입 확인
        event_types = [e['type'] for e in result['history']]
        self.assertIn('plan_created', event_types)
        self.assertIn('task_added', event_types)
        self.assertIn('task_completed', event_types)


if __name__ == '__main__':
    unittest.main(verbosity=2)
