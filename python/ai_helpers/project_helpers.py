"""
프로젝트 관리 헬퍼 함수들
MCP 도구를 대체하는 execute_code 기반 함수
"""
import os
import threading
import time

def project_switch(project_name, timeout=30):
    """프로젝트 전환 - MCP flow_project 대체"""
    import builtins
    helpers = builtins.__dict__.get('helpers')
    if helpers and hasattr(helpers, 'cmd_flow_with_context'):
        return helpers.cmd_flow_with_context(project_name)
    return {'success': False, 'error': 'helpers not available'}

def safe_flow_project(project_name, timeout=30):
    """타임아웃 보호된 프로젝트 전환"""
    result = {'success': False}
    exception = None

    def run():
        nonlocal result, exception
        try:
            result = project_switch(project_name)
        except Exception as e:
            exception = e

    thread = threading.Thread(target=run)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        return {'success': False, 'error': f'Timeout after {timeout}s'}

    return result

def project_create(project_name, init_git=True):
    """새 프로젝트 생성 - MCP start_project 대체"""
    import builtins
    helpers = builtins.__dict__.get('helpers')
    if helpers and hasattr(helpers, 'start_project'):
        return helpers.start_project(project_name, init_git=init_git)
    return {'success': False, 'error': 'helpers not available'}

def check_project_status():
    """현재 프로젝트 상태 확인"""
    return {
        'current_dir': os.getcwd(),
        'project_name': os.path.basename(os.getcwd()),
        'has_context': os.path.exists("memory/context.json"),
        'has_workflow': os.path.exists("memory/workflow.json")
    }
