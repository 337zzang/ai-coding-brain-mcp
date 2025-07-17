"""
워크플로우 명령어 디스패처
AI helpers에서 워크플로우 명령을 실행하기 위한 인터페이스
"""

import os
import json
from pathlib import Path
from .improved_manager import ImprovedWorkflowManager

# workflow_helper import 추가
import sys
sys.path.append(str(Path(__file__).parent.parent))
from workflow_helper import generate_docs_for_project, flow_project

# 전역 매니저 인스턴스
_manager_instance = None

def get_manager():
    """워크플로우 매니저 싱글톤 인스턴스 반환"""
    global _manager_instance
    if _manager_instance is None:
        # 현재 프로젝트명 감지
        project_name = None
        
        # 1. workflow.json에서 읽기 시도
        workflow_file = os.path.join(os.getcwd(), "memory", "workflow.json")
        if os.path.exists(workflow_file):
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    project_name = data.get('project_name')
            except:
                pass
        
        # 2. 없으면 현재 디렉토리명 사용
        if not project_name:
            project_name = os.path.basename(os.getcwd())
        
        _manager_instance = ImprovedWorkflowManager(project_name)
    return _manager_instance

def execute_workflow_command(command: str):
    """워크플로우 명령 실행"""
    try:
        # /flow 명령 처리 (프로젝트 전환)
        if command.startswith("/flow"):
            parts = command.split(None, 1)
            if len(parts) > 1:
                project_name = parts[1]
                # flow_project 함수 import 필요
                from workflow_helper import flow_project
                result = flow_project(project_name)
                if result.get("success"):
                    return f"✅ 프로젝트 '{project_name}'로 전환 완료"
                else:
                    return f"Error: 프로젝트 전환 실패"
            else:
                return "Error: 프로젝트명을 지정해주세요. 예: /flow my-project"

        # generate_docs_for_project 명령 처리
        elif command == "/analyze" or command == "/a":
            print("\n📊 프로젝트 분석 시작...")
            generate_docs_for_project(Path.cwd())
            return "✅ 프로젝트 분석 완료"

        # 워크플로우 매니저로 명령 전달
        manager = get_manager()
        result = manager.process_command(command)

        # 결과 포맷팅
        if result.get("success"):
            return result.get("message", "완료")
        else:
            return f"Error: {result.get('message', '알 수 없는 오류')}"

    except Exception as e:
        return f"Error: {str(e)}"
# 추가 헬퍼 함수들
def get_workflow_status():
    """워크플로우 상태 조회"""
    manager = get_manager()
    return manager.get_status()

def reset_workflow():
    """워크플로우 초기화"""
    global _manager_instance
    _manager_instance = None
    return "워크플로우가 초기화되었습니다"
