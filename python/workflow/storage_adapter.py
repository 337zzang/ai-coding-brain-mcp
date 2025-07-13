"""
WorkflowStorage 어댑터 - 기존 API 호환성 유지하면서 통합 스토리지 사용
"""
from typing import Dict, Any, Optional
from .unified_storage import UnifiedWorkflowStorage


class WorkflowStorage:
    """기존 WorkflowStorage API를 유지하면서 통합 스토리지 사용"""
    
    # 전역 통합 스토리지 인스턴스
    _unified_storage = None
    
    @classmethod
    def _get_unified_storage(cls) -> UnifiedWorkflowStorage:
        """싱글톤 통합 스토리지 인스턴스"""
        if cls._unified_storage is None:
            cls._unified_storage = UnifiedWorkflowStorage()
        return cls._unified_storage
    
    def __init__(self, project_name: str, base_dir: str = None):
        """기존 API 호환성을 위한 초기화
        
        Args:
            project_name: 프로젝트 이름
            base_dir: (무시됨) 통합 스토리지는 단일 경로 사용
        """
        self.project_name = project_name
        self.storage = self._get_unified_storage()
        
        # 호환성을 위한 속성들
        self.main_file = self.storage.workflow_file  # 실제로는 통합 파일
        self.backup_dir = self.storage.backup_dir
        self.max_backups = self.storage.max_backups
        self.auto_backup_interval = self.storage.auto_backup_interval
        self.last_backup_time = None
    
    def save(self, data: Dict[str, Any], create_backup: bool = True) -> bool:
        """데이터 저장 (프로젝트별)
        
        Args:
            data: 저장할 데이터 (current_plan, events 등)
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
        """데이터 로드"""
        return self.storage.get_project_data(self.project_name)
    
    def exists(self) -> bool:
        """프로젝트 데이터 존재 여부"""
        return self.project_name in self.storage.list_projects()
    
    def delete(self) -> bool:
        """프로젝트 데이터 삭제"""
        return self.storage.delete_project(self.project_name)
    
    def create_backup(self, suffix: str = "") -> bool:
        """백업 생성 (통합 백업으로 위임)"""
        self.storage._create_backup()
        return True
    
    def list_backups(self) -> list:
        """백업 목록 (통합 백업)"""
        return sorted(self.storage.backup_dir.glob("workflow_backup_*.json"))
    
    def restore_from_backup(self, backup_path: str) -> bool:
        """백업에서 복구
        
        Note: 통합 스토리지에서는 전체 복구만 지원
        """
        # TODO: 프로젝트별 복구 구현 필요
        return False
    
    # === 추가 헬퍼 메서드 ===
    
    @classmethod
    def migrate_all_v3_files(cls) -> Dict[str, bool]:
        """모든 V3 파일을 통합 스토리지로 마이그레이션"""
        storage = cls._get_unified_storage()
        return storage.migrate_from_v3_files()
    
    @classmethod
    def get_all_projects(cls) -> list:
        """모든 프로젝트 목록"""
        storage = cls._get_unified_storage()
        return storage.list_projects()
    
    @classmethod
    def get_statistics(cls) -> Dict[str, Any]:
        """전체 통계"""
        storage = cls._get_unified_storage()
        return storage.get_statistics()
