"""
워크플로우 V3 시스템 테스트
"""
import sys
sys.path.append('.')

from python.workflow.v3 import WorkflowManager, execute_workflow_command
from python.ai_helpers import workflow

def test_v3_workflow():
    """V3 워크플로우 기본 기능 테스트"""
    print("=== V3 워크플로우 테스트 시작 ===")

    # 1. 플랜 생성
    print("\n1. 플랜 생성 테스트")
    result = workflow("/start V3테스트플랜 테스트용 플랜")
    assert result.ok, f"플랜 생성 실패: {result.error}"
    print(f"✅ 플랜 생성 성공: {result.data}")

    # 2. 태스크 추가
    print("\n2. 태스크 추가 테스트")
    tasks = ["테스트 태스크 1", "테스트 태스크 2", "테스트 태스크 3"]
    for task in tasks:
        result = workflow(f"/task {task}")
        assert result.ok, f"태스크 추가 실패: {result.error}"
    print(f"✅ {len(tasks)}개 태스크 추가 성공")

    # 3. 상태 조회
    print("\n3. 상태 조회 테스트")
    result = workflow("/status")
    assert result.ok, "상태 조회 실패"
    status = result.data.get('status', {})
    print(f"✅ 상태 조회 성공:")
    print(f"   - 플랜: {status.get('plan_name')}")
    print(f"   - 태스크: {status.get('total_tasks')}개")
    print(f"   - 진행률: {status.get('progress_percent')}%")

    # 4. 태스크 완료
    print("\n4. 태스크 완료 테스트")
    result = workflow("/next 첫 번째 태스크 완료!")
    assert result.ok, "태스크 완료 실패"
    print("✅ 태스크 완료 성공")

    # 5. 히스토리 조회
    print("\n5. 히스토리 조회 테스트")
    result = workflow("/status history")
    assert result.ok, "히스토리 조회 실패"
    print(f"✅ 히스토리 조회 성공: {len(result.data.get('history', []))}개 이벤트")

    print("\n=== 모든 테스트 통과 ===")

if __name__ == "__main__":
    test_v3_workflow()
