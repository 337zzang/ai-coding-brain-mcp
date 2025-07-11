"""
Workflow v3 Manager
싱글톤 패턴의 중앙 워크플로우 관리자
"""
from typing import Dict, Optional, List, Any
from datetime import datetime, timezone
import json
import os
from pathlib import Path

from .models import (
    WorkflowPlan, Task, WorkflowState, WorkflowEvent,
    TaskStatus, PlanStatus, EventType
)
from .events import EventStore, EventBuilder
from .parser import CommandParser
from .storage import WorkflowStorage
from .context_integration import ContextIntegration
from .workflow_event_adapter import WorkflowEventAdapter
from .errors import (
    WorkflowError, ErrorCode, ErrorMessages, 
    ErrorHandler, InputValidator, SuccessMessages
)
from .api.internal_api import InternalWorkflowAPI
from .api.user_api import UserCommandAPI
from .commands.auto_executor import AutoTaskExecutor
from python.ai_helpers.helper_result import HelperResult
import logging

logger = logging.getLogger(__name__)


class WorkflowManager:
    """워크플로우 중앙 관리자 (싱글톤)"""
    
    _instances: Dict[str, 'WorkflowManager'] = {}
    _lock = False  # 간단한 락 (향후 threading.Lock으로 대체 가능)
    
    def __init__(self, project_name: str):
        """프로젝트별 워크플로우 관리자 초기화"""
        self.project_name = project_name
        self.state = WorkflowState()
        self.auto_archive_completed = False  # 완료된 플랜 자동 보관

        self.event_store = EventStore()
        self.parser = CommandParser()
        self.storage = WorkflowStorage(project_name)
        self.context = ContextIntegration(project_name)
        
        # EventBus 연동을 위한 어댑터 초기화
        self.event_adapter = WorkflowEventAdapter(self)
        
        # API 초기화 (v3 개선)
        self.internal_api = InternalWorkflowAPI(self)
        self.user_api = UserCommandAPI(self)
        
        # 자동 실행기 (필요시 생성)
        self._auto_executor: Optional[AutoTaskExecutor] = None
        
        # 명령어 핸들러 매핑
        self.command_handlers = {
            'start': self._handle_start,
            'focus': self._handle_focus,
            'plan': self._handle_plan,
            'task': self._handle_task,
            'next': self._handle_next,
            'build': self._handle_build,
            'status': self._handle_status,
        }
        
        # 기존 데이터 로드
        self._load_data()
        
        # 컨텍스트 동기화
        if self.state.current_plan:
            self.context.sync_plan_summary(self.state.current_plan)
        
    @classmethod
    def get_instance(cls, project_name: str) -> 'WorkflowManager':
        """프로젝트별 싱글톤 인스턴스 반환"""
        if project_name not in cls._instances:
            cls._instances[project_name] = cls(project_name)
        return cls._instances[project_name]

        
    
    @classmethod
    def clear_instance(cls, project_name: str = None) -> None:
        """인스턴스 캐시 무효화

        Args:
            project_name: 특정 프로젝트만 제거. None이면 모든 캐시 제거
        """
        if project_name:
            if project_name in cls._instances:
                del cls._instances[project_name]
                logger.info(f"Cleared instance cache for {project_name}")
        else:
            cls._instances.clear()
            logger.info("Cleared all instance caches")

    @classmethod
    def invalidate_and_reload(cls, project_name: str) -> 'WorkflowManager':
        """인스턴스 캐시 무효화 후 새로 로드

        Args:
            project_name: 프로젝트 이름

        Returns:
            새로 로드된 WorkflowManager 인스턴스
        """
        cls.clear_instance(project_name)
        return cls.get_instance(project_name)

    def _load_data(self) -> None:
        """저장된 데이터 로드"""
        data = self.storage.load()
        if data:
            try:
                self.state = WorkflowState.from_dict(data)
                logger.info(f"Loaded workflow state for {self.project_name}")
                
                # events 로드는 별도로 처리 (실패해도 state는 유지)
                try:
                    if hasattr(self.state, 'events') and self.state.events:
                        # events가 이미 WorkflowEvent 객체 리스트인지 확인
                        if len(self.state.events) > 0 and hasattr(self.state.events[0], '__dict__'):
                            # 이미 객체인 경우 - 딕셔너리로 변환
                            events_dict = [event.__dict__ if hasattr(event, '__dict__') else event for event in self.state.events]
                            self.event_store.from_list(events_dict)
                        else:
                            # 딕셔너리인 경우 - 그대로 사용
                            self.event_store.from_list(self.state.events)
                        logger.info(f"Loaded {len(self.state.events)} events")
                except Exception as e:
                    logger.warning(f"Failed to load events: {e}")
                    self.event_store = EventStore()
                    
            except Exception as e:
                logger.error(f"Failed to parse workflow data: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # 파싱 실패 시 새로운 상태로 시작
                self.state = WorkflowState()
                self.event_store = EventStore()
        else:
            # 데이터가 없으면 새로운 상태로 시작
            self.state = WorkflowState()
            self.event_store = EventStore()
                
    def _save_data(self) -> bool:
        """데이터를 파일에 저장"""
        try:
            # 이벤트 스토어를 상태에 동기화
            self.state.events = self.event_store.events
            self.state.last_saved = datetime.now(timezone.utc)
            
            # 저장 (백업은 storage.save()에서 자동 처리)
            success = self.storage.save(self.state.to_dict())
            
            if success:
                logger.info(f"Workflow data saved successfully for {self.project_name}")
            else:
                logger.warning(f"Failed to save workflow data for {self.project_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to save workflow data: {e}")
            return False
            
    # 플랜 관리 메서드
    
    def start_plan(self, name: str, description: str = "") -> Optional[WorkflowPlan]:
        """새 플랜 시작"""
        try:
            # 현재 플랜이 있으면 먼저 아카이브
            if self.state.current_plan:
                self.archive_plan()
                
            # 새 플랜 생성
            plan = WorkflowPlan(name=name, description=description)
            plan.start()  # 상태를 ACTIVE로
            
            self.state.current_plan = plan
            
            # 이벤트 기록
            self._add_event(EventBuilder.plan_created(plan))
            self._add_event(EventBuilder.plan_started(plan))
            
            # 컨텍스트 동기화
            self.context.sync_plan_summary(plan)
            self.context.record_event(self.event_store.events[-2])  # plan_created
            self.context.record_event(self.event_store.events[-1])  # plan_started
            
            # 저장
            self._save_data()
            
            return plan
            
        except ValueError as e:
            logger.error(f"Failed to create plan: {e}")
            return None

            
    def add_task(self, title: str, description: str = "") -> Optional[Task]:
        """현재 플랜에 태스크 추가"""
        if not self.state.current_plan:
            logger.error("No active plan to add task")
            return None
            
        try:
            # 태스크 생성
            task = Task(title=title, description=description)
            
            # 플랜에 추가
            self.state.current_plan.tasks.append(task)
            self.state.current_plan.updated_at = datetime.now(timezone.utc)
            
            # 이벤트 기록
            event = EventBuilder.task_added(self.state.current_plan.id, task)
            self._add_event(event)
            
            # 컨텍스트 동기화
            self.context.sync_plan_summary(self.state.current_plan)
            
            # 저장
            self._save_data()
            
            return task
            
        except ValueError as e:
            logger.error(f"Failed to add task: {e}")
            return None
            
    def add_task_note(self, note: str, task_id: str = None) -> Optional[Task]:
        """현재 태스크 또는 지정된 태스크에 노트 추가"""
        if not self.state.current_plan:
            logger.warning("No active plan for adding note")
            return None
            
        # 태스크 찾기
        if task_id:
            # 특정 태스크 ID로 찾기
            task = None
            for t in self.state.current_plan.tasks:
                if t.id == task_id:
                    task = t
                    break
            if not task:
                logger.warning(f"Task not found: {task_id}")
                return None
        else:
            # 현재 태스크 사용
            task = self.get_current_task()
            if not task:
                logger.warning("No current task to add note")
                return None
                
        # 노트 추가
        task.notes.append(note)
        task.updated_at = datetime.now(timezone.utc)
        
        # 이벤트 기록
        event = WorkflowEvent(
            type=EventType.NOTE_ADDED,
            plan_id=self.state.current_plan.id,
            task_id=task.id,
            details={'note': note}
        )
        self.state.add_event(event)
        self._add_event(event)
        
        # 저장
        self._save_data()
        
        logger.info(f"Note added to task {task.title}: {note[:50]}...")
        return task
            
    def complete_task(self, task_id: str, note: str = "") -> bool:
        """태스크 완료 처리"""
        if not self.state.current_plan:
            return False
            
        # 태스크 찾기
        task = None
        for t in self.state.current_plan.tasks:
            if t.id == task_id:
                task = t
                break
                
        if not task:
            logger.error(f"Task not found: {task_id}")
            return False
            
        # 이미 완료된 경우
        if task.status == TaskStatus.COMPLETED:
            return True
            
        # 완료 처리
        task.complete(note)
        self.state.current_plan.updated_at = datetime.now(timezone.utc)
        
        # 이벤트 기록
        event = EventBuilder.task_completed(self.state.current_plan.id, task, note)
        self._add_event(event)
        self.context.record_event(event)  # 중요 이벤트이므로 컨텍스트에 기록
        
        # 모든 태스크가 완료되었는지 확인
        if self.is_plan_completed():
            self.state.current_plan.complete()
            complete_event = EventBuilder.plan_completed(self.state.current_plan)
            self._add_event(complete_event)
            self.context.record_event(complete_event)
            
        # 컨텍스트 동기화
        self.context.sync_plan_summary(self.state.current_plan)
            
        # 저장
        self._save_data()
        
        return True

            
    def complete_current_task(self, note: str = "") -> Optional[Task]:
        """현재 태스크 완료하고 다음 태스크 반환"""
        current = self.get_current_task()
        if not current:
            return None
            
        # 완료 처리
        if self.complete_task(current.id, note):
            # 다음 태스크 찾기
            return self.get_current_task()
            
        return None
        
    def fail_task(self, task_id: str, error: str) -> bool:
        """태스크 실패 처리"""
        if not self.state.current_plan:
            return False
            
        # 태스크 찾기
        task = None
        for t in self.state.current_plan.tasks:
            if t.id == task_id:
                task = t
                break
                
        if not task:
            logger.error(f"Task not found: {task_id}")
            return False
            
        # 실패 처리
        task.fail(error)
        self.state.current_plan.updated_at = datetime.now(timezone.utc)
        
        # 이벤트 기록
        event = EventBuilder.task_failed(self.state.current_plan.id, task, error)
        self._add_event(event)
        
        # 컨텍스트 동기화
        self.context.sync_plan_summary(self.state.current_plan)
        
        # 저장
        self._save_data()
        
        return True
        
    def block_task(self, task_id: str, blocker: str) -> bool:
        """태스크 차단 처리"""
        if not self.state.current_plan:
            return False
            
        # 태스크 찾기
        task = None
        for t in self.state.current_plan.tasks:
            if t.id == task_id:
                task = t
                break
                
        if not task:
            logger.error(f"Task not found: {task_id}")
            return False
            
        # 차단 처리
        task.block(blocker)
        self.state.current_plan.updated_at = datetime.now(timezone.utc)
        
        # 이벤트 기록
        event = EventBuilder.task_blocked(self.state.current_plan.id, task, blocker)
        self._add_event(event)
        
        # 컨텍스트 동기화
        self.context.sync_plan_summary(self.state.current_plan)
        
        # 저장
        self._save_data()
        
        return True
        
    def unblock_task(self, task_id: str) -> bool:
        """태스크 차단 해제 처리"""
        if not self.state.current_plan:
            return False
            
        # 태스크 찾기
        task = None
        for t in self.state.current_plan.tasks:
            if t.id == task_id:
                task = t
                break
                
        if not task:
            logger.error(f"Task not found: {task_id}")
            return False
            
        # 차단 해제 처리
        task.unblock()
        self.state.current_plan.updated_at = datetime.now(timezone.utc)
        
        # 이벤트 기록
        event = EventBuilder.task_unblocked(self.state.current_plan.id, task)
        self._add_event(event)
        
        # 컨텍스트 동기화
        self.context.sync_plan_summary(self.state.current_plan)
        
        # 저장
        self._save_data()
        
        return True
        
    def cancel_task(self, task_id: str, reason: str = "") -> bool:
        """태스크 취소 처리"""
        if not self.state.current_plan:
            return False
            
        # 태스크 찾기
        task = None
        for t in self.state.current_plan.tasks:
            if t.id == task_id:
                task = t
                break
                
        if not task:
            logger.error(f"Task not found: {task_id}")
            return False
            
        # 취소 처리
        task.cancel(reason)
        self.state.current_plan.updated_at = datetime.now(timezone.utc)
        
        # 이벤트 기록
        event = EventBuilder.task_cancelled(self.state.current_plan.id, task, reason)
        self._add_event(event)
        
        # 컨텍스트 동기화
        self.context.sync_plan_summary(self.state.current_plan)
        
        # 저장
        self._save_data()
        
        return True
        
    def archive_plan(self) -> bool:
        """현재 플랜 아카이브"""
        if not self.state.current_plan:
            return False
            
        # 아카이브 처리
        self.state.current_plan.archive()
        
        # 이벤트 기록
        event = EventBuilder.plan_archived(self.state.current_plan)
        self._add_event(event)
        self.context.record_event(event)  # 중요 이벤트
        
        # 현재 플랜 제거
        self.state.current_plan = None
        
        # 컨텍스트 초기화
        self.context.sync_plan_summary(None)
        
        # 저장
        self._save_data()
        
        return True
        
    # 조회 메서드
    
    def get_current_task(self) -> Optional[Task]:
        """현재 작업 중인 태스크 반환"""
        if not self.state.current_plan:
            return None
            
        return self.state.current_plan.get_current_task()
        
    def get_task_by_number(self, number: int) -> Optional[Task]:
        """번호로 태스크 조회 (1부터 시작)"""
        if not self.state.current_plan or number < 1:
            return None
            
        idx = number - 1
        if idx < len(self.state.current_plan.tasks):
            return self.state.current_plan.tasks[idx]
            
        return None
        
    def is_plan_completed(self) -> bool:
        """플랜의 모든 태스크가 완료되었는지 확인"""
        if not self.state.current_plan:
            return False
            
        for task in self.state.current_plan.tasks:
            if task.status != TaskStatus.COMPLETED:
                return False
                
        return True

        
    def get_status(self) -> Dict[str, Any]:
        """워크플로우 상태 정보"""
        if not self.state.current_plan:
            return {
                'status': 'no_plan',
                'message': '활성 플랜이 없습니다'
            }
            
        plan = self.state.current_plan
        total_tasks = len(plan.tasks)
        completed_tasks = len([t for t in plan.tasks if t.status == TaskStatus.COMPLETED])
        
        current_task = self.get_current_task()
        
        return {
            'status': plan.status.value if hasattr(plan.status, 'value') else str(plan.status),

            'plan_id': plan.id,
            'plan_name': plan.name,
            'plan_description': plan.description,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'progress_percent': int((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0),
            'current_task': {
                'id': current_task.id,
                'title': current_task.title,
                'description': current_task.description,
                'status': current_task.status.value if hasattr(current_task.status, 'value') else str(current_task.status)
            } if current_task else None,
            'created_at': plan.created_at.isoformat(),
            'updated_at': plan.updated_at.isoformat()
        }
        
    def get_tasks(self) -> List[Dict[str, Any]]:
        """현재 플랜의 태스크 목록"""
        if not self.state.current_plan:
            return []
            
        tasks = []
        for i, task in enumerate(self.state.current_plan.tasks, 1):
            tasks.append({
                'number': i,
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status.value,
                'created_at': task.created_at.isoformat(),
                'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                'duration': task.duration
            })
            
        return tasks
        
    def get_plan_history(self) -> List[Dict[str, Any]]:
        """플랜 히스토리 (이벤트 로그 기반)"""
        return self.state.get_plan_history()
        
    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 이벤트 목록"""
        events = self.event_store.get_recent_events(limit)
        return [e.to_dict() for e in events]

        
    # 명령어 실행 메서드
    
    def execute_command(self, command_str: str) -> HelperResult:
        """명령어 문자열 실행 (개선된 버전)"""
        # UserCommandAPI를 통해 실행
        if hasattr(self, 'user_api'):
            return self.user_api.execute_command(command_str)
        
        # 기존 방식 (fallback)
        try:
            # 명령어 파싱
            parsed = self.parser.parse(command_str)
            
            # 명령어 핸들러 찾기
            handler = self.command_handlers.get(parsed.command)
            if handler:
                return handler(parsed)
            else:
                raise WorkflowError(
                    ErrorCode.INVALID_COMMAND,
                    ErrorMessages.get(ErrorCode.INVALID_COMMAND, command=parsed.command)
                )
                
        except WorkflowError as e:
            return HelperResult(False, error=e.message, data=e.to_dict())
        except ValueError as e:
            return HelperResult(False, error=str(e))
        except Exception as e:
            logger.exception(f"Command execution error: {command_str}")
            error_data = ErrorHandler.handle_error(e, f"execute_command({command_str})")
            return HelperResult(False, error=error_data['error'], data=error_data)
            
    def _handle_start(self, parsed) -> HelperResult:
        """start 명령 처리"""
        if parsed.title:
            # 새 플랜 시작
            plan = self.start_plan(parsed.title, parsed.description)
            if plan:
                return HelperResult(True, data={
                    'success': True,
                    'plan_id': plan.id,
                    'plan_name': plan.name,
                    'message': SuccessMessages.get('PLAN_CREATED', name=plan.name)
                })
            else:
                return HelperResult(False, error="플랜 생성 실패")
        else:
            # 현재 플랜 재개
            if self.state.current_plan:
                return HelperResult(True, data={
                    'success': True,
                    'plan_id': self.state.current_plan.id,
                    'plan_name': self.state.current_plan.name,
                    'message': f"📋 현재 플랜: {self.state.current_plan.name}"
                })
            else:
                return HelperResult(False, error="활성 플랜이 없습니다. /start [플랜명]으로 새 플랜을 시작하세요")

                
    def _handle_focus(self, parsed) -> HelperResult:
        """focus 명령 처리"""
        if not self.state.current_plan:
            return HelperResult(False, error="활성 플랜이 없습니다")
            
        if not parsed.title:
            # 현재 태스크 표시
            current = self.get_current_task()
            if current:
                return HelperResult(True, data={
                    'success': True,
                    'current_task': {
                        'id': current.id,
                        'title': current.title,
                        'description': current.description,
                        'status': current.status.value
                    }
                })
            else:
                # 태스크가 없는지 확인
                if not self.state.current_plan.tasks:
                    message = "플랜에 태스크가 없습니다. /task [태스크명]으로 추가하세요"
                else:
                    message = "모든 태스크가 완료되었습니다"
                    
                return HelperResult(True, data={
                    'success': True,
                    'current_task': None,
                    'message': message
                })
                
        # 특정 태스크로 포커스
        task = None
        if 'task_number' in parsed.args:
            task = self.get_task_by_number(parsed.args['task_number'])
        elif 'task_id' in parsed.args:
            # ID로 찾기
            for t in self.state.current_plan.tasks:
                if t.id == parsed.args['task_id']:
                    task = t
                    break
                    
        if task:
            # 현재 태스크 인덱스 업데이트
            for i, t in enumerate(self.state.current_plan.tasks):
                if t.id == task.id:
                    self.state.current_plan.current_task_index = i
                    break
                    
            # 변경사항 저장
            self._save_data()
            
            return HelperResult(True, data={
                'success': True,
                'focused_task': {
                    'id': task.id,
                    'title': task.title,
                    'description': task.description,
                    'status': task.status.value
                },
                'message': f"🎯 포커스: {task.title}"
            })
        else:
            return HelperResult(False, error="태스크를 찾을 수 없습니다")

            
    def _handle_plan(self, parsed) -> HelperResult:
        """plan 명령 처리"""
        if parsed.subcommand == 'list':
            # 플랜 히스토리
            history = self.get_plan_history()
            return HelperResult(True, data={
                'success': True,
                'plans': history,
                'count': len(history)
            })
            
        elif parsed.title:
            # 새 플랜 생성
            if parsed.args.get('reset') and self.state.current_plan:
                self.archive_plan()
                
            plan = self.start_plan(parsed.title, parsed.description)
            if plan:
                return HelperResult(True, data={
                    'success': True,
                    'plan_id': plan.id,
                    'plan_name': plan.name,
                    'message': f"✅ 플랜 생성: {plan.name}"
                })
            else:
                return HelperResult(False, error="플랜 생성 실패")
                
        else:
            # 현재 플랜 정보
            if self.state.current_plan:
                status = self.get_status()
                # enum 값들을 문자열로 변환
                if isinstance(status, dict):
                    if 'status' in status and hasattr(status['status'], 'value'):
                        status['status'] = status['status'].value
                    if 'current_task' in status and status['current_task'] and 'status' in status['current_task']:
                        if hasattr(status['current_task']['status'], 'value'):
                            status['current_task']['status'] = status['current_task']['status'].value
                return HelperResult(True, data=status)
            else:
                return HelperResult(False, error="활성 플랜이 없습니다")
                
    def _handle_task(self, parsed) -> HelperResult:
        """task 명령 처리"""
        if not self.state.current_plan:
            raise WorkflowError(
                ErrorCode.NO_ACTIVE_PLAN,
                ErrorMessages.get(ErrorCode.NO_ACTIVE_PLAN)
            )
            
        if parsed.subcommand == 'current':
            # 현재 태스크
            return self._handle_focus(parsed)
            
        elif parsed.subcommand == 'list':
            # 태스크 목록 명시적 처리
            tasks = self.get_tasks()  # 이미 dict 리스트를 반환
            return HelperResult(True, data={
                'success': True,
                'tasks': tasks,
                'total': len(tasks),
                'completed': len([t for t in tasks if t.get('status') == 'completed']),
                'message': f"📋 전체 태스크: {len(tasks)}개"
            })
            
        elif parsed.subcommand == 'note':
            # 현재 태스크에 노트 추가
            note = parsed.args.get('note', parsed.title)
            if not note:
                return HelperResult(False, error="노트 내용을 입력해주세요")
                
            task = self.add_task_note(note)
            if task:
                return HelperResult(True, data={
                    'success': True,
                    'task': {
                        'id': task.id,
                        'title': task.title,
                        'notes': task.notes
                    },
                    'message': f"✅ 노트 추가: {note[:50]}..."
                })
            else:
                return HelperResult(False, error="노트 추가 실패")
            
        elif parsed.subcommand == 'add':
            # 명시적인 add 서브커맨드 처리
            if not parsed.title or not parsed.title.strip():
                return HelperResult(False, error="태스크 제목을 입력해주세요")
            
            task = self.add_task(parsed.title, parsed.description)
            if task:
                task_count = len(self.state.current_plan.tasks)
                return HelperResult(True, data={
                    'success': True,
                    'task': {
                        'id': task.id,
                        'title': task.title,
                        'description': task.description,
                        'index': task_count
                    },
                    'message': f"✅ 태스크 추가: {task.title}"
                })
            else:
                return HelperResult(False, error="태스크 추가 실패")
            
        elif parsed.title and parsed.subcommand != 'note' and parsed.subcommand != 'add':
            # 서브커맨드가 필요한 경우
            return HelperResult(False, error="서브커맨드를 사용해주세요. 예: /task add 새로운 태스크 | /task list | /task current")
                
        else:
            # 태스크 목록 (인자 없이 /task만 입력한 경우)
            tasks = self.get_tasks()
            return HelperResult(True, data={
                'success': True,
                'tasks': tasks,
                'count': len(tasks)
            })

            
    def _handle_next(self, parsed) -> HelperResult:
        """next 명령 처리"""
        if not self.state.current_plan:
            return HelperResult(False, error="활성 플랜이 없습니다")
            
        current = self.get_current_task()
        if not current:
            # 태스크가 하나도 없는 경우와 모든 태스크가 완료된 경우 구분
            if not self.state.current_plan.tasks:
                return HelperResult(True, data={
                    'success': True,
                    'message': "플랜에 태스크가 없습니다. /task [태스크명]으로 추가하세요",
                    'completed': False
                })
            else:
                # 모든 태스크가 실제로 완료된 경우
                return HelperResult(True, data={
                    'success': True,
                    'message': "모든 태스크가 완료되었습니다",
                    'completed': True
                })
            
        # 현재 태스크 완료
        note = parsed.args.get('note', parsed.title)
        next_task = self.complete_current_task(note)
        
        # 진행률 정보 계산
        total_tasks = len(self.state.current_plan.tasks)
        completed_tasks = sum(1 for t in self.state.current_plan.tasks if t.status.value == 'completed')
        progress_percent = int((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)
        
        result_data = {
            'success': True,
            'completed_task': {
                'id': current.id,
                'title': current.title,
                'duration': current.duration
            },
            'message': f"✅ 완료: {current.title}",
            # 진행률 정보 추가
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'progress_percent': progress_percent
        }
        
        if next_task:
            result_data['next_task'] = {
                'id': next_task.id,
                'title': next_task.title,
                'description': next_task.description
            }
            result_data['message'] += f"\n🎯 다음: {next_task.title}"
        else:
            result_data['completed'] = True
            result_data['message'] += "\n🎉 모든 태스크 완료!"
            
        return HelperResult(True, data=result_data)
        
    def _handle_build(self, parsed) -> HelperResult:
        """build 명령 처리 - 개선된 버전"""
        from pathlib import Path
        import json
        import os

        # 간단한 프로젝트 정보 수집
        project_info = {
            'name': Path.cwd().name,
            'path': str(Path.cwd()),
            'file_count': 0,
            'dir_count': 0
        }

        # 파일 개수 세기 (간단한 버전)
        try:
            for root, dirs, files in os.walk('.'):
                if '.git' not in root:
                    project_info['file_count'] += len(files)
                    project_info['dir_count'] += len(dirs)
        except:
            pass

        if parsed.subcommand == 'review':
            # 플랜 리뷰
            if not self.state.current_plan:
                return HelperResult(False, error="활성 플랜이 없습니다")

            status = self.get_status()
            events = self.get_recent_events(20)

            return HelperResult(True, data={
                'success': True,
                'type': 'review_with_context',
                'plan_status': status,
                'recent_events': events,
                'project_info': project_info,
                'message': "📊 플랜 리뷰 (프로젝트 정보 포함)"
            })

        elif parsed.subcommand == 'task':
            # 현재 태스크 문서화
            current = self.get_current_task()
            if not current:
                return HelperResult(False, error="현재 작업 중인 태스크가 없습니다")

            return HelperResult(True, data={
                'success': True,
                'type': 'task_doc_with_context',
                'task': {
                    'id': current.id,
                    'title': current.title,
                    'description': current.description,
                    'notes': current.notes,
                    'outputs': current.outputs
                },
                'project_info': project_info,
                'message': f"📄 태스크 문서화: {current.title}"
            })

        else:
            # 기본 빌드
            status = self.get_status()

            # README 확인
            readme_exists = Path('README.md').exists()

            return HelperResult(True, data={
                'success': True,
                'type': 'build_with_context',
                'workflow_status': status,
                'project_info': project_info,
                'readme_exists': readme_exists,
                'message': f"🔨 빌드 완료 - {project_info['name']} ({project_info['file_count']} files)"
            })
    def _handle_status(self, parsed) -> HelperResult:
        """status 명령 처리"""
        if parsed.subcommand == 'history':
            # 히스토리 조회
            history = self.get_plan_history()
            events = self.get_recent_events(30)
            
            return HelperResult(True, data={
                'success': True,
                'history': {
                    'plans': history,
                    'recent_events': events
                },
                'message': f"📜 히스토리: {len(history)}개 플랜, {len(events)}개 최근 이벤트"
            })
            
        else:
            # 현재 상태
            status = self.get_status()
            
            if status['status'] == 'no_plan':
                return HelperResult(True, data={
                    'success': True,
                    'status': status
                })
            else:
                # 추가 정보 포함
                tasks = self.get_tasks()
                recent_events = self.get_recent_events(5)
                
                return HelperResult(True, data={
                    'success': True,
                    'status': status,
                    'tasks_summary': {
                        'total': len(tasks),
                        'completed': len([t for t in tasks if t['status'] == 'completed']),
                        'in_progress': len([t for t in tasks if t['status'] == 'in_progress']),
                        'todo': len([t for t in tasks if t['status'] == 'todo'])
                    },
                    'recent_activity': recent_events
                })
                
    # 유틸리티 메서드
    
    def clear_cache(self) -> None:
        """캐시 클리어 (필요시 구현)"""
        pass
        
    def save(self) -> bool:
        """워크플로우 상태를 파일에 저장 (public 메서드)"""
        return self._save_data()
        
    def reload(self) -> None:
        """데이터 다시 로드"""
        self._load_data()
        
    def export_data(self) -> Dict[str, Any]:
        """전체 데이터 내보내기"""
        return self.state.to_dict()
        
    def import_data(self, data: Dict[str, Any]) -> bool:
        """데이터 가져오기"""
        try:
            self.state = WorkflowState.from_dict(data)
            self.event_store.from_list(self.state.events)
            self._save_data()
            return True
        except Exception as e:
            logger.error(f"Failed to import data: {e}")
            return False
    
    def cleanup(self):
        """리소스 정리 및 이벤트 어댑터 해제"""
        if hasattr(self, 'event_adapter'):
            self.event_adapter.cleanup()
            logger.info(f"WorkflowEventAdapter cleaned up for project: {self.project_name}")
    
    def _add_event(self, event):
        """이벤트를 EventStore에 추가하고 EventBus로 발행"""
        # EventStore에 추가
        self.event_store.add(event)
        
        # EventBus로 발행 (event_adapter가 있는 경우)
        if hasattr(self, 'event_adapter') and self.event_adapter:
            try:
                self.event_adapter.publish_workflow_event(event)
            except Exception as e:
                logger.error(f"Failed to publish event to EventBus: {e}")
