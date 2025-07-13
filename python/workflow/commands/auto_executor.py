"""
Auto Task Executor
==================

태스크를 자동으로 순차 실행하는 실행기
"""

import threading
import logging
import time
from typing import Optional, Callable, Dict, Any
from datetime import datetime
from queue import Queue, Empty

from ..models import Task, TaskStatus, EventType
from ..event_bus import event_bus

logger = logging.getLogger(__name__)


class AutoTaskExecutor:
    """
    자동 태스크 실행기
    
    태스크를 자동으로 순차 실행하며 실행 전/후 훅을 지원
    """
    
    def __init__(self, workflow_manager):
        self.manager = workflow_manager
        self.is_running = False
        self.is_paused = False
        self.current_task: Optional[Task] = None
        
        # 실행 제어
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        
        # 실행 옵션
        self.pause_on_error = True
        self.auto_skip_blocked = True
        self.delay_between_tasks = 1.0  # 초
        
        # 실행 훅
        self.hooks: Dict[str, list[Callable]] = {
            'before_task': [],
            'after_task': [],
            'on_error': [],
            'on_blocked': [],
            'on_complete': []
        }
        
        # 통계
        self.stats = {
            'total_executed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None,
            'end_time': None
        }
        
        # 이벤트 구독
        self._subscribe_events()
        
    def _subscribe_events(self):
        """워크플로우 이벤트 구독"""
        # 태스크 완료 이벤트 구독
        event_bus.subscribe(EventType.TASK_COMPLETED.value, self._on_task_completed)
        event_bus.subscribe(EventType.TASK_FAILED.value, self._on_task_failed)
        
    def start(self):
        """자동 실행 시작"""
        if self.is_running:
            logger.warning("Auto executor is already running")
            return
            
        self.is_running = True
        self.is_paused = False
        self._stop_event.clear()
        self.stats['start_time'] = datetime.now()
        
        # 실행 스레드 시작
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        logger.info("Auto task executor started")
        
    def stop(self):
        """자동 실행 중지"""
        if not self.is_running:
            return
            
        self.is_running = False
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=5)
            
        self.stats['end_time'] = datetime.now()
        logger.info("Auto task executor stopped")
        
    def pause(self):
        """일시 정지"""
        if not self.is_running:
            return
            
        self.is_paused = True
        self._pause_event.set()
        logger.info("Auto task executor paused")
        
    def resume(self):
        """재개"""
        if not self.is_running:
            return
            
        self.is_paused = False
        self._pause_event.clear()
        logger.info("Auto task executor resumed")
        
    def _run_loop(self):
        """메인 실행 루프"""
        logger.info("Auto execution loop started")
        
        while not self._stop_event.is_set():
            try:
                # 일시 정지 체크
                if self.is_paused:
                    time.sleep(0.5)
                    continue
                    
                # 다음 실행할 태스크 가져오기
                task = self._get_next_executable_task()
                
                if not task:
                    # 모든 태스크 완료 또는 실행할 태스크 없음
                    logger.info("No more tasks to execute")
                    self._on_all_complete()
                    break
                    
                # 태스크 실행
                self._execute_task(task)
                
                # 태스크 간 지연
                time.sleep(self.delay_between_tasks)
                
            except Exception as e:
                logger.error(f"Error in auto execution loop: {e}")
                if self.pause_on_error:
                    self.pause()
                    
        logger.info("Auto execution loop ended")
        
    def _get_next_executable_task(self) -> Optional[Task]:
        """다음 실행 가능한 태스크 찾기"""
        current = self.manager.get_current_task()
        
        if not current:
            return None
            
        # 상태 체크
        if current.status == TaskStatus.COMPLETED:
            # 이미 완료된 경우 다음 태스크로
            return self._get_next_executable_task()
            
        if current.status == TaskStatus.CANCELLED:
            # 취소된 태스크는 건너뛰기
            self.stats['skipped'] += 1
            return self._get_next_executable_task()
            
        # 의존성 체크
        if self._has_unmet_dependencies(current):
            if self.auto_skip_blocked:
                logger.info(f"Skipping blocked task: {current.title}")
                self.stats['skipped'] += 1
                self._run_hooks('on_blocked', current)
                
                # 차단 상태로 표시
                if hasattr(self.manager, 'block_task'):
                    self.manager.block_task(current.id, "의존성 미충족")
                    
                return self._get_next_executable_task()
            else:
                # 의존성이 해결될 때까지 대기
                return None
                
        return current
        
    def _has_unmet_dependencies(self, task: Task) -> bool:
        """태스크의 의존성이 충족되지 않았는지 확인"""
        if 'dependencies' not in task.outputs:
            return False
            
        dependencies = task.outputs['dependencies']
        if not isinstance(dependencies, list):
            return False
            
        # 각 의존성 체크
        for dep_id in dependencies:
            dep_task = self.manager.internal_api.get_task_by_id(dep_id)
            if dep_task and dep_task.status != TaskStatus.COMPLETED:
                return True
                
        return False
        
    def _execute_task(self, task: Task):
        """태스크 실행"""
        self.current_task = task
        self.stats['total_executed'] += 1
        
        logger.info(f"Auto executing task: {task.title}")
        
        try:
            # 실행 전 훅
            self._run_hooks('before_task', task)
            
            # 태스크 시작
            self.manager.internal_api.update_task_status(
                task.id, 
                TaskStatus.IN_PROGRESS,
                {'auto_executed': True, 'auto_start_time': datetime.now().isoformat()}
            )
            
            # 실제 태스크 실행 로직
            # 여기서는 시뮬레이션을 위해 지연만 추가
            # 실제로는 태스크의 명령어나 스크립트를 실행해야 함
            self._simulate_task_execution(task)
            
            # 태스크 완료
            self.manager.complete_task(task.id, "자동 실행 완료")
            self.stats['successful'] += 1
            
            # 실행 후 훅
            self._run_hooks('after_task', task)
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            self.stats['failed'] += 1
            
            # 실패 처리
            if hasattr(self.manager, 'fail_task'):
                self.manager.fail_task(task.id, str(e))
                
            # 에러 훅
            self._run_hooks('on_error', task, error=e)
            
            if self.pause_on_error:
                self.pause()
                
        finally:
            self.current_task = None
            
    def _simulate_task_execution(self, task: Task):
        """태스크 실행 시뮬레이션 (실제 구현 시 교체 필요)"""
        # 태스크 설명에서 실행 명령어 추출
        if task.description and task.description.startswith("CMD:"):
            command = task.description[4:].strip()
            logger.info(f"Would execute command: {command}")
            
        # 시뮬레이션을 위한 지연
        execution_time = task.outputs.get('estimated_duration', 2.0)
        time.sleep(execution_time)
        
    def _on_task_completed(self, event):
        """태스크 완료 이벤트 핸들러"""
        if self.is_running and not self.is_paused:
            # 자동 실행 중이면 다음 태스크 확인
            if event.task_id == self.current_task.id if self.current_task else False:
                logger.debug("Current task completed, checking for next task")
                
    def _on_task_failed(self, event):
        """태스크 실패 이벤트 핸들러"""
        if self.pause_on_error and self.is_running:
            self.pause()
            
    def _on_all_complete(self):
        """모든 태스크 완료 시 호출"""
        logger.info("All tasks completed")
        self._run_hooks('on_complete')
        self.stop()
        
    def _run_hooks(self, hook_type: str, task: Optional[Task] = None, **kwargs):
        """훅 실행"""
        if hook_type not in self.hooks:
            return
            
        for hook in self.hooks[hook_type]:
            try:
                hook(task, **kwargs)
            except Exception as e:
                logger.error(f"Hook execution error: {e}")
                
    def register_hook(self, hook_type: str, callback: Callable):
        """훅 등록
        
        Args:
            hook_type: 'before_task', 'after_task', 'on_error', 'on_blocked', 'on_complete'
            callback: 콜백 함수
        """
        if hook_type not in self.hooks:
            raise ValueError(f"Invalid hook type: {hook_type}")
            
        self.hooks[hook_type].append(callback)
        logger.debug(f"Registered hook: {hook_type}")
        
    def unregister_hook(self, hook_type: str, callback: Callable):
        """훅 제거"""
        if hook_type in self.hooks and callback in self.hooks[hook_type]:
            self.hooks[hook_type].remove(callback)
            
    def get_status(self) -> Dict[str, Any]:
        """실행기 상태 조회"""
        status = {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'current_task': self.current_task.title if self.current_task else None,
            'stats': self.stats.copy()
        }
        
        # 실행 시간 계산
        if self.stats['start_time']:
            end_time = self.stats['end_time'] or datetime.now()
            duration = (end_time - self.stats['start_time']).total_seconds()
            status['stats']['duration_seconds'] = duration
            
        return status
        
    def __del__(self):
        """소멸자"""
        self.stop()
        # 이벤트 구독 해제
        event_bus.unsubscribe(EventType.TASK_COMPLETED.value, self._on_task_completed)
        event_bus.unsubscribe(EventType.TASK_FAILED.value, self._on_task_failed)


# Export
__all__ = ['AutoTaskExecutor']
