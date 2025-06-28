"""
AI Coding Brain 통합 컨텍스트 관리자 - Pydantic 기반
버전: 8.0 (완전 재작성)
작성일: 2025-06-24

모든 데이터는 Pydantic 모델로 관리됩니다.
"""

import os
import json
from pathlib import Path
import datetime as dt
from typing import Optional, Dict, Any, List
from collections import defaultdict
import copy

# Pydantic 모델 import - 절대 경로 사용
import sys
import os
# Python 경로에 추가
python_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if python_path not in sys.path:
    sys.path.insert(0, python_path)

from core.models import (
from pydantic import ValidationError
    ProjectContext, Plan, Phase, Task,
    FileAccessEntry, WorkTracking, 
    validate_context_data
)
# TaskStatus를 별도로 import
try:
    from core.models import TaskStatus
except ImportError:
    # TaskStatus가 import 되지 않을 경우 임시로 정의
    from enum import Enum
    class TaskStatus(str, Enum):
        PENDING = "pending"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        BLOCKED = "blocked"
        CANCELED = "canceled"
from core.decorators import autosave


class UnifiedContextManager:
    """통합 컨텍스트 관리자 - 완전 Pydantic 기반"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.context: Optional[ProjectContext] = None
            self.project_path = None
            self.project_name = None
            self.memory_root = None
            self.base_path = None
            self.memory_path = None
            self.cache_dir = None
            self.helpers = None  # helpers 객체 추가
            self.initialized = True
    
    def initialize(self, project_path: str, project_name: str = None, 
                   memory_root: str = None, existing_context: Dict[str, Any] = None) -> ProjectContext:
        """프로젝트 컨텍스트 초기화 - ProjectContext 반환"""
        self.project_path = Path(project_path)
        
        # project_name이 None이면 경로에서 자동 추출
        if project_name is None:
            project_name = os.path.basename(os.path.abspath(project_path))
            print(f"✅ 프로젝트 이름 자동 추출: {project_name}")
        
        self.project_name = project_name
        self.base_path = project_path
        
        # 메모리 루트 설정
        if memory_root:
            self.memory_root = Path(memory_root)
        else:
            # 기본값: 프로젝트 내부 memory 폴더
            self.memory_root = Path(project_path) / "memory"
        
        # 메모리 경로 설정
        self.memory_path = self.memory_root
        self.cache_dir = self.memory_root / '.cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 백업 디렉토리 생성
        self.backup_dir = self.memory_root / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 기존 context가 있으면 ProjectContext로 변환
        if existing_context:
            if isinstance(existing_context, ProjectContext):
                self.context = existing_context
            else:
                # dict를 ProjectContext로 변환
                self.context = ProjectContext.from_dict(existing_context)
            print(f"✅ 기존 컨텍스트 사용: {project_name}")
        else:
            # 캐시된 컨텍스트 로드 시도
            cached_context = self._try_load_cached_context()
            if cached_context:
                self.context = cached_context
                print(f"✅ 캐시된 컨텍스트 로드: {project_name}")
            else:
                self.context = self._create_new_context()
                print(f"✅ 새 컨텍스트 생성: {project_name}")
        
        # 경로 정보 업데이트
        self.context.project_path = str(self.project_path)
        self.context.memory_root = str(self.memory_root)
        
        # helpers 객체 초기화
        if not self.helpers:
            try:
                import sys
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from json_repl_session import AIHelpers
                self.helpers = AIHelpers()
                print("✅ helpers 객체 초기화 완료")
            except Exception as e:
                print(f"⚠️ helpers 초기화 실패: {e}")
                self.helpers = None
        
        return self.context
    
    def _get_cache_file_paths(self) -> Dict[str, Path]:
        """각 캐시 파일 경로 반환"""
        if not self.cache_dir:
            return {}
        
        return {
            'core': self.cache_dir / 'cache_core.json',
            'analyzed_files': self.cache_dir / 'cache_analyzed_files.json',
            'work_tracking': self.cache_dir / 'cache_work_tracking.json',
        # 'tasks': self.cache_dir / 'cache_tasks.json', # Plan에서 파생되므로 제거
            'plan': self.cache_dir / 'cache_plan.json'
        }
    
    def _create_new_context(self) -> ProjectContext:
        """새로운 컨텍스트 생성 - ProjectContext 반환"""
        return ProjectContext(
            project_name=self.project_name,
            project_id=self.project_name,
            project_path=str(self.project_path),
            memory_root=str(self.memory_root),
            created_at=dt.datetime.now(),
            updated_at=dt.datetime.now(),
            version='8.0',
            current_focus='',
            current_task=None,
            analyzed_files={},
            work_tracking=WorkTracking(),
            tasks={'next': [], 'done': []},
            plan=None,
            plan_history=[],
            coding_experiences=[],
            progress={
                'completed_tasks': 0,
                'total_tasks': 0,
                'percentage': 0.0
            },
            phase_reports={},
            error_log=[],
            file_access_history=[],
            metadata={
                'version': '8.0',
                'last_saved': dt.datetime.now().isoformat()
            }
        )
    
    def _try_load_cached_context(self) -> Optional[ProjectContext]:
        """캐시된 컨텍스트 로드"""
        if not self.memory_root or not self.project_name:
            return None
        
        cache_paths = self._get_cache_file_paths()
        if not cache_paths:
            return None
        
        try:
            # 1. 핵심 데이터 로드
            if not cache_paths['core'].exists():
                return None
            
            with open(cache_paths['core'], 'r', encoding='utf-8') as f:
                context_data = json.load(f)
            
            # 2. 나머지 파일들 로드 및 병합
            # analyzed_files
            if cache_paths['analyzed_files'].exists():
                with open(cache_paths['analyzed_files'], 'r', encoding='utf-8') as f:
                    context_data['analyzed_files'] = json.load(f)
            
            # work_tracking
            if cache_paths['work_tracking'].exists():
                with open(cache_paths['work_tracking'], 'r', encoding='utf-8') as f:
                    context_data['work_tracking'] = json.load(f)
            
            # tasks
            # if cache_paths['tasks'].exists():
                # with open(cache_paths['tasks'], 'r', encoding='utf-8') as f:
                    # context_data['tasks'] = json.load(f)
            
            # plan
            if cache_paths['plan'].exists():
                with open(cache_paths['plan'], 'r', encoding='utf-8') as f:
                    plan_data = json.load(f)
                    # Plan 데이터를 직접 사용 (이미 model_dump()로 저장됨)
                    context_data['plan'] = plan_data
                    # plan_history는 context의 별도 필드
                    if 'plan_history' in context_data:
                        context_data['plan_history'] = context_data.get('plan_history', [])
            
            # 경로 업데이트
            context_data['project_path'] = str(self.project_path)
            context_data['memory_root'] = str(self.memory_root)
            
            # ProjectContext로 변환
            # ProjectContext 생성 (필수 필드 추가)
            if 'project_id' not in context_data:
                context_data['project_id'] = context_data.get('project_name', self.project_name)
            
            # Plan 데이터가 있으면 Plan 객체로 변환
            if 'plan' in context_data and context_data['plan']:
                from core.models import Plan
                context_data['plan'] = Plan(**context_data['plan'])
            
            try:
                return ProjectContext(**context_data)
            except ValidationError as e:
                print(f"경고: 기존 Task 데이터가 새 UUID 형식과 맞지 않아 초기화합니다. 오류: {e}")
                # Task 목록만 비워서 새로 시작
                if 'tasks' in context_data:
                    context_data['tasks'] = []
                return ProjectContext(**context_data)
            
        except Exception as e:
            print(f"⚠️ 캐시 로드 실패: {e}")
            return None
    
    def save(self) -> bool:
        """컨텍스트를 여러 캐시 파일로 저장"""
        if not self.context or not self.memory_root:
            print("❌ 저장 실패: 컨텍스트가 없거나 메모리 루트가 설정되지 않았습니다.")
            return False

        try:
            # 업데이트 시간 갱신
            self.context.updated_at = dt.datetime.now()
            
            # 캐시 디렉토리 생성
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            context_dict = self.context.model_dump()
            cache_paths = self._get_cache_file_paths()
            
            # 사용 가능한 캐시 파일만 저장
            saved_count = 0
            
            # 1. 코어 정보 저장
            if 'core' in cache_paths:
                with open(cache_paths['core'], 'w', encoding='utf-8') as f:
                    core_data = {
                        'project_name': context_dict.get('project_name'),
                        'project_path': context_dict.get('project_path'),
                        'language': context_dict.get('language', 'python'),
                        'created_at': context_dict.get('created_at'),
                        'updated_at': context_dict.get('updated_at'),
                        'current_phase': context_dict.get('current_phase', 'initialization'),
                        'current_task': context_dict.get('current_task'),
                        'api_safety': context_dict.get('api_safety', {}),
                        'phase_history': context_dict.get('phase_history', [])
                    }
                    json.dump(core_data, f, indent=2, ensure_ascii=False, default=str)
                    saved_count += 1
            
            # 2. 분석된 파일 정보 저장
            if 'analyzed_files' in cache_paths:
                with open(cache_paths['analyzed_files'], 'w', encoding='utf-8') as f:
                    json.dump(context_dict.get('analyzed_files', {}), f, indent=2, ensure_ascii=False, default=str)
                    saved_count += 1
            
            # 3. 작업 추적 정보 저장
            if 'work_tracking' in cache_paths:
                with open(cache_paths['work_tracking'], 'w', encoding='utf-8') as f:
                    json.dump(context_dict.get('work_tracking', {}), f, indent=2, ensure_ascii=False, default=str)
                    saved_count += 1
            
            # 4. tasks는 Plan에서 파생되므로 저장하지 않음
            
            # 5. 계획 저장 (cache_plan.json)
            if 'plan' in cache_paths and hasattr(self.context, 'plan') and self.context.plan:
                with open(cache_paths['plan'], 'w', encoding='utf-8') as f:
                    json.dump(self.context.plan.model_dump(), f, indent=2, ensure_ascii=False, default=str)
                    saved_count += 1
            
            print(f"💾 {saved_count}개 변수 저장됨")
            return True
            
        except Exception as e:
            print(f"❌ 캐시 저장 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    def get_context(self) -> ProjectContext:
        """현재 컨텍스트 반환"""
        return self.context
    
    def update_context(self, **kwargs):
        """컨텍스트 업데이트"""
        if not self.context:
            return
        
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)
        
        self.context.updated_at = dt.datetime.now()
    
    def add_file_access(self, file_path: str, operation: str, task_id: Optional[str] = None):
        """파일 접근 기록 추가"""
        if not self.context:
            return
        
        entry = FileAccessEntry(
            file=file_path,
            operation=operation,
            timestamp=dt.datetime.now(),
            task_id=task_id or self.context.current_task
        )
        
        self.context.file_access_history.append(entry)
        
        # work_tracking에도 추가
        if not hasattr(self.context.work_tracking, 'file_access'):
            self.context.work_tracking.file_access = {}
        
        if file_path not in self.context.work_tracking.file_access:
            self.context.work_tracking.file_access[file_path] = {
                'read_count': 0,
                'write_count': 0,
                'first_access': dt.datetime.now().isoformat(),
                'last_access': dt.datetime.now().isoformat()
            }
        
        access_info = self.context.work_tracking.file_access[file_path]
        if operation == 'read':
            access_info['read_count'] = access_info.get('read_count', 0) + 1
        elif operation in ['write', 'create']:
            access_info['write_count'] = access_info.get('write_count', 0) + 1
        access_info['last_access'] = dt.datetime.now().isoformat()
    
    @autosave
    def update_progress(self):
        """진행률 업데이트"""
        if self.context and self.context.plan:
            self.context.update_progress()
    
    def get_current_task(self) -> Optional[Task]:
        """현재 작업 반환"""
        if not self.context or not self.context.current_task:
            return None
        
        if self.context.plan:
            return self.context.plan.get_task_by_id(self.context.current_task)
        return None
    
    @autosave
    def set_current_task(self, task_id: str):
        """현재 작업 설정"""
        if self.context:
            self.context.current_task = task_id
            # work_tracking 업데이트
            self.context.work_tracking.current_task_work = {
                'task_id': task_id,
                'start_time': dt.datetime.now().isoformat(),
                'files_accessed': [],
                'functions_edited': [],
                'operations': []
            }
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """컨텍스트에서 값 가져오기"""
        if not self.context:
            return default
        
        # nested key 지원 (예: "work_tracking.total_operations")
        keys = key.split('.')
        value = self.context
        
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            elif isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    @autosave
    def update_cache(self, key: str, value: Any):
        """캐시 업데이트"""
        if not self.context:
            return
        
        # nested key 지원
        keys = key.split('.')
        target = self.context
        
        for i, k in enumerate(keys[:-1]):
            if hasattr(target, k):
                target = getattr(target, k)
            else:
                return
        
        # 마지막 키에 값 설정
        last_key = keys[-1]
        if hasattr(target, last_key):
            setattr(target, last_key, value)
        
        self.context.updated_at = dt.datetime.now()
    
    def sync_plan_to_tasks(self):
        """Plan 모델의 모든 작업을 context.tasks 형식으로 동기화
        
        Plan을 Single Source of Truth로 사용하고,
        context.tasks는 읽기 전용 뷰로 동작하도록 함
        """
        if not self.context.plan:
            return
            
        # 새로운 tasks 구조 생성
        next_tasks = []
        done_tasks = []
        
        # 모든 phase의 작업들을 순회
        for phase_id, phase in self.context.plan.phases.items():
            for task in phase.tasks.values():
                task_info = {
                    'id': task.id,
                    'phase': phase_id,
                    'title': task.title,
                    'description': task.description,
                    'status': task.status.value if hasattr(task.status, 'value') else task.status
                }
                
                if task.status == TaskStatus.COMPLETED or (hasattr(task.status, 'value') and task.status.value == 'completed'):
                    task_info['completed_at'] = task.completed_at.isoformat() if task.completed_at else None
                    done_tasks.append(task_info)
                else:
                    next_tasks.append(task_info)
        
        # context.tasks 업데이트
        self.context.tasks = {
            'next': next_tasks,
            'done': done_tasks
        }
        
        # 변경사항 저장
        self.save()
        
    def add_task_to_plan(self, phase_id: str, title: str, description: str = "") -> Optional[Task]:
        """Plan의 특정 Phase에 작업 추가하고 동기화"""
        if not self.context.plan or phase_id not in self.context.plan.phases:
            return None
            
        phase = self.context.plan.phases[phase_id]
        task = phase.add_task(title, description)
        
        # 즉시 동기화
        self.sync_plan_to_tasks()
        
        return task
        
    def update_task_status(self, task_id: str, new_status: TaskStatus):
        """작업 상태 업데이트하고 동기화"""
        if not self.context.plan:
            return
            
        # 모든 phase에서 task 찾기
        for phase in self.context.plan.phases.values():
            task = phase.get_task_by_id(task_id)
            if task:
                task.update_status(new_status)
                # 즉시 동기화
                self.sync_plan_to_tasks()
                break


# 싱글톤 인스턴스
_context_manager = UnifiedContextManager()


def get_context_manager() -> UnifiedContextManager:
    """Get singleton instance of Context Manager"""
    return _context_manager


def initialize_context(project_path: str, project_name: str = None, 
                      memory_root: str = None, existing_context: Dict[str, Any] = None) -> ProjectContext:
    """Initialize context using the singleton Context Manager"""
    return _context_manager.initialize(project_path, project_name, memory_root, existing_context)
