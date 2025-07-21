"""
Test script for /flow commands
"""

import os
import sys
sys.path.append('python')

# Context 활성화
os.environ['CONTEXT_SYSTEM'] = 'on'

from workflow_wrapper import wf

def test_flow_commands():
    """Test /flow commands"""
    print("🧪 Flow 명령어 테스트")
    print("="*60)

    # 1. 현재 flow 상태
    print("\n1️⃣ 현재 flow 상태:")
    result = wf("/flow")
    print(f"  결과: {result['ok']}")
    if result['ok']:
        print(f"  {result['data']}")

    # 2. flow 목록
    print("\n2️⃣ Flow 목록:")
    result = wf("/flow list")
    print(f"  결과: {result['ok']}")
    if result['ok']:
        print(f"  {result['data']}")

    # 3. 새 flow 생성
    print("\n3️⃣ 새 Flow 생성:")
    result = wf("/flow create Test Flow Project")
    print(f"  결과: {result['ok']}")
    if result['ok']:
        print(f"  {result['data']}")

    # 4. flow에 plan 추가
    print("\n4️⃣ Plan 추가:")
    result = wf("/flow plan add 테스트 계획")
    print(f"  결과: {result['ok']}")
    if result['ok']:
        print(f"  {result['data']}")

    # 5. plan 목록
    print("\n5️⃣ Plan 목록:")
    result = wf("/flow plan list")
    print(f"  결과: {result['ok']}")
    if result['ok']:
        print(f"  {result['data']}")

    # 6. flow 상태
    print("\n6️⃣ Flow 상태:")
    result = wf("/flow status")
    print(f"  결과: {result['ok']}")
    if 'data' in result:
        # 길이가 길 수 있으므로 일부만 출력
        data = str(result['data'])
        if len(data) > 200:
            print(f"  {data[:200]}...")
        else:
            print(f"  {data}")

    # 7. flow help
    print("\n7️⃣ Flow 도움말:")
    result = wf("/flow help")
    print(f"  결과: {result['ok']}")
    if result['ok']:
        # help는 전체 출력
        print(result['data'])

def test_help_integration():
    """Test if /flow is in main help"""
    print("\n\n📋 통합 도움말 테스트:")
    result = wf("/help")
    if result['ok']:
        help_text = str(result['data'])
        if '/flow' in help_text:
            print("  ✅ /flow 명령어가 help에 포함됨")
        else:
            print("  ❌ /flow 명령어가 help에 없음")

if __name__ == "__main__":
    test_flow_commands()
    test_help_integration()

    print("\n✅ 테스트 완료!")

    # 환경 변수 복원
    os.environ['CONTEXT_SYSTEM'] = 'off'
