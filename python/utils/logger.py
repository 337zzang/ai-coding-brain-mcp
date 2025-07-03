"""
MCP 서버용 로깅 유틸리티
stdout으로 출력되는 것을 방지하고 stderr로 리다이렉트
"""
import sys
import logging
from typing import Optional

# 로거 설정 - stderr로만 출력
def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """MCP 서버용 로거 설정"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 기존 핸들러 제거
    logger.handlers = []
    
    # stderr 핸들러만 추가
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    
    # 포맷 설정
    formatter = logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger

# 기본 로거
logger = setup_logger('mcp_server')

# print 함수 오버라이드 (디버깅용)
def safe_print(*args, **kwargs):
    """stdout 대신 stderr로 출력하는 안전한 print"""
    print(*args, **kwargs, file=sys.stderr)
