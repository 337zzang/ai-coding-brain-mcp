"""
타입 안전성 테스트
JsonFlowRepository의 타입 체크가 제대로 작동하는지 확인
"""

from ai_helpers_new.infrastructure.flow_repository import JsonFlowRepository
from ai_helpers_new.infrastructure.project_context import ProjectContext
from pathlib import Path


def test_type_safety():
    """타입 안전성 테스트"""

    # Test 1: 정상 케이스 - ProjectContext
    try:
        context = ProjectContext(Path.cwd())
        repo = JsonFlowRepository(context=context)
        print("✅ Test 1 Pass: ProjectContext 정상 작동")
    except Exception as e:
        print(f"❌ Test 1 Fail: {e}")

    # Test 2: 정상 케이스 - storage_path
    try:
        repo = JsonFlowRepository(storage_path=".ai-brain/flows.json")
        print("✅ Test 2 Pass: storage_path 정상 작동")
    except Exception as e:
        print(f"❌ Test 2 Fail: {e}")

    # Test 3: 에러 케이스 - 잘못된 context 타입
    try:
        repo = JsonFlowRepository(".ai-brain/flows.json")  # 버그 재현
        print("❌ Test 3 Fail: TypeError가 발생해야 함")
    except TypeError as e:
        if "Did you mean to use storage_path parameter?" in str(e):
            print("✅ Test 3 Pass: 올바른 에러 메시지")
        else:
            print(f"❌ Test 3 Partial: {e}")

    # Test 4: 에러 케이스 - 잘못된 storage_path 타입
    try:
        repo = JsonFlowRepository(storage_path=12345)
        print("❌ Test 4 Fail: TypeError가 발생해야 함")
    except TypeError as e:
        print("✅ Test 4 Pass: storage_path 타입 체크 작동")


if __name__ == "__main__":
    print("🧪 JsonFlowRepository 타입 안전성 테스트\n")
    test_type_safety()
    print("\n✅ 모든 테스트 완료!")
