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


from python.workflow.v3.code_integration import WorkflowCodeIntegration
import os
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

        # v44: 특정 메서드들을 명시적으로 바인딩 (캐시 우선순위 문제 해결)
        self._bind_override_methods()

    def _bind_override_methods(self):
        """클래스에 정의된 메서드들을 명시적으로 바인딩"""
        # 이 메서드들은 HelpersWrapper에서 오버라이드되었으므로
        # __getattr__를 거치지 않고 직접 사용되어야 함
        override_methods = ['list_functions', 'workflow', 'read_file']
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
                'workflow', 'scan_directory_dict', 'run_command',
                'git_status', 'git_add', 'git_commit', 'git_push',
                'read_file', 'create_file', 'edit_block', 'replace_block',
                'search_files', 'search_code', 'parse_with_snippets'
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
        return dir(self._helpers)

    # 자주 사용하는 메서드들에 대한 타입 힌트와 문서화
    def read_file(self, path: str, **kwargs) -> HelperResult:
        """파일 읽기 - offset/length 파라미터 지원 (v44 개선)"""
        try:
            # Desktop Commander의 read_file 파라미터 매핑
            dc_params = {}

            # offset과 length는 Desktop Commander에서 지원
            if 'offset' in kwargs:
                dc_params['offset'] = kwargs['offset']
            if 'length' in kwargs:
                dc_params['length'] = kwargs['length']
            if 'isUrl' in kwargs:
                dc_params['isUrl'] = kwargs['isUrl']

            # Desktop Commander의 read_file 호출
            if hasattr(self._dc, 'read_file'):
                # Desktop Commander 사용
                result = self._dc.read_file(path=path, **dc_params)
                if hasattr(result, 'data'):
                    return HelperResult(True, result.data)
                else:
                    return HelperResult(True, result)
            else:
                # AI Helpers fallback
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
        """v2: 명령어 실행"""
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
        """v2: 태스크 완료"""
        try:
            from workflow.v3 import WorkflowManager
            # V2 complete_current_task는 V3에서 다르게 처리됨
            manager = WorkflowManager("default")
            return manager.execute_command(f"/next {notes}")
        except Exception as e:
            return HelperResult(False, error=str(e))

    def workflow_status(self) -> HelperResult:
        """v2: 상태 조회"""
        try:
            from workflow.v3 import WorkflowManager
            # V2 get_status는 V3에서 다르게 처리됨
            manager = WorkflowManager("default")
            result = manager.execute_command("/status")
            return HelperResult(True, result)
        except Exception as e:
            return HelperResult(False, error=str(e))


    def process_workflow_command(self, command: str) -> HelperResult:
        """V1 호환성을 위한 래퍼"""
        return self.workflow(command)

# 자동 초기화 헬퍼
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
                if any(kw in output_str for kw in ['완료', 'complete', 'done']):
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
