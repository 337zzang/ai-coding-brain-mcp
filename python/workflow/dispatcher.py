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
from workflow_helper import generate_docs_for_project

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
        # /a 명령 처리 추가
        if command.strip() == "/a":
            project_root = Path.cwd()
            generate_docs_for_project(project_root)
            return f"✅ {project_root}에 file_directory.md, README.md 생성 완료"
        
        # 기존 워크플로우 명령 처리
        manager = get_manager()
        result = manager.process_command(command)

        # 성공 시 문자열 반환
        if result.get('success'):
            return result.get('message', '완료')
        else:
            # 실패 시 Error: 접두사 추가
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
