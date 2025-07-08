#!/usr/bin/env python3
"""
HelperResult 이중 래핑 문제 테스트
목적: 현재 상태 확인 및 수정 후 검증
"""

import sys
import os

# 프로젝트 루트 경로를 PYTHONPATH에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# python 디렉토리도 추가 (ai_helpers를 찾을 수 있도록)
python_path = os.path.join(project_root, 'python')
sys.path.insert(0, python_path)

from helpers_wrapper import HelpersWrapper

def test_double_wrapping():
    """이중 래핑 발생 여부 테스트"""
    print("\n=== 이중 래핑 테스트 시작 ===\n")

    helpers = HelpersWrapper()
    test_cases = []

    # 1. Git 명령 테스트
    print("1. Git status 테스트:")
    try:
        result = helpers.git_status()
        print(f"   - result 타입: {type(result).__name__}")
        print(f"   - result.ok: {result.ok}")
        print(f"   - result.data 타입: {type(result.data).__name__}")

        is_double_wrapped = hasattr(result.data, 'ok') and hasattr(result.data, 'data')
        print(f"   - 이중 래핑 발생: {'❌ YES' if is_double_wrapped else '✅ NO'}")
        test_cases.append(('git_status', is_double_wrapped))

        if is_double_wrapped:
            print(f"   - 실제 데이터 접근: result.data.data 필요")
            print(f"   - 실제 데이터 타입: {type(result.data.data).__name__}")
    except Exception as e:
        print(f"   - 에러 발생: {e}")
        test_cases.append(('git_status', True))  # 에러도 실패로 처리

    # 2. 워크플로우 명령 테스트
    print("\n2. Workflow status 테스트:")
    try:
        result = helpers.workflow("/status")
        print(f"   - result 타입: {type(result).__name__}")
        print(f"   - result.ok: {result.ok}")
        print(f"   - result.data 타입: {type(result.data).__name__}")

        is_double_wrapped = hasattr(result.data, 'ok') and hasattr(result.data, 'data')
        print(f"   - 이중 래핑 발생: {'❌ YES' if is_double_wrapped else '✅ NO'}")
        test_cases.append(('workflow_status', is_double_wrapped))
    except Exception as e:
        print(f"   - 에러 발생: {e}")
        test_cases.append(('workflow_status', True))

    # 3. 파일 읽기 테스트
    print("\n3. Read file 테스트:")
    try:
        result = helpers.read_file('README.md')
        print(f"   - result 타입: {type(result).__name__}")
        print(f"   - result.ok: {result.ok}")
        print(f"   - result.data 타입: {type(result.data).__name__}")

        is_double_wrapped = hasattr(result.data, 'ok') and hasattr(result.data, 'data')
        print(f"   - 이중 래핑 발생: {'❌ YES' if is_double_wrapped else '✅ NO'}")
        test_cases.append(('read_file', is_double_wrapped))
    except Exception as e:
        print(f"   - 에러 발생: {e}")
        test_cases.append(('read_file', True))

    # 결과 요약
    print("\n=== 테스트 결과 요약 ===")
    failed_count = sum(1 for _, failed in test_cases if failed)
    print(f"전체 테스트: {len(test_cases)}개")
    print(f"이중 래핑 발생: {failed_count}개")
    print(f"정상: {len(test_cases) - failed_count}개")

    if failed_count > 0:
        print("\n❌ 이중 래핑 문제가 발생하고 있습니다!")
        print("\n현재 helpers_wrapper.py의 import:")
        print("from ai_helpers.helper_result import HelperResult")
        print("\n문제: helpers_wrapper.py가 ai_helpers.HelperResult를 사용하지만")
        print("실제로는 루트의 HelperResult와 충돌이 발생 중")
    else:
        print("\n✅ 모든 테스트 통과! 이중 래핑 문제가 해결되었습니다.")

    return failed_count == 0

if __name__ == "__main__":
    test_double_wrapping()
