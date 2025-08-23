"""
웹 자동화 공통 유틸리티
재사용 가능한 헬퍼 함수 및 데코레이터
"""

import logging
import functools
import time
from typing import Any, Callable, Optional, List, Dict, TypeVar, Union
from pathlib import Path
from datetime import datetime

from .types import HelperResult
from .exceptions import WebAutomationError, TimeoutError, ElementError

# 로깅 설정
logger = logging.getLogger("web_automation")
logger.setLevel(logging.INFO)

# 타입 변수
T = TypeVar('T')


def setup_logging(log_dir: Optional[Path] = None) -> None:
    """로깅 설정 초기화"""
    if log_dir is None:
        log_dir = Path("logs/web_automation")

    log_dir.mkdir(parents=True, exist_ok=True)

    # 파일 핸들러
    log_file = log_dir / f"web_{datetime.now():%Y%m%d}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )

    # 핸들러 추가 (중복 방지)
    if not logger.handlers:
        logger.addHandler(file_handler)


def safe_execute(func: Callable[..., T]) -> Callable[..., HelperResult]:
    """
    함수 실행을 안전하게 래핑하는 데코레이터
    모든 예외를 캐치하고 HelperResult로 반환
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> HelperResult:
        try:
            result = func(*args, **kwargs)

            # 이미 HelperResult인 경우 그대로 반환
            if isinstance(result, HelperResult):
                return result

            # 딕셔너리이고 'ok' 키가 있는 경우
            if isinstance(result, dict) and 'ok' in result:
                return HelperResult(
                    ok=result['ok'],
                    data=result.get('data'),
                    error=result.get('error'),
                    metadata=result.get('metadata')
                )

            # 그 외의 경우 성공 결과로 래핑
            return HelperResult.success(result)

        except WebAutomationError as e:
            logger.error(f"{func.__name__} failed: {e}")
            return HelperResult.failure(str(e))
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}")
            return HelperResult.failure(f"Unexpected error: {e}")

    return wrapper


def with_retry(max_attempts: int = 3, delay: float = 1.0):
    """
    재시도 로직을 추가하는 데코레이터

    Args:
        max_attempts: 최대 시도 횟수
        delay: 재시도 간 대기 시간 (초)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts")

            raise last_error

        return wrapper

    return decorator


def measure_time(func: Callable[..., T]) -> Callable[..., T]:
    """실행 시간을 측정하는 데코레이터"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> T:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(f"{func.__name__} took {elapsed:.2f} seconds")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.2f} seconds")
            raise

    return wrapper


def validate_selector(selector: str) -> bool:
    """CSS 선택자 유효성 검증"""
    if not selector or not isinstance(selector, str):
        return False

    # 기본적인 선택자 패턴 검증
    invalid_patterns = ['<', '>', 'javascript:', 'data:']
    for pattern in invalid_patterns:
        if pattern in selector.lower():
            return False

    return True


def get_alternative_selectors(selector: str) -> List[str]:
    """
    대체 선택자 목록 생성
    기존 web.py의 _get_multiple_selectors 로직 개선
    """
    selectors = [selector]

    # data-testid 변형 추가
    if not selector.startswith('[data-testid'):
        if '#' in selector:
            testid = selector.replace('#', '').replace('-', '_')
            selectors.append(f'[data-testid="{testid}"]')
        elif '.' in selector:
            testid = selector.replace('.', '').replace('-', '_')
            selectors.append(f'[data-testid="{testid}"]')

    # 버튼 관련 선택자
    if 'btn' in selector.lower() or 'button' in selector.lower():
        selectors.extend([
            'button',
            'input[type="submit"]',
            'input[type="button"]',
            '[role="button"]'
        ])

    # 링크 관련 선택자
    if 'link' in selector.lower() or 'a' in selector.lower():
        selectors.extend([
            'a[href]',
            '[role="link"]'
        ])

    # 입력 필드 관련 선택자
    if 'input' in selector.lower() or 'field' in selector.lower():
        selectors.extend([
            'input',
            'textarea',
            '[contenteditable="true"]'
        ])

    # 중복 제거
    return list(dict.fromkeys(selectors))


def sanitize_filename(filename: str) -> str:
    """파일명 안전하게 변환"""
    invalid_chars = '<>:"|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:255]  # 최대 길이 제한


def parse_timeout(timeout: Optional[Union[int, float]]) -> int:
    """타임아웃 값 파싱 및 검증"""
    if timeout is None:
        return 10000  # 기본값 10초

    if isinstance(timeout, (int, float)):
        # 초 단위를 밀리초로 변환 (1000 이하인 경우)
        if timeout <= 1000:
            timeout = int(timeout * 1000)
        return max(100, min(int(timeout), 300000))  # 100ms ~ 5분

    return 10000


def create_session_id(prefix: str = "web") -> str:
    """유니크한 세션 ID 생성"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}"


def safe_get_data(result: Dict, key: Optional[str] = None, default: Any = None) -> Any:
    """
    안전한 데이터 접근
    기존 web.py의 safe_get_data 함수 재구현
    """
    if not result or not isinstance(result, dict):
        return default

    if not result.get('ok', False):
        return default

    data = result.get('data')
    if data is None:
        return default

    if key and isinstance(data, dict):
        return data.get(key, default)

    return data


class ContextManager:
    """리소스 자동 관리를 위한 컨텍스트 매니저 베이스 클래스"""

    def __enter__(self):
        """리소스 획득"""
        raise NotImplementedError

    def __exit__(self, exc_type, exc_val, exc_tb):
        """리소스 해제"""
        raise NotImplementedError


def format_error_message(error: Exception, context: Optional[str] = None) -> str:
    """에러 메시지 포맷팅"""
    msg = f"{error.__class__.__name__}: {str(error)}"
    if context:
        msg = f"[{context}] {msg}"
    return msg


def is_valid_url(url: str) -> bool:
    """URL 유효성 검증"""
    if not url or not isinstance(url, str):
        return False

    valid_schemes = ['http://', 'https://', 'file://', 'about:']
    return any(url.startswith(scheme) for scheme in valid_schemes)


# 상수 정의
DEFAULT_TIMEOUT = 10000  # 10초
DEFAULT_VIEWPORT = {"width": 1280, "height": 720}
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
