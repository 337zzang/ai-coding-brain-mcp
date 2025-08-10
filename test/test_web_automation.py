"""
웹 자동화 테스트 스크립트
"""

import sys
sys.path.insert(0, 'python')

try:
    import ai_helpers_new as h
    print("✅ ai_helpers_new 모듈 로드 성공")

    # Web 모듈 확인
    if hasattr(h, 'web'):
        print("✅ web 네임스페이스 존재")

        # 함수 목록 확인
        web_functions = [
            'start', 'goto', 'click', 'type', 'extract',
            'screenshot', 'close', 'wait', 'execute_js', 'list_sessions'
        ]

        for func in web_functions:
            if hasattr(h.web, func):
                print(f"  ✅ h.web.{func}")
            else:
                print(f"  ❌ h.web.{func} 없음")

        # 간단한 테스트
        print("\n📋 기능 테스트:")
        print("-" * 40)

        # 세션 목록
        sessions = h.web.list_sessions()
        print(f"현재 세션: {len(sessions)}개")

        # 브라우저 시작 (headless)
        session_id = h.web.start(session_id="test_session", headless=True)
        print(f"세션 시작: {session_id}")

        # 페이지 이동
        if h.web.goto("https://example.com"):
            print("페이지 이동: https://example.com")

            # 타이틀 추출
            title = h.web.extract("title")
            print(f"타이틀: {title}")

        # 브라우저 종료
        h.web.close()
        print("브라우저 종료")

        print("\n✅ 테스트 완료!")

    else:
        print("❌ web 네임스페이스 없음")

except ImportError as e:
    print(f"❌ 모듈 로드 실패: {e}")
except Exception as e:
    print(f"❌ 테스트 실패: {e}")
