"""
공통 유틸리티 함수
외부 의존성 최소화
"""
import re
from datetime import datetime
from typing import Any, Dict

def sanitize_filename(name: str) -> str:
    """파일명으로 사용할 수 있도록 문자열 정제"""
    # 특수문자를 언더스코어로 변경
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', name)
    # 연속된 언더스코어를 하나로
    sanitized = re.sub(r'_+', '_', sanitized)
    # 앞뒤 공백 및 언더스코어 제거
    return sanitized.strip('_ ')

def safe_dict_get(data: Dict, key: str, default: Any = None) -> Any:
    """안전한 딕셔너리 접근"""
    try:
        return data.get(key, default)
    except (AttributeError, TypeError):
        return default

def format_timestamp(dt: datetime) -> str:
    """일관된 타임스탬프 포맷"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def generate_id(prefix: str, timestamp: datetime = None) -> str:
    """고유 ID 생성"""
    if timestamp is None:
        timestamp = datetime.now()
    return f"{prefix}_{timestamp.strftime('%Y%m%d_%H%M%S')}"

def truncate_text(text: str, max_length: int = 80, suffix: str = "...") -> str:
    """텍스트를 지정된 길이로 자르기"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
