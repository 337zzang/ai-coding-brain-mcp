"""
HelpersWrapper - 모든 헬퍼 함수를 HelperResult로 래핑
개선 사항:
1. 자동 래핑 메커니즘
2. safe_helper 데코레이터 확대 적용
3. 더 나은 에러 처리
"""
import functools
from typing import Any, Callable
from ai_helpers.helper_result import HelperResult
from pathlib import Path
import os

# 프로젝트 루트 경로 중앙화
ROOT = Path(__file__).resolve().parent.parent  # ai-coding-brain-mcp 루트

from python.workflow.v3.code_integration import WorkflowCodeIntegration
def safe_helper(func: Callable) -> Callable:
    """헬퍼 함수를 안전하게 래핑하는 데코레이터"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)

            # 이미 HelperResult인 경우
            if isinstance(result, HelperResult):
                # 이중 래핑 방지: data가 또 다른 HelperResult인지 확인
                if hasattr(result.data, 'ok') and hasattr(result.data, 'data'):
                    # 이미 이중 래핑된 경우 그대로 반환
                    return result
                return result

            # dict 형태의 결과 처리
            elif isinstance(result, dict):
                if 'success' in result and 'error' in result:
                    # 기존 형식 변환
                    if result['success']:
                        return HelperResult(True, data=result.get('data', result))
                    else:
                        return HelperResult(False, error=result.get('error', 'Unknown error'))
                else:
                    # 일반 dict는 성공으로 처리
                    return HelperResult(True, data=result)

            # bool 결과 처리
            elif isinstance(result, bool):
                if result:
                    return HelperResult(True, data=True)
                else:
                    return HelperResult(False, error='Operation failed')

            # None 처리
            elif result is None:
                return HelperResult(True, data=None)

            # 기타 모든 결과는 성공으로 처리
            else:
                return HelperResult(True, data=result)

        except Exception as e:
            return HelperResult(False, error=str(e))

    return wrapper


class HelpersWrapper:
    """AIHelpers 인스턴스를 래핑하여 모든 메서드가 HelperResult를 반환하도록 함"""

    def __init__(self, helpers_instance):
        self._helpers = helpers_instance
        self._cache = {}
        self._dc = None  # Desktop Commander 인스턴스 (lazy loading)

        # v44: 특정 메서드들을 명시적으로 바인딩 (캐시 우선순위 문제 해결)
        self._bind_override_methods()

    def _bind_override_methods(self):
        """클래스에 정의된 메서드들을 명시적으로 바인딩"""
        # 이 메서드들은 HelpersWrapper에서 오버라이드되었으므로
        # __getattr__를 거치지 않고 직접 사용되어야 함
        override_methods = [
            'list_functions', 'workflow', 'read_file',
            'scan_directory_dict', 'search_files_advanced', 'search_code_content',
            'search_files', 'parse_with_snippets', 'get_project_name', 'get_project_path'
        ]
        for method_name in override_methods:
            if hasattr(self.__class__, method_name):
                # 클래스 메서드를 인스턴스에 바인딩
                method = getattr(self.__class__, method_name)
                if callable(method):
                    # 바운드 메서드로 인스턴스의 __dict__에 직접 설정
                    # 이렇게 하면 __getattr__보다 우선순위가 높음
                    self.__dict__[method_name] = method.__get__(self, self.__class__)

    def __getattr__(self, name: str) -> Any:
        """동적으로 helpers 메서드를 래핑"""
        # v44 개선: 오버라이드된 메서드는 __dict__에 있으므로 여기로 오지 않음
        # 하지만 안전을 위해 추가 체크
        override_methods = ['list_functions', 'workflow', 'read_file']
        if name in override_methods and hasattr(self.__class__, name):
            method = getattr(self.__class__, name)
            bound_method = method.__get__(self, self.__class__)
            # 캐시에 저장하여 다음 접근 시 빠르게 반환
            self.__dict__[name] = bound_method
            return bound_method

        # 캐시 확인
        if name in self._cache:
            return self._cache[name]

        # helpers 인스턴스에서 속성 가져오기
        try:
            attr = getattr(self._helpers, name)
        except AttributeError:
            raise AttributeError(f"'{self._helpers.__class__.__name__}' has no attribute '{name}'")

        # 함수인 경우
        if callable(attr):
            # 이미 HelperResult를 반환하는 메서드들은 추가 래핑하지 않음
            no_wrap_methods = {
                # Workflow 관련
                'workflow', 'flow_project', 'list_functions',
                
                # File 관련
                'read_file', 'create_file', 'write_file', 'append_to_file',
                
                # Directory/Search 관련  
                'scan_directory_dict', 'scan_directory',
                'search_files_advanced', 'search_code_content',
                'search_code', 'find_class', 'find_function', 'find_import',
                
                # Git 관련
                'git_status', 'git_add', 'git_commit', 'git_push', 'git_pull',
                'git_branch', 'git_log', 'git_diff', 'git_stash', 'git_stash_pop',
                'git_commit_smart', 'git_branch_smart', 'is_git_repository', 'git_init',
                
                # Compile/Code 관련
                'edit_block', 'replace_block', 'parse_with_snippets',
                'check_syntax', 'compile_project', 'parse_code',
                
                # Utils
                'run_command',
                
                # Context 관련
                'get_context', 'save_context', 'update_context',
                
                # Project 관련
                'get_project_progress', 'get_system_summary'
            }
            
            if name in no_wrap_methods:
                # 이미 HelperResult를 반환하는 메서드는 그대로 사용
                self._cache[name] = attr
                return attr
            else:
                # 그 외의 메서드는 safe_helper로 래핑
                wrapped = safe_helper(attr)
                self._cache[name] = wrapped
                return wrapped

        # 함수가 아닌 경우 그대로 반환
        return attr

    def __dir__(self):
        """사용 가능한 메서드 목록 반환"""
        base_methods = dir(self._helpers)
        # 추가된 search 메서드들도 포함
        additional_methods = [
            'scan_directory_dict', 'search_files_advanced', 'search_code_content',
            'search_files', 'parse_with_snippets', 'get_project_name', 'get_project_path'
        ]
        return list(set(base_methods + additional_methods))
    
    # Search 관련 메서드들 추가
    def scan_directory_dict(self, directory: str) -> HelperResult:
        """디렉토리 스캔 (딕셔너리 반환)"""
        from pathlib import Path
        try:
            scan_path = Path(directory).resolve()
            
            if not scan_path.exists():
                return HelperResult(False, error=f"경로가 존재하지 않습니다: {directory}")
                
            if not scan_path.is_dir():
                return HelperResult(False, error=f"디렉토리가 아닙니다: {directory}")
            
            files = []
            directories = []
            
            for item in scan_path.iterdir():
                if item.is_file():
                    files.append({
                        'name': item.name,
                        'path': str(item),
                        'size': item.stat().st_size
                    })
                elif item.is_dir():
                    directories.append({
                        'name': item.name,
                        'path': str(item)
                    })
            
            return HelperResult(True, data={
                'files': files,
                'directories': directories,
                'total_files': len(files),
                'total_directories': len(directories)
            })
            
        except Exception as e:
            return HelperResult(False, error=f"디렉토리 스캔 중 오류: {str(e)}")
    
    def search_files_advanced(self, directory: str, pattern: str = '*', **kwargs) -> HelperResult:
        """파일 검색 (고급)"""
        from pathlib import Path
        try:
            results = []
            search_path = Path(directory).resolve()
            
            if not search_path.exists():
                return HelperResult(False, error=f"경로가 존재하지 않습니다: {directory}")
            
            # 재귀적으로 파일 검색
            if search_path.is_dir():
                for file_path in search_path.rglob(pattern):
                    if file_path.is_file():
                        results.append(str(file_path))
                        
            return HelperResult(True, data={'results': results})
            
        except Exception as e:
            return HelperResult(False, error=f"파일 검색 중 오류: {str(e)}")
    
    def search_code_content(self, path: str, pattern: str, file_pattern: str = "*.py") -> HelperResult:
        """코드 내용 검색"""
        from pathlib import Path
        try:
            results = []
            search_path = Path(path).resolve()
            
            if not search_path.exists():
                return HelperResult(False, error=f"경로가 존재하지 않습니다: {path}")
            
            # 파일 패턴에 맞는 파일들 검색
            for file_path in search_path.rglob(file_pattern):
                if file_path.is_file():
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        if pattern in content:
                            # 패턴이 포함된 라인 찾기
                            lines = content.split('\n')
                            matches = []
                            for i, line in enumerate(lines):
                                if pattern in line:
                                    matches.append({
                                        'line_number': i + 1,
                                        'line_content': line.strip()
                                    })
                            
                            if matches:
                                results.append({
                                    'file_path': str(file_path),
                                    'matches': matches
                                })
                                
                    except Exception:
                        # 읽을 수 없는 파일은 건너뛰기
                        continue
                        
            return HelperResult(True, data={'results': results})
            
        except Exception as e:
            return HelperResult(False, error=f"코드 검색 중 오류: {str(e)}")

    def search_files(self, directory: str, pattern: str = '*', **kwargs) -> HelperResult:
        """파일 검색 - search_files_advanced의 간단한 별칭"""
        return self.search_files_advanced(directory, pattern, **kwargs)
    
    def parse_with_snippets(self, file_path: str) -> HelperResult:
        """파일을 파싱하여 코드 구조 분석"""
        try:
            # 절대 경로로 변환
            if not Path(file_path).is_absolute():
                file_path = str(ROOT / file_path)
            
            # ai_helpers.code 모듈에서 직접 import
            from ai_helpers.code import parse_with_snippets as _parse_with_snippets
            
            result = _parse_with_snippets(file_path)
            
            # 이미 HelperResult인 경우
            if hasattr(result, 'ok'):
                return result
            # dict나 다른 타입인 경우 래핑
            else:
                return HelperResult(True, data=result)
                
        except ImportError:
            return HelperResult(False, error="parse_with_snippets를 사용할 수 없습니다. ai_helpers.code 모듈을 확인하세요.")
        except Exception as e:
            return HelperResult(False, error=f"파싱 중 오류: {str(e)}")
    
    def get_project_name(self) -> HelperResult:
        """현재 프로젝트 이름 반환"""
        try:
            # 현재 작업 디렉토리의 이름을 프로젝트 이름으로 사용
            project_name = os.path.basename(os.getcwd())
            return HelperResult(True, data=project_name)
        except Exception as e:
            return HelperResult(False, error=f"프로젝트 이름 획득 중 오류: {str(e)}")
    
    def get_project_path(self) -> HelperResult:
        """현재 프로젝트 경로 반환"""
        try:
            project_path = os.getcwd()
            return HelperResult(True, data=project_path)
        except Exception as e:
            return HelperResult(False, error=f"프로젝트 경로 획득 중 오류: {str(e)}")

    # 자주 사용하는 메서드들에 대한 타입 힌트와 문서화
    def read_file(self, path: str, **kwargs) -> HelperResult:
        """파일 읽기 - offset/length 파라미터 지원 (v44 개선)"""
        try:
            # Desktop Commander 지원 파라미터 확인
            dc_params = {}
            use_dc = False
            
            # offset과 length는 Desktop Commander에서만 지원
            if 'offset' in kwargs:
                dc_params['offset'] = kwargs['offset']
                use_dc = True
            if 'length' in kwargs:
                dc_params['length'] = kwargs['length']
                use_dc = True
            if 'isUrl' in kwargs:
                dc_params['isUrl'] = kwargs['isUrl']
                use_dc = True

            # Desktop Commander가 필요하고 사용 가능한 경우
            if use_dc:
                try:
                    # Desktop Commander lazy loading
                    if self._dc is None:
                        import desktop_commander as dc
                        self._dc = dc
                    
                    if hasattr(self._dc, 'read_file'):
                        result = self._dc.read_file(path=path, **dc_params)
                        if hasattr(result, 'data'):
                            return HelperResult(True, result.data)
                        else:
                            return HelperResult(True, result)
                except (ImportError, AttributeError):
                    # Desktop Commander 사용 불가 시 AI Helpers로 fallback
                    pass
            
            # AI Helpers 사용 (기본 동작)
            result = self._helpers.read_file(path)
            if hasattr(result, 'ok'):
                return result
            else:
                return HelperResult(True, result)

        except Exception as e:
            return HelperResult(False, error=f"read_file 오류: {str(e)}")

    def create_file(self, path: str, content: str, **kwargs) -> HelperResult:
        """파일 생성/쓰기 - HelperResult 반환"""
        return self.__getattr__('create_file')(path, content, **kwargs)

    def git_status(self, **kwargs) -> HelperResult:
        """Git 상태 확인 - HelperResult 반환"""
        return self.__getattr__('git_status')(**kwargs)

    def git_commit_smart(self, message: str, **kwargs) -> HelperResult:
        """스마트 커밋 - HelperResult 반환"""
        return self.__getattr__('git_commit_smart')(message, **kwargs)


    def workflow(self, command: str) -> HelperResult:
        """v3: 명령어 실행"""
        try:
            from python.workflow.v3.dispatcher import execute_workflow_command
            return execute_workflow_command(command)
        except ImportError as e:
            return HelperResult(False, error=f"Workflow 모듈 import 실패: {str(e)}")
        except Exception as e:
            return HelperResult(False, error=f"Workflow 실행 오류: {str(e)}")

    def list_functions(self) -> HelperResult:
        """사용 가능한 함수 목록 조회 (v44 개선)"""
        try:
            # 직접 구현 - utils 모듈 의존성 제거
            funcs = {}
            modules = {}
            suggestions = {}

            # helpers의 모든 public 메서드 수집
            for attr in dir(self._helpers):
                if not attr.startswith('_'):
                    obj = getattr(self._helpers, attr, None)
                    if callable(obj):
                        funcs[attr] = obj
                        # 모듈별 분류
                        module = getattr(obj, '__module__', 'unknown')
                        if module not in modules:
                            modules[module] = []
                        modules[module].append(attr)

            # 자주 착각하는 함수명 제안
            suggestions = {
                'get_project_name': 'flow_project 또는 execute_code에서 os.getcwd()',
                'list_functions': 'helpers.list_functions() - 이제 사용 가능!',
                'read_file_lines': 'read_file() 사용',
                'write_file_lines': 'write_file() 또는 create_file() 사용'
            }

            # 사용법 안내
            usage = "helpers.함수명() 형태로 사용하세요"

            result = {
                'total_count': len(funcs),
                'functions': modules,
                'suggestions': suggestions,
                'usage': usage
            }

            return HelperResult(True, result)

        except Exception as e:
            # 오류 시에도 기본 정보 제공
            return HelperResult(True, {
                'total_count': 0,
                'error': str(e),
                'message': '함수 목록을 가져올 수 없지만 helpers는 정상 작동합니다'
            })
    def workflow_done(self, notes: str = "") -> HelperResult:
        """v3: 태스크 완료"""
        try:
            from workflow.v3 import WorkflowManager
            # V2 complete_current_task는 V3에서 다르게 처리됨
            manager = WorkflowManager("default")
            return manager.execute_command(f"/next {notes}")
        except Exception as e:
            return HelperResult(False, error=str(e))

    def workflow_status(self) -> HelperResult:
        """v3: 상태 조회"""
        try:
            from workflow.v3 import WorkflowManager
            # V2 get_status는 V3에서 다르게 처리됨
            manager = WorkflowManager("default")
            result = manager.execute_command("/status")
            return HelperResult(True, result)
        except Exception as e:
            return HelperResult(False, error=str(e))


def auto_wrap_helpers():
    """builtins의 helpers를 자동으로 래핑"""
    import builtins

    if hasattr(builtins, 'helpers'):
        wrapped = HelpersWrapper(builtins.helpers)
        builtins.wrapped_helpers = wrapped
        builtins.w = wrapped  # 짧은 별칭
        return wrapped
    else:
        raise RuntimeError("builtins.helpers not found")


# 전역 래핑 설정
def setup_global_wrapper():
    """JSON REPL 세션 시작 시 자동 실행"""
    try:
        wrapped = auto_wrap_helpers()
        print("✅ HelpersWrapper 자동 적용 완료!")
        print("   사용: w.read_file('file.py') 또는 wrapped_helpers.read_file('file.py')")
        return wrapped
    except Exception as e:
        print(f"⚠️ HelpersWrapper 자동 적용 실패: {e}")
        return None


__all__ = ['HelpersWrapper', 'safe_helper', 'auto_wrap_helpers', 'setup_global_wrapper']



def execute_code_with_workflow(code: str, auto_progress: bool = False) -> HelperResult:
    """워크플로우와 연계된 코드 실행

    Args:
        code: 실행할 코드
        auto_progress: 성공 시 태스크 자동 완료 여부

    Returns:
        HelperResult with execution result
    """
    try:
        import time

        # 프로젝트 이름 가져오기
        project_name = HelpersWrapper('').get_project_name()
        if not project_name.ok:
            project_name = 'unknown'
        else:
            project_name = project_name.data

        # 워크플로우 통합 객체 생성
        integration = WorkflowCodeIntegration(project_name)

        # 현재 태스크 확인
        current_task = integration.get_current_task_context()
        if current_task:
            print(f"🎯 현재 태스크: {current_task['task_title']}")

        # 코드 실행
        start_time = time.time()
        result = execute_code(code)
        execution_time = time.time() - start_time

        # 실행 결과 기록
        if current_task and result.ok:
            integration.record_code_execution(
                code, 
                {'success': result.ok, 'output': str(result.data)}, 
                execution_time
            )

            # 자동 진행 확인
            if auto_progress and result.ok:
                output_str = str(result.data).lower()
                # 더 정교한 키워드 매칭
                # 1. 명시적 마커 체크 (최우선)
                if "task_complete:" in output_str or "task_done:" in output_str:
                    progress_result = integration.auto_progress_task("코드 실행으로 자동 완료")
                    print(f"✅ 태스크 자동 완료 (명시적 마커)")
                # 2. 독립된 단어로 존재하는 경우만 체크
                else:
                    import re
                    # 단어 경계를 확인하는 정규식
                    complete_pattern = r'\b(완료됨?|completed?|done|finished?)\b'
                    if re.search(complete_pattern, output_str):
                        # 추가 컨텍스트 확인 (false positive 방지)
                        negative_patterns = [
                            r'not\s+(completed?|done|finished?)',
                            r'(completed?|done|finished?)\s+\w+\.(txt|json|py)',  # 파일명
                            r'(error|failed|unable)'
                        ]
                        if not any(re.search(pat, output_str) for pat in negative_patterns):
                            progress_result = integration.auto_progress_task("코드 실행 성공")
                            print(f"✅ 태스크 자동 완료")

        return result

    except Exception as e:
        return HelperResult(False, None, str(e))


def get_workflow_context() -> HelperResult:
    """현재 워크플로우 컨텍스트 조회"""
    try:
        project_name = HelpersWrapper('').get_project_name()
        if not project_name.ok:
            return HelperResult(False, None, "프로젝트를 찾을 수 없습니다")

        integration = WorkflowCodeIntegration(project_name.data)
        context = integration.get_current_task_context()

        return HelperResult(True, context)

    except Exception as e:
        return HelperResult(False, None, str(e))


# helpers_extension 함수들을 HelpersWrapper에 추가
try:
    from python.helpers_extension import (
        create_directory, list_directory, delete_directory,
        file_exists, delete_file, copy_file, move_file, get_file_size,
        append_to_file, read_lines, backup_file,
        read_json, write_json,
        run_command,
        get_project_name as ext_get_project_name,
        get_project_path as ext_get_project_path, 
        get_current_branch as ext_get_current_branch,
        get_timestamp
    )
    
    # HelpersWrapper 클래스에 동적으로 메서드 추가
    # 디렉토리 관련
    HelpersWrapper.create_directory = lambda self, path: create_directory(path)
    HelpersWrapper.list_directory = lambda self, path=".": list_directory(path)
    HelpersWrapper.delete_directory = lambda self, path: delete_directory(path)
    
    # 파일 관련
    HelpersWrapper.file_exists = lambda self, path: file_exists(path)
    HelpersWrapper.delete_file = lambda self, path: delete_file(path)
    HelpersWrapper.copy_file = lambda self, src, dst: copy_file(src, dst)
    HelpersWrapper.move_file = lambda self, src, dst: move_file(src, dst)
    HelpersWrapper.get_file_size = lambda self, path: get_file_size(path)
    HelpersWrapper.backup_file = lambda self, path, backup_dir="backups": backup_file(path, backup_dir)
    
    # 텍스트 파일 관련 (append_to_file은 이미 있을 수 있음)
    if not hasattr(HelpersWrapper, 'append_to_file'):
        HelpersWrapper.append_to_file = lambda self, path, content: append_to_file(path, content)
    HelpersWrapper.read_lines = lambda self, path, start=0, count=None: read_lines(path, start, count)
    
    # JSON 관련
    HelpersWrapper.read_json = lambda self, path, default=None: read_json(path, default)
    HelpersWrapper.write_json = lambda self, path, data, indent=2: write_json(path, data, indent)
    
    # 명령어 실행 (run_command는 이미 있을 수 있음)
    if not hasattr(HelpersWrapper, 'run_command'):
        HelpersWrapper.run_command = lambda self, cmd, timeout=30, encoding=None: run_command(cmd, timeout, encoding)
    
    # 유틸리티
    HelpersWrapper.get_timestamp = lambda self, format="%Y%m%d_%H%M%S": get_timestamp(format)
    
    print("✅ helpers_extension 함수들이 helpers에 자동 등록되었습니다!")
    
except ImportError as e:
    print(f"⚠️ helpers_extension 자동 등록 실패: {e}")
except Exception as e:
    print(f"❌ 예상치 못한 오류: {e}")