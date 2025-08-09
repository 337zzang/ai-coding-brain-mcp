#!/usr/bin/env python3
"""
BrowserManager 테스트 스크립트
세션 생성, 재연결, 추적 테스트
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from browser_manager import BrowserManager
import time

def test_browser_manager():
    """BrowserManager 기본 기능 테스트"""
    print("🧪 BrowserManager 테스트 시작")
    print("=" * 60)

    # 1. 매니저 생성
    print("\n1️⃣ BrowserManager 초기화...")
    manager = BrowserManager()

    # 2. 세션 생성
    print("\n2️⃣ 새 세션 생성...")
    try:
        session = manager.create_session("test_user_001")
        print(f"   ✅ 세션 생성 성공: {session.session_id}")
        print(f"   - PID: {session.pid}")
        print(f"   - WebSocket: {session.ws_endpoint}")
    except Exception as e:
        print(f"   ❌ 세션 생성 실패: {e}")
        return

    # 3. 세션 목록 확인
    print("\n3️⃣ 활성 세션 목록...")
    sessions = manager.list_sessions()
    for s in sessions:
        print(f"   - {s['session_id']}: {s['status']}")

    # 4. 재연결 테스트
    print("\n4️⃣ 세션 재연결 테스트...")
    try:
        browser = manager.connect(session.session_id)
        if browser:
            print(f"   ✅ 재연결 성공!")
            pages = browser.pages
            print(f"   - 현재 페이지 수: {len(pages)}")
        else:
            print(f"   ❌ 재연결 실패")
    except Exception as e:
        print(f"   ❌ 재연결 오류: {e}")

    # 5. 정리
    print("\n5️⃣ 세션 종료...")
    try:
        manager.terminate_session(session.session_id)
        print(f"   ✅ 세션 종료 완료")
    except Exception as e:
        print(f"   ⚠️ 종료 중 오류: {e}")

    print("\n" + "=" * 60)
    print("✅ 테스트 완료!")

if __name__ == "__main__":
    test_browser_manager()
