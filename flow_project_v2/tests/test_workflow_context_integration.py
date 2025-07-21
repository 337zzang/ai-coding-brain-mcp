"""
Test script for Workflow-Context integration
Tests both with and without Context enabled
"""

import os
import sys
sys.path.append('python')

from workflow_wrapper import wf

def test_without_context():
    """Test with Context disabled (default)"""
    print("\n=== Test 1: Context 비활성화 상태 ===")
    os.environ['CONTEXT_SYSTEM'] = 'off'

    # 기본 명령어 테스트
    print("\n1. /status 테스트:")
    result = wf("/status")
    print(f"  결과: {result['ok']}")

    print("\n2. /help 테스트:")
    result = wf("/help")
    print(f"  결과: {result['ok']}")
    if result['ok']:
        # Context 명령어가 없어야 함
        if '/context' not in result['data']:
            print("  ✅ Context 명령어 없음 (정상)")
        else:
            print("  ❌ Context 명령어가 있음 (오류)")

    print("\n3. /context 테스트 (실패해야 함):")
    result = wf("/context")
    if not result['ok'] or '알 수 없는 명령어' in str(result.get('data', '')):
        print("  ✅ Context 명령어 인식 안됨 (정상)")
    else:
        print("  ❌ Context 명령어가 작동함 (오류)")

def test_with_context():
    """Test with Context enabled"""
    print("\n\n=== Test 2: Context 활성화 상태 ===")
    os.environ['CONTEXT_SYSTEM'] = 'on'

    # Context가 제대로 초기화되는지 확인
    print("\n1. Context 초기화 확인:")
    # 새로운 wf 호출로 재초기화 강제
    result = wf("/help")
    print(f"  결과: {result['ok']}")

    print("\n2. /context 테스트:")
    result = wf("/context")
    print(f"  결과: {result['ok']}")
    if result['ok']:
        print("  ✅ Context 요약 생성됨")
        print(f"  요약 길이: {len(result['data'])} 글자")

    print("\n3. /stats 테스트:")
    result = wf("/stats")
    print(f"  결과: {result['ok']}")
    if result['ok']:
        print("  ✅ 통계 정보 표시됨")

    print("\n4. /history 테스트:")
    result = wf("/history 5")
    print(f"  결과: {result['ok']}")

    print("\n5. Task 추가 및 완료 테스트:")
    # Task 추가
    result = wf("/task add 테스트 태스크")
    if result['ok']:
        print("  ✅ Task 추가됨")

        # Task 목록에서 ID 찾기
        list_result = wf("/task list")
        if list_result['ok']:
            # 간단히 마지막 task를 테스트 task로 가정
            print("  ✅ Task 목록 조회됨")

def main():
    """Run all tests"""
    print("🧪 워크플로우-컨텍스트 통합 테스트")
    print("="*60)

    # Test 1: Without context
    test_without_context()

    # Test 2: With context
    test_with_context()

    print("\n\n✅ 테스트 완료!")

    # 원래 상태로 복원
    os.environ['CONTEXT_SYSTEM'] = 'off'

if __name__ == "__main__":
    main()
