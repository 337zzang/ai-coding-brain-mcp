# === json_repl_session.py 수정 사항 ===
# 파일 상단에 추가 (import 섹션 아래)

import importlib
import warnings
import types
from functools import wraps

class LazyHelperProxy(types.ModuleType):
    """지연 로딩과 캐싱을 지원하는 헬퍼 프록시

    네임스페이스 오염을 방지하면서 기존 API와 호환성 유지
    """

    def __init__(self, name='helpers'):
        super().__init__(name)
        self._module = None
        self._warned = set()
        self.__file__ = "LazyHelperProxy"
        self.__doc__ = "AI Helpers v2.0 프록시"

    def _load(self):
        """실제 모듈을 지연 로딩"""
        if self._module is None:
            try:
                self._module = importlib.import_module('ai_helpers_new')
            except ImportError as e:
                raise ImportError(f"Failed to load ai_helpers_new: {e}")

    def __getattr__(self, item):
        """속성 접근 시 실제 모듈에서 가져오고 캐싱"""
        self._load()
        try:
            attr = getattr(self._module, item)
            # 함수나 클래스인 경우만 캐싱 (변경 가능한 값은 제외)
            if callable(attr) or isinstance(attr, type):
                setattr(self, item, attr)
            return attr
        except AttributeError:
            raise AttributeError(f"'helpers' has no attribute '{item}'")

    def __setattr__(self, name, value):
        """헬퍼 함수 덮어쓰기 방지"""
        if name.startswith('_') or name in ['__file__', '__doc__']:
            super().__setattr__(name, value)
        else:
            raise AttributeError(
                f"Cannot override helper function '{name}'. "
                f"Helper functions are read-only for safety."
            )

    def __dir__(self):
        """자동완성을 위한 속성 목록"""
        self._load()
        return dir(self._module)

# 레거시 경고 추적용 전역 변수
_legacy_warnings = set()

def create_legacy_stub(h, func_name):
    """레거시 호환성을 위한 스텁 생성

    기존 코드가 read(), write() 등을 직접 호출할 때
    경고를 표시하고 h.read(), h.write()로 위임
    """
    def legacy_stub(*args, **kwargs):
        # 함수별로 첫 호출 시에만 경고
        if func_name not in _legacy_warnings:
            _legacy_warnings.add(func_name)
            warnings.warn(
                f"\n"
                f"DeprecationWarning: Direct use of '{func_name}()' is deprecated.\n"
                f"Please use 'h.{func_name}()' instead.\n"
                f"This will be removed in a future version.",
                DeprecationWarning,
                stacklevel=2
            )
        # 실제 함수 호출
        return getattr(h, func_name)(*args, **kwargs)

    # 원본 함수의 메타데이터 보존
    legacy_stub.__name__ = func_name
    legacy_stub.__doc__ = f"Deprecated: Use h.{func_name}() instead"

    return legacy_stub

# load_helpers() 함수를 다음으로 교체:

def load_helpers():
    """AI Helpers v2.0과 워크플로우 시스템 로드 (개선된 버전)"""
    global helpers, HELPERS_AVAILABLE
    if HELPERS_AVAILABLE:
        return True

    try:
        # LazyHelperProxy 인스턴스 생성
        h = LazyHelperProxy('helpers')

        # 전역에는 h와 helpers만 등록 (동일 객체)
        globals()['h'] = h
        globals()['helpers'] = h

        # 레거시 호환성을 위한 함수들
        # 가장 자주 사용되는 함수들만 우선 지원
        legacy_functions = [
            # 파일 작업
            'read', 'write', 'append', 'read_json', 'write_json', 'exists',
            # 코드 분석
            'parse', 'view', 'replace',
            # 검색
            'search_files', 'search_code', 'find_function', 'grep',
            # LLM
            'ask_o3_async', 'check_o3_status', 'get_o3_result',
            # Git (조건부)
            'git_status', 'git_add', 'git_commit', 'git_push', 'git_pull',
            'git_branch', 'git_log', 'git_diff',
            # Flow
            'flow', 'create_task_logger',
            # 프로젝트
            'get_current_project', 'flow_project_with_workflow'
        ]

        # 스텁 함수 생성 및 등록
        for func_name in legacy_functions:
            # 실제로 존재하는 함수만 스텁 생성
            if hasattr(h, func_name):
                globals()[func_name] = create_legacy_stub(h, func_name)

        HELPERS_AVAILABLE = True
        print("✅ AI Helpers v2.0 로드 완료 (네임스페이스 격리 모드)")
        return True

    except Exception as e:
        print(f"❌ 헬퍼 로드 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
