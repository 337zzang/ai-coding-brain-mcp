# python/utils/io_helpers.py
"""
통합된 I/O 헬퍼 함수들 - 원자적 쓰기, 인코딩 안전, 동시성 보장
atomic_io.py와 io_helpers.py의 기능을 통합
"""
import os
import json
import tempfile
import logging
import shutil
import io
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union
from functools import wraps
from contextlib import contextmanager

try:
    import filelock
except ImportError:
    # filelock이 없는 경우 기본 파일 락 사용
    import threading

    class FileLock:
        """간단한 파일 락 구현 (filelock 대체)"""
        _locks = {}
        _lock_manager = threading.Lock()

        def __init__(self, lock_file: str):
            self.lock_file = lock_file
            with FileLock._lock_manager:
                if lock_file not in FileLock._locks:
                    FileLock._locks[lock_file] = threading.Lock()
                self.lock = FileLock._locks[lock_file]

        def __enter__(self):
            self.lock.acquire()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.lock.release()

    filelock = type('filelock', (), {'FileLock': FileLock})()

logger = logging.getLogger(__name__)

# 기본 인코딩
DEFAULT_ENCODING = os.getenv("PYTHONIOENCODING", "utf-8")

def open_text(path: Union[str, Path], mode: str = "r", encoding: str = None) -> io.TextIOWrapper:
    """텍스트 파일 열기 - 인코딩 자동 처리

    Args:
        path: 파일 경로
        mode: 열기 모드 (기본값: 'r')
        encoding: 인코딩 (기본값: None - 환경변수 사용)

    Returns:
        파일 객체
    """
    encoding = encoding or DEFAULT_ENCODING
    return open(path, mode, encoding=encoding, errors="replace")

def ensure_directory(path: Union[str, Path]) -> Path:
    """디렉토리 존재 보장"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def with_retry(max_attempts: int = 3, delay: float = 0.1):
    """재시도 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (2 ** attempt))  # 지수 백오프
                    else:
                        raise
            raise last_error
        return wrapper
    return decorator

@with_retry(max_attempts=3)
def atomic_write(filepath: Union[str, Path], data: Any, mode: str = 'auto') -> bool:
    """원자적 파일 쓰기 - 동시성 안전

    Args:
        filepath: 대상 파일 경로
        data: 저장할 데이터
        mode: 'json', 'text', 'binary', 'auto' (자동 감지)

    Returns:
        성공 여부
    """
    filepath = Path(filepath)
    lock = filelock.FileLock(str(filepath) + ".lock")

    # 모드 자동 감지
    if mode == 'auto':
        if isinstance(data, (dict, list)):
            mode = 'json'
        elif isinstance(data, (bytes, bytearray)):
            mode = 'binary'
        else:
            mode = 'text'

    with lock:
        try:
            # 디렉토리 생성
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # 임시 파일에 쓰기
            with tempfile.NamedTemporaryFile(
                mode='wb' if mode == 'binary' else 'w',
                dir=filepath.parent,
                delete=False,
                encoding=None if mode == 'binary' else DEFAULT_ENCODING
            ) as tmp:
                # 데이터 쓰기
                if mode == 'json':
                    json.dump(data, tmp, indent=2, ensure_ascii=False)
                elif mode == 'binary':
                    tmp.write(data if isinstance(data, bytes) else data.encode(DEFAULT_ENCODING))
                else:  # text
                    tmp.write(str(data))

                # 디스크에 확실히 쓰기
                tmp.flush()
                os.fsync(tmp.fileno())
                tmp_path = tmp.name

            # 원자적 교체
            if os.name == 'nt':  # Windows
                if filepath.exists():
                    filepath.unlink()
                os.rename(tmp_path, filepath)
            else:  # Unix-like
                os.replace(tmp_path, filepath)

            logger.debug(f"Successfully wrote to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to write to {filepath}: {e}")
            # 임시 파일 정리
            try:
                if 'tmp_path' in locals() and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except:
                pass
            raise

@with_retry(max_attempts=3)
def safe_read(filepath: Union[str, Path], mode: str = 'auto', default: Any = None) -> Any:
    """안전한 파일 읽기

    Args:
        filepath: 파일 경로
        mode: 'json', 'text', 'binary', 'auto' (자동 감지)
        default: 파일이 없거나 에러 시 반환할 기본값

    Returns:
        파일 내용 또는 기본값
    """
    filepath = Path(filepath)

    if not filepath.exists():
        return default

    # 모드 자동 감지
    if mode == 'auto':
        if filepath.suffix.lower() == '.json':
            mode = 'json'
        else:
            mode = 'text'

    try:
        if mode == 'json':
            with open_text(filepath, 'r') as f:
                return json.load(f)
        elif mode == 'binary':
            with open(filepath, 'rb') as f:
                return f.read()
        else:  # text
            with open_text(filepath, 'r') as f:
                return f.read()

    except Exception as e:
        logger.error(f"Failed to read {filepath}: {e}")
        return default

def read_json(path: Union[str, Path], default: Any = None) -> Any:
    """JSON 파일 읽기"""
    return safe_read(path, mode='json', default=default)

def write_json(path: Union[str, Path], data: Any, **kwargs) -> bool:
    """JSON 파일 쓰기"""
    return atomic_write(path, data, mode='json')

def backup_file(path: Union[str, Path], backup_dir: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """파일 백업

    Args:
        path: 백업할 파일 경로
        backup_dir: 백업 디렉토리 (None이면 같은 디렉토리에 .bak 추가)

    Returns:
        백업 파일 경로 또는 None
    """
    path = Path(path)

    if not path.exists():
        return None

    try:
        if backup_dir:
            backup_dir = ensure_directory(backup_dir)
            backup_path = backup_dir / f"{path.stem}_{int(time.time())}{path.suffix}"
        else:
            backup_path = path.with_suffix(path.suffix + '.bak')

        shutil.copy2(path, backup_path)
        logger.info(f"Backed up {path} to {backup_path}")
        return backup_path

    except Exception as e:
        logger.error(f"Failed to backup {path}: {e}")
        return None

@contextmanager
def temp_file(suffix: str = '', prefix: str = 'tmp', dir: Optional[Union[str, Path]] = None):
    """임시 파일 컨텍스트 매니저"""
    temp = tempfile.NamedTemporaryFile(
        suffix=suffix,
        prefix=prefix,
        dir=dir,
        delete=False
    )
    try:
        yield Path(temp.name)
    finally:
        try:
            temp.close()
            if os.path.exists(temp.name):
                os.unlink(temp.name)
        except:
            pass

# 호환성을 위한 별칭
safe_write = atomic_write
safe_json_read = read_json
safe_json_write = write_json
