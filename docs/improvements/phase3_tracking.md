
## 📊 Phase 3: ID 기반 추적 시스템 구축

### 3.1 활동 로그 레코더

```python
import json
from datetime import datetime
from typing import Dict, Any

class ActivityRecorder:
    """세션별 활동 기록기"""

    def __init__(self, session_id: str, log_dir: str = "browser_sessions/activities"):
        self.session_id = session_id
        self.log_file = os.path.join(log_dir, f"{session_id}_activities.jsonl")
        os.makedirs(log_dir, exist_ok=True)

    def record(self, action: str, details: Dict[str, Any]):
        """활동 기록"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "action": action,
            "details": details
        }

        # JSONL 형식으로 저장 (각 줄이 하나의 JSON)
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(record) + '\n')

    def get_activities(self, limit: int = 100) -> list:
        """최근 활동 조회"""
        activities = []
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                lines = f.readlines()[-limit:]  # 최근 N개
                for line in lines:
                    activities.append(json.loads(line))
        return activities
```

### 3.2 실시간 모니터링 대시보드

```python
class SessionMonitor:
    """세션 모니터링 도구"""

    def __init__(self):
        self.manager = ImprovedBrowserManager()

    def get_active_sessions(self) -> list:
        """활성 세션 목록"""
        active = []
        for session_id, info in self.manager.sessions.items():
            if self._is_session_active(info):
                active.append({
                    "session_id": session_id,
                    "pid": info["pid"],
                    "created": info["created_at"],
                    "last_activity": info["last_activity"]
                })
        return active

    def _is_session_active(self, session_info: dict) -> bool:
        """세션 활성 상태 확인"""
        try:
            # PID 확인
            pid = session_info["pid"]
            os.kill(pid, 0)  # 프로세스 존재 확인
            return True
        except OSError:
            return False

    def get_session_stats(self, session_id: str) -> dict:
        """세션 통계"""
        recorder = ActivityRecorder(session_id)
        activities = recorder.get_activities()

        stats = {
            "total_actions": len(activities),
            "action_types": {},
            "recent_actions": activities[-10:]  # 최근 10개
        }

        # 액션 타입별 집계
        for activity in activities:
            action = activity["action"]
            stats["action_types"][action] = stats["action_types"].get(action, 0) + 1

        return stats
```

### 3.3 통합된 헬퍼 함수

```python
def web_action(session_id: str, action: str, func, *args, **kwargs):
    """모든 웹 액션을 감싸는 래퍼"""
    # 로거
    logger = logging.getLogger(f"web_auto.{session_id}")

    # 활동 기록기
    recorder = ActivityRecorder(session_id)

    try:
        # 액션 실행
        result = func(*args, **kwargs)

        # 성공 로깅
        logger.info(f"{action} succeeded")
        recorder.record(action, {
            "status": "success",
            "args": str(args),
            "kwargs": str(kwargs)
        })

        return result

    except Exception as e:
        # 실패 로깅
        logger.error(f"{action} failed: {e}")
        recorder.record(action, {
            "status": "failed",
            "error": str(e),
            "args": str(args),
            "kwargs": str(kwargs)
        })
        raise

# 사용 예시
def web_goto_tracked(session_id: str, url: str):
    def _goto():
        browser = web_connect(session_id, create_new=False)
        page = browser.pages[0]
        page.goto(url)
        return page

    return web_action(session_id, f"goto:{url}", _goto)

def web_click_tracked(session_id: str, selector: str):
    def _click():
        browser = web_connect(session_id, create_new=False)
        page = browser.pages[0]
        page.click(selector)

    return web_action(session_id, f"click:{selector}", _click)
```

### 3.4 로그 분석 도구

```python
def analyze_session_logs(session_id: str):
    """세션 로그 분석"""
    monitor = SessionMonitor()
    stats = monitor.get_session_stats(session_id)

    print(f"📊 Session {session_id} 분석 보고서")
    print("=" * 50)
    print(f"총 액션 수: {stats['total_actions']}")
    print("\n액션 타입별 통계:")
    for action, count in stats['action_types'].items():
        print(f"  • {action}: {count}회")

    print("\n최근 활동:")
    for activity in stats['recent_actions']:
        print(f"  [{activity['timestamp']}] {activity['action']}")
```
