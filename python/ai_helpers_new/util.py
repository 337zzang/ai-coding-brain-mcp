"""
Utility functions for standard responses
"""

import os
from pathlib import Path

def ok(data):
    """Success response"""
    return {'ok': True, 'data': data}

def err(message):
    """Error response"""
    return {'ok': False, 'error': message}

def is_ok(result):
    """Check if result is successful"""
    return result.get('ok', False)

def get_data(result):
    """Get data from result"""
    return result.get('data')

def get_error(result):
    """Get error from result"""
    return result.get('error')

def safe_read_file(filepath, encoding='utf-8'):
    """Safely read file with error handling"""
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            return f.read()
    except (FileNotFoundError, PermissionError, IOError, UnicodeDecodeError) as e:
        return None

def safe_write_file(filepath, content, encoding='utf-8'):
    """Safely write file with error handling"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True) if os.path.dirname(filepath) else None
        
        with open(filepath, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except (PermissionError, IOError) as e:
        return False

def resolve_project_path(path):
    """
    프로젝트 경로 해결 유틸리티
    상대 경로를 절대 경로로 변환하고 Path 객체로 반환
    
    Args:
        path: 파일 또는 디렉토리 경로 (str, Path)
    
    Returns:
        Path: 절대 경로 Path 객체
    """
    if isinstance(path, str):
        path = Path(path)
    
    # 절대 경로가 아니면 현재 작업 디렉토리 기준으로 변환
    if not path.is_absolute():
        path = Path.cwd() / path
    
    return path

def safe_get_data(result, *fallback_keys):
    """
    KeyError 방지 안전한 데이터 추출
    
    중첩된 data 구조와 다양한 API 응답 형식을 안전하게 처리합니다.
    
    Args:
        result: API 응답 딕셔너리
        *fallback_keys: 대체 키들 (data가 없을 경우 시도)
    
    Returns:
        추출된 데이터 또는 빈 리스트/딕셔너리
    """
    if isinstance(result, dict):
        if result.get('ok', False):
            data = result.get('data', {})
            # 중첩된 data 구조 처리 (list_directory 등)
            if isinstance(data, dict) and 'data' in data:
                return data['data']
            return data
        # 실패한 경우 fallback 키들 시도
        for key in fallback_keys:
            if key in result:
                return result[key]
    # 기본값 반환
    return [] if not result else result

def get_list_items(result):
    """
    list_directory 결과에서 안전하게 항목 추출
    
    items 또는 entries 키를 자동으로 찾아서 반환합니다.
    
    Args:
        result: list_directory API 응답
    
    Returns:
        파일/디렉토리 항목 리스트
    """
    data = safe_get_data(result)
    if isinstance(data, dict):
        # items와 entries 둘 다 확인
        return data.get('items', data.get('entries', []))
    # 이미 리스트인 경우 그대로 반환
    return data if isinstance(data, list) else []

def normalize_api_response(result):
    """
    API 응답을 표준 형식으로 정규화
    
    모든 API 응답을 {'ok': bool, 'data': Any, 'error': str} 형식으로 통일
    
    Args:
        result: 원본 API 응답
    
    Returns:
        정규화된 응답 딕셔너리
    """
    # 이미 표준 형식인 경우
    if isinstance(result, dict) and 'ok' in result:
        return result
    
    # 비표준 형식 변환
    if isinstance(result, dict):
        # 성공/실패 판단
        if 'error' in result or 'exception' in result:
            return {
                'ok': False,
                'data': None,
                'error': result.get('error') or result.get('exception', 'Unknown error')
            }
        # 데이터가 있는 경우
        if 'data' in result or 'items' in result or 'entries' in result:
            data = result.get('data') or result.get('items') or result.get('entries', result)
            return {'ok': True, 'data': data}
    
    # 기본 처리
    return {'ok': True, 'data': result}