class SessionRegistry:
    """세션 정보 영속화 관리"""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.sessions_file = os.path.join(base_dir, "sessions.json")
        self.sessions: Dict[str, SessionInfo] = {}
        self._load_sessions()

    def _load_sessions(self):
        """파일에서 세션 정보 로드"""
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, 'r') as f:
                    data = json.load(f)
                    for sid, info in data.items():
                        self.sessions[sid] = SessionInfo(**info)
            except Exception as e:
                logging.error(f"Failed to load sessions: {e}")
                self.sessions = {}

    def _save_sessions(self):
        """세션 정보를 파일에 저장"""
        data = {
            sid: asdict(info) 
            for sid, info in self.sessions.items()
        }
        with open(self.sessions_file, 'w') as f:
            json.dump(data, f, indent=2)

    def save_session(self, session_info: SessionInfo):
        """세션 저장"""
        self.sessions[session_info.session_id] = session_info
        self._save_sessions()

    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """세션 조회"""
        return self.sessions.get(session_id)

    def update_status(self, session_id: str, status: str):
        """상태 업데이트"""
        if session_id in self.sessions:
            self.sessions[session_id].status = status
            self._save_sessions()

    def update_activity(self, session_id: str):
        """활동 시간 업데이트"""
        if session_id in self.sessions:
            self.sessions[session_id].last_activity = datetime.now().isoformat()
            self._save_sessions()

    def list_sessions(self) -> List[SessionInfo]:
        """전체 세션 목록"""
        return list(self.sessions.values())

    def find_orphans(self) -> List[SessionInfo]:
        """고아 세션 찾기"""
        orphans = []
        for session in self.sessions.values():
            if session.status == "active":
                # 매니저 재시작 후 모든 활성 세션은 잠재적 고아
                orphans.append(session)
        return orphans
