"""
웹 자동화 오버레이 UI 모듈
브라우저에 플로팅 제어 패널을 제공
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .types import HelperResult, OverlayConfig
from .exceptions import OverlayError
from .utils import safe_execute
from .browser import get_browser_manager
from .session import get_session_manager

logger = logging.getLogger(__name__)


class OverlayManager:
    """오버레이 UI 관리자"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.browser_manager = get_browser_manager()
        self.session_manager = get_session_manager()
        self.is_active = False
        self.config = OverlayConfig()
        self.actions: List[Dict[str, Any]] = []

    def _get_page(self):
        """페이지 객체 가져오기"""
        result = self.browser_manager.get_page(self.session_id)
        if not result.ok:
            raise OverlayError(f"Cannot get page: {result.error}")
        return result.data

    @safe_execute
    def activate(
        self,
        config: Optional[OverlayConfig] = None
    ) -> HelperResult:
        """
        오버레이 활성화

        Args:
            config: 오버레이 설정

        Returns:
            HelperResult
        """
        if self.is_active:
            return HelperResult.success({"message": "Overlay already active"})

        if config:
            self.config = config

        page = self._get_page()

        try:
            # CSS 주입
            page.add_style_tag(content=self._get_overlay_css())

            # JavaScript 주입
            page.evaluate(self._get_overlay_javascript())

            # 이벤트 핸들러 설정
            self._setup_event_handlers(page)

            self.is_active = True

            logger.info(f"Overlay activated for session {self.session_id}")
            return HelperResult.success({
                "session_id": self.session_id,
                "config": {
                    "mini_mode": self.config.mini_mode,
                    "position": self.config.position,
                    "theme": self.config.theme
                }
            })

        except Exception as e:
            logger.error(f"Failed to activate overlay: {e}")
            return HelperResult.failure(str(e))

    @safe_execute
    def deactivate(self) -> HelperResult:
        """
        오버레이 비활성화

        Returns:
            HelperResult
        """
        if not self.is_active:
            return HelperResult.success({"message": "Overlay not active"})

        page = self._get_page()

        try:
            # 오버레이 제거
            page.evaluate("""
                const overlay = document.getElementById('web-automation-overlay');
                if (overlay) {
                    overlay.remove();
                }

                // 이벤트 리스너 정리
                if (window.__overlayManager) {
                    window.__overlayManager.cleanup();
                    delete window.__overlayManager;
                }
            """)

            self.is_active = False

            logger.info(f"Overlay deactivated for session {self.session_id}")
            return HelperResult.success({"session_id": self.session_id})

        except Exception as e:
            logger.error(f"Failed to deactivate overlay: {e}")
            return HelperResult.failure(str(e))

    def _get_overlay_css(self) -> str:
        """오버레이 CSS 반환"""
        position_map = {
            "top-right": "top: 20px; right: 20px;",
            "top-left": "top: 20px; left: 20px;",
            "bottom-right": "bottom: 20px; right: 20px;",
            "bottom-left": "bottom: 20px; left: 20px;"
        }

        position_style = position_map.get(self.config.position, position_map["top-right"])

        return f"""
        #web-automation-overlay {{
            position: fixed;
            {position_style}
            z-index: 999999;
            background: rgba(255, 255, 255, 0.95);
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 14px;
            min-width: 200px;
            transition: all 0.3s ease;
        }}

        #web-automation-overlay.mini {{
            min-width: 50px;
            padding: 5px;
        }}

        #web-automation-overlay.dark {{
            background: rgba(30, 30, 30, 0.95);
            border-color: #444;
            color: #fff;
        }}

        .overlay-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            padding-bottom: 8px;
            border-bottom: 1px solid #eee;
        }}

        .overlay-title {{
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .overlay-controls {{
            display: flex;
            gap: 5px;
        }}

        .overlay-btn {{
            background: #007bff;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: background 0.2s;
        }}

        .overlay-btn:hover {{
            background: #0056b3;
        }}

        .overlay-btn.danger {{
            background: #dc3545;
        }}

        .overlay-btn.danger:hover {{
            background: #c82333;
        }}

        .overlay-btn.success {{
            background: #28a745;
        }}

        .overlay-btn.success:hover {{
            background: #218838;
        }}

        .overlay-status {{
            margin: 10px 0;
            padding: 8px;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 12px;
        }}

        .overlay-actions {{
            max-height: 200px;
            overflow-y: auto;
            margin: 10px 0;
        }}

        .overlay-action-item {{
            padding: 4px 8px;
            margin: 2px 0;
            background: #fff;
            border: 1px solid #e9ecef;
            border-radius: 3px;
            font-size: 11px;
        }}

        .overlay-minimize {{
            width: 20px;
            height: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        """

    def _get_overlay_javascript(self) -> str:
        """오버레이 JavaScript 반환"""
        return f"""
        (() => {{
            // 기존 오버레이 제거
            const existing = document.getElementById('web-automation-overlay');
            if (existing) existing.remove();

            // 오버레이 관리자
            window.__overlayManager = {{
                actions: [],
                isRecording: false,

                init: function() {{
                    this.createOverlay();
                    this.attachEventHandlers();
                }},

                createOverlay: function() {{
                    const overlay = document.createElement('div');
                    overlay.id = 'web-automation-overlay';
                    overlay.className = '{self.config.theme}';

                    overlay.innerHTML = `
                        <div class="overlay-header">
                            <div class="overlay-title">Web Automation</div>
                            <div class="overlay-minimize" onclick="__overlayManager.toggleMinimize()">
                                ▼
                            </div>
                        </div>

                        <div class="overlay-body">
                            <div class="overlay-status">
                                Status: <span id="overlay-status-text">Ready</span>
                            </div>

                            <div class="overlay-controls">
                                <button class="overlay-btn" onclick="__overlayManager.startRecording()">
                                    Record
                                </button>
                                <button class="overlay-btn danger" onclick="__overlayManager.stopRecording()">
                                    Stop
                                </button>
                                <button class="overlay-btn success" onclick="__overlayManager.replay()">
                                    Replay
                                </button>
                            </div>

                            <div class="overlay-actions" id="overlay-actions-list">
                                <!-- Actions will be listed here -->
                            </div>

                            <div class="overlay-info">
                                <small>Actions: <span id="action-count">0</span></small>
                            </div>
                        </div>
                    `;

                    document.body.appendChild(overlay);
                }},

                toggleMinimize: function() {{
                    const overlay = document.getElementById('web-automation-overlay');
                    const body = overlay.querySelector('.overlay-body');

                    if (overlay.classList.contains('mini')) {{
                        overlay.classList.remove('mini');
                        body.style.display = 'block';
                    }} else {{
                        overlay.classList.add('mini');
                        body.style.display = 'none';
                    }}
                }},

                startRecording: function() {{
                    this.isRecording = true;
                    this.actions = [];
                    this.updateStatus('Recording...');

                    // 커스텀 이벤트 발생
                    window.dispatchEvent(new CustomEvent('overlay_action', {{
                        detail: {{ type: 'start_recording' }}
                    }}));
                }},

                stopRecording: function() {{
                    this.isRecording = false;
                    this.updateStatus('Stopped');

                    window.dispatchEvent(new CustomEvent('overlay_action', {{
                        detail: {{ type: 'stop_recording' }}
                    }}));
                }},

                replay: function() {{
                    this.updateStatus('Replaying...');

                    window.dispatchEvent(new CustomEvent('overlay_action', {{
                        detail: {{ 
                            type: 'replay',
                            actions: this.actions
                        }}
                    }}));
                }},

                addAction: function(action) {{
                    this.actions.push(action);
                    this.updateActionsList();
                }},

                updateStatus: function(text) {{
                    const statusEl = document.getElementById('overlay-status-text');
                    if (statusEl) statusEl.textContent = text;
                }},

                updateActionsList: function() {{
                    const listEl = document.getElementById('overlay-actions-list');
                    const countEl = document.getElementById('action-count');

                    if (listEl) {{
                        listEl.innerHTML = this.actions.slice(-5).map(a => 
                            `<div class="overlay-action-item">
                                ${{a.type}}: ${{a.selector || a.url || ''}}
                            </div>`
                        ).join('');
                    }}

                    if (countEl) {{
                        countEl.textContent = this.actions.length;
                    }}
                }},

                attachEventHandlers: function() {{
                    // 드래그 기능
                    const overlay = document.getElementById('web-automation-overlay');
                    let isDragging = false;
                    let currentX;
                    let currentY;
                    let initialX;
                    let initialY;
                    let xOffset = 0;
                    let yOffset = 0;

                    const header = overlay.querySelector('.overlay-header');

                    header.addEventListener('mousedown', (e) => {{
                        initialX = e.clientX - xOffset;
                        initialY = e.clientY - yOffset;
                        isDragging = true;
                    }});

                    document.addEventListener('mousemove', (e) => {{
                        if (isDragging) {{
                            e.preventDefault();
                            currentX = e.clientX - initialX;
                            currentY = e.clientY - initialY;
                            xOffset = currentX;
                            yOffset = currentY;

                            overlay.style.transform = 
                                `translate(${{currentX}}px, ${{currentY}}px)`;
                        }}
                    }});

                    document.addEventListener('mouseup', () => {{
                        isDragging = false;
                    }});
                }},

                cleanup: function() {{
                    // 정리 작업
                    this.actions = [];
                    this.isRecording = false;
                }}
            }};

            // 초기화
            window.__overlayManager.init();

            console.log('Overlay Manager initialized');
        }})();
        """

    def _setup_event_handlers(self, page):
        """이벤트 핸들러 설정"""
        # Python 함수를 JavaScript에서 호출 가능하게 노출
        page.expose_function('__handle_overlay_action', self._handle_overlay_action)

        # 이벤트 리스너 등록
        page.evaluate("""
            window.addEventListener('overlay_action', (e) => {
                window.__handle_overlay_action(e.detail);
            });
        """)

    def _handle_overlay_action(self, action: Dict[str, Any]):
        """오버레이 액션 처리"""
        action_type = action.get('type')

        self.actions.append({
            'type': action_type,
            'timestamp': datetime.now().isoformat(),
            'data': action
        })

        logger.debug(f"Overlay action: {action_type}")

    @safe_execute
    def get_actions(self) -> HelperResult:
        """
        오버레이 액션 조회

        Returns:
            HelperResult with list of actions
        """
        return HelperResult.success({
            "actions": self.actions,
            "count": len(self.actions),
            "is_active": self.is_active
        })

    @safe_execute
    def update_status(self, status: str) -> HelperResult:
        """
        오버레이 상태 업데이트

        Args:
            status: 상태 텍스트

        Returns:
            HelperResult
        """
        if not self.is_active:
            return HelperResult.failure("Overlay not active")

        page = self._get_page()

        try:
            page.evaluate(f"""
                if (window.__overlayManager) {{
                    window.__overlayManager.updateStatus('{status}');
                }}
            """)

            return HelperResult.success({"status": status})

        except Exception as e:
            logger.error(f"Failed to update status: {e}")
            return HelperResult.failure(str(e))

    @safe_execute
    def add_action_to_display(
        self,
        action_type: str,
        details: str
    ) -> HelperResult:
        """
        오버레이에 액션 표시 추가

        Args:
            action_type: 액션 타입
            details: 액션 상세

        Returns:
            HelperResult
        """
        if not self.is_active:
            return HelperResult.failure("Overlay not active")

        page = self._get_page()

        try:
            page.evaluate(f"""
                if (window.__overlayManager) {{
                    window.__overlayManager.addAction({{
                        type: '{action_type}',
                        selector: '{details}',
                        timestamp: new Date().toISOString()
                    }});
                }}
            """)

            return HelperResult.success()

        except Exception as e:
            logger.error(f"Failed to add action: {e}")
            return HelperResult.failure(str(e))


# 전역 오버레이 관리
_overlays: Dict[str, OverlayManager] = {}


def get_overlay_manager(session_id: str) -> OverlayManager:
    """세션별 오버레이 관리자 반환"""
    if session_id not in _overlays:
        _overlays[session_id] = OverlayManager(session_id)
    return _overlays[session_id]


def remove_overlay_manager(session_id: str):
    """오버레이 관리자 제거"""
    if session_id in _overlays:
        overlay = _overlays[session_id]
        if overlay.is_active:
            overlay.deactivate()
        del _overlays[session_id]
