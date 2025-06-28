"""
UUID 통합 테스트
- Task ID가 UUID로 생성되는지 검증
- 기존 숫자 ID 데이터 로드 시 안전하게 처리되는지 검증
"""

import pytest
import json
import tempfile
import uuid
from pathlib import Path
import sys
import os

# 프로젝트 루트 경로 추가
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from python.core.models import Task, Phase, Plan, ProjectContext
from python.core.context_manager import UnifiedContextManager
from python.core.workflow_manager import WorkflowManager


class TestUUIDIntegration:
    """UUID 통합 테스트 클래스"""
    
    def test_add_task_generates_valid_uuid(self):
        """add_task로 생성된 Task의 ID가 유효한 UUID 형식인지 검증"""
        # Phase 생성
        phase = Phase(
            id="phase-1",
            name="테스트 Phase",  # name 필드 추가
            title="테스트 Phase",
            goals=["테스트 목표"]
        )
        
        # Task 추가
        task = phase.add_task("테스트 작업", "작업 설명")
        
        # 검증
        assert isinstance(task.id, str), "Task ID는 문자열이어야 합니다"
        
        # UUID 형식 검증
        try:
            uuid_obj = uuid.UUID(task.id)
            assert str(uuid_obj) == task.id, "Task ID는 유효한 UUID여야 합니다"
        except ValueError:
            pytest.fail(f"Task ID '{task.id}'는 유효한 UUID가 아닙니다")
        
        print(f"✅ 생성된 Task ID (UUID): {task.id}")
    
    def test_task_model_auto_generates_uuid(self):
        """Task 모델이 ID 없이 생성될 때 자동으로 UUID를 생성하는지 검증"""
        # ID 없이 Task 생성
        task = Task(
            title="테스트 작업",
            description="설명"
        )
        
        # 검증
        assert hasattr(task, 'id'), "Task에 id 필드가 있어야 합니다"
        assert isinstance(task.id, str), "Task ID는 문자열이어야 합니다"
        
        # UUID 검증
        try:
            uuid.UUID(task.id)
            print(f"✅ 자동 생성된 UUID: {task.id}")
        except ValueError:
            pytest.fail(f"자동 생성된 ID '{task.id}'는 유효한 UUID가 아닙니다")
    
    def test_context_loads_with_old_manifest(self):
        """숫자 ID가 포함된 오래된 manifest 파일 로드 시 안전하게 처리되는지 검증"""
        # 임시 디렉토리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            # 오래된 형식의 manifest 생성 (숫자 ID 사용)
            old_manifest = {
                "project_name": "test_project",
                "tasks": [
                    {
                        "id": 1,  # 숫자 ID
                        "title": "Old Task 1",
                        "description": "설명1",
                        "status": "pending"
                    },
                    {
                        "id": 2,  # 숫자 ID
                        "title": "Old Task 2",
                        "description": "설명2",
                        "status": "completed"
                    }
                ]
            }
            
            # manifest 파일 저장
            manifest_path = Path(temp_dir) / "project_manifest.json"
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(old_manifest, f, ensure_ascii=False, indent=2)
            
            print(f"\n📄 테스트용 오래된 manifest 생성: {manifest_path}")
            print(f"  - 숫자 ID 작업 2개 포함")
            
            # Context Manager로 로드 시도
            context_manager = UnifiedContextManager()
            
            # 캐시 경로를 임시 디렉토리로 설정
            context_manager.memory_root = Path(temp_dir)
            context_manager.project_name = "test_project"
            
            # 로드 시도 - 예외가 발생하지 않아야 함
            try:
                # _try_load_cached_context 메서드 직접 호출
                # (실제로는 내부적으로 호출되지만 테스트를 위해 직접 호출)
                context = context_manager._try_load_cached_context()
                
                # 새로운 ProjectContext가 생성되었거나 task가 비어있어야 함
                if context:
                    print(f"\n✅ 컨텍스트 로드 성공")
                    print(f"  - Task 개수: {len(context.tasks) if hasattr(context, 'tasks') else 0}")
                else:
                    print("\n✅ 컨텍스트가 None으로 반환됨 (정상)")
                    
            except Exception as e:
                pytest.fail(f"오래된 manifest 로드 중 예외 발생: {e}")
    
    def test_task_operations_with_uuid(self):
        """UUID 문자열로 Task 작업이 올바르게 동작하는지 검증"""
        # Phase와 Task 직접 생성
        phase = Phase(
            id="phase-1",
            name="테스트 Phase",
            title="테스트 Phase",
            goals=["목표"]
        )
        
        # Task 추가
        task1 = phase.add_task("작업1", "설명1")
        task2 = phase.add_task("작업2", "설명2")
        
        print(f"\n📋 생성된 Tasks:")
        print(f"  - Task 1: {task1.id} - {task1.title}")
        print(f"  - Task 2: {task2.id} - {task2.title}")
        
        # UUID 형식 검증
        import uuid
        try:
            uuid.UUID(task1.id)
            uuid.UUID(task2.id)
            print("\n✅ 모든 Task ID가 유효한 UUID입니다!")
        except ValueError as e:
            pytest.fail(f"유효하지 않은 UUID: {e}")
        
        # Phase의 tasks 딕셔너리에서 UUID로 접근 가능한지 확인
        assert task1.id in phase.tasks, "Task 1이 Phase.tasks에 있어야 합니다"
        assert task2.id in phase.tasks, "Task 2가 Phase.tasks에 있어야 합니다"
        assert phase.tasks[task1.id] == task1, "UUID로 올바른 Task를 가져와야 합니다"
        
        print("\n✅ UUID로 Task 접근 성공!")


if __name__ == "__main__":
    # 직접 실행 시 테스트
    test = TestUUIDIntegration()
    
    print("\n" + "="*60)
    print("UUID 통합 테스트 시작")
    print("="*60)
    
    # 각 테스트 실행
    test.test_task_model_auto_generates_uuid()
    print("\n" + "-"*60)
    
    test.test_add_task_generates_valid_uuid()
    print("\n" + "-"*60)
    
    test.test_context_loads_with_old_manifest()
    print("\n" + "-"*60)
    
    test.test_task_operations_with_uuid()
    
    print("\n" + "="*60)
    print("✅ 모든 테스트 통과!")
    print("="*60)
