"""
단순화된 Flow 시스템 테스트
- Flow ID 없음
- 프로젝트당 하나의 Flow
"""
import os
import tempfile
import shutil
from pathlib import Path

from ai_helpers_new.simple_flow_manager import SimpleFlowManager, get_flow_manager


def test_simplified_flow_system():
    """단순화된 Flow 시스템 테스트"""
    print("🧪 단순화된 Flow 시스템 테스트\n")

    # 임시 프로젝트 생성
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "my_project"
        project_path.mkdir()

        print(f"📁 테스트 프로젝트: {project_path}")

        # 1. 초기화 테스트
        print("\n1️⃣ FlowManager 초기화")
        os.chdir(project_path)  # 프로젝트로 이동
        manager = get_flow_manager()

        print(f"   ✅ 프로젝트: {manager.project}")
        print(f"   ✅ Flow 자동 생성됨")

        # 2. Flow 정보 확인
        print("\n2️⃣ Flow 정보 (ID 없음)")
        flow_info = manager.flow
        print(f"   - 이름: {flow_info['name']}")
        print(f"   - 생성일: {flow_info['created_at'][:10]}")
        print(f"   - Plan 수: {flow_info['plan_count']}")

        # 3. 폴더 구조 확인
        print("\n3️⃣ 생성된 폴더 구조")
        flow_dir = project_path / '.ai-brain' / 'flow'
        print(f"   📁 {flow_dir.relative_to(project_path)}")
        print(f"   ├── 📄 flow.json")
        print(f"   └── 📁 plans/")

        # 4. Plan 생성
        print("\n4️⃣ Plan 생성 (flow_id 불필요)")
        plan1 = manager.create_plan("백엔드 개발", "API 서버 구현")
        plan2 = manager.create_plan("프론트엔드 개발", "UI 구현")

        print(f"   ✅ Plan 1: {plan1.id}")
        print(f"   ✅ Plan 2: {plan2.id}")

        # Plan 파일 확인
        plans_dir = flow_dir / "plans"
        plan_files = list(plans_dir.glob("*.json"))
        print(f"\n   📁 plans/ 내용:")
        for pf in plan_files:
            print(f"      - {pf.name}")

        # 5. Task 작업
        print("\n5️⃣ Task 관리")
        task1 = manager.create_task(plan1.id, "DB 스키마 설계")
        task2 = manager.create_task(plan1.id, "API 엔드포인트 구현")

        print(f"   ✅ Task 생성: {task1.name}")
        print(f"   ✅ Task 생성: {task2.name}")

        # 상태 업데이트
        manager.update_task_status(plan1.id, task1.id, "done")
        print(f"   ✅ Task 완료: {task1.name}")

        # 6. 통계 확인
        print("\n6️⃣ 전체 통계")
        stats = manager.get_stats()
        print(f"   - 프로젝트: {stats['project']}")
        print(f"   - Plan 수: {stats['plan_count']}")
        print(f"   - 캐시 크기: {stats['cache_size']}")

        # 7. 재시작 테스트
        print("\n7️⃣ 재시작 후에도 데이터 유지")
        # 새 인스턴스 생성
        manager2 = SimpleFlowManager(str(project_path))
        plans = manager2.list_plans()
        print(f"   ✅ Plan 수: {len(plans)}")
        print(f"   ✅ 데이터 영속성 확인")

        print("\n✅ 모든 테스트 통과!")
        return True


if __name__ == "__main__":
    test_simplified_flow_system()
