"""
워크플로우 V3 Storage - 프로젝트별 독립 저장소
각 프로젝트의 memory 폴더에 직접 저장
"""
import json
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import logging
from threading import Lock

from python.utils.io_helpers import write_json, read_json, read_json

logger = logging.getLogger(__name__)


class WorkflowStorage:
    """프로젝트별 독립 워크플로우 저장소 - memory 폴더 직접 사용"""

    def __init__(self, project_name: str = None, base_dir: str = None):
        self.project_name = project_name

        # 현재 작업 디렉토리 = 프로젝트 루트
        self.project_root = Path.cwd()

        # memory 디렉토리 (프로젝트 루트 바로 아래)
        self.base_dir = self.project_root / "memory"
        self.base_dir.mkdir(exist_ok=True)

        # 파일 경로 (memory 바로 아래)
        self.main_file = self.base_dir / "workflow.json"
        self.backup_dir = self.base_dir / "backups"
        self.cache_dir = self.base_dir / "cache"

        # 디렉토리 생성
        self.backup_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)

        # 스레드 안전성을 위한 락
        self._lock = Lock()

        # 설정
        self.max_backups = 20
        self.auto_backup_interval = 3600
        self.last_backup_time = None

        # 초기화
        self._ensure_file_exists()

    def save(self, data: Dict[str, Any], create_backup: bool = True) -> bool:
        """데이터 저장 (원자적 쓰기)"""
        with self._lock:
            try:
                # 백업 생성
                if create_backup and self.main_file.exists():
                    self._create_backup()

                # 메타데이터 업데이트
                if "metadata" not in data:
                    data["metadata"] = {}

                data["metadata"].update({
                    "last_modified": datetime.now(timezone.utc).isoformat(),
                    "project_name": self.project_name,
                    "project_root": str(self.project_root),
                    "version": "3.0"
                })

                # 프로젝트 이름도 최상위에 저장
                data["project_name"] = self.project_name

                # 원자적 쓰기
                temp_file = self.main_file.with_suffix(".tmp")
                write_json(data, temp_file)
                temp_file.replace(self.main_file)

                logger.info(f"Workflow saved: {self.main_file}")
                return True

            except Exception as e:
                logger.error(f"Failed to save workflow: {e}")
                if "temp_file" in locals() and temp_file.exists():
                    temp_file.unlink()
                return False

    def load(self) -> Optional[Dict[str, Any]]:
        """데이터 로드"""
        with self._lock:
            if self.main_file.exists():
                try:
                    data = read_json(self.main_file)
                    logger.info(f"Workflow loaded: {self.main_file}")
                    return data
                except Exception as e:
                    logger.error(f"Failed to load workflow: {e}")
                    return None
            return None

    def exists(self) -> bool:
        """워크플로우 파일 존재 여부"""
        return self.main_file.exists()

    def delete(self) -> bool:
        """워크플로우 데이터 삭제"""
        try:
            if self.main_file.exists():
                # 삭제 전 백업
                self._create_backup(suffix="_before_delete")
                self.main_file.unlink()

            logger.info(f"Workflow deleted for project: {self.project_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete workflow: {e}")
            return False

    def _create_backup(self, suffix: str = "") -> bool:
        """백업 생성"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"workflow_backup_{timestamp}{suffix}.json"
            backup_path = self.backup_dir / backup_name

            shutil.copy2(self.main_file, backup_path)
            self.last_backup_time = datetime.now(timezone.utc)

            # 오래된 백업 정리
            self._cleanup_old_backups()

            logger.info(f"Backup created: {backup_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False

    def _cleanup_old_backups(self):
        """오래된 백업 파일 정리"""
        try:
            backups = sorted(self.backup_dir.glob("workflow_backup_*.json"))

            if len(backups) > self.max_backups:
                for old_backup in backups[:-self.max_backups]:
                    old_backup.unlink()
                    logger.info(f"Old backup removed: {old_backup.name}")

        except Exception as e:
            logger.error(f"Failed to cleanup backups: {e}")

    def _ensure_file_exists(self):
        """워크플로우 파일이 없으면 생성"""
        if not self.main_file.exists():
            default_data = {
                "version": "3.0",
                "project_name": self.project_name,
                "current_plan": None,
                "events": [],
                "metadata": {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "project_root": str(self.project_root)
                }
            }
            self.save(default_data, create_backup=False)

    def list_backups(self) -> List[Path]:
        """백업 파일 목록"""
        return sorted(self.backup_dir.glob("workflow_backup_*.json"))

    def restore_from_backup(self, backup_path: Path) -> bool:
        """백업에서 복구"""
        try:
            # 백업 파일 읽기
            with open(backup_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)

            # 현재 파일 백업
            if self.main_file.exists():
                self._create_backup(suffix="_before_restore")

            # 복구
            return self.save(backup_data, create_backup=False)

        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return False

    def get_file_info(self) -> Dict[str, Any]:
        """파일 정보"""
        if self.main_file.exists():
            stat = self.main_file.stat()
            return {
                "path": str(self.main_file),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "exists": True
            }
        else:
            return {
                "path": str(self.main_file),
                "exists": False
            }

    def get_statistics(self) -> Dict[str, Any]:
        """통계 정보"""
        stats = {
            "project_name": self.project_name,
            "project_root": str(self.project_root),
            "backup_count": len(list(self.backup_dir.glob("*.json"))),
            "cache_files": len(list(self.cache_dir.glob("*.json")))
        }

        if self.main_file.exists():
            stat = self.main_file.stat()
            stats["workflow_size"] = stat.st_size
            stats["last_modified"] = datetime.fromtimestamp(
                stat.st_mtime, timezone.utc
            ).isoformat()

        return stats

    # 기존 UnifiedWorkflowStorage와의 호환성을 위한 메서드들
    def get_project_data(self, project_name: str) -> Optional[Dict[str, Any]]:
        """프로젝트 데이터 반환 (호환성)"""
        if project_name == self.project_name:
            return self.load()
        return None

    def save_project_data(self, project_name: str, data: Dict[str, Any], 
                         create_backup: bool = True) -> bool:
        """프로젝트 데이터 저장 (호환성)"""
        if project_name == self.project_name:
            return self.save(data, create_backup)
        return False

    def get_active_project(self) -> str:
        """활성 프로젝트 반환 (호환성)"""
        return self.project_name

    def set_active_project(self, project_name: str) -> bool:
        """활성 프로젝트 설정 (호환성)"""
        return project_name == self.project_name

    def list_projects(self) -> List[str]:
        """프로젝트 목록 (호환성)"""
        return [self.project_name]

    def delete_project(self, project_name: str) -> bool:
        """프로젝트 삭제 (호환성)"""
        if project_name == self.project_name:
            return self.delete()
        return False


# 기존 UnifiedWorkflowStorage 대신 사용할 별칭
UnifiedWorkflowStorage = WorkflowStorage
