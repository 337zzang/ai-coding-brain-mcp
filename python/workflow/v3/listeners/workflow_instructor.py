"""
Workflow Instructor Integration System
워크플로우 전체를 관리하고 AI에게 종합적인 지시를 내리는 통합 시스템
"""
from python.workflow.v3.listeners.base import BaseEventListener
from python.workflow.v3.listeners.ai_instruction_base import AIInstruction, ActionType, Priority
from python.workflow.v3.events import EventType, WorkflowEvent
from typing import List, Dict, Any, Optional
import json
import os

class WorkflowInstructor(BaseEventListener):
    """워크플로우 이벤트를 AI 지시로 변환하는 통합 관리자"""

    def __init__(self):
        super().__init__()
        self.instruction_path = "logs/ai_instructions.json"
        self.workflow_state_path = "logs/workflow_ai_state.json"
        self._ensure_state_file()

    def get_subscribed_events(self) -> List[EventType]:
        """모든 주요 워크플로우 이벤트 구독"""
        return [
            EventType.PLAN_CREATED,
            EventType.PLAN_STARTED, 
            EventType.TASK_STARTED,
            EventType.TASK_COMPLETED,
            EventType.TASK_FAILED,
            EventType.PLAN_COMPLETED
        ]

    def _ensure_state_file(self):
        """워크플로우 상태 파일 초기화"""
        os.makedirs("logs", exist_ok=True)
        if not os.path.exists(self.workflow_state_path):
            initial_state = {
                "current_plan": None,
                "current_task": None,
                "pending_instructions": [],
                "completed_instructions": [],
                "workflow_context": {}
            }
            with open(self.workflow_state_path, 'w', encoding='utf-8') as f:
                json.dump(initial_state, f, indent=2)

    def handle_event(self, event: WorkflowEvent) -> bool:
        """워크플로우 이벤트별 AI 지시 생성"""
        try:
            # 이벤트 타입별 처리
            if event.type == EventType.PLAN_CREATED:
                return self._handle_plan_created(event)
            elif event.type == EventType.PLAN_STARTED:
                return self._handle_plan_started(event)
            elif event.type == EventType.TASK_STARTED:
                return self._handle_task_started(event)
            elif event.type == EventType.TASK_COMPLETED:
                return self._handle_task_completed(event)
            elif event.type == EventType.TASK_FAILED:
                return self._handle_task_failed(event)
            elif event.type == EventType.PLAN_COMPLETED:
                return self._handle_plan_completed(event)

            return True

        except Exception as e:
            print(f"❌ WorkflowInstructor 오류: {e}")
            return False

    def _handle_plan_created(self, event: WorkflowEvent) -> bool:
        """플랜 생성 시 AI 지시"""
        instruction = AIInstruction(
            event_type="plan_created",
            context={
                "plan_id": event.plan_id,
                "plan_name": event.details.get('name'),
                "description": event.details.get('description', ''),
                "task_count": event.details.get('task_count', 0)
            }
        )

        # 1. 플랜 시작 준비 지시
        instruction.add_action(
            ActionType.REPORT_USER,
            params={
                "message": f"📋 새로운 플랜 생성: **{event.details.get('name')}**\n\n준비 작업을 시작합니다...",
                "format": "markdown"
            }
        )

        # 2. 프로젝트 구조 분석 지시
        instruction.add_action(
            ActionType.ANALYZE_CODE,
            params={
                "action": "analyze_project_structure",
                "purpose": "플랜 실행을 위한 프로젝트 상태 파악"
            }
        )

        # 3. 의존성 확인 지시
        instruction.add_action(
            ActionType.WORKFLOW_COMMAND,
            params={
                "command": "helpers.read_file('requirements.txt')",
                "purpose": "필요 라이브러리 확인"
            }
        )

        instruction.save()
        self._update_state("current_plan", event.plan_id)
        return True

    def _handle_plan_started(self, event: WorkflowEvent) -> bool:
        """플랜 시작 시 AI 지시"""
        instruction = AIInstruction(
            event_type="plan_started",
            context={
                "plan_id": event.plan_id,
                "plan_name": event.details.get('name')
            }
        )

        # Git 브랜치 생성 지시 (필요시)
        if event.details.get('create_branch'):
            branch_name = f"feature/{event.details.get('name', 'new-feature').replace(' ', '-').lower()}"
            instruction.add_action(
                ActionType.GIT_COMMIT,
                params={
                    "message": f"chore: {event.details.get('name')} 플랜 시작",
                    "allow_empty": True
                }
            )

            instruction.add_action(
                ActionType.WORKFLOW_COMMAND,
                params={
                    "command": f"helpers.git_branch_smart('{branch_name}')",
                    "purpose": "플랜용 브랜치 생성"
                }
            )

        instruction.save()
        return True

    def _handle_task_started(self, event: WorkflowEvent) -> bool:
        """태스크 시작 시 AI 지시"""
        instruction = AIInstruction(
            event_type="task_started", 
            context={
                "task_id": event.task_id,
                "task_title": event.details.get('title'),
                "plan_id": event.plan_id
            }
        )

        # 1. 태스크 시작 알림
        instruction.add_action(
            ActionType.REPORT_USER,
            params={
                "message": f"🚀 태스크 시작: **{event.details.get('title')}**",
                "format": "markdown"
            }
        )

        # 2. 관련 파일 준비
        if "test" in event.details.get('title', '').lower():
            instruction.add_action(
                ActionType.CREATE_FILE,
                params={
                    "path": f"tests/test_{event.task_id}.py",
                    "content": "import pytest\n\n# TODO: Add tests",
                    "if_not_exists": True
                }
            )

        # 3. 태스크별 환경 설정
        instruction.add_action(
            ActionType.WORKFLOW_COMMAND,
            params={
                "command": f"# 태스크 {event.task_id} 작업 환경 준비",
                "setup": True
            }
        )

        instruction.save()
        self._update_state("current_task", event.task_id)
        return True

    def _handle_task_completed(self, event: WorkflowEvent) -> bool:
        """태스크 완료는 TaskCompletionInstructor가 처리하므로 여기서는 상태만 업데이트"""
        self._update_state("last_completed_task", {
            "task_id": event.task_id,
            "title": event.details.get('title'),
            "completed_at": event.timestamp.isoformat()
        })
        return True

    def _handle_task_failed(self, event: WorkflowEvent) -> bool:
        """태스크 실패는 ErrorInstructor가 처리하므로 여기서는 복구 전략만 추가"""
        # 전체 워크플로우 차원의 복구 전략
        instruction = AIInstruction(
            event_type="task_failed_workflow",
            context={
                "task_id": event.task_id,
                "error_type": event.details.get('error_type'),
                "plan_id": event.plan_id
            }
        )

        # 워크플로우 상태 저장 (복구용)
        instruction.add_action(
            ActionType.WORKFLOW_COMMAND,
            params={
                "command": "helpers.workflow('/status')",
                "save_state": True,
                "purpose": "오류 발생 시점의 워크플로우 상태 저장"
            }
        )

        instruction.set_priority(Priority.HIGH)
        instruction.save()
        return True

    def _handle_plan_completed(self, event: WorkflowEvent) -> bool:
        """플랜 완료 시 종합 보고 및 마무리 작업 지시"""
        instruction = AIInstruction(
            event_type="plan_completed",
            context={
                "plan_id": event.plan_id,
                "plan_name": event.details.get('name'),
                "total_tasks": event.details.get('total_tasks', 0),
                "completed_tasks": event.details.get('completed_tasks', 0)
            }
        )

        # 1. 최종 보고서 작성
        instruction.add_action(
            ActionType.UPDATE_DOCS,
            params={
                "file": f"docs/plans/{event.plan_id}_report.md",
                "template": "plan_completion_report",
                "data": event.details
            }
        )

        # 2. Git 커밋 및 푸시
        instruction.add_action(
            ActionType.GIT_COMMIT,
            params={
                "message": f"feat: {event.details.get('name')} 플랜 완료\n\n- 총 {event.details.get('completed_tasks')}개 태스크 완료",
                "detailed": True
            }
        )

        instruction.add_action(
            ActionType.GIT_PUSH,
            params={
                "branch": "current",
                "create_pr": True,
                "pr_title": f"Feature: {event.details.get('name')}"
            }
        )

        # 3. 사용자에게 최종 보고
        completion_rate = (event.details.get('completed_tasks', 0) / max(event.details.get('total_tasks', 1), 1)) * 100
        instruction.add_action(
            ActionType.REPORT_USER,
            params={
                "message": f"""## 🎉 플랜 완료!

**플랜명**: {event.details.get('name')}
**완료율**: {completion_rate:.1f}%
**완료 태스크**: {event.details.get('completed_tasks')}/{event.details.get('total_tasks')}

### 주요 성과:
{self._generate_achievements_summary(event)}

### 다음 단계:
1. PR 리뷰 요청
2. 테스트 실행
3. 배포 준비
""",
                "format": "markdown",
                "important": True
            }
        )

        # 4. 다음 플랜 제안
        instruction.add_action(
            ActionType.SEND_NOTIFICATION,
            params={
                "type": "plan_suggestion",
                "message": "다음 플랜을 제안해드릴까요?",
                "options": ["테스트 작성", "문서 업데이트", "성능 최적화"]
            }
        )

        instruction.save()
        self._update_state("current_plan", None)
        return True

    def _update_state(self, key: str, value: Any):
        """워크플로우 상태 업데이트"""
        try:
            with open(self.workflow_state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)

            state[key] = value
            state['last_updated'] = os.path.getmtime(self.workflow_state_path)

            with open(self.workflow_state_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"상태 업데이트 실패: {e}")

    def _generate_achievements_summary(self, event: WorkflowEvent) -> str:
        """플랜 성과 요약 생성"""
        # 실제로는 더 복잡한 로직으로 성과 분석
        achievements = []

        if event.details.get('completed_tasks', 0) > 0:
            achievements.append(f"- ✅ {event.details.get('completed_tasks')}개 태스크 성공적으로 완료")

        if event.details.get('files_created', 0) > 0:
            achievements.append(f"- 📄 {event.details.get('files_created')}개 파일 생성")

        if event.details.get('tests_passed', 0) > 0:
            achievements.append(f"- 🧪 {event.details.get('tests_passed')}개 테스트 통과")

        return "\n".join(achievements) if achievements else "- 플랜이 성공적으로 완료되었습니다"
