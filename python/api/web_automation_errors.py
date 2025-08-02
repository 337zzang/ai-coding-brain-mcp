"""
웹 자동화 시스템 에러 처리 및 디버깅 모듈

이 모듈은 기존 API와 100% 호환되면서 디버깅 기능을 추가합니다.
환경변수 WEB_AUTO_DEBUG=true 설정 시 상세 디버깅 정보를 제공합니다.
"""

import os
import json
import logging
import traceback
from datetime import datetime
from functools import wraps
from typing import Dict, Any, Callable, Optional
from pathlib import Path


# 디버그 모드 확인
DEBUG_MODE = os.getenv('WEB_AUTO_DEBUG', '').lower() == 'true'

# 로깅 설정
def setup_logging():
    """웹 자동화 로깅 설정"""
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f'web_automation_{datetime.now().strftime("%Y%m%d")}.log'

    # 로거 설정
    logger = logging.getLogger('web_automation')
    logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)

    # 파일 핸들러
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # 포맷터 (JSON 라인 형식)
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'level': record.levelname,
                'function': record.funcName,
                'message': record.getMessage(),
                'module': record.module
            }
            if hasattr(record, 'error_info'):
                log_data['error_info'] = record.error_info
            return json.dumps(log_data, ensure_ascii=False)

    file_handler.setFormatter(JsonFormatter())

    # 콘솔 핸들러 (디버그 모드에서만)
    if DEBUG_MODE:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(
            logging.Formatter('[%(levelname)s] %(message)s')
        )
        logger.addHandler(console_handler)

    logger.addHandler(file_handler)
    return logger


# 로거 초기화
logger = setup_logging()


def safe_execute(func_name: str, 
                impl_func: Callable,
                *args, 
                check_instance: bool = True,
                **kwargs) -> Dict[str, Any]:
    """
    웹 자동화 함수의 안전한 실행을 위한 래퍼

    Args:
        func_name: 함수 이름 (로깅/디버깅용)
        impl_func: 실제 실행할 함수
        *args: 함수 인자
        check_instance: 인스턴스 체크 여부 (web_start는 False)
        **kwargs: 함수 키워드 인자

    Returns:
        표준 응답 형식 {'ok': bool, 'error/data': ...}
    """
    start_time = datetime.now()

    try:
        # 로깅
        logger.debug(f"Executing {func_name} with args={args}, kwargs={kwargs}")

        # 인스턴스 검증 (필요한 경우)
        if check_instance:
            # web_automation_helpers의 _get_web_instance import 필요
            from . import web_automation_helpers
            if not web_automation_helpers._get_web_instance():
                error_msg = 'web_start()를 먼저 실행하세요'
                logger.warning(f"{func_name}: {error_msg}")
                return {'ok': False, 'error': error_msg}

        # 실제 함수 실행
        result = impl_func(*args, **kwargs)

        # 결과 정규화
        if isinstance(result, dict) and 'ok' in result:
            # 이미 표준 형식
            if result['ok']:
                logger.info(f"{func_name} succeeded")
            else:
                logger.warning(f"{func_name} failed: {result.get('error', 'Unknown error')}")
            return result
        else:
            # 표준 형식으로 변환
            logger.info(f"{func_name} succeeded (wrapped result)")
            return {'ok': True, 'data': result}

    except Exception as e:
        # 에러 정보 수집
        error_type = type(e).__name__
        error_msg = str(e) or '알 수 없는 오류'
        stack_trace = traceback.format_exc()

        # 에러 로깅
        logger.error(f"{func_name} raised {error_type}: {error_msg}", 
                    extra={'error_info': {
                        'type': error_type,
                        'stack_trace': stack_trace,
                        'args': args,
                        'kwargs': kwargs
                    }})

        # 기본 에러 응답
        error_response = {
            'ok': False,
            'error': error_msg
        }

        # 디버그 모드에서 추가 정보
        if DEBUG_MODE:
            error_response['_debug'] = {
                'error_type': error_type,
                'stack_trace': stack_trace,
                'context': {
                    'function': func_name,
                    'args': args,
                    'kwargs': kwargs,
                    'execution_time': (datetime.now() - start_time).total_seconds()
                },
                'timestamp': datetime.now().isoformat()
            }
            print(f"\n[DEBUG] {func_name} 에러 발생:")
            print(f"  타입: {error_type}")
            print(f"  메시지: {error_msg}")
            print(f"  실행시간: {(datetime.now() - start_time).total_seconds():.3f}초")

        return error_response


def enable_debug_mode():
    """프로그램 실행 중 디버그 모드 활성화"""
    global DEBUG_MODE
    DEBUG_MODE = True
    os.environ['WEB_AUTO_DEBUG'] = 'true'
    logger.setLevel(logging.DEBUG)
    logger.info("Debug mode enabled")


def disable_debug_mode():
    """프로그램 실행 중 디버그 모드 비활성화"""
    global DEBUG_MODE
    DEBUG_MODE = False
    os.environ['WEB_AUTO_DEBUG'] = 'false'
    logger.setLevel(logging.INFO)
    logger.info("Debug mode disabled")


def get_debug_status() -> Dict[str, Any]:
    """현재 디버그 상태 확인"""
    return {
        'debug_mode': DEBUG_MODE,
        'log_level': logger.level,
        'log_file': str(list(logger.handlers)[0].baseFilename) if logger.handlers else None
    }


# 데코레이터 버전 (선택적 사용)
def with_error_handling(func_name: str = None, check_instance: bool = True):
    """에러 처리 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = func_name or func.__name__
            return safe_execute(name, func, *args, check_instance=check_instance, **kwargs)
        return wrapper
    return decorator
