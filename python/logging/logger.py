"""
워크플로우 시스템을 위한 로깅 모듈
"""
import json
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from collections import deque
import threading

class LogLevel:
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory:
    WORKFLOW = "workflow"
    SYSTEM = "system"
    ERROR = "error"
    GIT = "git"
    FILE = "file"
    COMMAND = "command"

class WorkflowLogger:
    """워크플로우 시스템 전용 로거"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.buffer = deque(maxlen=1000)
        self.lock = threading.Lock()

    def log(self, level: str, category: str, message: str, 
            details: Optional[Dict[str, Any]] = None, user: str = "system") -> Dict[str, Any]:
        """로그 항목 기록"""
        timestamp = datetime.datetime.now()

        log_entry = {
            "id": f"{timestamp.strftime('%Y%m%d%H%M%S')}-{id(timestamp) % 10000:04d}",
            "timestamp": timestamp.isoformat(),
            "level": level,
            "category": category,
            "message": message,
            "details": details or {},
            "user": user
        }

        with self.lock:
            self.buffer.append(log_entry)
            self._write_to_file(log_entry, timestamp)

            if level in ["ERROR", "CRITICAL"]:
                self._write_to_error_file(log_entry, timestamp)

        return log_entry

    def _write_to_file(self, entry: Dict[str, Any], timestamp: datetime.datetime):
        """로그 파일에 기록"""
        category = entry["category"]
        date_str = timestamp.strftime("%Y%m%d")

        category_dir = self.log_dir / category
        category_dir.mkdir(exist_ok=True)

        log_file = category_dir / f"{category}_{date_str}.jsonl"

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def _write_to_error_file(self, entry: Dict[str, Any], timestamp: datetime.datetime):
        """에러 전용 파일에 기록"""
        error_dir = self.log_dir / "errors"
        error_dir.mkdir(exist_ok=True)

        date_str = timestamp.strftime("%Y%m%d")
        error_file = error_dir / f"errors_{date_str}.jsonl"

        with open(error_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    def get_recent_logs(self, count: int = 100, level: Optional[str] = None,
                       category: Optional[str] = None) -> List[Dict[str, Any]]:
        """최근 로그 조회"""
        with self.lock:
            logs = list(self.buffer)

        if level:
            logs = [log for log in logs if log["level"] == level]
        if category:
            logs = [log for log in logs if log["category"] == category]

        return logs[-count:][::-1]

    # 편의 메서드들
    def debug(self, message: str, category: str = "system", **kwargs):
        return self.log("DEBUG", category, message, kwargs)

    def info(self, message: str, category: str = "system", **kwargs):
        return self.log("INFO", category, message, kwargs)

    def warning(self, message: str, category: str = "system", **kwargs):
        return self.log("WARNING", category, message, kwargs)

    def error(self, message: str, category: str = "error", **kwargs):
        return self.log("ERROR", category, message, kwargs)

# 전역 로거 인스턴스
_logger = None

def get_logger() -> WorkflowLogger:
    """싱글톤 로거 인스턴스 반환"""
    global _logger
    if _logger is None:
        _logger = WorkflowLogger()
    return _logger
