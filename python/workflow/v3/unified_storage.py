"""
통합 Workflow Storage - 단일 workflow.json으로 모든 프로젝트 관리
"""
import json
import os
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import logging
from threading import Lock

from python.utils.io_helpers import write_json, read_json
from python.path_utils import get_memory_path, get_project_root

logger = logging.getLogger(__name__)


class UnifiedWorkflowStorage:
    """통합 워크플로우 저장 관리자 - 단일 workflow.json 파일 사용"""
    
    def __init__(self):
        # 현재 작업 디렉토리의 memory 사용 (분산형)
        current_project_path = Path.cwd()
        memory_dir = current_project_path / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        
        # 새로운 구조 우선 확인
        active_workflow = memory_dir / "active" / "workflow.json"
        if active_workflow.exists():
            self.workflow_file = active_workflow
        else:
            # active 디렉토리 생성 후 workflow.json 생성
            active_dir = memory_dir / "active"
            active_dir.mkdir(parents=True, exist_ok=True)
            self.workflow_file = active_dir / "workflow.json"
            
        self.backup_dir = memory_dir / "workflow_backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 스레드 안전성을 위한 락
        self._lock = Lock()
        
        # 설정
        self.max_backups = 20  # 백업 파일 최대 개수
        self.auto_backup_interval = 3600  # 1시간마다 자동 백업
        
        # 초기화
        self._ensure_file_exists()
        
    def _ensure_file_exists(self):
        """workflow.json 파일이 없으면 생성"""
        if not self.workflow_file.exists():
            initial_data = {
                "version": "3.0",
                "projects": {},
                "active_project": None,
                "metadata": {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "last_modified": datetime.now(timezone.utc).isoformat()
                }
            }
            self._write_file(initial_data)
            logger.info("Created new workflow.json")
    
    def _read_file(self) -> Dict[str, Any]:
        """파일 읽기 (에러 처리 포함)"""
        try:
            with open(self.workflow_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Failed to read workflow.json: {e}")
            # 백업에서 복구 시도
            return self._recover_from_backup() or {
                "version": "3.0",
                "projects": {},
                "active_project": None,
                "metadata": {}
            }
    
    def _write_file(self, data: Dict[str, Any]) -> bool:
        """파일 쓰기 (원자적 쓰기)"""
        try:
            # 메타데이터 업데이트
            data["metadata"]["last_modified"] = datetime.now(timezone.utc).isoformat()
            
            # JSON 쓰기
            write_json(data, self.workflow_file)
            return True
        except Exception as e:
            logger.error(f"Failed to write workflow.json: {e}")
            return False
    
    def _create_backup(self):
        """현재 파일 백업"""
        if not self.workflow_file.exists():
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"workflow_backup_{timestamp}.json"
        
        try:
            shutil.copy2(self.workflow_file, backup_file)
            logger.info(f"Created backup: {backup_file.name}")
            
            # 오래된 백업 삭제
            self._cleanup_old_backups()
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
    
    def _cleanup_old_backups(self):
        """오래된 백업 파일 삭제"""
        backups = sorted(self.backup_dir.glob("workflow_backup_*.json"))
        if len(backups) > self.max_backups:
            for backup in backups[:-self.max_backups]:
                backup.unlink()
                logger.info(f"Deleted old backup: {backup.name}")
    
    def _recover_from_backup(self) -> Optional[Dict[str, Any]]:
        """최신 백업에서 복구"""
        backups = sorted(self.backup_dir.glob("workflow_backup_*.json"), reverse=True)
        
        for backup in backups[:3]:  # 최근 3개 백업 시도
            try:
                with open(backup, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"Recovered from backup: {backup.name}")
                return data
            except:
                continue
        
        return None
    
    # === 프로젝트별 데이터 관리 ===
    
    def get_project_data(self, project_name: str) -> Optional[Dict[str, Any]]:
        """특정 프로젝트의 데이터 가져오기"""
        with self._lock:
            data = self._read_file()
            return data.get("projects", {}).get(project_name)
    
    def save_project_data(self, project_name: str, project_data: Dict[str, Any], 
                         create_backup: bool = True) -> bool:
        """특정 프로젝트의 데이터 저장"""
        with self._lock:
            if create_backup:
                self._create_backup()
            
            # 전체 데이터 읽기
            data = self._read_file()
            
            # 프로젝트 데이터 업데이트
            if "projects" not in data:
                data["projects"] = {}
            
            # 타임스탬프 추가
            project_data["last_updated"] = datetime.now(timezone.utc).isoformat()
            data["projects"][project_name] = project_data
            
            # 활성 프로젝트 설정
            data["active_project"] = project_name
            
            # 저장
            return self._write_file(data)
    
    def delete_project(self, project_name: str) -> bool:
        """프로젝트 삭제"""
        with self._lock:
            data = self._read_file()
            
            if project_name in data.get("projects", {}):
                self._create_backup()  # 삭제 전 백업
                
                del data["projects"][project_name]
                
                # 활성 프로젝트가 삭제된 경우
                if data.get("active_project") == project_name:
                    data["active_project"] = None
                
                return self._write_file(data)
            
            return False
    
    def list_projects(self) -> List[str]:
        """모든 프로젝트 목록"""
        with self._lock:
            data = self._read_file()
            return list(data.get("projects", {}).keys())
    
    def get_active_project(self) -> Optional[str]:
        """현재 활성 프로젝트"""
        with self._lock:
            data = self._read_file()
            return data.get("active_project")
    
    def set_active_project(self, project_name: str) -> bool:
        """활성 프로젝트 설정"""
        with self._lock:
            data = self._read_file()
            
            if project_name in data.get("projects", {}):
                data["active_project"] = project_name
                return self._write_file(data)
            
            return False
    
    # === 마이그레이션 지원 ===
    
    def migrate_from_v3_files(self) -> Dict[str, bool]:
        """기존 V3 파일들을 통합 workflow.json으로 마이그레이션"""
        results = {}
        memory_dir = os.path.dirname(get_memory_path("dummy"))
        # v3_dir 대신 active 디렉토리의 기존 파일들 확인
        v3_dir = Path(memory_dir) / "workflow_v3"
        active_dir = Path(memory_dir) / "active"
        
        # workflow_v3가 있으면 마이그레이션, 없으면 active 디렉토리 사용
        if v3_dir.exists():
            migrate_dir = v3_dir
        elif active_dir.exists():
            migrate_dir = active_dir
        else:
            return results
        
        with self._lock:
            self._create_backup()  # 마이그레이션 전 백업
            data = self._read_file()
            
            # V3 파일들 탐색
            for file in v3_dir.glob("*_workflow.json"):
                if file.name.startswith("default_"):
                    continue
                    
                project_name = file.stem.replace("_workflow", "")
                
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        v3_data = json.load(f)
                    
                    # 프로젝트 데이터로 변환
                    project_data = {
                        "current_plan": v3_data.get("current_plan"),
                        "events": v3_data.get("events", []),
                        "version": v3_data.get("version", "3.0.0"),
                        "metadata": v3_data.get("metadata", {}),
                        "migrated_from": str(file),
                        "migrated_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    # 저장
                    data["projects"][project_name] = project_data
                    results[project_name] = True
                    logger.info(f"Migrated {project_name} from {file}")
                    
                except Exception as e:
                    logger.error(f"Failed to migrate {file}: {e}")
                    results[project_name] = False
            
            # 통합 파일 저장
            if results:
                self._write_file(data)
                
        return results
    
    # === 통계 및 정보 ===
    
    def get_statistics(self) -> Dict[str, Any]:
        """전체 워크플로우 통계"""
        with self._lock:
            data = self._read_file()
            projects = data.get("projects", {})
            
            stats = {
                "total_projects": len(projects),
                "active_project": data.get("active_project"),
                "total_events": sum(len(p.get("events", [])) for p in projects.values()),
                "projects": {}
            }
            
            for name, project in projects.items():
                plan = project.get("current_plan", {})
                tasks = plan.get("tasks", [])
                completed = sum(1 for t in tasks if t.get("status") == "completed")
                
                stats["projects"][name] = {
                    "plan_name": plan.get("name", "No active plan"),
                    "total_tasks": len(tasks),
                    "completed_tasks": completed,
                    "progress": (completed / len(tasks) * 100) if tasks else 0,
                    "events": len(project.get("events", [])),
                    "last_updated": project.get("last_updated", "Unknown")
                }
            
            return stats
