"""
Workflow v3 파일 저장 시스템
원자적 쓰기, 백업, 버전 관리
통합 workflow.json 사용
"""
import json
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import logging

from python.utils.io_helpers import write_json
from python.path_utils import get_workflow_v3_dir
from .unified_storage import UnifiedWorkflowStorage

logger = logging.getLogger(__name__)


class WorkflowStorage:
    """워크플로우 데이터 저장 관리자 - 프로젝트별 독립 workflow.json 사용"""
    
    def __init__(self, project_name: str, base_dir: str = None):
        self.project_name = project_name
        # 싱글톤 제거 - 프로젝트마다 새 인스턴스 생성
        self.storage = UnifiedWorkflowStorage()
        
        # 호환성을 위한 속성들 (기존 코드가 참조할 수 있음)
        self.base_dir = Path(base_dir) if base_dir else get_workflow_v3_dir()
        self.main_file = self.storage.workflow_file  # 실제로는 통합 파일
        self.backup_dir = self.storage.backup_dir
        
        # 설정
        self.max_backups = self.storage.max_backups
        self.auto_backup_interval = self.storage.auto_backup_interval
        self.last_backup_time = None
        
    def save(self, data: Dict[str, Any], create_backup: bool = True) -> bool:
        """데이터 저장 (원자적 쓰기)
        
        Args:
            data: 저장할 데이터
            create_backup: 백업 생성 여부
            
        Returns:
            성공 여부
        """
        return self.storage.save_project_data(
            self.project_name, 
            data, 
            create_backup=create_backup
        )
    
    def load(self) -> Optional[Dict[str, Any]]:
        """데이터 로드
        
        Returns:
            로드된 데이터 또는 None
        """
        return self.storage.get_project_data(self.project_name)
    
    def exists(self) -> bool:
        """워크플로우 파일 존재 여부 확인"""
        return self.project_name in self.storage.list_projects()
    
    def delete(self) -> bool:
        """워크플로우 데이터 삭제"""
        return self.storage.delete_project(self.project_name)
    
    def create_backup(self, suffix: str = "") -> bool:
        """백업 생성
        
        Args:
            suffix: 백업 파일명 suffix (무시됨 - 통합 백업 사용)
            
        Returns:
            성공 여부
        """
        self.storage._create_backup()
        self.last_backup_time = datetime.now(timezone.utc)
        return True
    
    def list_backups(self) -> List[Path]:
        """백업 파일 목록 조회
        
        Returns:
            백업 파일 경로 리스트
        """
        return sorted(self.storage.backup_dir.glob("workflow_backup_*.json"))
    
    def restore_from_backup(self, backup_path: Path) -> bool:
        """백업에서 복구
        
        Args:
            backup_path: 백업 파일 경로
            
        Returns:
            성공 여부
            
        Note:
            현재는 전체 workflow.json 복구만 지원
            추후 프로젝트별 복구 구현 예정
        """
        try:
            # 백업 파일 읽기
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # 프로젝트 데이터 확인
            if self.project_name in backup_data.get("projects", {}):
                project_data = backup_data["projects"][self.project_name]
                return self.save(project_data)
            else:
                logger.error(f"Project {self.project_name} not found in backup")
                return False
                
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
            return False
    
    def get_file_info(self) -> Dict[str, Any]:
        """파일 정보 조회
        
        Returns:
            파일 정보 딕셔너리
        """
        file_path = self.storage.workflow_file
        
        if file_path.exists():
            stat = file_path.stat()
            return {
                "path": str(file_path),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "exists": True
            }
        else:
            return {
                "path": str(file_path),
                "size": 0,
                "modified": None,
                "exists": False
            }
    
    # === 클래스 메서드 (추가 기능) ===
    
    @classmethod
    def migrate_all_v3_files(cls) -> Dict[str, bool]:
        """모든 V3 파일을 통합 스토리지로 마이그레이션"""
        storage = cls._get_unified_storage()
        return storage.migrate_from_v3_files()
    
    @classmethod
    def get_all_projects(cls) -> List[str]:
        """모든 프로젝트 목록"""
        storage = cls._get_unified_storage()
        return storage.list_projects()
    
    @classmethod
    def get_statistics(cls) -> Dict[str, Any]:
        """전체 통계"""
        storage = cls._get_unified_storage()
        return storage.get_statistics()
    
    @classmethod
    def get_active_project(cls) -> Optional[str]:
        """현재 활성 프로젝트"""
        storage = cls._get_unified_storage()
        return storage.get_active_project()
    
    @classmethod
    def set_active_project(cls, project_name: str) -> bool:
        """활성 프로젝트 설정"""
        storage = cls._get_unified_storage()
        return storage.set_active_project(project_name)
