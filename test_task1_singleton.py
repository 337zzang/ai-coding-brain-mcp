"""
Task 1 테스트: WorkflowManager 싱글톤 문제 해결
"""

import os
import sys
sys.path.insert(0, os.path.abspath('.'))

from python.workflow_integration import (
    get_workflow_instance, 
    reset_workflow_instance,
    get_current_project_name,
    switch_project_workflow
)

print("Task 1 테스트: WorkflowManager 프로젝트별 격리")
print("=" * 60)

# 1. 현재 프로젝트 인스턴스 생성
current_project = os.path.basename(os.getcwd())
print(f"\n1. 현재 프로젝트: {current_project}")

manager1, commands1 = get_workflow_instance()
print(f"   인스턴스 ID: {id(manager1)}")
print(f"   현재 프로젝트명: {get_current_project_name()}")

# 2. 다른 프로젝트명으로 인스턴스 요청
print(f"\n2. 다른 프로젝트 인스턴스 요청: test-project")
manager2, commands2 = get_workflow_instance("test-project")
print(f"   인스턴스 ID: {id(manager2)}")
print(f"   다른 인스턴스인가? {id(manager1) != id(manager2)}")

# 3. 같은 프로젝트명으로 다시 요청
print(f"\n3. 같은 프로젝트 재요청: {current_project}")
manager3, commands3 = get_workflow_instance(current_project)
print(f"   인스턴스 ID: {id(manager3)}")
print(f"   기존과 동일한가? {id(manager1) == id(manager3)}")

# 4. 인스턴스 초기화 테스트
print(f"\n4. 인스턴스 초기화 테스트")
reset_result = reset_workflow_instance(current_project)
print(f"   초기화 성공: {reset_result}")

manager4, commands4 = get_workflow_instance(current_project)
print(f"   새 인스턴스 ID: {id(manager4)}")
print(f"   초기화되었나? {id(manager1) != id(manager4)}")

print("\n✅ Task 1 테스트 완료!")
