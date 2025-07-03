"""claude_code_ai_brain 대체 구현"""

from core.context_manager import get_context_manager


def cmd_flow(project_name: str):
    """프로젝트 전환 명령 (flow_project로 대체됨)"""
    print(f"⚠️ cmd_flow는 더 이상 사용되지 않습니다. flow_project('{project_name}')를 사용하세요.")
    # flow_project MCP 도구를 직접 호출할 수 없으므로 경고만 표시
    return None


def track_file_access(filepath: str):
    """파일 접근 추적"""
    try:
        cm = get_context_manager()
        if cm:
            return cm.track_file_access(filepath)
    except Exception as e:
        # 조용히 실패 (추적은 선택적 기능)
        pass
    return None


def track_function_edit(file: str, function: str, changes: str = ""):
    """함수 수정 추적"""
    try:
        cm = get_context_manager()
        if cm:
            return cm.track_function_edit(file, function, changes)
    except Exception as e:
        # 조용히 실패 (추적은 선택적 기능)
        pass
    return None


def get_work_tracking_summary():
    """작업 추적 요약 (간단한 구현)"""
    try:
        cm = get_context_manager()
        if cm and cm.context:
            summary = {
                'accessed_files': cm.context.get('accessed_files', []),
                'function_edits': cm.context.get('function_edits', []),
                'current_task': cm.context.get('current_task', 'Unknown')
            }
            return summary
    except:
        pass
    
    return {
        'accessed_files': [],
        'function_edits': [],
        'current_task': 'No active task'
    }
