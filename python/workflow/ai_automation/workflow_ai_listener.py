# python/workflow/ai_automation/workflow_ai_listener.py
"""
워크플로우 메시지를 감지하고 AI 액션을 트리거하는 리스너
"""
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class WorkflowAIListener:
    """워크플로우 메시지를 감지하고 AI에게 작업을 지시"""

    def __init__(self, project_name: str):
        self.project = project_name
        self.context_path = Path(f"memory/projects/{project_name}/ai_context.json")
        self.docs_path = Path("docs/workflow_reports")
        self.docs_path.mkdir(exist_ok=True)

    def listen(self):
        """stdout 메시지 모니터링"""
        for line in sys.stdin:
            if line.startswith("st:"):
                self.process_message(line.strip())

    def process_message(self, message: str):
        """메시지 파싱 및 처리"""
        try:
            parts = message.split(":", 3)
            if len(parts) >= 4:
                _, msg_type, entity_id, data = parts
                data = json.loads(data)

                # 메시지 타입별 처리
                if msg_type == "state_changed":
                    self.handle_state_change(entity_id, data)
                elif msg_type == "error_occurred":
                    self.handle_error(entity_id, data)
                elif msg_type == "task_summary":
                    self.handle_task_summary(entity_id, data)
                elif msg_type == "progress_update":
                    self.handle_progress(entity_id, data)

        except Exception as e:
            print(f"[AI-Listener] Error: {e}")

    def handle_state_change(self, entity_id: str, data: Dict):
        """상태 변경 처리"""
        from_state = data.get("from")
        to_state = data.get("to")

        if "task" in entity_id:
            if to_state == "completed":
                self.trigger_task_report(entity_id, data)
            elif to_state == "in_progress":
                self.trigger_next_design(entity_id, data)
            elif to_state == "error":
                self.trigger_error_fix(entity_id, data)

        elif "plan" in entity_id and to_state == "completed":
            self.trigger_phase_report(entity_id, data)

    def trigger_task_report(self, task_id: str, data: Dict):
        """태스크 완료 보고서 트리거"""
        print(f"""
🎯 AI Action Required: Task Completion Report
Task ID: {task_id}
Action: Generate detailed task completion report
Include:
- 작업 내용 요약
- 변경된 파일 목록
- 테스트 결과
- 성능 지표
- 다음 단계 제안
""")

    def trigger_next_design(self, task_id: str, data: Dict):
        """다음 작업 설계 트리거"""
        print(f"""
🎨 AI Action Required: Next Task Design
Task ID: {task_id}
Action: Design next implementation step
Include:
- 설계 목적 및 배경
- 이해한 요구사항
- 구현 방향성
- 영향받는 모듈 분석
- 위험 요소 및 대응책
- 예상 작업 시간
""")

    def trigger_error_fix(self, entity_id: str, data: Dict):
        """에러 수정 트리거"""
        print(f"""
🔧 AI Action Required: Error Analysis & Fix
Entity ID: {entity_id}
Action: Analyze error and provide fix
Steps:
1. 로그 파일 분석 (logs/)
2. 에러 발생 코드 확인
3. 근본 원인 파악
4. 수정 코드 제안
5. 테스트 케이스 작성
""")

    def trigger_phase_report(self, plan_id: str, data: Dict):
        """페이즈 완료 보고서 트리거"""
        date = datetime.now().strftime("%Y%m%d")
        filename = f"{self.project}_{plan_id}_phase_complete_{date}.md"

        print(f"""
📊 AI Action Required: Phase Completion Report
Plan ID: {plan_id}
Action: Generate comprehensive phase report
Filename: {filename}
Include:
- 페이즈 목표 달성도
- 주요 성과물
- 문제점 및 해결 과정
- 학습된 교훈
- 다음 페이즈 권장사항
""")
