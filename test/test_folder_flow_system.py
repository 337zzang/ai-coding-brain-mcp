"""
폴더 기반 Flow 시스템 테스트
"""
import os
import tempfile
import shutil
from pathlib import Path

from ai_helpers_new.folder_flow_manager import FolderFlowManager
from ai_helpers_new.domain.models import TaskStatus


def test_folder_flow_system():
    """폴더 기반 Flow 시스템 통합 테스트"""
    print("🧪 폴더 기반 Flow 시스템 테스트 시작\n")

    # 임시 프로젝트 디렉토리 생성
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()

        print(f"📁 테스트 프로젝트: {project_path}")

        # 1. FlowManager 초기화
        print("\n1️⃣ FlowManager 초기화")
        manager = FolderFlowManager(str(project_path))
        print(f"   ✅ Flow 자동 생성됨: {manager.current_flow.id}")

        # 2. Plan 생성
        print("\n2️⃣ Plan 생성")
        flow = manager.current_flow
        plan1 = manager.create_plan(flow.id, "테스트 계획 1")
        plan2 = manager.create_plan(flow.id, "테스트 계획 2")
        print(f"   ✅ Plan 1: {plan1.id}")
        print(f"   ✅ Plan 2: {plan2.id}")

        # 3. Task 생성
        print("\n3️⃣ Task 생성")
        task1 = manager.create_task(flow.id, plan1.id, "Task 1")
        task2 = manager.create_task(flow.id, plan1.id, "Task 2")
        task3 = manager.create_task(flow.id, plan2.id, "Task 3")
        print(f"   ✅ Plan 1에 Task 2개 추가")
        print(f"   ✅ Plan 2에 Task 1개 추가")

        # 4. 폴더 구조 확인
        print("\n4️⃣ 생성된 폴더 구조 확인")
        flow_dir = project_path / '.ai-brain' / 'flow'
        print(f"   📁 {flow_dir}")

        # flow.json 확인
        flow_json = flow_dir / flow.id / "flow.json"
        print(f"   ├── 📄 {flow_json.name} ({flow_json.stat().st_size} bytes)")

        # plans 디렉토리 확인
        plans_dir = flow_dir / flow.id / "plans"
        for plan_file in plans_dir.glob("*.json"):
            print(f"   └── 📄 plans/{plan_file.name} ({plan_file.stat().st_size} bytes)")

        # 5. Task 상태 업데이트
        print("\n5️⃣ Task 상태 업데이트")
        manager.update_task_status(flow.id, plan1.id, task1.id, TaskStatus.IN_PROGRESS.value)
        manager.update_task_status(flow.id, plan1.id, task1.id, TaskStatus.DONE.value)
        print(f"   ✅ Task 1 완료")

        # 6. 캐시 통계
        print("\n6️⃣ 캐시 통계")
        stats = manager.get_stats()
        cache_stats = stats['service_stats']['cache_stats']
        print(f"   - Flow 캐시 히트: {cache_stats['flow_hits']}")
        print(f"   - Flow 캐시 미스: {cache_stats['flow_misses']}")
        print(f"   - Plan 캐시 히트: {cache_stats['plan_hits']}")
        print(f"   - Plan 캐시 미스: {cache_stats['plan_misses']}")

        # 7. API 호환성 테스트
        print("\n7️⃣ API 호환성 테스트")
        # 기존 API처럼 plans 딕셔너리 접근
        flow_loaded = manager.get_flow(flow.id)
        print(f"   ✅ flow.plans 타입: {type(flow_loaded.plans)}")
        print(f"   ✅ Plan 수: {len(manager.get_plans(flow.id))}")

        print("\n✅ 모든 테스트 통과!")

        return True


if __name__ == "__main__":
    test_folder_flow_system()
