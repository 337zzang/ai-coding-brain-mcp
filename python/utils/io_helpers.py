# python/utils/io_helpers.py
"""
I/O 헬퍼 함수들 - 인코딩 안전한 파일 작업
"""
from pathlib import Path
from tempfile import NamedTemporaryFile
import json, os, shutil, io, contextlib
import filelock

DEFAULT_ENCODING = os.getenv("PYTHONIOENCODING", "utf-8")

def open_text(path: str | Path, mode: str = "r", enc: str | None = None) -> io.TextIOWrapper:
    """텍스트 파일 열기 - 인코딩 자동 처리
    
    Args:
        path: 파일 경로
        mode: 열기 모드 (기본값: 'r')
        enc: 인코딩 (기본값: None - 환경변수 사용)
    
    Returns:
        파일 객체
    """
    enc = enc or DEFAULT_ENCODING
    return open(path, mode, encoding=enc, errors="replace")

def atomic_write(data: str | bytes, path: Path):
    """원자적 파일 쓰기 - 동시성 안전
    
    임시 파일에 쓴 후 원본을 대체하여 파일 손상 방지
    filelock으로 동시 쓰기 충돌 방지
    
    Args:
        data: 쓸 데이터 (str 또는 bytes)
        path: 대상 파일 경로
    """
    path = Path(path)
    lock = filelock.FileLock(str(path) + ".lock")
    
    with lock:
        with NamedTemporaryFile("wb", delete=False, dir=path.parent) as tmp:
            # 데이터 쓰기
            if isinstance(data, (bytes, bytearray)):
                tmp.write(data)
            else:
                tmp.write(data.encode(DEFAULT_ENCODING))
            
            # 디스크에 확실히 쓰기
            tmp.flush()
            os.fsync(tmp.fileno())
        
        # 원자적으로 교체
        shutil.move(tmp.name, path)

def read_json(path: Path):
    """JSON 파일 안전하게 읽기"""
    with open_text(path) as f:
        return json.load(f)

def write_json(data: dict, path: Path, indent: int = 2):
    """JSON 파일 원자적으로 쓰기"""
    json_str = json.dumps(data, ensure_ascii=False, indent=indent)
    atomic_write(json_str, path)

def read_text_safe(path, encoding=None):
    """안전한 텍스트 파일 읽기 (기존 호환성 유지)"""
    with open_text(path, 'r', encoding) as f:
        return f.read()

def write_text_safe(path, content, encoding=None):
    """안전한 텍스트 파일 쓰기 (기존 호환성 유지)"""
    if encoding is None:
        encoding = DEFAULT_ENCODING
    atomic_write(content if isinstance(content, bytes) else content.encode(encoding), Path(path))
