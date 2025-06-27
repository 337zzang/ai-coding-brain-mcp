"""
import sys
import os
# Python 경로 설정
python_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if python_path not in sys.path:
    sys.path.insert(0, python_path)

AI Coding Brain MCP - Workflow Manager
통합 워크플로우 관리자
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import logging

from core.context_manager import get_context_manager
from core.models import Plan, Phase, Task, ProjectContext
from core.decorators import autosave
from core.error_handler import ErrorHandler, ErrorType, StandardResponse

logger = logging.getLogger(__name__)


class WorkflowManager:
    """Plan/Task 조작을 일원화하는 통합 매니저"""
    
    def __init__(self):
        self.context_manager = get_context_manager()
        self._event_hooks = {
            'task_started': [],
            'task_completed': [],
            'plan_created': [],
            'task_blocked': []
        }
    
    @property
    def context(self) -> Optional[ProjectContext]:
        """현재 컨텍스트"""
        return self.context_manager.context
    
    @property
    def plan(self) -> Optional[Plan]:
        """현재 계획"""
        return self.context.plan if self.context else None
    
    # ========== 프로젝트 관리 ==========
    
    def load_project(self, project_name: str) -> StandardResponse:
        """프로젝트 로드"""
        try:
            # 컨텍스트 초기화는 context_manager가 담당
            # 여기서는 Plan 관련 추가 작업만
            if not self.context:
                return StandardResponse.error(
                    ErrorType.CONTEXT_ERROR,
                    "프로젝트 컨텍스트 로드 실패"
                )
            
            # 레거시 큐 마이그레이션 체크
            if hasattr(self.context, 'tasks') and self.context.tasks:
                self.migrate_legacy_queue()
            
            return StandardResponse.success({
                'project': self.context.project_name,
                'plan': self.plan.name if self.plan else None
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e, ErrorType.CONTEXT_ERROR)
    
    @autosave
    def create_plan(self, name: str, description: str, phases: List[Dict[str, Any]] = None) -> StandardResponse:
        """새 계획 생성"""
        try:
            # 기본 Phase 구조
            if not phases:
                phases = self._get_default_phases()
            
            # Plan 객체 생성
            plan = Plan(
                name=name,
                description=description,
                phases={phase['id']: Phase(**phase) for phase in phases}
            )
            
            # 컨텍스트에 설정
            self.context.plan = plan
            self.context.updated_at = datetime.now()
            
            # 이벤트 발생
            self._trigger_event('plan_created', plan)
            
            return StandardResponse.success({
                'plan': plan,
                'plan_name': plan.name,
                'phases': len(plan.phases),
                'tasks': len(plan.get_all_tasks())
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e, ErrorType.PLAN_ERROR)
    
    @autosave
    def reset_plan(self) -> StandardResponse:
        """계획 초기화 (모든 계획과 작업 삭제)"""
        try:
            if self.context.plan:
                old_plan_name = self.context.plan.name
                self.context.plan = None
                self.context.updated_at = datetime.now()
                
                # 이벤트 발생
                self._trigger_event('plan_reset', {'old_plan': old_plan_name})
                
                return StandardResponse.success({
                    'message': f"계획 '{old_plan_name}'이(가) 초기화되었습니다."
                })
            else:
                return StandardResponse.success({
                    'message': "초기화할 계획이 없습니다."
                })
        except Exception as e:
            return ErrorHandler.handle_exception(e, ErrorType.PLAN_ERROR)
    
    # ========== 작업 관리 ==========
    
    @autosave
    def add_task(self, phase_id: str, title: str, description: str = "", 
                 priority: str = "medium", dependencies: List[str] = None) -> StandardResponse:
        """작업 추가"""
        try:
            if not self.plan:
                return StandardResponse.error(ErrorType.PLAN_ERROR, "계획이 없습니다")
            
            phase = self.plan.phases.get(phase_id)
            if not phase:
                return StandardResponse.error(
                    ErrorType.VALIDATION_ERROR,
                    f"Phase {phase_id}를 찾을 수 없습니다"
                )
            
            # Task 추가 (Phase의 add_task 메서드 사용)
            task = phase.add_task(title, description)
            
            # 의존성 설정
            if dependencies:
                for dep_id in dependencies:
                    task.add_dependency(dep_id)
            
            # Plan을 context.tasks와 동기화
            self.context_manager.sync_plan_to_tasks()
            
            return StandardResponse.success({
                'task_id': task.id,
                'title': task.title,
                'phase': phase.name
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e, ErrorType.TASK_ERROR)
    
    @autosave
    def start_next_task(self) -> StandardResponse:
        """다음 작업 시작"""
        try:
            if not self.plan:
                return StandardResponse.error(ErrorType.PLAN_ERROR, "계획이 없습니다")
            
            # 현재 작업이 있으면 확인
            if self.context.current_task:
                current = self.plan.get_task_by_id(self.context.current_task)
                if current and current.status == 'in_progress':
                    return StandardResponse.error(
                        ErrorType.TASK_ERROR,
                        f"현재 작업 '{current.title}'이 진행 중입니다"
                    )
            
            # 다음 작업 선택
            next_task = self.plan.get_next_task()
            if not next_task:
                # 차단된 작업 확인
                blocked = self.plan.get_blocked_tasks()
                if blocked:
                    return StandardResponse.success({
                        'status': 'blocked',
                        'blocked_tasks': len(blocked),
                        'message': f"{len(blocked)}개 작업이 의존성으로 차단됨"
                    })
                else:
                    return StandardResponse.success({
                        'status': 'no_tasks',
                        'message': "대기 중인 작업이 없습니다"
                    })
            
            # 작업 시작
            next_task.transition_to('in_progress')
            self.context.current_task = next_task.id
            self.context_manager.set_current_task(next_task.id)
            
            # Phase 상태 업데이트
            phase = self._get_task_phase(next_task.id)
            if phase and phase.status == 'pending':
                phase.status = 'in_progress'
            
            # 이벤트 발생
            self._trigger_event('task_started', next_task)
            
            return StandardResponse.success({
                'task_id': next_task.id,
                'title': next_task.title,
                'phase': phase.name if phase else None,
                'estimated_hours': next_task.estimated_hours
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e, ErrorType.TASK_ERROR)
    
    @autosave
    def complete_task(self, task_id: Optional[str] = None) -> StandardResponse:
        """작업 완료"""
        try:
            if not self.plan:
                return StandardResponse.error(ErrorType.PLAN_ERROR, "계획이 없습니다")
            
            # 대상 작업 확인
            if not task_id:
                task_id = self.context.current_task
            
            if not task_id:
                return StandardResponse.error(ErrorType.TASK_ERROR, "완료할 작업이 없습니다")
            
            task = self.plan.get_task_by_id(task_id)
            if not task:
                return StandardResponse.error(
                    ErrorType.TASK_ERROR,
                    f"작업 {task_id}를 찾을 수 없습니다"
                )
            
            # 상태 전환
            if not task.transition_to('completed'):
                return StandardResponse.error(
                    ErrorType.TASK_ERROR,
                    f"작업을 완료할 수 없습니다 (현재 상태: {task.status})"
                )
            
            # 현재 작업이면 해제
            if task_id == self.context.current_task:
                self.context.current_task = None
                self.context_manager.set_current_task(None)
            
            # Phase 완료 체크
            phase = self._get_task_phase(task_id)
            if phase and phase.can_complete():
                phase.status = 'completed'
            
            # 진행률 업데이트
            self.context_manager.update_progress()
            
            # Plan을 context.tasks와 동기화
            self.context_manager.sync_plan_to_tasks()
            
            # 이벤트 발생
            self._trigger_event('task_completed', task)
            
            return StandardResponse.success({
                'task_id': task.id,
                'title': task.title,
                'actual_hours': task.actual_hours,
                'phase_completed': phase.status == 'completed' if phase else False
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e, ErrorType.TASK_ERROR)
    
    # ========== 조회 및 분석 ==========
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """전체 워크플로우 상태"""
        if not self.plan:
            return {'status': 'no_plan'}
        
        all_tasks = self.plan.get_all_tasks()
        
        status_count = {}
        for task in all_tasks:
            status_count[task.status] = status_count.get(task.status, 0) + 1
        
        return {
            'plan': self.plan.name,
            'total_tasks': len(all_tasks),
            'status_breakdown': status_count,
            'current_task': self.context.current_task,
            'progress': self.plan.overall_progress,
            'phases': {
                phase_id: {
                    'name': phase.name,
                    'status': phase.status,
                    'progress': phase.progress
                }
                for phase_id, phase in self.plan.phases.items()
            }
        }
    
    def get_task_analytics(self) -> Dict[str, Any]:
        """작업 분석 데이터"""
        if not self.plan:
            return {}
        
        tasks = self.plan.get_all_tasks()
        
        # 시간 분석
        total_estimated = sum(t.estimated_hours or 0 for t in tasks)
        total_actual = sum(t.actual_hours or 0 for t in tasks if t.status == 'completed')
        
        # 상태별 평균 시간
        time_by_status = {}
        for status in ['pending', 'in_progress', 'completed']:
            status_times = [t.get_time_in_state(status) for t in tasks]
            time_by_status[status] = sum(status_times) / len(status_times) if status_times else 0
        
        return {
            'total_estimated_hours': total_estimated,
            'total_actual_hours': total_actual,
            'efficiency': (total_estimated / total_actual * 100) if total_actual > 0 else None,
            'average_time_by_status': time_by_status,
            'blocked_tasks': len(self.plan.get_blocked_tasks()),
            'ready_tasks': len(self.plan.get_ready_tasks())
        }
    
    def get_bottlenecks(self) -> List[Dict[str, Any]]:
        """병목 현상 분석"""
        if not self.plan:
            return []
        
        bottlenecks = []
        
        # 차단된 작업들
        blocked_tasks = self.plan.get_blocked_tasks()
        for task in blocked_tasks:
            bottlenecks.append({
                'type': 'blocked_task',
                'task_id': task.id,
                'title': task.title,
                'reason': task.blocking_reason or '의존성 미충족',
                'dependencies': task.check_dependencies()
            })
        
        # 오래 진행 중인 작업
        for task in self.plan.get_all_tasks():
            if task.status == 'in_progress':
                hours_in_progress = task.get_time_in_state('in_progress')
                if task.estimated_hours and hours_in_progress > task.estimated_hours * 1.5:
                    bottlenecks.append({
                        'type': 'overdue_task',
                        'task_id': task.id,
                        'title': task.title,
                        'estimated': task.estimated_hours,
                        'actual': hours_in_progress,
                        'overdue_by': hours_in_progress - task.estimated_hours
                    })
        
        return bottlenecks
    
    # ========== 동기화 및 마이그레이션 ==========
    
    @autosave
    def migrate_legacy_queue(self) -> StandardResponse:
        """레거시 큐(context.tasks) 마이그레이션"""
        try:
            if not self.context or not hasattr(self.context, 'tasks'):
                return StandardResponse.success({'migrated': 0})
            
            migrated = 0
            
            # next 큐의 작업들을 Plan에 반영
            if 'next' in self.context.tasks:
                for task_info in self.context.tasks['next']:
                    task_id = task_info.get('id')
                    if task_id and self.plan:
                        task = self.plan.get_task_by_id(task_id)
                        if task and task.status == 'pending':
                            # ready 상태로 변경 (큐에 있었으므로)
                            task.status = 'ready'
                            migrated += 1
            
            # 큐 제거
            if hasattr(self.context, 'tasks'):
                delattr(self.context, 'tasks')
            
            return StandardResponse.success({
                'migrated': migrated,
                'message': f"{migrated}개 작업을 마이그레이션했습니다"
            })
        except Exception as e:
            return ErrorHandler.handle_exception(e, ErrorType.CONTEXT_ERROR)
    
    # ========== 헬퍼 메서드 ==========
    
    def _get_default_phases(self) -> List[Dict[str, Any]]:
        """기본 Phase 구조"""
        return [
            {
                'id': 'phase-1',
                'name': 'Phase 1: 분석 및 설계',
                'description': '요구사항 분석 및 설계',
                'tasks': []
            },
            {
                'id': 'phase-2',
                'name': 'Phase 2: 핵심 구현',
                'description': '주요 기능 구현',
                'tasks': []
            },
            {
                'id': 'phase-3',
                'name': 'Phase 3: 테스트 및 문서화',
                'description': '테스트 및 문서 작성',
                'tasks': []
            }
        ]
    
    def _get_task_phase(self, task_id: str) -> Optional[Phase]:
        """작업이 속한 Phase 찾기"""
        if not self.plan:
            return None
        
        for phase in self.plan.phases.values():
            if phase.get_task_by_id(task_id):
                return phase
        return None
    
    def _trigger_event(self, event_name: str, data: Any) -> None:
        """이벤트 발생"""
        if event_name in self._event_hooks:
            for hook in self._event_hooks[event_name]:
                try:
                    hook(data)
                except Exception as e:
                    logger.error(f"Event hook error: {e}")
    
    def register_hook(self, event_name: str, callback: callable) -> None:
        """이벤트 훅 등록"""
        if event_name in self._event_hooks:
            self._event_hooks[event_name].append(callback)


# 싱글톤 인스턴스
_workflow_manager_instance = None

def get_workflow_manager() -> WorkflowManager:
    """WorkflowManager 싱글톤 인스턴스 반환"""
    global _workflow_manager_instance
    if _workflow_manager_instance is None:
        _workflow_manager_instance = WorkflowManager()
    return _workflow_manager_instance
