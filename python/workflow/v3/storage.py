"""
Workflow v3 파일 저장 시스템
원자적 쓰기, 백업, 버전 관리
"""
import json
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import logging

from python.atomic_io import atomic_write

logger = logging.getLogger(__name__)


class WorkflowStorage:
    """워크플로우 데이터 저장 관리자"""
    
    def __init__(self, project_name: str, base_dir: str = "memory/workflow_v3"):
        self.project_name = project_name
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일 경로들 - 각 프로젝트별 독립적인 파일
        self.main_file = self.base_dir / f"{project_name}_workflow.json"
        self.backup_dir = self.base_dir / "backups" / project_name
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 설정
        self.max_backups = 10  # 최대 백업 파일 수
        self.auto_backup_interval = 3600  # 1시간마다 자동 백업
        self.last_backup_time = None
        
    def save(self, data: Dict[str, Any], create_backup: bool = True) -> bool:
        """데이터 저장 (원자적 쓰기)
        
        Args:
            data: 저장할 데이터
            create_backup: 백업 생성 여부
            
        Returns:
            성공 여부
        """
        try:
            # 백업 생성 (필요시)
            if create_backup and self.main_file.exists():
                self._create_backup()
                
            # JSON 직렬화
            json_data = json.dumps(data, indent=2, ensure_ascii=False)

            # 원자적 쓰기 (text 모드로 저장)
            atomic_write(str(self.main_file), json_data, mode='text')
            
            logger.info(f"Saved workflow data for {self.project_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save workflow data: {e}")
            return False

            
    def load(self) -> Optional[Dict[str, Any]]:
        """데이터 로드
        
        Returns:
            로드된 데이터 또는 None
        """
        if not self.main_file.exists():
            logger.info(f"No workflow file found for {self.project_name}")
            return None
            
        try:
            with open(self.main_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            logger.info(f"Loaded workflow data for {self.project_name}")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in workflow file: {e}")
            # 손상된 파일은 백업으로 이동
            self._move_corrupted_file()
            return None
            
        except Exception as e:
            logger.error(f"Failed to load workflow data: {e}")
            return None
            
    def _create_backup(self) -> Optional[Path]:
        """백업 파일 생성
        
        Returns:
            백업 파일 경로 또는 None
        """
        try:
            # 타임스탬프 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"{self.project_name}_backup_{timestamp}.json"
            
            # 파일 복사
            shutil.copy2(self.main_file, backup_file)
            
            logger.info(f"Created backup: {backup_file.name}")
            
            # 오래된 백업 정리
            self._cleanup_old_backups()
            
            self.last_backup_time = datetime.now(timezone.utc)
            return backup_file
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

            
    def _cleanup_old_backups(self) -> None:
        """오래된 백업 파일 정리"""
        try:
            # 백업 파일 목록 가져오기
            backup_files = sorted(
                self.backup_dir.glob(f"{self.project_name}_backup_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            # 최대 개수 초과분 삭제
            if len(backup_files) > self.max_backups:
                for old_backup in backup_files[self.max_backups:]:
                    old_backup.unlink()
                    logger.info(f"Deleted old backup: {old_backup.name}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup backups: {e}")
            
    def _move_corrupted_file(self) -> None:
        """손상된 파일을 백업 디렉토리로 이동"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            corrupted_file = self.backup_dir / f"{self.project_name}_corrupted_{timestamp}.json"
            
            shutil.move(str(self.main_file), str(corrupted_file))
            logger.warning(f"Moved corrupted file to: {corrupted_file.name}")
            
        except Exception as e:
            logger.error(f"Failed to move corrupted file: {e}")
            
    def get_backups(self) -> List[Dict[str, Any]]:
        """백업 파일 목록 조회
        
        Returns:
            백업 파일 정보 목록
        """
        backups = []
        
        try:
            backup_files = sorted(
                self.backup_dir.glob(f"{self.project_name}_backup_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            for backup_file in backup_files:
                stat = backup_file.stat()
                backups.append({
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'age_hours': (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).total_seconds() / 3600
                })
                
        except Exception as e:
            logger.error(f"Failed to get backups: {e}")
            
        return backups

            
    def restore_backup(self, backup_filename: str) -> bool:
        """백업 파일 복원
        
        Args:
            backup_filename: 백업 파일명
            
        Returns:
            성공 여부
        """
        backup_path = self.backup_dir / backup_filename
        
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_filename}")
            return False
            
        try:
            # 현재 파일 백업 (있는 경우)
            if self.main_file.exists():
                self._create_backup()
                
            # 백업 파일 복원
            shutil.copy2(backup_path, self.main_file)
            
            logger.info(f"Restored backup: {backup_filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
            
    def should_auto_backup(self) -> bool:
        """자동 백업이 필요한지 확인
        
        Returns:
            백업 필요 여부
        """
        if not self.last_backup_time:
            return True
            
        elapsed = (datetime.now(timezone.utc) - self.last_backup_time).total_seconds()
        return elapsed >= self.auto_backup_interval
        
    def export_to_file(self, data: Dict[str, Any], export_path: str) -> bool:
        """데이터를 특정 파일로 내보내기
        
        Args:
            data: 내보낼 데이터
            export_path: 내보낼 파일 경로
            
        Returns:
            성공 여부
        """
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            json_data = json.dumps(data, indent=2, ensure_ascii=False)
            atomic_write(str(export_file), json_data)
            
            logger.info(f"Exported data to: {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export data: {e}")
            return False
            
    def get_storage_info(self) -> Dict[str, Any]:
        """저장소 정보 조회
        
        Returns:
            저장소 상태 정보
        """
        info = {
            'project_name': self.project_name,
            'main_file': str(self.main_file),
            'file_exists': self.main_file.exists(),
            'file_size': 0,
            'backup_count': 0,
            'total_backup_size': 0,
            'last_backup': None
        }
        
        try:
            # 메인 파일 정보
            if self.main_file.exists():
                info['file_size'] = self.main_file.stat().st_size
                
            # 백업 정보
            backups = self.get_backups()
            info['backup_count'] = len(backups)
            info['total_backup_size'] = sum(b['size'] for b in backups)
            
            if backups:
                info['last_backup'] = backups[0]['modified']
                
        except Exception as e:
            logger.error(f"Failed to get storage info: {e}")
            
        return info
