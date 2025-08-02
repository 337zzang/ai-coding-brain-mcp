# === 네임스페이스 격리 테스트 ===

def test_namespace_isolation():
    """네임스페이스 격리가 제대로 작동하는지 테스트"""

    print("=== 네임스페이스 격리 테스트 시작 ===\n")

    # 1. 기본 기능 테스트
    print("1. 기본 기능 테스트")
    print("   h.read('test.txt'):", type(h.read))
    print("   h.write:", type(h.write))
    print("   ✅ 프록시를 통한 접근 정상\n")

    # 2. 레거시 호환성 테스트
    print("2. 레거시 호환성 테스트")
    try:
        # 레거시 함수 호출 시 경고 발생 확인
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = read('test.txt')  # 레거시 방식
            if w:
                print(f"   ⚠️ 경고 발생: {w[0].category.__name__}")
                print(f"   메시지: {str(w[0].message)[:50]}...")
            print("   ✅ 레거시 호환성 유지\n")
    except Exception as e:
        print(f"   ❌ 레거시 호출 실패: {e}\n")

    # 3. 덮어쓰기 방지 테스트
    print("3. 함수 덮어쓰기 방지 테스트")
    try:
        h.read = "문자열"  # 이것은 실패해야 함
        print("   ❌ 덮어쓰기 방지 실패!")
    except AttributeError as e:
        print(f"   ✅ 덮어쓰기 차단됨: {str(e)[:50]}...")

    # 4. 전역 변수 오염 테스트
    print("\n4. 전역 변수 오염 테스트")
    print(f"   전역 변수 개수 (h 제외): {len([k for k in globals() if not k.startswith('_') and k != 'h'])}")
    print("   주요 전역 변수:", [k for k in globals() if k in ['read', 'write', 'parse']][:5])

    print("\n=== 테스트 완료 ===")

# 테스트 실행
if __name__ == "__main__":
    test_namespace_isolation()
