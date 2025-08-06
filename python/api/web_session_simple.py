# web_session_simple.py - 기존 구조 활용 버전
"""
간단한 세션 유지 시스템
- 기존 BrowserManager와 REPLBrowserWithRecording 활용
- 세션 정보를 파일로 저장하여 다른 프로세스에서 참조
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

# 세션 정보 저장 경로
SESSION_DIR = Path.home() / ".web_sessions_simple"
SESSION_DIR.mkdir(exist_ok=True)


def save_session_info(session_id: str, info: Dict[str, Any]) -> bool:
    """세션 정보를 파일로 저장"""
    try:
        session_file = SESSION_DIR / f"{session_id}.json"
        with open(session_file, 'w') as f:
            json.dump(info, f, indent=2)
        return True
    except Exception as e:
        print(f"❌ 세션 저장 실패: {e}")
        return False


def load_session_info(session_id: str) -> Optional[Dict[str, Any]]:
    """저장된 세션 정보 로드"""
    try:
        session_file = SESSION_DIR / f"{session_id}.json"
        if session_file.exists():
            with open(session_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"❌ 세션 로드 실패: {e}")
    return None


def delete_session_info(session_id: str) -> bool:
    """세션 정보 삭제"""
    try:
        session_file = SESSION_DIR / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            return True
    except Exception as e:
        print(f"❌ 세션 삭제 실패: {e}")
    return False


def list_saved_sessions() -> list:
    """저장된 세션 목록"""
    sessions = []
    try:
        for file in SESSION_DIR.glob("*.json"):
            session_id = file.stem
            info = load_session_info(session_id)
            if info:
                sessions.append({
                    "id": session_id,
                    "created": info.get("created"),
                    "url": info.get("url"),
                    "title": info.get("title")
                })
    except Exception as e:
        print(f"❌ 세션 목록 조회 실패: {e}")
    return sessions


# 헬퍼 함수와 통합
def web_save_session(session_id: str = "default") -> Dict[str, Any]:
    """현재 브라우저 세션 정보 저장"""
    try:
        from api.web_automation_manager import browser_manager
        from datetime import datetime

        # 현재 브라우저 인스턴스 확인
        instance = browser_manager.get_instance(session_id)

        if instance and hasattr(instance, 'page'):
            page = instance.page
            info = {
                "id": session_id,
                "created": datetime.now().isoformat(),
                "url": page.url if hasattr(page, 'url') else "about:blank",
                "title": page.title() if hasattr(page, 'title') else "",
                "cookies": page.context.cookies() if hasattr(page, 'context') else [],
                "active": True
            }

            if save_session_info(session_id, info):
                return {
                    'ok': True,
                    'data': {
                        'session_id': session_id,
                        'saved': True,
                        'file': str(SESSION_DIR / f"{session_id}.json")
                    }
                }

        return {
            'ok': False,
            'error': f'세션 {session_id}를 찾을 수 없습니다'
        }
    except Exception as e:
        return {
            'ok': False,
            'error': str(e)
        }


def web_load_session(session_id: str = "default") -> Dict[str, Any]:
    """저장된 세션 정보 로드 및 복원"""
    try:
        info = load_session_info(session_id)

        if not info:
            return {
                'ok': False,
                'error': f'저장된 세션 {session_id}를 찾을 수 없습니다'
            }

        from api.web_automation_integrated import REPLBrowserWithRecording
        from api.web_automation_manager import browser_manager

        # 새 브라우저 인스턴스 생성
        instance = REPLBrowserWithRecording(headless=False)
        instance.start()

        # 저장된 URL로 이동
        if info.get('url'):
            instance.goto(info['url'])

        # 쿠키 복원
        if info.get('cookies'):
            try:
                for cookie in info['cookies']:
                    instance.page.context.add_cookies([cookie])
            except:
                pass

        # BrowserManager에 등록
        browser_manager.set_instance(instance, session_id)

        # 전역 인스턴스 설정
        from api.web_automation_helpers import _set_web_instance
        _set_web_instance(instance)

        return {
            'ok': True,
            'data': {
                'session_id': session_id,
                'loaded': True,
                'url': info.get('url'),
                'title': info.get('title')
            }
        }
    except Exception as e:
        return {
            'ok': False,
            'error': str(e)
        }


def web_session_status(session_id: str = "default") -> Dict[str, Any]:
    """세션 상태 확인"""
    try:
        from api.web_automation_manager import browser_manager

        # 메모리에서 확인
        instance = browser_manager.get_instance(session_id)
        memory_active = instance is not None

        # 파일에서 확인
        info = load_session_info(session_id)
        file_exists = info is not None

        return {
            'ok': True,
            'data': {
                'session_id': session_id,
                'memory_active': memory_active,
                'file_exists': file_exists,
                'url': info.get('url') if info else None,
                'title': info.get('title') if info else None,
                'created': info.get('created') if info else None
            }
        }
    except Exception as e:
        return {
            'ok': False,
            'error': str(e)
        }
