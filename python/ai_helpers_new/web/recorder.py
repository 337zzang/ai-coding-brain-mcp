"""
웹 자동화 레코더 모듈
브라우저 액션을 기록하고 재생하는 기능 제공
"""

import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from .types import HelperResult, WebAction, SessionStatus, RecorderConfig
from .exceptions import RecorderError, SessionNotFoundError
from .utils import safe_execute, create_session_id
from .browser import get_browser_manager
from .session import get_session_manager

logger = logging.getLogger(__name__)


class ActionRecorder:
    """브라우저 액션 레코더"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.browser_manager = get_browser_manager()
        self.session_manager = get_session_manager()
        self.actions: List[WebAction] = []
        self.is_recording = False
        self.config = RecorderConfig()

    def _get_page(self):
        """페이지 객체 가져오기"""
        result = self.browser_manager.get_page(self.session_id)
        if not result.ok:
            raise RecorderError(f"Cannot get page: {result.error}")
        return result.data

    @safe_execute
    def start_recording(
        self,
        config: Optional[RecorderConfig] = None
    ) -> HelperResult:
        """
        레코딩 시작

        Args:
            config: 레코더 설정

        Returns:
            HelperResult
        """
        if self.is_recording:
            return HelperResult.failure("Recording already in progress")

        if config:
            self.config = config

        page = self._get_page()

        try:
            # 이벤트 리스너 주입
            page.evaluate(self._get_recorder_script())

            # 이벤트 핸들러 등록
            self._setup_event_handlers(page)

            self.is_recording = True
            self.actions = []

            # 세션 상태 업데이트
            self.session_manager.update_session(
                self.session_id,
                status=SessionStatus.RECORDING
            )

            logger.info(f"Started recording for session {self.session_id}")
            return HelperResult.success({"session_id": self.session_id})

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return HelperResult.failure(str(e))

    @safe_execute
    def stop_recording(self) -> HelperResult:
        """
        레코딩 중지

        Returns:
            HelperResult with recorded actions
        """
        if not self.is_recording:
            return HelperResult.failure("No recording in progress")

        self.is_recording = False

        # 세션 상태 업데이트
        self.session_manager.update_session(
            self.session_id,
            status=SessionStatus.ACTIVE
        )

        logger.info(f"Stopped recording for session {self.session_id}")

        return HelperResult.success({
            "session_id": self.session_id,
            "actions": [action.to_dict() for action in self.actions],
            "count": len(self.actions)
        })

    def _get_recorder_script(self) -> str:
        """레코더 JavaScript 코드 반환"""
        return """
        (() => {
            // 이미 설치되어 있으면 스킵
            if (window.__webRecorder) return;

            window.__webRecorder = {
                actions: [],

                recordAction: function(type, data) {
                    const action = {
                        type: type,
                        data: data,
                        timestamp: new Date().toISOString(),
                        url: window.location.href
                    };

                    this.actions.push(action);

                    // 커스텀 이벤트 발생
                    window.dispatchEvent(new CustomEvent('__recorder_action', {
                        detail: action
                    }));
                },

                getSelector: function(element) {
                    // 요소의 선택자 생성
                    if (element.id) {
                        return '#' + element.id;
                    }

                    if (element.className) {
                        const classes = element.className.split(' ')
                            .filter(c => c.trim())
                            .join('.');
                        if (classes) {
                            return element.tagName.toLowerCase() + '.' + classes;
                        }
                    }

                    // 기본 선택자
                    return element.tagName.toLowerCase();
                }
            };

            // 클릭 이벤트 캡처
            document.addEventListener('click', function(e) {
                const selector = window.__webRecorder.getSelector(e.target);
                window.__webRecorder.recordAction('click', {
                    selector: selector,
                    text: e.target.textContent?.substring(0, 100)
                });
            }, true);

            // 입력 이벤트 캡처
            document.addEventListener('input', function(e) {
                if (e.target.tagName === 'INPUT' || 
                    e.target.tagName === 'TEXTAREA') {
                    const selector = window.__webRecorder.getSelector(e.target);
                    window.__webRecorder.recordAction('input', {
                        selector: selector,
                        value: e.target.value,
                        type: e.target.type
                    });
                }
            }, true);

            // 폼 제출 캡처
            document.addEventListener('submit', function(e) {
                const selector = window.__webRecorder.getSelector(e.target);
                window.__webRecorder.recordAction('submit', {
                    selector: selector,
                    method: e.target.method,
                    action: e.target.action
                });
            }, true);

            // 페이지 이동 캡처
            const originalPushState = history.pushState;
            history.pushState = function() {
                originalPushState.apply(history, arguments);
                window.__webRecorder.recordAction('navigate', {
                    url: arguments[2]
                });
            };

            console.log('Web Recorder installed');
        })();
        """

    def _setup_event_handlers(self, page):
        """페이지 이벤트 핸들러 설정"""
        # 페이지에서 발생하는 커스텀 이벤트 수신
        page.expose_function('__record_action', self._handle_action)

        # 이벤트 리스너 등록
        page.evaluate("""
            window.addEventListener('__recorder_action', (e) => {
                window.__record_action(e.detail);
            });
        """)

    def _handle_action(self, action_data: Dict[str, Any]):
        """액션 이벤트 처리"""
        if not self.is_recording:
            return

        action = WebAction(
            action_type=action_data.get('type'),
            selector=action_data.get('data', {}).get('selector'),
            value=action_data.get('data', {}).get('value'),
            metadata=action_data.get('data', {})
        )

        self.actions.append(action)
        logger.debug(f"Recorded action: {action.action_type}")

    @safe_execute
    def get_actions(self) -> HelperResult:
        """
        기록된 액션 조회

        Returns:
            HelperResult with list of actions
        """
        return HelperResult.success({
            "actions": [action.to_dict() for action in self.actions],
            "count": len(self.actions),
            "is_recording": self.is_recording
        })

    @safe_execute
    def clear_actions(self) -> HelperResult:
        """
        기록된 액션 초기화

        Returns:
            HelperResult
        """
        count = len(self.actions)
        self.actions = []

        return HelperResult.success({
            "cleared": count,
            "message": f"Cleared {count} actions"
        })

    @safe_execute
    def save_actions(
        self,
        filepath: str,
        format: str = "json"
    ) -> HelperResult:
        """
        액션을 파일로 저장

        Args:
            filepath: 저장 경로
            format: 저장 형식 (json, script)

        Returns:
            HelperResult
        """
        try:
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)

            if format == "json":
                # JSON 형식으로 저장
                data = {
                    "session_id": self.session_id,
                    "recorded_at": datetime.now().isoformat(),
                    "actions": [action.to_dict() for action in self.actions]
                }

                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)

            elif format == "script":
                # Python 스크립트로 변환
                script = self._generate_script()

                with open(path, 'w', encoding='utf-8') as f:
                    f.write(script)
            else:
                return HelperResult.failure(f"Unknown format: {format}")

            logger.info(f"Saved {len(self.actions)} actions to {filepath}")
            return HelperResult.success({"path": str(path)})

        except Exception as e:
            logger.error(f"Failed to save actions: {e}")
            return HelperResult.failure(str(e))

    def _generate_script(self) -> str:
        """액션을 Python 스크립트로 변환"""
        lines = [
            "# Auto-generated replay script",
            f"# Recorded at: {datetime.now().isoformat()}",
            f"# Actions: {len(self.actions)}",
            "",
            "from ai_helpers_new.web import WebAutomation",
            "",
            "# Initialize",
            "web = WebAutomation()",
            "web.start('replay_session')",
            "",
            "# Replay actions",
        ]

        for action in self.actions:
            if action.action_type == "click":
                lines.append(
                    f"web.click('{action.selector}')"
                )
            elif action.action_type == "input":
                value = action.value.replace("'", "\\'")
                lines.append(
                    f"web.type('{action.selector}', '{value}')"
                )
            elif action.action_type == "navigate":
                url = action.metadata.get('url', '')
                lines.append(
                    f"web.goto('{url}')"
                )
            elif action.action_type == "submit":
                lines.append(
                    f"# Form submit: {action.selector}"
                )

        lines.extend([
            "",
            "# Cleanup",
            "web.close()",
            "",
            "print('Replay completed')"
        ])

        return "\n".join(lines)

    @safe_execute
    def replay_actions(
        self,
        actions: Optional[List[Dict[str, Any]]] = None,
        speed: float = 1.0
    ) -> HelperResult:
        """
        액션 재생

        Args:
            actions: 재생할 액션 목록 (None이면 기록된 액션 사용)
            speed: 재생 속도 (1.0 = 정상)

        Returns:
            HelperResult
        """
        from .actions import get_web_actions
        import time

        if actions is None:
            actions_to_replay = self.actions
        else:
            # Dict를 WebAction으로 변환
            actions_to_replay = [
                WebAction(
                    action_type=a['action_type'],
                    selector=a.get('selector'),
                    value=a.get('value'),
                    metadata=a.get('metadata', {})
                )
                for a in actions
            ]

        if not actions_to_replay:
            return HelperResult.failure("No actions to replay")

        web_actions = get_web_actions()
        delay = 1.0 / speed if speed > 0 else 1.0

        results = []
        for i, action in enumerate(actions_to_replay):
            try:
                if action.action_type == "click":
                    result = web_actions.click(
                        self.session_id,
                        action.selector
                    )
                elif action.action_type == "input":
                    result = web_actions.type_text(
                        self.session_id,
                        action.selector,
                        action.value
                    )
                elif action.action_type == "navigate":
                    url = action.metadata.get('url')
                    if url:
                        result = web_actions.goto(
                            self.session_id,
                            url
                        )
                else:
                    result = HelperResult.success(
                        f"Skipped: {action.action_type}"
                    )

                results.append({
                    "index": i,
                    "action": action.action_type,
                    "success": result.ok if hasattr(result, 'ok') else True
                })

                # 딜레이
                time.sleep(delay)

            except Exception as e:
                logger.error(f"Failed to replay action {i}: {e}")
                results.append({
                    "index": i,
                    "action": action.action_type,
                    "success": False,
                    "error": str(e)
                })

        successful = sum(1 for r in results if r['success'])

        return HelperResult.success({
            "total": len(actions_to_replay),
            "successful": successful,
            "failed": len(actions_to_replay) - successful,
            "results": results
        })


# 전역 레코더 관리
_recorders: Dict[str, ActionRecorder] = {}


def get_recorder(session_id: str) -> ActionRecorder:
    """세션별 레코더 인스턴스 반환"""
    if session_id not in _recorders:
        _recorders[session_id] = ActionRecorder(session_id)
    return _recorders[session_id]


def remove_recorder(session_id: str):
    """레코더 제거"""
    if session_id in _recorders:
        del _recorders[session_id]
