# python/workflow/ai_automation/run_automation.py
"""
워크플로우 AI 자동화 실행 스크립트
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from workflow.ai_automation.workflow_ai_listener import WorkflowAIListener
from workflow.ai_automation.log_analyzer import LogAnalyzer

def main():
    project_name = os.environ.get("PROJECT_NAME", "ai-coding-brain-mcp")

    print(f"🤖 AI 워크플로우 자동화 시작: {project_name}")
    print("메시지 모니터링 중...")

    listener = WorkflowAIListener(project_name)
    listener.listen()

if __name__ == "__main__":
    main()
