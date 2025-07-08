"""
워크플로우 v2 시스템 통합 테스트
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflow.v2 import (
    execute_workflow_command,
    workflow_plan,
    workflow_task,
    workflow_done,
    workflow_status,
    workflow_current
)
from ai_helpers.helper_result import HelperResult

def test_direct_api():
    """직접 함수 호출 테스트"""
    print("\n=== 직접 API 호출 테스트 ===")

    # 1. 플랜 생성
    result = workflow_plan("테스트 플랜", "v2 시스템 테스트용")
    assert result.ok, f"플랜 생성 실패: {result.error}"
    print(f"✅ 플랜 생성: {result.data}")

    # 2. 태스크 추가
    result = workflow_task("첫 번째 태스크", "테스트 태스크입니다")
    assert result.ok, f"태스크 추가 실패: {result.error}"
    print(f"✅ 태스크 추가: {result.data}")

    # 3. 현재 태스크 확인
    result = workflow_current()
    assert result.ok, f"현재 태스크 조회 실패: {result.error}"
    print(f"✅ 현재 태스크: {result.data}")

    # 4. 태스크 완료
    result = workflow_done("테스트 완료")
    assert result.ok, f"태스크 완료 실패: {result.error}"
    print(f"✅ 태스크 완료: {result.data}")

    # 5. 상태 확인
    result = workflow_status()
    assert result.ok, f"상태 조회 실패: {result.error}"
    print(f"✅ 전체 상태: {result.data}")

    return True

def test_command_dispatcher():
    """명령어 디스패처 테스트"""
    print("\n=== 명령어 디스패처 테스트 ===")

    # 1. 플랜 생성 명령
    result = execute_workflow_command("/plan 디스패처 테스트 | 명령어 파싱 테스트")
    assert result.ok, f"명령어 실행 실패: {result.error}"
    print(f"✅ /plan 명령: {result.data}")

    # 2. 태스크 추가 명령
    result = execute_workflow_command("/task 파싱 테스트 | 파이프 구분자 테스트")
    assert result.ok, f"명령어 실행 실패: {result.error}"
    print(f"✅ /task 명령: {result.data}")

    # 3. 잘못된 명령어 테스트
    result = execute_workflow_command("/invalid_command")
    assert not result.ok, "잘못된 명령어가 성공함"
    print(f"✅ 에러 처리: {result.error}")
    print(f"   제안: {result.data}")

    # 4. 빈 명령어 테스트
    result = execute_workflow_command("")
    assert not result.ok, "빈 명령어가 성공함"
    print(f"✅ 빈 명령어 처리: {result.error}")

    return True

def test_error_handling():
    """에러 처리 테스트"""
    print("\n=== 에러 처리 테스트 ===")

    # 1. 플랜 없이 태스크 추가
    result = execute_workflow_command("/plan 에러 테스트 --reset")
    result = workflow_task("테스트", "설명")
    assert result.ok, "정상 케이스 실패"

    # 2. 완료되지 않은 태스크에서 next
    result = workflow_next()
    assert not result.ok, "완료되지 않은 태스크에서 next가 성공함"
    print(f"✅ 미완료 태스크 보호: {result.error}")

    # 3. 잘못된 인자
    result = execute_workflow_command("/status extra arguments")
    assert not result.ok, "불필요한 인자를 받아들임"
    print(f"✅ 인자 검증: {result.error}")

    return True

def run_all_tests():
    """모든 테스트 실행"""
    print("\n" + "="*50)
    print("워크플로우 v2 통합 테스트 시작")
    print("="*50)

    try:
        # 테스트 실행
        test_direct_api()
        test_command_dispatcher()
        test_error_handling()

        print("\n" + "="*50)
        print("✅ 모든 테스트 통과!")
        print("="*50)
        return True

    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
