"""
JSON 파일 기반 저장소 - FileLock으로 동시성 문제 해결
"""
import json
import os
import time
import uuid
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)


class FileLock:
    """간단한 파일 기반 Lock 구현 (filelock 패키지 없이)"""
    def __init__(self, lock_path: str, timeout: float = 30.0):
        self.lock_path = Path(lock_path)
        self.timeout = timeout
        self._lock_file = None

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def acquire(self):
        """Lock 획득"""
        start_time = time.time()
        while True:
            try:
                # O_EXCL은 파일이 이미 존재하면 실패
                self._lock_file = os.open(str(self.lock_path), 
                                         os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                # PID 기록
                os.write(self._lock_file, str(os.getpid()).encode())
                break
            except FileExistsError:
                # Lock이 이미 있음
                if time.time() - start_time > self.timeout:
                    # 타임아웃 - stale lock 제거
                    try:
                        self.lock_path.unlink()
                        logger.warning(f"Removed stale lock: {self.lock_path}")
                    except:
                        pass
                    raise TimeoutError(f"Failed to acquire lock: {self.lock_path}")
                time.sleep(0.1)

    def release(self):
        """Lock 해제"""
        if self._lock_file is not None:
            try:
                os.close(self._lock_file)
                self.lock_path.unlink()
            except:
                pass
            self._lock_file = None


class JsonRepository:
    """
    JSON 파일 기반 저장소
    - FileLock으로 프로세스 간 동시성 제어
    - Atomic 파일 쓰기
    - 자동 백업
    """

    def __init__(self, base_path: str = '.ai-brain', 
                 filename: str = 'flows.json',
                 backup_enabled: bool = True,
                 backup_interval: int = 300):  # 5분
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

        self.data_path = self.base_path / filename
        self.lock_path = self.base_path / f"{filename}.lock"
        self.backup_path = self.base_path / 'backups'

        self.backup_enabled = backup_enabled
        self.backup_interval = backup_interval
        self._last_backup = 0

        # 스레드 로컬 Lock (같은 프로세스 내)
        self._local_lock = threading.RLock()

        if self.backup_enabled:
            self.backup_path.mkdir(exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """데이터 로드"""
        with self._local_lock:
            with FileLock(self.lock_path):
                if not self.data_path.exists():
                    return {}

                try:
                    with open(self.data_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    # 백업에서 복구 시도
                    return self._recover_from_backup()
                except Exception as e:
                    logger.error(f"Failed to load data: {e}")
                    return {}

    def save(self, data: Dict[str, Any]) -> bool:
        """데이터 저장 - Atomic 쓰기"""
        with self._local_lock:
            with FileLock(self.lock_path):
                try:
                    # 임시 파일에 쓰기
                    tmp_path = self.data_path.with_suffix(f'.{uuid.uuid4().hex}.tmp')
                    with open(tmp_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                    # Atomic 교체 (POSIX에서 원자적)
                    tmp_path.replace(self.data_path)

                    # 백업 체크
                    self._check_backup(data)

                    return True

                except Exception as e:
                    logger.error(f"Failed to save data: {e}")
                    # 임시 파일 정리
                    try:
                        if tmp_path.exists():
                            tmp_path.unlink()
                    except:
                        pass
                    return False

    def _check_backup(self, data: Dict[str, Any]):
        """백업 필요 여부 확인 및 수행"""
        if not self.backup_enabled:
            return

        current_time = time.time()
        if current_time - self._last_backup > self.backup_interval:
            self._create_backup(data)
            self._last_backup = current_time
            self._cleanup_old_backups()

    def _create_backup(self, data: Dict[str, Any]):
        """백업 생성"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_path / f"flows_{timestamp}.json"

            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Backup created: {backup_file}")

        except Exception as e:
            logger.error(f"Backup failed: {e}")

    def _cleanup_old_backups(self, keep_count: int = 10):
        """오래된 백업 정리"""
        try:
            backups = sorted(self.backup_path.glob('flows_*.json'))
            if len(backups) > keep_count:
                for backup in backups[:-keep_count]:
                    backup.unlink()
                    logger.info(f"Deleted old backup: {backup}")
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")

    def _recover_from_backup(self) -> Dict[str, Any]:
        """백업에서 복구"""
        if not self.backup_enabled:
            return {}

        try:
            backups = sorted(self.backup_path.glob('flows_*.json'), reverse=True)
            for backup in backups[:3]:  # 최근 3개 시도
                try:
                    with open(backup, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    logger.warning(f"Recovered from backup: {backup}")
                    return data
                except:
                    continue
        except Exception as e:
            logger.error(f"Recovery failed: {e}")

        return {}

    def exists(self) -> bool:
        """데이터 파일 존재 여부"""
        return self.data_path.exists()

    def get_info(self) -> Dict[str, Any]:
        """저장소 정보"""
        info = {
            'data_path': str(self.data_path),
            'exists': self.exists(),
            'size': 0,
            'modified': None,
            'backup_count': 0
        }

        if self.exists():
            stat = self.data_path.stat()
            info['size'] = stat.st_size
            info['modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()

        if self.backup_enabled and self.backup_path.exists():
            info['backup_count'] = len(list(self.backup_path.glob('flows_*.json')))

        return info
