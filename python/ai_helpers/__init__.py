"""
AI Helpers - 통합 헬퍼 모듈 v11.0
"""

# 핵심 imports만
try:
    from ai_helpers.search import scan_directory_dict, search_code_content, search_files_advanced
except:
    def scan_directory_dict(path):
        return {"files": [], "directories": []}
    def search_code_content(*args, **kwargs):
        return {"success": False, "error": "search module not available"}
    def search_files_advanced(*args, **kwargs):
        return {"success": False, "error": "search module not available"}

try:
    from ai_helpers.file import read_file, create_file
except:
    from ai_helpers.io import read_file, create_file

try:
    from ai_helpers.git import git_status
except:
    def git_status():
        return {"success": True, "data": {}}

try:
    from ai_helpers.code import replace_block
except:
    def replace_block(*args, **kwargs):
        return {"success": False, "error": "Not implemented"}

try:
    from ai_helpers.compile import compile_project, check_syntax
except:
    def compile_project(*args, **kwargs):
        return {"success": False, "error": "compile module not available"}
    def check_syntax(*args, **kwargs):
        return {"success": False, "error": "compile module not available"}

# Legacy
try:
    from ai_helpers.legacy_replacements import cmd_flow
except ImportError:
    def cmd_flow(*args, **kwargs):
        """enhanced_flow의 cmd_flow_with_context 호출"""
        try:
            import sys
            sys.path.insert(0, 'python')
            from enhanced_flow import cmd_flow_with_context
            if args and len(args) > 0:
                return cmd_flow_with_context(args[0])
            return {"success": False, "error": "프로젝트 이름이 필요합니다"}
        except ImportError:
            return {"success": False, "error": "enhanced_flow 모듈을 찾을 수 없습니다"}

# 워크플로우 관련 함수들 - 모듈 레벨에 직접 정의
def workflow(command="/status"):
    """워크플로우 명령 실행"""
    try:
        import sys
        sys.path.insert(0, 'python')
        from workflow_integration import process_workflow_command
        return process_workflow_command(command)
    except ImportError:
        return {"success": False, "error": "workflow_integration 모듈을 찾을 수 없습니다"}

def get_project_root():
    """프로젝트 루트 경로 반환"""
    import os
    return os.getcwd()

def get_workflow_status():
    """워크플로우 상태 조회"""
    try:
        import sys
        sys.path.insert(0, 'python')
        from workflow_integration import get_workflow_status as _get_status
        return _get_status()
    except ImportError:
        return {"success": False, "error": "workflow_integration 모듈을 찾을 수 없습니다"}

# 기타 필요한 함수들
def track_file_access(*args, **kwargs):
    return None

def track_function_edit(*args, **kwargs):
    return None

def get_work_tracking_summary(*args, **kwargs):
    return {}

__all__ = [
    'scan_directory_dict', 'search_code_content', 'search_files_advanced',
    'read_file', 'create_file', 'git_status', 'replace_block',
    'cmd_flow', 'workflow', 'get_project_root', 'get_workflow_status',
    'track_file_access', 'track_function_edit', 'get_work_tracking_summary',
    'compile_project', 'check_syntax',
    'AIHelpers',
    'ai_helpers'  # 인스턴스
]


# ==================== AIHelpers 호환 레이어 ====================
class AIHelpers:
    """
    레거시 코드 호환성을 위한 어댑터 클래스.
    기존 코드가 AIHelpers 클래스를 기대하는 경우를 위해 제공.
    새 코드에서는 함수를 직접 import해서 사용하세요.
    """
    # file 관련
    read_file = staticmethod(read_file)
    create_file = staticmethod(create_file)
    
    # search 관련
    scan_directory_dict = staticmethod(scan_directory_dict)
    search_code_content = staticmethod(search_code_content)
    search_files_advanced = staticmethod(search_files_advanced)
    
    # git 관련
    git_status = staticmethod(git_status)
    
    # code 관련
    replace_block = staticmethod(replace_block)
    
    # 추가 메서드들
    @staticmethod
    def get_project_root():
        """프로젝트 루트 경로 반환"""
        from utils.path_utils import get_project_root
        return get_project_root()
    
    @staticmethod
    def ensure_dir(path):
        """디렉토리 생성"""
        from utils.path_utils import ensure_dir
        return ensure_dir(path)

# 하위 호환성을 위해 인스턴스도 생성
ai_helpers = AIHelpers()
