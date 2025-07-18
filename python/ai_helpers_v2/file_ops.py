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
from .helper_result import FileResult

@track_execution
def read_file(filepath: str, encoding: str = 'utf-8') -> FileResult:
    """파일 읽기

    Returns:
        FileResult: 파일 내용과 메타데이터를 포함한 결과 객체
    """
    try:
        with open(filepath, 'r', encoding=encoding) as f:
            content = f.read()
        return FileResult(content=content, path=filepath, success=True)
    except Exception as e:
        return FileResult(content=None, path=filepath, success=False, 
                         error=str(e), error_type=type(e).__name__)

@track_execution
def write_file(filepath: str, content: str, encoding: str = 'utf-8') -> bool:
    """파일 쓰기 (원자적 저장으로 개선)"""
    try:
        # 디렉토리가 없으면 생성
        dir_path = os.path.dirname(filepath)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)

        # 임시 파일에 먼저 쓰기
        fd, tmp_path = tempfile.mkstemp(dir=dir_path if dir_path else None, text=True)
        try:
            with os.fdopen(fd, 'w', encoding=encoding) as f:
                f.write(content)
            # 원자적으로 교체
            shutil.move(tmp_path, filepath)
            return True
        except Exception:
            # 실패 시 임시 파일 정리
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
    except Exception:
        return False

@track_execution
def create_file(filepath: str, content: str = '', encoding: str = 'utf-8') -> bool:
    """파일 생성 (덮어쓰기)"""
    return write_file(filepath, content, encoding)

@track_execution
def append_to_file(filepath: str, content: str, encoding: str = 'utf-8') -> bool:
    """파일에 내용 추가"""
    try:
        with open(filepath, 'a', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception:
        return False

@track_execution
def file_exists(filepath: str) -> bool:
    """파일 존재 여부 확인"""
    return os.path.isfile(filepath)

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
def write_json(filepath: str, data: Any, indent: int = 2) -> bool:
    """JSON 파일 쓰기"""
    try:
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        return write_file(filepath, content)
    except Exception:
        return False
