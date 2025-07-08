"""
Workflow v2 단위 테스트 (독립 실행)
"""
import os
import sys

# 직접 경로 설정
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
python_path = os.path.join(project_root, 'python')
sys.path.insert(0, python_path)

def test_models():
    """모델 테스트"""
    print("1. 모델 import 테스트...")
    try:
        from workflow.v2.models import WorkflowPlan, Task, TaskStatus
        print("   ✅ 성공")

        # Task 생성
        task = Task(title="테스트", description="설명")
        assert task.title == "테스트"
        print("   ✅ Task 생성 성공")

        # WorkflowPlan 생성
        plan = WorkflowPlan(name="테스트 플랜")
        assert plan.name == "테스트 플랜"
        print("   ✅ WorkflowPlan 생성 성공")

        return True
    except Exception as e:
        print(f"   ❌ 실패: {e}")
        return False

def test_manager():
    """매니저 테스트"""
    print("\n2. 매니저 테스트...")
    try:
        from workflow.v2.manager import WorkflowV2Manager
        print("   ✅ import 성공")

        # 매니저 생성
        manager = WorkflowV2Manager("test_project")
        assert manager.project_name == "test_project"
        print("   ✅ 매니저 생성 성공")

        # 플랜 생성
        plan = manager.create_plan("테스트", "설명")
        assert plan.name == "테스트"
        print("   ✅ 플랜 생성 성공")

        return True
    except Exception as e:
        print(f"   ❌ 실패: {e}")
        return False

def test_handlers():
    """핸들러 테스트"""
    print("\n3. 핸들러 API 테스트...")
    try:
        from workflow.v2.handlers import get_status
        print("   ✅ import 성공")

        # 상태 조회
        result = get_status()
        assert hasattr(result, 'ok')
        print("   ✅ get_status 호출 성공")

        return True
    except Exception as e:
        print(f"   ❌ 실패: {e}")
        return False

def test_dispatcher():
    """디스패처 테스트"""
    print("\n4. 디스패처 테스트...")
    try:
        from workflow.v2.dispatcher import execute_workflow_command
        print("   ✅ import 성공")

        # 명령 실행
        result = execute_workflow_command("/status")
        assert hasattr(result, 'ok')
        print("   ✅ 명령 실행 성공")

        return True
    except Exception as e:
        print(f"   ❌ 실패: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("🧪 Workflow v2 단위 테스트\n")
    print("=" * 50)

    results = []
    results.append(test_models())
    results.append(test_manager())
    results.append(test_handlers())
    results.append(test_dispatcher())

    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"\n📊 결과: {passed}/{total} 테스트 통과")

    if passed == total:
        print("✅ 모든 테스트 통과!")
        return 0
    else:
        print("❌ 일부 테스트 실패")
        return 1

if __name__ == '__main__':
    exit(main())
