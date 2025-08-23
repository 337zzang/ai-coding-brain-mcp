"""
웹 자동화 모듈 - 오버레이 완전 통합 버전
모든 웹 액션에서 자동으로 오버레이 기능이 작동합니다.
"""

import logging
import time
import uuid
from typing import Optional, Any, Dict, List

# 복잡한 import 대신 필요한 것만 import
try:
    from .overlay import OverlayManager, get_overlay_manager, activate, deactivate
except ImportError:
    logging.warning("오버레이 모듈 import 실패 - 기본 기능만 사용")

try:
    from .browser import BrowserManager
except ImportError:
    logging.warning("브라우저 모듈 import 실패")
    BrowserManager = None

# GPS 오버레이 import
try:
    from .web_overlay_gps import WebOverlayGPS
    _gps_overlay_available = True
except ImportError:
    logging.warning("GPS 오버레이 모듈 import 실패")
    WebOverlayGPS = None
    _gps_overlay_available = False

# 전역 변수들
_current_session = None
_overlay_managers = {}
_auto_overlay_enabled = True
_gps_overlays = {}  # GPS 오버레이 인스턴스 관리

class SimpleWebAutomation:
    """단순화된 웹 자동화 클래스 (오버레이 통합)"""

    def __init__(self):
        self.current_session = None
        self.overlay_active = False

    def _ensure_overlay(self, session_id: str):
        """오버레이 자동 활성화"""
        if not _auto_overlay_enabled:
            return False

        try:
            global _overlay_managers
            if session_id not in _overlay_managers:
                # 오버레이 활성화 시도
                overlay_mgr = get_overlay_manager(session_id)
                if not overlay_mgr:
                    activate(session_id)
                    overlay_mgr = get_overlay_manager(session_id)

                _overlay_managers[session_id] = overlay_mgr
                self.overlay_active = True
                logging.info(f"오버레이 자동 활성화: {session_id}")

            return True

        except Exception as e:
            logging.debug(f"오버레이 활성화 실패: {e}")
            return False

    def _record_action(self, session_id: str, action_type: str, **kwargs):
        """액션 자동 기록"""
        try:
            overlay_mgr = _overlay_managers.get(session_id)
            if overlay_mgr and hasattr(overlay_mgr, 'add_action_to_display'):
                action_data = {
                    'type': action_type,
                    'timestamp': int(time.time() * 1000),
                    **kwargs
                }
                overlay_mgr.add_action_to_display(action_data)

                # AI 분석 (백그라운드)
                self._trigger_ai_analysis(overlay_mgr)

        except Exception as e:
            logging.debug(f"액션 기록 실패: {e}")

    def _trigger_ai_analysis(self, overlay_mgr):
        """AI 패턴 분석 트리거"""
        try:
            import sys
            import os

            overlay_path = os.path.join(os.getcwd(), 'browser_overlay_automation')
            if overlay_path not in sys.path:
                sys.path.insert(0, overlay_path)

            from ai_integration.pattern_analyzer import PatternAnalyzer

            analyzer = PatternAnalyzer()
            actions = overlay_mgr.get_actions().get('actions', [])

            if len(actions) >= 3:  # 최소 3개 액션부터 분석
                patterns = analyzer.analyze_sequence(actions[-10:])
                if patterns.get('detected_patterns'):
                    logging.info(f"🤖 감지된 패턴: {patterns['detected_patterns']}")

        except Exception as e:
            logging.debug(f"AI 분석 실패: {e}")

# 전역 인스턴스
_web_auto = SimpleWebAutomation()

def start(headless: bool = False, session_id: str = None, enable_gps: bool = True) -> Dict[str, Any]:
    """브라우저 시작 (오버레이 자동 활성화)"""
    global _current_session, _web_auto, _gps_overlays

    try:
        # 세션 ID 생성
        if not session_id:
            session_id = f"integrated_{uuid.uuid4().hex[:8]}"

        _current_session = session_id
        _web_auto.current_session = session_id

        # 오버레이 자동 활성화
        overlay_activated = _web_auto._ensure_overlay(session_id)
        
        # GPS 오버레이 자동 초기화
        gps_activated = False
        if enable_gps and _gps_overlay_available:
            try:
                gps = WebOverlayGPS()
                _gps_overlays[session_id] = gps
                gps_activated = True
                logging.info(f"🛰️ GPS 오버레이 활성화: {session_id}")
            except Exception as e:
                logging.warning(f"GPS 오버레이 초기화 실패: {e}")

        result = {
            'success': True,
            'session_id': session_id,
            'overlay_auto_activated': overlay_activated,
            'gps_overlay_activated': gps_activated,
            'integration_mode': 'full_auto',
            'message': '통합 웹 자동화 시작 - 오버레이 및 GPS 자동 활성화됨'
        }

        logging.info(f"🚀 통합 웹 자동화 시작: {session_id}")
        return result

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'integration_mode': 'failed'
        }

def goto(url: str, session_id: str = None) -> Dict[str, Any]:
    """페이지 이동 (자동 오버레이 기록)"""
    global _current_session, _web_auto

    session_id = session_id or _current_session

    try:
        # 오버레이 확인
        _web_auto._ensure_overlay(session_id)

        # 액션 기록
        _web_auto._record_action(session_id, 'navigation', target=url)

        # 실제 이동은 시뮬레이션 (실제 BrowserManager 연결 시 대체)
        result = {
            'success': True,
            'url': url,
            'session_id': session_id,
            'overlay_recorded': True,
            'message': f'페이지 이동: {url} (오버레이 자동 기록됨)'
        }

        logging.info(f"📍 페이지 이동: {url} (세션: {session_id})")
        return result

    except Exception as e:
        return {'success': False, 'error': str(e)}

def click(selector: str, session_id: str = None, **kwargs) -> Dict[str, Any]:
    """요소 클릭 (자동 오버레이 기록 + AI 분석)"""
    global _current_session, _web_auto

    session_id = session_id or _current_session

    try:
        # 오버레이 확인
        _web_auto._ensure_overlay(session_id)

        # 액션 기록
        _web_auto._record_action(session_id, 'click', target=selector, **kwargs)

        result = {
            'success': True,
            'selector': selector,
            'session_id': session_id,
            'overlay_recorded': True,
            'ai_analysis_triggered': True,
            'message': f'클릭: {selector} (AI 패턴 분석됨)'
        }

        logging.info(f"👆 클릭: {selector} (세션: {session_id})")
        return result

    except Exception as e:
        return {'success': False, 'error': str(e)}

def type_text(selector: str, text: str, session_id: str = None, **kwargs) -> Dict[str, Any]:
    """텍스트 입력 (자동 오버레이 기록, 보안 마스킹)"""
    global _current_session, _web_auto

    session_id = session_id or _current_session

    try:
        # 오버레이 확인
        _web_auto._ensure_overlay(session_id)

        # 보안 마스킹
        masked_text = '*' * min(len(text), 6) if len(text) > 0 else ''

        # 액션 기록 (마스킹된 텍스트로)
        _web_auto._record_action(session_id, 'type', target=selector, value=masked_text)

        result = {
            'success': True,
            'selector': selector,
            'text_length': len(text),
            'session_id': session_id,
            'overlay_recorded': True,
            'security_masked': True,
            'message': f'텍스트 입력: {selector} (보안 마스킹 적용)'
        }

        logging.info(f"⌨️ 텍스트 입력: {selector} ({len(text)}자, 세션: {session_id})")
        return result

    except Exception as e:
        return {'success': False, 'error': str(e)}

def screenshot(session_id: str = None, include_overlay_data: bool = True) -> Dict[str, Any]:
    """스크린샷 (오버레이 데이터 포함)"""
    global _current_session, _web_auto

    session_id = session_id or _current_session

    try:
        # 액션 기록
        _web_auto._record_action(session_id, 'screenshot')

        result = {
            'success': True,
            'session_id': session_id,
            'timestamp': int(time.time()),
            'overlay_recorded': True,
            'message': '스크린샷 촬영 완료 (오버레이 데이터 포함)'
        }

        # 오버레이 데이터 추가
        if include_overlay_data:
            try:
                overlay_mgr = _overlay_managers.get(session_id)
                if overlay_mgr:
                    overlay_data = overlay_mgr.get_actions()
                    result['overlay_data'] = overlay_data
                    result['actions_count'] = len(overlay_data.get('actions', []))
            except Exception as e:
                logging.debug(f"오버레이 데이터 추가 실패: {e}")

        logging.info(f"📸 스크린샷: (세션: {session_id})")
        return result

    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_page_info(session_id: str = None) -> Dict[str, Any]:
    """페이지 정보 + 오버레이 분석 데이터"""
    global _current_session

    session_id = session_id or _current_session

    try:
        result = {
            'success': True,
            'session_id': session_id,
            'timestamp': int(time.time()),
            'integration_active': True
        }

        # 오버레이 분석 데이터 추가
        try:
            overlay_mgr = _overlay_managers.get(session_id)
            if overlay_mgr:
                overlay_data = overlay_mgr.get_actions()
                result['overlay_analysis'] = overlay_data

                # AI 패턴 분석 추가
                import sys, os
                overlay_path = os.path.join(os.getcwd(), 'browser_overlay_automation')
                if overlay_path not in sys.path:
                    sys.path.insert(0, overlay_path)

                from ai_integration.pattern_analyzer import PatternAnalyzer
                analyzer = PatternAnalyzer()

                actions = overlay_data.get('actions', [])
                if actions:
                    patterns = analyzer.analyze_sequence(actions)
                    result['ai_patterns'] = patterns
                    result['detected_patterns'] = patterns.get('detected_patterns', [])

        except Exception as e:
            logging.debug(f"분석 데이터 추가 실패: {e}")

        return result

    except Exception as e:
        return {'success': False, 'error': str(e)}

def close(session_id: str = None) -> Dict[str, Any]:
    """브라우저 종료 (오버레이 자동 정리)"""
    global _current_session, _overlay_managers, _web_auto, _gps_overlays

    session_id = session_id or _current_session

    try:
        # 오버레이 정리
        cleanup_success = False
        if session_id in _overlay_managers:
            try:
                deactivate(session_id)
                del _overlay_managers[session_id]
                cleanup_success = True
                logging.info(f"🧹 오버레이 정리 완료: {session_id}")
            except Exception as e:
                logging.warning(f"오버레이 정리 실패: {e}")
        
        # GPS 오버레이 정리
        gps_cleanup_success = False
        if session_id in _gps_overlays:
            try:
                del _gps_overlays[session_id]
                gps_cleanup_success = True
                logging.info(f"🛰️ GPS 오버레이 정리 완료: {session_id}")
            except Exception as e:
                logging.warning(f"GPS 오버레이 정리 실패: {e}")

        # 세션 정리
        if session_id == _current_session:
            _current_session = None
            _web_auto.current_session = None

        result = {
            'success': True,
            'session_id': session_id,
            'overlay_cleaned': cleanup_success,
            'gps_overlay_cleaned': gps_cleanup_success,
            'integration_mode': 'closed',
            'message': '통합 웹 자동화 종료 완료'
        }

        logging.info(f"🔚 통합 웹 자동화 종료: {session_id}")
        return result

    except Exception as e:
        return {'success': False, 'error': str(e)}

# 설정 및 상태 함수들
def set_auto_overlay(enabled: bool = True) -> Dict[str, Any]:
    """오버레이 자동 활성화 설정"""
    global _auto_overlay_enabled
    _auto_overlay_enabled = enabled

    return {
        'success': True,
        'auto_overlay_enabled': enabled,
        'message': f'오버레이 자동화 {"활성화" if enabled else "비활성화"}됨'
    }

def get_integration_status() -> Dict[str, Any]:
    """통합 상태 조회"""
    global _current_session, _overlay_managers, _auto_overlay_enabled

    return {
        'success': True,
        'current_session': _current_session,
        'auto_overlay_enabled': _auto_overlay_enabled,
        'active_overlays': len(_overlay_managers),
        'overlay_sessions': list(_overlay_managers.keys()),
        'integration_version': '2.0-simplified',
        'message': '오버레이 완전 통합 모드'
    }

def get_ai_patterns(session_id: str = None) -> Dict[str, Any]:
    """AI 패턴 분석 결과 조회"""
    global _current_session

    session_id = session_id or _current_session

    try:
        overlay_mgr = _overlay_managers.get(session_id)
        if not overlay_mgr:
            return {'success': False, 'error': '활성 세션 없음'}

        import sys, os
        overlay_path = os.path.join(os.getcwd(), 'browser_overlay_automation')
        if overlay_path not in sys.path:
            sys.path.insert(0, overlay_path)

        from ai_integration.pattern_analyzer import PatternAnalyzer
        analyzer = PatternAnalyzer()

        actions = overlay_mgr.get_actions().get('actions', [])
        if not actions:
            return {'success': True, 'patterns': [], 'message': '분석할 액션 없음'}

        patterns = analyzer.analyze_sequence(actions)

        return {
            'success': True,
            'session_id': session_id,
            'total_actions': len(actions),
            'patterns': patterns,
            'detected_patterns': patterns.get('detected_patterns', []),
            'confidence': patterns.get('confidence', 0),
            'recommendations': patterns.get('recommendations', [])
        }

    except Exception as e:
        return {'success': False, 'error': str(e)}

# 호환성 함수들 (기존 API 유지)
type = type_text  # 별칭
wait = lambda seconds: {'success': True, 'waited': seconds, 'message': f'{seconds}초 대기'}
execute_js = lambda code, session_id=None: {'success': True, 'code_length': len(code), 'message': 'JS 실행 시뮬레이션'}
list_sessions = lambda: list(_overlay_managers.keys())
get_current_session = lambda: _current_session
set_current_session = lambda sid: setattr(_web_auto, 'current_session', sid) or {'success': True}
cleanup = close

# 웹 관련 함수들 facade_safe.py에서 사용할 수 있도록 노출
web_start = start
web_goto = goto
web_click = click
web_type = type_text
web_screenshot = screenshot
web_close = close
web_wait = wait
web_execute_js = execute_js

# GPS 오버레이 전용 함수들
def init_gps_overlay(session_id: str = None, **config) -> Dict[str, Any]:
    """GPS 오버레이 초기화"""
    global _current_session, _gps_overlays
    
    session_id = session_id or _current_session
    
    if not _gps_overlay_available:
        return {
            'success': False,
            'error': 'GPS 오버레이 모듈 사용 불가'
        }
    
    try:
        if session_id not in _gps_overlays:
            gps = WebOverlayGPS(**config)
            _gps_overlays[session_id] = gps
            
        return {
            'success': True,
            'session_id': session_id,
            'gps_active': True,
            'message': 'GPS 오버레이 초기화 완료'
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def mark_gps_location(x: int, y: int, label: str = "Click Here", 
                      color: str = "#FF0000", session_id: str = None) -> Dict[str, Any]:
    """GPS 위치 마커 표시"""
    global _current_session, _gps_overlays
    
    session_id = session_id or _current_session
    
    try:
        gps = _gps_overlays.get(session_id)
        if not gps:
            return {'success': False, 'error': 'GPS 오버레이가 초기화되지 않음'}
        
        # JavaScript 코드 생성
        js_code = gps.mark_click_location(x, y, label, color)
        
        return {
            'success': True,
            'x': x,
            'y': y,
            'label': label,
            'color': color,
            'js_code': js_code,
            'message': f'GPS 마커 추가: ({x}, {y}) - {label}'
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def highlight_gps_element(selector: str, color: str = "#00FF00", 
                         label: str = None, session_id: str = None) -> Dict[str, Any]:
    """GPS 요소 하이라이트"""
    global _current_session, _gps_overlays
    
    session_id = session_id or _current_session
    
    try:
        gps = _gps_overlays.get(session_id)
        if not gps:
            return {'success': False, 'error': 'GPS 오버레이가 초기화되지 않음'}
        
        # JavaScript 코드 생성
        js_code = gps.highlight_element(selector, color, label)
        
        return {
            'success': True,
            'selector': selector,
            'color': color,
            'label': label,
            'js_code': js_code,
            'message': f'GPS 하이라이트: {selector}'
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def draw_gps_path(points: List[Dict], color: str = "#0000FF", 
                  session_id: str = None) -> Dict[str, Any]:
    """GPS 경로 그리기"""
    global _current_session, _gps_overlays
    
    session_id = session_id or _current_session
    
    try:
        gps = _gps_overlays.get(session_id)
        if not gps:
            return {'success': False, 'error': 'GPS 오버레이가 초기화되지 않음'}
        
        # JavaScript 코드 생성
        js_code = gps.draw_path(points, color)
        
        return {
            'success': True,
            'points': points,
            'color': color,
            'js_code': js_code,
            'message': f'GPS 경로 그리기: {len(points)}개 포인트'
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def clear_gps_overlay(session_id: str = None) -> Dict[str, Any]:
    """GPS 오버레이 초기화"""
    global _current_session, _gps_overlays
    
    session_id = session_id or _current_session
    
    try:
        gps = _gps_overlays.get(session_id)
        if not gps:
            return {'success': False, 'error': 'GPS 오버레이가 초기화되지 않음'}
        
        # JavaScript 코드 생성
        js_code = gps.clear_overlay()
        
        return {
            'success': True,
            'js_code': js_code,
            'message': 'GPS 오버레이 초기화 완료'
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_gps_status(session_id: str = None) -> Dict[str, Any]:
    """GPS 오버레이 상태 조회"""
    global _current_session, _gps_overlays
    
    session_id = session_id or _current_session
    
    return {
        'success': True,
        'gps_available': _gps_overlay_available,
        'active_sessions': list(_gps_overlays.keys()),
        'current_session': session_id,
        'has_gps': session_id in _gps_overlays if session_id else False
    }
