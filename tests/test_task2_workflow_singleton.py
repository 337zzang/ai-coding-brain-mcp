"""
Task 2: WorkflowManager 싱글톤 개선 테스트
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from workflow_integration import (
    get_workflow_instance,
    reset_workflow_instance,
    reset_all_workflow_instances,
    switch_project_workflow
)
from core.context_manager import ContextManager


def test_workflow_singleton():
    """워크플로우 싱글톤 테스트"""
    print("=== WorkflowManager 싱글톤 테스트 ===")

    # 1. 동일 프로젝트에서 여러 번 호출
    print("\n1. 동일 프로젝트 인스턴스 테스트")
    manager1, _ = get_workflow_instance("project1")
    manager2, _ = get_workflow_instance("project1")
    assert manager1 is manager2, "동일 프로젝트는 같은 인스턴스를 반환해야 함"
    print("✅ 동일 프로젝트는 같은 인스턴스 반환")

    # 2. 다른 프로젝트는 다른 인스턴스
    print("\n2. 다른 프로젝트 인스턴스 테스트")
    manager3, _ = get_workflow_instance("project2")
    assert manager1 is not manager3, "다른 프로젝트는 다른 인스턴스를 반환해야 함"
    print("✅ 다른 프로젝트는 다른 인스턴스 반환")

    # 3. reset 테스트
    print("\n3. reset 테스트")
    reset_workflow_instance("project1")
    manager4, _ = get_workflow_instance("project1")
    assert manager1 is not manager4, "reset 후에는 새 인스턴스를 반환해야 함"
    print("✅ reset 후 새 인스턴스 생성됨")

    # 4. reset_all 테스트
    print("\n4. reset_all 테스트")
    reset_all_workflow_instances()
    manager5, _ = get_workflow_instance("project1")
    manager6, _ = get_workflow_instance("project2")
    assert manager4 is not manager5, "reset_all 후 모든 인스턴스가 재생성되어야 함"
    print("✅ reset_all 후 모든 인스턴스 재생성됨")

    print("\n✅ 모든 테스트 통과!")


if __name__ == "__main__":
    test_workflow_singleton()
