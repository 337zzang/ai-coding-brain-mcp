"""
통합 프로젝트 관리 모듈 - Context, Project, Workflow 기능 통합
중복 제거 및 일관된 인터페이스 제공
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Literal
from datetime import datetime, timezone
from dataclasses import dataclass, field
from .helper_result import HelperResult

# 타입 정의
TaskStatus = Literal['pending', 'in_progress', 'completed', 'cancelled', 'blocked']
ProjectType = Literal['python', 'nodejs', 'java', 'go', 'rust', 'generic']
PhaseType = Literal['planning', 'development', 'testing', 'deployment', 'maintenance']


@dataclass
class ProjectContext:
    """프로젝트 컨텍스트 클래스"""
    project_id: str
    name: str
    path: str
    type: ProjectType
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'project_id': self.project_id,
            'name': self.name,
            'path': self.path,
            'type': self.type,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata,
            'settings': self.settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectContext':
        return cls(
            project_id=data['project_id'],
            name=data['name'],
            path=data['path'],
            type=data['type'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            metadata=data.get('metadata', {}),
            settings=data.get('settings', {})
        )


@dataclass
class Task:
    """태스크 클래스"""
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: int
    project_id: str
    phase_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'project_id': self.project_id,
            'phase_id': self.phase_id,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        return cls(
            id=data['id'],
            title=data['title'],
            description=data['description'],
            status=data['status'],
            priority=data['priority'],
            project_id=data['project_id'],
            phase_id=data.get('phase_id'),
            created_at=datetime.fromisoformat(data['created_at']),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            metadata=data.get('metadata', {})
        )


@dataclass
class Phase:
    """페이즈 클래스"""
    id: str
    name: str
    type: PhaseType
    order: int
    project_id: str
    is_active: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'order': self.order,
            'project_id': self.project_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Phase':
        return cls(
            id=data['id'],
            name=data['name'],
            type=data['type'],
            order=data['order'],
            project_id=data['project_id'],
            is_active=data.get('is_active', False),
            created_at=datetime.fromisoformat(data['created_at']),
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            metadata=data.get('metadata', {})
        )


class UnifiedProjectManager:
    """통합 프로젝트 관리자"""
    
    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir or Path.home() / '.ai-coding-brain')
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.projects_file = self.storage_dir / 'projects.json'
        self.tasks_file = self.storage_dir / 'tasks.json'
        self.phases_file = self.storage_dir / 'phases.json'
        
        self.current_project_id: Optional[str] = None
        self._cache = {}
        
        self._load_current_project()
    
    def _load_current_project(self):
        """현재 프로젝트 로드"""
        current_file = self.storage_dir / 'current_project.txt'
        if current_file.exists():
            self.current_project_id = current_file.read_text().strip()
    
    def _save_current_project(self):
        """현재 프로젝트 저장"""
        current_file = self.storage_dir / 'current_project.txt'
        if self.current_project_id:
            current_file.write_text(self.current_project_id)
        elif current_file.exists():
            current_file.unlink()
    
    def _load_data(self, file_path: Path) -> List[Dict[str, Any]]:
        """데이터 파일 로드"""
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _save_data(self, file_path: Path, data: List[Dict[str, Any]]):
        """데이터 파일 저장"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Project Management
    def create_project(self, name: str, path: str, project_type: ProjectType = 'generic',
                      set_current: bool = True) -> HelperResult:
        """
        새 프로젝트 생성
        
        Args:
            name: 프로젝트 이름
            path: 프로젝트 경로
            project_type: 프로젝트 타입
            set_current: 현재 프로젝트로 설정
            
        Returns:
            HelperResult with project data
        """
        try:
            project_id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            project = ProjectContext(
                project_id=project_id,
                name=name,
                path=str(Path(path).resolve()),
                type=project_type,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # 저장
            projects = self._load_data(self.projects_file)
            projects.append(project.to_dict())
            self._save_data(self.projects_file, projects)
            
            # 현재 프로젝트 설정
            if set_current:
                self.current_project_id = project_id
                self._save_current_project()
            
            # 기본 페이즈 생성
            self.create_standard_phases(project_id)
            
            return HelperResult(True, data=project.to_dict())
            
        except Exception as e:
            return HelperResult(False, error=f"Failed to create project: {str(e)}")
    
    def get_project(self, project_id: Optional[str] = None) -> HelperResult:
        """프로젝트 조회"""
        try:
            project_id = project_id or self.current_project_id
            if not project_id:
                return HelperResult(False, error="No project specified or current")
            
            projects = self._load_data(self.projects_file)
            for proj_data in projects:
                if proj_data['project_id'] == project_id:
                    return HelperResult(True, data=proj_data)
            
            return HelperResult(False, error=f"Project not found: {project_id}")
            
        except Exception as e:
            return HelperResult(False, error=f"Failed to get project: {str(e)}")
    
    def list_projects(self) -> HelperResult:
        """모든 프로젝트 목록"""
        try:
            projects = self._load_data(self.projects_file)
            return HelperResult(True, data=projects)
        except Exception as e:
            return HelperResult(False, error=f"Failed to list projects: {str(e)}")
    
    def set_current_project(self, project_id: str) -> HelperResult:
        """현재 프로젝트 설정"""
        project_result = self.get_project(project_id)
        if not project_result.ok:
            return project_result
        
        self.current_project_id = project_id
        self._save_current_project()
        return HelperResult(True, data={'current_project_id': project_id})
    
    # Task Management
    def create_task(self, title: str, description: str = "",
                   priority: int = 1, project_id: Optional[str] = None,
                   phase_id: Optional[str] = None) -> HelperResult:
        """태스크 생성"""
        try:
            project_id = project_id or self.current_project_id
            if not project_id:
                return HelperResult(False, error="No project specified")
            
            task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:20]}"
            
            task = Task(
                id=task_id,
                title=title,
                description=description,
                status='pending',
                priority=priority,
                project_id=project_id,
                phase_id=phase_id
            )
            
            tasks = self._load_data(self.tasks_file)
            tasks.append(task.to_dict())
            self._save_data(self.tasks_file, tasks)
            
            return HelperResult(True, data=task.to_dict())
            
        except Exception as e:
            return HelperResult(False, error=f"Failed to create task: {str(e)}")
    
    def get_tasks(self, project_id: Optional[str] = None,
                 status: Optional[TaskStatus] = None,
                 phase_id: Optional[str] = None) -> HelperResult:
        """태스크 목록 조회"""
        try:
            project_id = project_id or self.current_project_id
            if not project_id:
                return HelperResult(False, error="No project specified")
            
            tasks = self._load_data(self.tasks_file)
            filtered_tasks = []
            
            for task_data in tasks:
                if task_data['project_id'] != project_id:
                    continue
                if status and task_data['status'] != status:
                    continue
                if phase_id and task_data.get('phase_id') != phase_id:
                    continue
                
                filtered_tasks.append(task_data)
            
            # 우선순위 및 생성 시간으로 정렬
            filtered_tasks.sort(key=lambda x: (x['priority'], x['created_at']))
            
            return HelperResult(True, data=filtered_tasks)
            
        except Exception as e:
            return HelperResult(False, error=f"Failed to get tasks: {str(e)}")
    
    def update_task_status(self, task_id: str, status: TaskStatus,
                          note: Optional[str] = None) -> HelperResult:
        """태스크 상태 업데이트"""
        try:
            tasks = self._load_data(self.tasks_file)
            
            for i, task_data in enumerate(tasks):
                if task_data['id'] == task_id:
                    task_data['status'] = status
                    
                    now = datetime.now()
                    if status == 'in_progress' and not task_data.get('started_at'):
                        task_data['started_at'] = now.isoformat()
                    elif status == 'completed':
                        task_data['completed_at'] = now.isoformat()
                    
                    if note:
                        if 'metadata' not in task_data:
                            task_data['metadata'] = {}
                        task_data['metadata']['completion_note'] = note
                    
                    tasks[i] = task_data
                    self._save_data(self.tasks_file, tasks)
                    
                    return HelperResult(True, data=task_data)
            
            return HelperResult(False, error=f"Task not found: {task_id}")
            
        except Exception as e:
            return HelperResult(False, error=f"Failed to update task: {str(e)}")
    
    # Phase Management
    def create_standard_phases(self, project_id: Optional[str] = None) -> HelperResult:
        """표준 페이즈 생성"""
        try:
            project_id = project_id or self.current_project_id
            if not project_id:
                return HelperResult(False, error="No project specified")
            
            standard_phases = [
                ('Planning', 'planning', 1),
                ('Development', 'development', 2),
                ('Testing', 'testing', 3),
                ('Deployment', 'deployment', 4),
                ('Maintenance', 'maintenance', 5)
            ]
            
            phases = self._load_data(self.phases_file)
            created_phases = []
            
            for name, phase_type, order in standard_phases:
                phase_id = f"phase_{project_id}_{phase_type}"
                
                # 이미 존재하는지 확인
                if any(p['id'] == phase_id for p in phases):
                    continue
                
                phase = Phase(
                    id=phase_id,
                    name=name,
                    type=phase_type,
                    order=order,
                    project_id=project_id,
                    is_active=(order == 1)  # 첫 번째 페이즈를 활성화
                )
                
                phases.append(phase.to_dict())
                created_phases.append(phase.to_dict())
            
            self._save_data(self.phases_file, phases)
            
            return HelperResult(True, data=created_phases)
            
        except Exception as e:
            return HelperResult(False, error=f"Failed to create phases: {str(e)}")
    
    def get_phases(self, project_id: Optional[str] = None) -> HelperResult:
        """페이즈 목록 조회"""
        try:
            project_id = project_id or self.current_project_id
            if not project_id:
                return HelperResult(False, error="No project specified")
            
            phases = self._load_data(self.phases_file)
            project_phases = [p for p in phases if p['project_id'] == project_id]
            project_phases.sort(key=lambda x: x['order'])
            
            return HelperResult(True, data=project_phases)
            
        except Exception as e:
            return HelperResult(False, error=f"Failed to get phases: {str(e)}")
    
    def get_current_phase(self, project_id: Optional[str] = None) -> HelperResult:
        """현재 활성 페이즈 조회"""
        phases_result = self.get_phases(project_id)
        if not phases_result.ok:
            return phases_result
        
        for phase in phases_result.data:
            if phase.get('is_active', False):
                return HelperResult(True, data=phase)
        
        return HelperResult(False, error="No active phase found")
    
    # Progress and Statistics
    def get_project_progress(self, project_id: Optional[str] = None) -> HelperResult:
        """프로젝트 진행률 조회"""
        try:
            project_id = project_id or self.current_project_id
            if not project_id:
                return HelperResult(False, error="No project specified")
            
            tasks_result = self.get_tasks(project_id)
            if not tasks_result.ok:
                return tasks_result
            
            tasks = tasks_result.data
            total_tasks = len(tasks)
            
            if total_tasks == 0:
                return HelperResult(True, data={
                    'total_tasks': 0,
                    'completed_tasks': 0,
                    'progress_percentage': 0,
                    'status_breakdown': {}
                })
            
            status_count = {}
            for task in tasks:
                status = task['status']
                status_count[status] = status_count.get(status, 0) + 1
            
            completed_tasks = status_count.get('completed', 0)
            progress_percentage = (completed_tasks / total_tasks) * 100
            
            return HelperResult(True, data={
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'progress_percentage': round(progress_percentage, 2),
                'status_breakdown': status_count
            })
            
        except Exception as e:
            return HelperResult(False, error=f"Failed to get progress: {str(e)}")
    
    # Context Management (Legacy compatibility)
    def get_context(self) -> HelperResult:
        """현재 프로젝트 컨텍스트 조회"""
        return self.get_project()
    
    def update_context(self, key: str, value: Any) -> HelperResult:
        """컨텍스트 업데이트"""
        try:
            if not self.current_project_id:
                return HelperResult(False, error="No current project")
            
            projects = self._load_data(self.projects_file)
            for i, proj_data in enumerate(projects):
                if proj_data['project_id'] == self.current_project_id:
                    if 'metadata' not in proj_data:
                        proj_data['metadata'] = {}
                    proj_data['metadata'][key] = value
                    proj_data['updated_at'] = datetime.now().isoformat()
                    
                    projects[i] = proj_data
                    self._save_data(self.projects_file, projects)
                    
                    return HelperResult(True, data=proj_data)
            
            return HelperResult(False, error="Current project not found")
            
        except Exception as e:
            return HelperResult(False, error=f"Failed to update context: {str(e)}")


# 전역 인스턴스
_project_manager = UnifiedProjectManager()


# 공개 API 함수들 (기존 인터페이스 호환)
def get_current_project() -> HelperResult:
    """현재 프로젝트 정보 반환"""
    return _project_manager.get_project()


def create_project(name: str, path: str = ".", project_type: ProjectType = 'generic') -> HelperResult:
    """새 프로젝트 생성"""
    return _project_manager.create_project(name, path, project_type)


def list_projects() -> HelperResult:
    """모든 프로젝트 목록"""
    return _project_manager.list_projects()


def quick_task(description: str, priority: int = 1) -> HelperResult:
    """현재 프로젝트에 빠르게 작업 추가"""
    return _project_manager.create_task(description, priority=priority)


def list_tasks(project_id: Optional[str] = None, status: Optional[TaskStatus] = None) -> HelperResult:
    """작업 목록 조회"""
    return _project_manager.get_tasks(project_id, status)


def complete_task(task_id: str, note: Optional[str] = None) -> HelperResult:
    """작업 완료 처리"""
    return _project_manager.update_task_status(task_id, 'completed', note)


def get_project_progress(project_id: Optional[str] = None) -> HelperResult:
    """프로젝트 진행률 조회"""
    return _project_manager.get_project_progress(project_id)


def create_standard_phases(project_id: Optional[str] = None) -> HelperResult:
    """표준 Phase 세트 생성"""
    return _project_manager.create_standard_phases(project_id)


def get_current_phase(project_id: Optional[str] = None) -> HelperResult:
    """현재 활성 Phase 조회"""
    return _project_manager.get_current_phase(project_id)


def get_pending_tasks() -> HelperResult:
    """대기 중인 작업 목록 조회"""
    return _project_manager.get_tasks(status='pending')


# Context management (Legacy compatibility)
def get_context() -> HelperResult:
    """현재 프로젝트 컨텍스트 반환"""
    return _project_manager.get_context()


def update_context(key: str, value: Any) -> HelperResult:
    """컨텍스트 업데이트"""
    return _project_manager.update_context(key, value)


def save_context() -> HelperResult:
    """컨텍스트 저장 (자동 저장되므로 항상 성공)"""
    return HelperResult(True, data={'status': 'auto_saved'})


def initialize_context(project_path: str = ".") -> HelperResult:
    """프로젝트 컨텍스트 초기화 (레거시 호환성)"""
    project_name = Path(project_path).name
    return create_project(project_name, project_path)