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


def safe_helper(func: Callable) -> Callable:
    """헬퍼 함수를 안전하게 래핑하는 데코레이터"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)

            # 이미 HelperResult인 경우
            if isinstance(result, HelperResult):
                return result

            # dict 형태의 결과 처리
            elif isinstance(result, dict):
                if 'success' in result and 'error' in result:
                    # 기존 형식 변환
                    if result['success']:
                        return HelperResult.success(result.get('data', result))
                    else:
                        return HelperResult.failure(result.get('error', 'Unknown error'))
                else:
                    # 일반 dict는 성공으로 처리
                    return HelperResult.success(result)

            # bool 결과 처리
            elif isinstance(result, bool):
                if result:
                    return HelperResult.success(True)
                else:
                    return HelperResult.failure('Operation failed')

            # None 처리
            elif result is None:
                return HelperResult.success(None)

            # 기타 모든 결과는 성공으로 처리
            else:
                return HelperResult.success(result)

        except Exception as e:
            return HelperResult.failure(str(e))

    return wrapper


class HelpersWrapper:
    """AIHelpers 인스턴스를 래핑하여 모든 메서드가 HelperResult를 반환하도록 함"""

    def __init__(self, helpers_instance):
        self._helpers = helpers_instance
        self._cache = {}

    def __getattr__(self, name: str) -> Any:
        """동적으로 helpers 메서드를 래핑"""
        # 캐시 확인
        if name in self._cache:
            return self._cache[name]

        # helpers 인스턴스에서 속성 가져오기
        try:
            attr = getattr(self._helpers, name)
        except AttributeError:
            raise AttributeError(f"'{self._helpers.__class__.__name__}' has no attribute '{name}'")

        # 함수인 경우 safe_helper로 래핑
        if callable(attr):
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
        """파일 읽기 - HelperResult 반환"""
        return self.__getattr__('read_file')(path, **kwargs)

    def create_file(self, path: str, content: str, **kwargs) -> HelperResult:
        """파일 생성/쓰기 - HelperResult 반환"""
        return self.__getattr__('create_file')(path, content, **kwargs)

    def git_status(self, **kwargs) -> HelperResult:
        """Git 상태 확인 - HelperResult 반환"""
        return self.__getattr__('git_status')(**kwargs)

    def git_commit_smart(self, message: str, **kwargs) -> HelperResult:
        """스마트 커밋 - HelperResult 반환"""
        return self.__getattr__('git_commit_smart')(message, **kwargs)

    def workflow(self, command: str, **kwargs) -> HelperResult:
        """워크플로우 명령 - HelperResult 반환"""
        return self.__getattr__('workflow')(command, **kwargs)


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
