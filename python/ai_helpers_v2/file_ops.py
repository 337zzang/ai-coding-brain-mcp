"""
파일 작업 - 프로토콜 추적 포함
"""
import os
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from .core import track_execution

@track_execution
def read_file(filepath: str, encoding: str = 'utf-8') -> str:
    """파일 읽기"""
    with open(filepath, 'r', encoding=encoding) as f:
        return f.read()

@track_execution
@track_execution
def write_file(filepath: str, content: str, encoding: str = 'utf-8') -> bool:
    """파일 쓰기 (경로 문제 수정됨)"""
    # 빈 경로 체크
    if not filepath:
        raise ValueError("파일 경로가 비어있습니다")

    # 절대 경로로 변환
    abs_path = os.path.abspath(filepath)

    # 디렉토리 경로 추출
    dir_path = os.path.dirname(abs_path)

    # 디렉토리가 있고 존재하지 않으면 생성
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

    # 파일 쓰기
    with open(abs_path, 'w', encoding=encoding) as f:
        f.write(content)
    return True
def create_file(filepath: str, content: str, encoding: str = 'utf-8') -> bool:
    """파일 생성 (write_file과 동일)"""
    return write_file(filepath, content, encoding)

@track_execution
def append_to_file(filepath: str, content: str, encoding: str = 'utf-8') -> bool:
    """파일에 내용 추가"""
    with open(filepath, 'a', encoding=encoding) as f:
        f.write(content)
    return True

@track_execution
def file_exists(filepath: str) -> bool:
    """파일 존재 여부 확인"""
    return os.path.exists(filepath) and os.path.isfile(filepath)

@track_execution
def read_json(filepath: str) -> Dict[str, Any]:
    """JSON 파일 읽기"""
    content = read_file(filepath)
    return json.loads(content)

@track_execution
def write_json(filepath: str, data: Dict[str, Any], indent: int = 2) -> bool:
    """JSON 파일 쓰기"""
    content = json.dumps(data, indent=indent, ensure_ascii=False)
    return write_file(filepath, content)

# 사용 가능한 함수 목록
__all__ = [
    'read_file', 'write_file', 'create_file', 
    'append_to_file', 'file_exists',
    'read_json', 'write_json'
]
