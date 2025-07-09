"""
Workflow v3 마이그레이션 도구
v2 데이터를 v3 구조로 전환
"""
import json
import os
import shutil
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import logging

from .models import (
    WorkflowPlan, Task, WorkflowState, WorkflowEvent,
    TaskStatus, PlanStatus, EventType
)
from .events import EventBuilder
from .storage import WorkflowStorage
from .errors import WorkflowError, ErrorCode, ErrorMessages

logger = logging.getLogger(__name__)


class WorkflowMigrator:
    """v2에서 v3로 워크플로우 데이터 마이그레이션"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
        self.v2_base_dir = Path("memory/workflow_v2")
        self.v2_file = self.v2_base_dir / f"{project_name}_workflow.json"
        self.v2_legacy_file = Path("memory/workflow_v2.json")
        
        self.storage = WorkflowStorage(project_name)
        self.migration_log = []
        
    def check_migration_needed(self) -> Tuple[bool, str]:
        """마이그레이션 필요 여부 확인
        
        Returns:
            (필요 여부, 이유)
        """
        # v3 파일이 이미 있는지 확인
        if self.storage.main_file.exists():
            return False, "v3 파일이 이미 존재합니다"
            
        # v2 파일 확인
        if self.v2_file.exists():
            return True, f"v2 파일 발견: {self.v2_file}"
            
        if self.v2_legacy_file.exists():
            return True, f"레거시 v2 파일 발견: {self.v2_legacy_file}"
            
        return False, "마이그레이션할 v2 데이터가 없습니다"
        
    def migrate(self, force: bool = False) -> Dict[str, Any]:
        """v2 데이터를 v3로 마이그레이션
        
        Args:
            force: 기존 v3 파일이 있어도 강제 마이그레이션
            
        Returns:
            마이그레이션 결과
        """
        try:
            # 마이그레이션 필요 여부 확인
            needed, reason = self.check_migration_needed()
            if not needed and not force:
                return {
                    'success': False,
                    'reason': reason,
                    'migrated': False
                }
                
            # v2 데이터 로드
            v2_data = self._load_v2_data()
            if not v2_data:
                return {
                    'success': False,
                    'reason': "v2 데이터를 로드할 수 없습니다",
                    'migrated': False
                }
                
            # 백업 생성
            if self.storage.main_file.exists():
                self._backup_existing_v3()
                
            # v3 상태 생성
            v3_state = self._convert_to_v3(v2_data)
            
            # 저장
            success = self.storage.save(v3_state.to_dict())
            
            if success:
                self._log("마이그레이션 완료")
                self._save_migration_log()
                
            return {
                'success': success,
                'migrated': True,
                'log': self.migration_log,
                'stats': self._get_migration_stats(v3_state)
            }
            
        except Exception as e:
            logger.exception("Migration failed")
            return {
                'success': False,
                'error': str(e),
                'migrated': False,
                'log': self.migration_log
            }

            
    def _load_v2_data(self) -> Optional[Dict[str, Any]]:
        """v2 데이터 로드"""
        # 프로젝트별 v2 파일 우선
        if self.v2_file.exists():
            try:
                with open(self.v2_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._log(f"v2 데이터 로드: {self.v2_file}")
                return data
            except Exception as e:
                self._log(f"v2 파일 로드 실패: {e}", level='error')
                
        # 레거시 v2 파일 확인
        if self.v2_legacy_file.exists():
            try:
                with open(self.v2_legacy_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # 프로젝트별 데이터 추출
                if self.project_name in data:
                    self._log(f"레거시 v2 데이터에서 프로젝트 추출: {self.project_name}")
                    return data[self.project_name]
                    
            except Exception as e:
                self._log(f"레거시 v2 파일 로드 실패: {e}", level='error')
                
        return None
        
    def _backup_existing_v3(self) -> None:
        """기존 v3 파일 백업"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"pre_migration_backup_{timestamp}.json"
            backup_path = self.storage.backup_dir / backup_name
            
            shutil.copy2(self.storage.main_file, backup_path)
            self._log(f"기존 v3 파일 백업: {backup_name}")
            
        except Exception as e:
            self._log(f"백업 실패: {e}", level='error')
            
    def _convert_to_v3(self, v2_data: Dict[str, Any]) -> WorkflowState:
        """v2 데이터를 v3 구조로 변환"""
        v3_state = WorkflowState()
        events = []
        
        # 현재 플랜 변환
        if 'current_plan' in v2_data and v2_data['current_plan']:
            v2_plan = v2_data['current_plan']
            v3_plan = self._convert_plan(v2_plan)
            v3_state.current_plan = v3_plan
            
            # 플랜 생성 이벤트 추가
            events.append(EventBuilder.plan_created(v3_plan))
            if v3_plan.status == PlanStatus.ACTIVE:
                events.append(EventBuilder.plan_started(v3_plan))
                
            # 태스크 이벤트 추가
            for task in v3_plan.tasks:
                events.append(EventBuilder.task_added(v3_plan.id, task))
                if task.status == TaskStatus.COMPLETED:
                    events.append(EventBuilder.task_completed(v3_plan.id, task))
                    
            self._log(f"현재 플랜 변환: {v3_plan.name}")
            
        # 히스토리 변환 (이벤트로)
        if 'history' in v2_data:
            for v2_hist_plan in v2_data['history']:
                hist_events = self._create_history_events(v2_hist_plan)
                events.extend(hist_events)
                
            self._log(f"히스토리 플랜 {len(v2_data['history'])}개 변환")
            
        # 이벤트 정렬 (시간순)
        events.sort(key=lambda e: e.timestamp)
        v3_state.events = events
        
        self._log(f"총 {len(events)}개 이벤트 생성")
        
        return v3_state

            
    def _convert_plan(self, v2_plan: Dict[str, Any]) -> WorkflowPlan:
        """v2 플랜을 v3 플랜으로 변환"""
        # 기본 필드 매핑
        v3_plan = WorkflowPlan(
            id=v2_plan.get('id', str(uuid.uuid4())),
            name=v2_plan.get('name', 'Untitled Plan'),
            description=v2_plan.get('description', ''),
            status=PlanStatus(v2_plan.get('status', 'active'))
        )
        
        # 타임스탬프 변환
        if 'created_at' in v2_plan:
            v3_plan.created_at = self._parse_timestamp(v2_plan['created_at'])
        if 'updated_at' in v2_plan:
            v3_plan.updated_at = self._parse_timestamp(v2_plan['updated_at'])
            
        # 태스크 변환
        v2_tasks = v2_plan.get('tasks', [])
        v3_plan.tasks = [self._convert_task(t) for t in v2_tasks]
        
        # 통계 업데이트
        v3_plan._update_stats()
        
        return v3_plan
        
    def _convert_task(self, v2_task: Dict[str, Any]) -> Task:
        """v2 태스크를 v3 태스크로 변환"""
        v3_task = Task(
            id=v2_task.get('id', str(uuid.uuid4())),
            title=v2_task.get('title', 'Untitled Task'),
            description=v2_task.get('description', ''),
            status=TaskStatus(v2_task.get('status', 'todo'))
        )
        
        # 타임스탬프 변환
        if 'created_at' in v2_task:
            v3_task.created_at = self._parse_timestamp(v2_task['created_at'])
        if 'updated_at' in v2_task:
            v3_task.updated_at = self._parse_timestamp(v2_task['updated_at'])
        if 'completed_at' in v2_task and v2_task['completed_at']:
            v3_task.completed_at = self._parse_timestamp(v2_task['completed_at'])
            
        # 노트와 출력 복사
        v3_task.notes = v2_task.get('notes', [])
        v3_task.outputs = v2_task.get('outputs', {})
        
        return v3_task
        
    def _create_history_events(self, v2_plan: Dict[str, Any]) -> List[WorkflowEvent]:
        """히스토리 플랜에서 이벤트 생성"""
        events = []
        plan_id = v2_plan.get('id', str(uuid.uuid4()))
        
        # 플랜 생성 이벤트
        created_at = self._parse_timestamp(v2_plan.get('created_at', datetime.now().isoformat()))
        events.append(WorkflowEvent(
            type=EventType.PLAN_CREATED,
            timestamp=created_at,
            plan_id=plan_id,
            details={
                'name': v2_plan.get('name', 'Unknown'),
                'description': v2_plan.get('description', '')
            }
        ))
        
        # 플랜 아카이브 이벤트
        archived_at = self._parse_timestamp(v2_plan.get('updated_at', created_at.isoformat()))
        events.append(WorkflowEvent(
            type=EventType.PLAN_ARCHIVED,
            timestamp=archived_at,
            plan_id=plan_id,
            details={
                'name': v2_plan.get('name', 'Unknown')
            }
        ))
        
        return events

        
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """타임스탬프 문자열을 datetime 객체로 변환"""
        try:
            dt = datetime.fromisoformat(timestamp_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except:
            return datetime.now(timezone.utc)
            
    def _log(self, message: str, level: str = 'info') -> None:
        """마이그레이션 로그 기록"""
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        self.migration_log.append(log_entry)
        
        if level == 'error':
            logger.error(message)
        else:
            logger.info(message)
            
    def _save_migration_log(self) -> None:
        """마이그레이션 로그 저장"""
        try:
            log_dir = Path("memory/workflow_v3/migration_logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"{self.project_name}_migration_{timestamp}.json"
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'project_name': self.project_name,
                    'migration_date': datetime.now().isoformat(),
                    'log': self.migration_log
                }, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Migration log saved: {log_file}")
            
        except Exception as e:
            logger.error(f"Failed to save migration log: {e}")
            
    def _get_migration_stats(self, v3_state: WorkflowState) -> Dict[str, Any]:
        """마이그레이션 통계"""
        stats = {
            'total_events': len(v3_state.events),
            'current_plan': v3_state.current_plan.name if v3_state.current_plan else None,
            'event_types': {}
        }
        
        # 이벤트 타입별 카운트
        for event in v3_state.events:
            event_type = event.type.value
            stats['event_types'][event_type] = stats['event_types'].get(event_type, 0) + 1
            
        return stats


class BatchMigrator:
    """여러 프로젝트 일괄 마이그레이션"""
    
    def __init__(self):
        self.results = []
        
    def migrate_all(self, force: bool = False) -> Dict[str, Any]:
        """모든 v2 프로젝트 마이그레이션
        
        Args:
            force: 강제 마이그레이션 여부
            
        Returns:
            마이그레이션 결과 요약
        """
        v2_dir = Path("memory/workflow_v2")
        if not v2_dir.exists():
            return {
                'success': False,
                'reason': "v2 디렉토리가 없습니다",
                'projects': []
            }
            
        # v2 프로젝트 파일 찾기
        v2_files = list(v2_dir.glob("*_workflow.json"))
        
        for v2_file in v2_files:
            project_name = v2_file.stem.replace("_workflow", "")
            
            logger.info(f"Migrating project: {project_name}")
            
            migrator = WorkflowMigrator(project_name)
            result = migrator.migrate(force)
            
            self.results.append({
                'project_name': project_name,
                'result': result
            })
            
        # 레거시 파일도 확인
        legacy_file = Path("memory/workflow_v2.json")
        if legacy_file.exists():
            self._migrate_legacy_file(legacy_file, force)
            
        return self._summarize_results()
        
    def _migrate_legacy_file(self, legacy_file: Path, force: bool) -> None:
        """레거시 v2 파일 마이그레이션"""
        try:
            with open(legacy_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for project_name in data.keys():
                if project_name == 'version':  # 메타데이터 스킵
                    continue
                    
                logger.info(f"Migrating legacy project: {project_name}")
                
                migrator = WorkflowMigrator(project_name)
                result = migrator.migrate(force)
                
                self.results.append({
                    'project_name': project_name,
                    'result': result,
                    'source': 'legacy'
                })
                
        except Exception as e:
            logger.error(f"Failed to migrate legacy file: {e}")
            
    def _summarize_results(self) -> Dict[str, Any]:
        """마이그레이션 결과 요약"""
        successful = [r for r in self.results if r['result'].get('success')]
        failed = [r for r in self.results if not r['result'].get('success')]
        
        return {
            'total_projects': len(self.results),
            'successful': len(successful),
            'failed': len(failed),
            'projects': self.results
        }
