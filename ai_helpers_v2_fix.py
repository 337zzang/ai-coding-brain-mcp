# Quick Fix for ai_helpers_v2/__init__.py
# 파일 끝에 추가할 내용

# 별칭 및 호환성 함수
from .code_ops import parse_with_snippets
parse_file = parse_with_snippets
extract_functions = parse_with_snippets  
extract_code_elements = parse_with_snippets

# 더미 workflow 함수들
def fp(project_name):
    """프로젝트 전환 (더미)"""
    return f"Switched to project: {project_name}"

def flow_project(project_name):
    """프로젝트 플로우 (더미)"""
    return fp(project_name)

def scan_directory(path):
    """디렉토리 스캔 (scan_directory_dict 래퍼)"""
    from .project_ops import scan_directory_dict
    return scan_directory_dict(path)

def workflow(command):
    """워크플로우 명령 (더미)"""
    return f"Workflow command: {command}"

# __all__에 추가
__all__.extend([
    'parse_file', 'extract_functions', 'extract_code_elements',
    'fp', 'flow_project', 'scan_directory', 'workflow'
])
