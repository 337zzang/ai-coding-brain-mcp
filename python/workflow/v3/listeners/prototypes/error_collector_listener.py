
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from python.workflow.v3.listeners.base import BaseEventListener
from python.workflow.v3.models import EventType, WorkflowEvent

class ErrorCollectorListener(BaseEventListener):
    """오류 수집 및 보고 리스너"""

    def __init__(self, enabled: bool = True):
        super().__init__(enabled)
        self.error_log_path = Path("memory/error_log.json")
        self.errors: Dict[str, List[Dict[str, Any]]] = self._load_errors()

    def _load_errors(self) -> Dict[str, List[Dict[str, Any]]]:
        """기존 오류 로그 로드"""
        if self.error_log_path.exists():
            try:
                return json.loads(self.error_log_path.read_text())
            except:
                return {}
        return {}

    def handle_event(self, event: WorkflowEvent) -> None:
        """이벤트 처리"""
        if event.type == EventType.TASK_FAILED:
            self._collect_error(event)

    def _collect_error(self, event: WorkflowEvent) -> None:
        """오류 수집"""
        task_id = event.task_id
        plan_id = event.plan_id

        error_entry = {
            "timestamp": event.timestamp,
            "task_id": task_id,
            "plan_id": plan_id,
            "error": event.details.get("error", "Unknown error"),
            "context": event.details.get("context", {}),
            "stack_trace": event.details.get("stack_trace", "")
        }

        # 플랜별로 오류 그룹화
        if plan_id not in self.errors:
            self.errors[plan_id] = []
        self.errors[plan_id].append(error_entry)

        # 저장
        self._save_errors()

        # 사용자에게 즉시 알림
        self._notify_user(error_entry)

    def _save_errors(self) -> None:
        """오류 로그 저장"""
        self.error_log_path.write_text(
            json.dumps(self.errors, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

    def _notify_user(self, error: Dict[str, Any]) -> None:
        """사용자에게 오류 알림"""
        print(f"""
⚠️ 태스크 오류 발생!
- Task ID: {error['task_id'][:8]}...
- 오류: {error['error']}
- 시간: {error['timestamp']}
""")

    def get_plan_errors(self, plan_id: str) -> List[Dict[str, Any]]:
        """특정 플랜의 모든 오류 반환"""
        return self.errors.get(plan_id, [])

    def generate_error_report(self, plan_id: str) -> str:
        """플랜 완료 시 오류 보고서 생성"""
        errors = self.get_plan_errors(plan_id)
        if not errors:
            return "오류 없음 ✅"

        report = f"## 오류 보고서\n\n총 {len(errors)}개 오류 발생:\n\n"
        for i, error in enumerate(errors, 1):
            report += f"""
### {i}. {error['error']}
- 시간: {error['timestamp']}
- Task: {error['task_id'][:8]}...
"""
            if error.get('stack_trace'):
                report += f"\n```\n{error['stack_trace']}\n```\n"

        return report
