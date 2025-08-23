"""
웹 자동화 세션 관리 모듈
브라우저 세션의 생명주기 관리 및 영속성 제공
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Any
from threading import Lock

from .types import SessionInfo, SessionStatus, BrowserType, HelperResult
from .exceptions import SessionNotFoundError, SessionAlreadyExistsError
from .utils import safe_execute, create_session_id

logger = logging.getLogger(__name__)


class SessionManager:
    """
    브라우저 세션 관리자
    세션 정보를 파일 시스템에 영속화하고 관리
    """

    _instance: Optional["SessionManager"] = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        """싱글톤 패턴 구현"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, base_dir: Optional[Path] = None):
        """
        세션 관리자 초기화

        Args:
            base_dir: 세션 정보를 저장할 디렉토리
        """
        # 이미 초기화된 경우 스킵
        if hasattr(self, '_initialized'):
            return

        self.base_dir = base_dir or Path.home() / ".web_sessions"
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.registry_file = self.base_dir / "registry.json"
        self.sessions: Dict[str, SessionInfo] = {}

        # 기존 세션 로드
        self._load_sessions()
        self._initialized = True

        logger.info(f"SessionManager initialized at {self.base_dir}")

    def _load_sessions(self) -> None:
        """저장된 세션 정보 로드"""
        if not self.registry_file.exists():
            self._save_registry()
            return

        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # SessionInfo 객체로 변환
            for session_id, session_data in data.items():
                self.sessions[session_id] = self._dict_to_session_info(session_data)

            logger.info(f"Loaded {len(self.sessions)} sessions")
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            self.sessions = {}

    def _save_registry(self) -> None:
        """세션 레지스트리 저장"""
        try:
            # SessionInfo를 딕셔너리로 변환
            data = {
                sid: session.to_dict() 
                for sid, session in self.sessions.items()
            }

            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(data)} sessions to registry")
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")

    def _dict_to_session_info(self, data: Dict[str, Any]) -> SessionInfo:
        """딕셔너리를 SessionInfo 객체로 변환"""
        return SessionInfo(
            session_id=data['session_id'],
            browser_type=BrowserType(data['browser_type']),
            status=SessionStatus(data['status']),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            url=data.get('url'),
            title=data.get('title'),
            metadata=data.get('metadata', {})
        )

    @safe_execute
    def create_session(
        self, 
        session_id: Optional[str] = None,
        browser_type: BrowserType = BrowserType.CHROMIUM
    ) -> HelperResult:
        """
        새 세션 생성

        Args:
            session_id: 세션 ID (None이면 자동 생성)
            browser_type: 브라우저 타입

        Returns:
            HelperResult with SessionInfo
        """
        # 세션 ID 생성 또는 검증
        if session_id is None:
            session_id = create_session_id()
        elif session_id in self.sessions:
            raise SessionAlreadyExistsError(session_id)

        # 새 세션 정보 생성
        now = datetime.now()
        session_info = SessionInfo(
            session_id=session_id,
            browser_type=browser_type,
            status=SessionStatus.IDLE,
            created_at=now,
            updated_at=now
        )

        # 세션 등록
        self.sessions[session_id] = session_info
        self._save_registry()

        logger.info(f"Created session: {session_id}")
        return HelperResult.success(session_info)

    @safe_execute
    def get_session(self, session_id: str) -> HelperResult:
        """
        세션 정보 조회

        Args:
            session_id: 세션 ID

        Returns:
            HelperResult with SessionInfo
        """
        if session_id not in self.sessions:
            raise SessionNotFoundError(session_id)

        return HelperResult.success(self.sessions[session_id])

    @safe_execute
    def update_session(
        self,
        session_id: str,
        status: Optional[SessionStatus] = None,
        url: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> HelperResult:
        """
        세션 정보 업데이트

        Args:
            session_id: 세션 ID
            status: 새 상태
            url: 현재 URL
            title: 페이지 제목
            metadata: 추가 메타데이터

        Returns:
            HelperResult with updated SessionInfo
        """
        if session_id not in self.sessions:
            raise SessionNotFoundError(session_id)

        session = self.sessions[session_id]

        # 업데이트
        if status is not None:
            session.status = status
        if url is not None:
            session.url = url
        if title is not None:
            session.title = title
        if metadata is not None:
            session.metadata.update(metadata)

        session.updated_at = datetime.now()

        # 저장
        self._save_registry()

        logger.debug(f"Updated session {session_id}: status={status}")
        return HelperResult.success(session)

    @safe_execute
    def delete_session(self, session_id: str) -> HelperResult:
        """
        세션 삭제

        Args:
            session_id: 세션 ID

        Returns:
            HelperResult
        """
        if session_id not in self.sessions:
            raise SessionNotFoundError(session_id)

        # 세션 정보 제거
        del self.sessions[session_id]
        self._save_registry()

        # 세션 파일 삭제 (있는 경우)
        session_file = self.base_dir / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()

        logger.info(f"Deleted session: {session_id}")
        return HelperResult.success()

    @safe_execute
    def list_sessions(
        self, 
        status: Optional[SessionStatus] = None
    ) -> HelperResult:
        """
        세션 목록 조회

        Args:
            status: 필터링할 상태 (None이면 전체)

        Returns:
            HelperResult with list of SessionInfo
        """
        sessions = list(self.sessions.values())

        # 상태 필터링
        if status is not None:
            sessions = [s for s in sessions if s.status == status]

        # 최신순 정렬
        sessions.sort(key=lambda s: s.updated_at, reverse=True)

        return HelperResult.success(sessions)

    @safe_execute
    def get_active_session(self) -> HelperResult:
        """
        현재 활성 세션 조회

        Returns:
            HelperResult with SessionInfo or None
        """
        active_sessions = [
            s for s in self.sessions.values()
            if s.status == SessionStatus.ACTIVE
        ]

        if not active_sessions:
            return HelperResult.success(None)

        # 가장 최근 업데이트된 세션 반환
        active_sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return HelperResult.success(active_sessions[0])

    @safe_execute
    def cleanup_stale_sessions(self, hours: int = 24) -> HelperResult:
        """
        오래된 세션 정리

        Args:
            hours: 정리할 세션 나이 (시간)

        Returns:
            HelperResult with number of cleaned sessions
        """
        from datetime import timedelta

        now = datetime.now()
        threshold = now - timedelta(hours=hours)

        stale_sessions = [
            sid for sid, session in self.sessions.items()
            if session.updated_at < threshold and 
               session.status in [SessionStatus.IDLE, SessionStatus.ERROR, SessionStatus.CLOSED]
        ]

        for sid in stale_sessions:
            self.delete_session(sid)

        logger.info(f"Cleaned {len(stale_sessions)} stale sessions")
        return HelperResult.success(len(stale_sessions))

    def save_session_data(self, session_id: str, data: Any) -> None:
        """
        세션별 데이터 저장

        Args:
            session_id: 세션 ID
            data: 저장할 데이터
        """
        session_file = self.base_dir / f"{session_id}.json"

        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            logger.debug(f"Saved data for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to save session data: {e}")

    def load_session_data(self, session_id: str) -> Optional[Any]:
        """
        세션별 데이터 로드

        Args:
            session_id: 세션 ID

        Returns:
            저장된 데이터 또는 None
        """
        session_file = self.base_dir / f"{session_id}.json"

        if not session_file.exists():
            return None

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load session data: {e}")
            return None


# 전역 세션 관리자 인스턴스
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """전역 세션 관리자 인스턴스 반환"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
