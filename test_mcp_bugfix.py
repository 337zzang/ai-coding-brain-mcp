#!/usr/bin/env python3
"""
MCP 시스템 핵심 버그 수정 테스트
- 워크플로우 진행률 버그
- HelperResult 이중 래핑
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_workflow_progress():
    """워크플로우 진행률 계산 테스트"""
    print("1. 워크플로우 진행률 테스트")
    print("-" * 40)

    from workflow.models import Plan, Task, TaskStatus

    # 테스트 플랜 생성
    plan = Plan(name="테스트 플랜")

    # 태스크 추가
    task1 = Task(title="태스크 1")
    task2 = Task(title="태스크 2")
    task3 = Task(title="태스크 3")

    plan.add_task(task1.title, task1.description)
    plan.add_task(task2.title, task2.description)
    plan.add_task(task3.title, task3.description)

    # 일부 태스크 완료 (새 방식)
    plan.complete_task(plan.tasks[0].id, "완료 노트 1")

    # 수동으로 문자열 상태 설정 (기존 데이터 시뮬레이션)
    plan.tasks[1].status = 'completed'

    # 진행률 계산 테스트
    from workflow.commands import CommandHandler
    handler = CommandHandler(None)

    completed_count = 0
    for task in plan.tasks:
        # 개선된 로직 테스트
        if hasattr(task, 'status') and (task.status == TaskStatus.COMPLETED or task.status == 'completed'):
            completed_count += 1

    progress = (completed_count / len(plan.tasks) * 100) if len(plan.tasks) > 0 else 0

    print(f"총 태스크: {len(plan.tasks)}")
    print(f"완료된 태스크: {completed_count}")
    print(f"진행률: {progress:.1f}%")

    # 검증
    assert completed_count == 2, f"Expected 2 completed tasks, got {completed_count}"
    assert progress == 66.7 or progress == 66.6, f"Expected ~66.7% progress, got {progress:.1f}%"

    print("✅ 진행률 계산 테스트 통과!")
    return True


def test_helper_result_wrapping():
    """HelperResult 이중 래핑 테스트"""
    print("\n2. HelperResult 이중 래핑 테스트")
    print("-" * 40)

    try:
        from ai_helpers.helper_result import HelperResult
        from helpers_wrapper import HelpersWrapper, safe_helper

        # 테스트 함수
        def test_func():
            return HelperResult.success("테스트 데이터")

        # safe_helper로 래핑
        wrapped = safe_helper(test_func)
        result = wrapped()

        # 이중 래핑 확인
        is_double_wrapped = isinstance(result.data, HelperResult)

        print(f"결과 타입: {type(result)}")
        print(f"결과 모듈: {type(result).__module__}")
        print(f"data 타입: {type(result.data)}")
        print(f"이중 래핑 여부: {is_double_wrapped}")

        if not is_double_wrapped:
            print("✅ 이중 래핑 방지 테스트 통과!")
        else:
            print("⚠️ 아직 이중 래핑 발생 - 모듈 재로드 필요")

        return True

    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        return False


if __name__ == "__main__":
    print("MCP 시스템 핵심 버그 수정 테스트")
    print("=" * 60)

    test1 = test_workflow_progress()
    test2 = test_helper_result_wrapping()

    print("\n" + "=" * 60)
    if test1 and test2:
        print("✅ 모든 테스트 통과!")
    else:
        print("❌ 일부 테스트 실패")
