"""
극단순 Flow 시스템 테스트
"""
import os
import tempfile
from pathlib import Path

from ai_helpers_new.ultra_simple_flow_manager import UltraSimpleFlowManager


def demo_ultra_simple():
    """극단순 시스템 데모"""
    print("🎯 극단순 Flow 시스템 데모\n")

    # 임시 프로젝트
    with tempfile.TemporaryDirectory() as temp_dir:
        project = Path(temp_dir) / "my_awesome_project"
        project.mkdir()
        os.chdir(project)

        # Manager 초기화
        manager = UltraSimpleFlowManager()
        print(f"프로젝트: {manager.project_name}\n")

        # Plan 생성
        plan1 = manager.create_plan("백엔드 API 개발")
        plan2 = manager.create_plan("프론트엔드 UI 개발")
        plan3 = manager.create_plan("데이터베이스 설계")

        print("✅ 생성된 Plans:")
        for plan in [plan1, plan2, plan3]:
            print(f"   - {plan.id}: {plan.name}")

        # 폴더 구조 확인
        print("\n📁 폴더 구조:")
        flow_dir = project / '.ai-brain' / 'flow'
        for file in sorted(flow_dir.iterdir()):
            print(f"   {file.name}")

        # Task 추가
        task1 = manager.create_task(plan1.id, "REST API 엔드포인트 설계")
        task2 = manager.create_task(plan1.id, "인증 시스템 구현")

        print(f"\n✅ Plan '{plan1.name}'에 Task 추가:")
        print(f"   - {task1.name}")
        print(f"   - {task2.name}")

        # 상태 업데이트
        manager.update_task_status(plan1.id, task1.id, "done")
        print(f"\n✅ Task 완료: {task1.name}")

        # 통계
        stats = manager.get_stats()
        print(f"\n📊 프로젝트 통계:")
        print(f"   - 프로젝트: {stats['project']}")
        print(f"   - Plan 수: {stats['plan_count']}")
        print(f"   - 총 크기: {stats['total_size']} bytes")

        # Plan 파일 내용 확인
        print(f"\n📄 Plan 파일 예시 ({plan1.id}.json):")
        plan_file = flow_dir / f"{plan1.id}.json"
        with open(plan_file) as f:
            import json
            content = json.load(f)
            print(json.dumps(content, indent=2, ensure_ascii=False)[:300] + "...")


if __name__ == "__main__":
    demo_ultra_simple()
