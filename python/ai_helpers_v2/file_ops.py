"""
파일 작업 - 프로토콜 추적 포함
"""
import os
import json
import yaml
import tempfile
import shutil
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
    """파일 쓰기 (원자적 저장으로 개선)"""
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

    # 원자적 쓰기: 임시 파일 생성 후 이동
    with tempfile.NamedTemporaryFile('w', dir=dir_path, delete=False, encoding=encoding) as tmp:
        tmp.write(content)
        tmp.flush()
        os.fsync(tmp.fileno())  # 디스크에 강제 동기화

    # 원자적 이동
    shutil.move(tmp.name, abs_path)
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
def read_json(filepath: str) -> FileResult:
    """JSON 파일 읽기

    Returns:
        FileResult: 파싱된 JSON 데이터를 포함한 결과 객체
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return FileResult(content=data, path=filepath, success=True)
    except Exception as e:
        return FileResult(content=None, path=filepath, success=False,
                         error=str(e), error_type=type(e).__name__)
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
