class ActivityLogger:
    """세션별 활동 로깅"""

    def __init__(self, session_id: str, base_dir: str):
        self.session_id = session_id
        self.activity_file = os.path.join(
            base_dir, "activities", f"{session_id}.jsonl"
        )

    def log_action(self, action: str, details: dict):
        """활동 기록"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "action": action,
            "details": details
        }

        # JSONL 형식으로 추가
        with open(self.activity_file, 'a') as f:
            f.write(json.dumps(record) + '\n')

    def get_activities(self, limit: int = 100) -> List[dict]:
        """최근 활동 조회"""
        if not os.path.exists(self.activity_file):
            return []

        activities = []
        with open(self.activity_file, 'r') as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                activities.append(json.loads(line))

        return activities
