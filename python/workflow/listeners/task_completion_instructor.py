"""
Task Completion Instructor for AI Actions
태스크 완료 시 AI에게 구체적인 작업 지시를 내리는 리스너
"""
from python.workflow.listeners.base import BaseEventListener
from python.workflow.listeners.ai_instruction_base import AIInstruction, ActionType, Priority
from python.workflow.events import EventType, WorkflowEvent
from typing import List, Dict, Any
import os

class TaskCompletionInstructor(BaseEventListener):
    """태스크 완료 시 AI에게 작업 지시"""

    def __init__(self):
        super().__init__()
        self.instruction_path = "logs/ai_instructions.json"

    def get_subscribed_events(self) -> List[EventType]:
        return [EventType.TASK_COMPLETED]

    def handle_event(self, event: WorkflowEvent) -> bool:
        """태스크 완료 이벤트를 AI 지시로 변환"""
        try:
            # AI 지시서 생성
            instruction = AIInstruction(
                event_type="task_completed",
                context={
                    "task_id": event.task_id,
                    "task_title": event.details.get('title', 'Unknown Task'),
                    "plan_id": event.plan_id,
                    "completion_note": event.details.get('note', ''),
                    "user": event.user,
                    "timestamp": event.timestamp.isoformat()
                }
            )

            # 1. Git 작업 지시
            if self._should_commit(event):
                instruction.add_action(
                    ActionType.GIT_COMMIT,
                    params={
                        "message": f"feat: {event.details.get('title')} 완료\n\n{event.details.get('note', '')}",
                        "task_id": event.task_id
                    }
                )

                instruction.add_action(
                    ActionType.GIT_PUSH,
                    params={
                        "branch": "current",
                        "force": False
                    },
                    depends_on=["ACT_1"]
                )

            # 2. 사용자 보고 지시
            next_task = event.details.get('next_task', {})
            report_message = self._create_report_message(event, next_task)

            instruction.add_action(
                ActionType.REPORT_USER,
                params={
                    "message": report_message,
                    "format": "markdown",
                    "channel": "console"  # 또는 "slack", "email" 등
                }
            )

            # 3. 문서 업데이트 지시
            if self._should_update_docs(event):
                instruction.add_action(
                    ActionType.UPDATE_DOCS,
                    params={
                        "task_id": event.task_id,
                        "task_title": event.details.get('title'),
                        "completion_note": event.details.get('note', ''),
                        "file": f"docs/tasks/{event.task_id}.md"
                    }
                )

            # 4. 다음 태스크 진행 지시
            if next_task:
                instruction.add_action(
                    ActionType.WORKFLOW_COMMAND,
                    params={
                        "command": f"/focus {next_task.get('id')}",
                        "reason": "이전 태스크 완료, 다음 태스크로 진행"
                    }
                )

            # 5. 테스트 실행 지시 (필요시)
            if "test" in event.details.get('title', '').lower():
                instruction.add_action(
                    ActionType.RUN_TEST,
                    params={
                        "test_type": "unit",
                        "module": event.details.get('module', 'all')
                    }
                )

            # 우선순위 설정
            if "critical" in event.details.get('note', '').lower():
                instruction.set_priority(Priority.HIGH)

            # 지시서 저장
            instruction.save()

            print(f"📤 TaskCompletionInstructor: {len(instruction.actions)}개 작업 지시 생성")
            print(f"   - Task: {event.details.get('title')}")
            print(f"   - Actions: {[a['type'] for a in instruction.actions]}")

            return True

        except Exception as e:
            print(f"❌ TaskCompletionInstructor 오류: {e}")
            return False

    def _should_commit(self, event: WorkflowEvent) -> bool:
        """Git 커밋이 필요한지 판단"""
        # 코드 변경이 있거나, 중요한 태스크인 경우
        keywords = ['구현', '수정', '추가', '개선', '버그', 'fix', 'feat', 'refactor']
        title = event.details.get('title', '').lower()
        return any(keyword in title for keyword in keywords)

    def _should_update_docs(self, event: WorkflowEvent) -> bool:
        """문서 업데이트가 필요한지 판단"""
        keywords = ['API', '기능', '설계', '인터페이스', 'docs']
        title = event.details.get('title', '').lower()
        return any(keyword in title for keyword in keywords)

    def _create_report_message(self, event: WorkflowEvent, next_task: Dict) -> str:
        """사용자 보고 메시지 생성"""
        message = f"## ✅ 태스크 완료\n\n"
        message += f"**태스크**: {event.details.get('title')}\n"
        message += f"**완료 시간**: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"

        if event.details.get('note'):
            message += f"**완료 내용**: {event.details.get('note')}\n"

        if next_task:
            message += f"\n**다음 태스크**: {next_task.get('title')}\n"
        else:
            message += f"\n**상태**: 모든 태스크 완료 🎉\n"

        return message
