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
import json
import logging
from core.context_manager import get_context_manager
from core.models import Plan, Phase, Task, ProjectContext, TaskStatus
from core.decorators import autosave
from core.error_handler import ErrorHandler, ErrorType, StandardResponse
import uuid
logger = logging.getLogger(__name__)

class WorkflowManager:
    """Plan/Task 조작을 일원화하는 통합 매니저"""

    def __init__(self):
        self.context_manager = get_context_manager()
        self._event_hooks = {'task_started': [], 'task_completed': [], 'plan_created': [], 'task_blocked': []}

    @property
    def context(self) -> Optional[ProjectContext]:
        """현재 컨텍스트"""
        return self.context_manager.context

    @property
    def plan(self) -> Optional[Plan]:
        """현재 계획"""
        return self.context.plan if self.context else None

    def load_project(self, project_name: str) -> StandardResponse:
        """프로젝트 로드"""
        try:
            if not self.context:
                return StandardResponse.error(ErrorType.CONTEXT_ERROR, '프로젝트 컨텍스트 로드 실패')
            return StandardResponse.success({'project': self.context.project_name, 'plan': self.plan.name if self.plan else None})
        except Exception as e:
            return ErrorHandler.handle_exception(e, ErrorType.CONTEXT_ERROR)

    @autosave
    def create_plan(self, name: str, description: str, phases: List[Dict[str, Any]]=None, content: str=None) -> StandardResponse:
        """새 계획 생성"""
        try:
            if not phases:
                phases = self._get_default_phases()
            plan = Plan(name=name, description=description, phases={phase['id']: Phase(**phase) for phase in phases}, phase_order=[phase['id'] for phase in phases], content=content)
            if content:
                plan.content_history.append({'timestamp': datetime.now().isoformat(), 'content': content, 'action': 'created'})
            self.context.plan = plan
            self.context.updated_at = datetime.now()
            self._trigger_event('plan_created', plan)
            return StandardResponse.success({'plan': plan, 'plan_name': plan.name, 'phases': len(plan.phases), 'tasks': len(plan.get_all_tasks())})
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
                self._trigger_event('plan_reset', {'old_plan': old_plan_name})
                return StandardResponse.success({'message': f"계획 '{old_plan_name}'이(가) 초기화되었습니다."})
            else:
                return StandardResponse.success({'message': '초기화할 계획이 없습니다.'})
        except Exception as e:
            return ErrorHandler.handle_exception(e, ErrorType.PLAN_ERROR)

    @autosave
    def add_task(self, phase_id: str, title: str, description: str='', content: Optional[str]=None, priority: str='medium', dependencies: List[str]=None) -> StandardResponse:
        """작업 추가"""
        try:
            if not self.plan:
                return StandardResponse.error(ErrorType.PLAN_ERROR, '계획이 없습니다')
            phase = self.plan.phases.get(phase_id)
            if not phase:
                return StandardResponse.error(ErrorType.VALIDATION_ERROR, f'Phase {phase_id}를 찾을 수 없습니다')
            task = phase.add_task(title, description)
            if dependencies:
                for dep_id in dependencies:
                    task.add_dependency(dep_id)
            self.context_manager.sync_plan_to_tasks()
            return StandardResponse.success({'task_id': task.id, 'title': task.title, 'phase': phase.name})
        except Exception as e:
            return ErrorHandler.handle_exception(e, ErrorType.TASK_ERROR)

    @autosave
    def start_next_task(self) -> StandardResponse:
        """다음 작업 시작"""
        try:
            if not self.plan:
                return StandardResponse.error(ErrorType.PLAN_ERROR, '계획이 없습니다')
            if self.context.current_task:
                current = self.plan.get_task_by_id(self.context.current_task)
                if current and current.status == 'in_progress':
                    return StandardResponse.error(ErrorType.TASK_ERROR, f"현재 작업 '{current.title}'이 진행 중입니다")
            result = self.plan.get_next_task()
            if not result:
                blocked = self.plan.get_blocked_tasks()
                if blocked:
                    return StandardResponse.success({'status': 'blocked', 'blocked_tasks': len(blocked), 'message': f'{len(blocked)}개 작업이 의존성으로 차단됨'})
                else:
                    return StandardResponse.success({'status': 'no_tasks', 'message': '대기 중인 작업이 없습니다'})
            phase_id, next_task = result
            next_task.status = TaskStatus.IN_PROGRESS
            self.context.current_task = next_task.id
            self.context_manager.set_current_task(next_task.id)
            phase = self.plan.phases.get(phase_id)
            if phase and phase.status == 'pending':
                phase.status = 'in_progress'
            self._trigger_event('task_started', next_task)
            return StandardResponse.success({'id': next_task.id, 'task_id': next_task.id, 'title': next_task.title, 'description': next_task.description, 'phase': phase_id, 'phase_name': phase.name if phase else None, 'estimated_hours': next_task.estimated_hours})
        except Exception as e:
            return ErrorHandler.handle_exception(e, ErrorType.TASK_ERROR)

    @autosave

    @autosave
    @autosave
    def advance_to_next_step(self, content: Optional[str] = None) -> Dict[str, Any]:
        """
        현재 Task를 완료 처리하고, 다음 Task를 찾아 진행 상태로 설정합니다.
        
        이 메서드는 complete_task와 start_next_task를 하나의 트랜잭션으로 처리하여
        상태 불일치를 방지하고 더 안정적인 워크플로우를 제공합니다.
        
        Args:
            content: 현재 작업의 완료 내용/요약 (선택사항)
            
        Returns:
            Dict[str, Any]: 작업 결과
                - success: bool
                - message: str
                - data: Optional[Dict] - 다음 작업 정보 또는 None
                - completed_task: Optional[Dict] - 완료된 작업 정보
        """
        result = {
            'success': False,
            'message': '',
            'data': None,
            'completed_task': None
        }
        
        try:
            # 1. 현재 작업이 있으면 완료 처리
            if self.context.current_task:
                try:
                    complete_result = self.complete_task(content=content)
                    if complete_result['success']:
                        result['completed_task'] = complete_result['data']
                    else:
                        # 완료 실패해도 다음 작업은 시도
                        result['message'] = f"작업 완료 실패: {complete_result['message']}. "
                except Exception as e:
                    # 오류가 발생해도 계속 진행
                    result['message'] = f"작업 완료 중 오류: {str(e)}. "
            
            # 2. 다음 작업 시작
            try:
                next_result = self.start_next_task()
                
                if next_result['success']:
                    result['success'] = True
                    result['data'] = next_result['data']
                    result['message'] += f"다음 작업 시작: {next_result['data']['title']}"
                else:
                    # 다음 작업이 없는 경우
                    result['success'] = True  # 이것도 정상적인 상황
                    result['message'] += next_result['message']
            except Exception as e:
                result['message'] += f"다음 작업 시작 중 오류: {str(e)}"
                
        except Exception as e:
            result['message'] = f"예상치 못한 오류: {str(e)}"
        
        return result
    def complete_task(self, task_id: Optional[str]=None, content: Optional[str]=None) -> StandardResponse:
        """작업 완료"""
        try:
            if not self.plan:
                return StandardResponse.error(ErrorType.PLAN_ERROR, '계획이 없습니다')
            if not task_id:
                task_id = self.context.current_task
            if not task_id:
                return StandardResponse.error(ErrorType.TASK_ERROR, '완료할 작업이 없습니다')
            task = self.plan.get_task_by_id(task_id)
            if not task:
                return StandardResponse.error(ErrorType.TASK_ERROR, f'작업 {task_id}를 찾을 수 없습니다')
            if content:
                task.content = content
            if not task.transition_to('completed'):
                return StandardResponse.error(ErrorType.TASK_ERROR, f'작업을 완료할 수 없습니다 (현재 상태: {task.status})')
            if task_id == self.context.current_task:
                self.context.current_task = None
                self.context_manager.set_current_task(None)
            phase = self._get_task_phase(task_id)
            if phase and phase.can_complete():
                try:
                    from core.models import TaskStatus
                    phase.status = TaskStatus.COMPLETED
                except:
                    phase.status = 'completed'
            self.context_manager.update_progress()
            self.context_manager.sync_plan_to_tasks()
            self._trigger_event('task_completed', task)
            return StandardResponse.success({'task_id': task.id, 'title': task.title, 'actual_hours': task.actual_hours, 'phase_completed': (phase.status == TaskStatus.COMPLETED if hasattr(phase.status, 'value') else phase.status == 'completed') if phase else False})
        except Exception as e:
            return ErrorHandler.handle_exception(e, ErrorType.TASK_ERROR)

    def get_workflow_status(self) -> dict:
        """워크플로우 진행 상태 반환
        
        Returns:
            진행률, 완료/전체 작업 수, 현재 작업 정보
        """
        all_tasks = self.plan.get_all_tasks() if self.plan else []
        completed = sum((1 for t in all_tasks if t.status == TaskStatus.COMPLETED))
        total = len(all_tasks)
        progress = completed / total * 100 if total > 0 else 0.0
        return {'progress': round(progress, 1), 'completed_tasks': completed, 'total_tasks': total, 'current_task': self.context.current_task}

    def get_task_analytics(self) -> Dict[str, Any]:
        """작업 분석 데이터"""
        if not self.plan:
            return {}
        tasks = self.plan.get_all_tasks()
        total_estimated = sum((t.estimated_hours or 0 for t in tasks))
        total_actual = sum((t.actual_hours or 0 for t in tasks if t.status == 'completed'))
        time_by_status = {}
        for status in ['pending', 'in_progress', 'completed']:
            status_times = [t.get_time_in_state(status) for t in tasks]
            time_by_status[status] = sum(status_times) / len(status_times) if status_times else 0
        return {'total_estimated_hours': total_estimated, 'total_actual_hours': total_actual, 'efficiency': total_estimated / total_actual * 100 if total_actual > 0 else None, 'average_time_by_status': time_by_status, 'average_completion_time': None}

    def get_bottlenecks(self) -> List[Dict[str, Any]]:
        """병목 현상 분석"""
        if not self.plan:
            return []
        bottlenecks = []
        blocked_tasks = []
        for task in blocked_tasks:
            bottlenecks.append({'type': 'blocked_task', 'task_id': task.id, 'title': task.title, 'reason': task.blocking_reason or '의존성 미충족', 'dependencies': task.check_dependencies()})
        for task in self.plan.get_all_tasks():
            if task.status == 'in_progress':
                hours_in_progress = task.get_time_in_state('in_progress')
                if task.estimated_hours and hours_in_progress > task.estimated_hours * 1.5:
                    bottlenecks.append({'type': 'overdue_task', 'task_id': task.id, 'title': task.title, 'estimated': task.estimated_hours, 'actual': hours_in_progress, 'overdue_by': hours_in_progress - task.estimated_hours})
        return bottlenecks

    def migrate_legacy_queue(self) -> StandardResponse:
        """레거시 큐(context.tasks) 마이그레이션"""
        try:
            if not self.context or not hasattr(self.context, 'tasks'):
                return StandardResponse.success({'migrated': 0})
            migrated = 0
            if 'next' in self.context.tasks:
                for task_info in self.context.tasks['next']:
                    task_id = task_info.get('id')
                    if task_id and self.plan:
                        task = self.plan.get_task_by_id(task_id)
                        if task and task.status == 'pending':
                            task.status = 'ready'
                            migrated += 1
            if hasattr(self.context, 'tasks'):
                delattr(self.context, 'tasks')
            return StandardResponse.success({'migrated': migrated, 'message': f'{migrated}개 작업을 마이그레이션했습니다'})
        except Exception as e:
            return ErrorHandler.handle_exception(e, ErrorType.CONTEXT_ERROR)

    def _get_default_phases(self) -> List[Dict[str, Any]]:
        """기본 Phase 구조"""
        return [{'id': 'phase-1', 'name': 'Phase 1: 분석 및 설계', 'description': '요구사항 분석 및 설계', 'tasks': {}}, {'id': 'phase-2', 'name': 'Phase 2: 핵심 구현', 'description': '주요 기능 구현', 'tasks': {}}, {'id': 'phase-3', 'name': 'Phase 3: 테스트 및 문서화', 'description': '테스트 및 문서 작성', 'tasks': {}}]

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
                    logger.error(f'Event hook error: {e}')

    def register_hook(self, event_name: str, callback: callable) -> None:
        """이벤트 훅 등록"""
        if event_name in self._event_hooks:
            self._event_hooks[event_name].append(callback)

    def save(self) -> None:
        """Plan 중심의 통합 저장"""
        import os
        workflow_data = {'version': '2.0', 'last_updated': datetime.now().isoformat(), 'current_plan': None}
        if self.context.plan:
            self.context.plan.update_progress()
            workflow_data['current_plan'] = json.loads(self.context.plan.json())
        unified_path = os.path.join(self.context_manager.cache_dir, 'workflow_unified.json')
        with open(unified_path, 'w', encoding='utf-8') as f:
            json.dump(workflow_data, f, indent=2, ensure_ascii=False)

    def load(self) -> bool:
        """통합 파일에서 Plan 로드"""
        unified_path = os.path.join(self.context_manager.cache_dir, 'workflow_unified.json')
        if os.path.exists(unified_path):
            try:
                with open(unified_path, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)
                if workflow_data.get('version') == '2.0':
                    if workflow_data.get('current_plan'):
                        self.context.plan = Plan(**workflow_data['current_plan'])
                        return True
            except Exception as e:
                print(f'워크플로우 로드 실패: {e}')
        return False

    def sync_plan_to_context(self) -> None:
        """
        Plan 객체(SSoT)의 상태를 context.tasks에 동기화
        - Plan의 모든 Task를 순회하며 상태별로 분류
        - completed 상태 → tasks['done']
        - 나머지 상태 → tasks['next'] 
        - 진행률 정보도 함께 업데이트
        """
        if not self.plan:
            self.context.tasks = {'next': [], 'done': []}
            return
        next_tasks = []
        done_tasks = []
        for phase_id in self.plan.phase_order:
            phase = self.plan.phases.get(phase_id)
            if not phase:
                continue
            for task_id in phase.task_order:
                task = phase.tasks.get(task_id)
                if not task:
                    continue
                task_info = {'id': task.id, 'title': task.title, 'description': task.description, 'phase': phase_id, 'phase_name': phase.name, 'status': task.status.value if hasattr(task.status, 'value') else task.status}
                if task.status == TaskStatus.COMPLETED or task.status == 'completed':
                    done_tasks.append(task_info)
                else:
                    next_tasks.append(task_info)
        self.context.tasks['next'] = next_tasks
        self.context.tasks['done'] = done_tasks
        total = len(next_tasks) + len(done_tasks)
        completed = len(done_tasks)
        if not hasattr(self.context, 'progress'):
            self.context.progress = {}
        self.context.progress.update({'total_tasks': total, 'completed_tasks': completed, 'percentage': round(completed / total * 100 if total > 0 else 0, 1)})

    def analyze_and_generate_tasks(self, project_path: str='.') -> Dict[str, List[Task]]:
        """ProjectAnalyzer를 사용하여 자동으로 Task 생성"""
        from analyzers.project_analyzer import ProjectAnalyzer
        from project_wisdom import get_wisdom_manager
        analyzer = ProjectAnalyzer()
        wisdom = get_wisdom_manager()
        print('🔍 프로젝트 분석 중...')
        analysis_result = analyzer.analyze_project(project_path)
        if self.context.plan:
            self.context.plan.project_insights = {'total_files': analysis_result.get('total_files', 0), 'file_types': analysis_result.get('file_types', {}), 'complexity_score': analysis_result.get('average_complexity', 0), 'largest_files': analysis_result.get('largest_files', []), 'analysis_timestamp': datetime.now().isoformat()}
        generated_tasks = {'analysis': [], 'wisdom': []}
        complex_files = analysis_result.get('complex_files', [])
        for idx, file_info in enumerate(complex_files[:5]):
            task = Task(id=f'auto-complexity-{idx + 1}', title=f"리팩토링: {file_info['file']}", description=f"복잡도 {file_info['complexity']:.1f}인 파일 개선", priority='high' if file_info['complexity'] > 15 else 'medium', auto_generated=True, wisdom_hints=['복잡한 함수를 작은 단위로 분리', '중복 코드 제거'], context_data={'file_path': file_info['file'], 'complexity': file_info['complexity'], 'functions': file_info.get('functions', [], content=content)})
            generated_tasks['analysis'].append(task)
        common_mistakes = wisdom.get_common_mistakes()
        for idx, (mistake_type, count) in enumerate(common_mistakes[:3]):
            task = Task(id=f'auto-wisdom-{idx + 1}', title=f'예방: {mistake_type} 패턴 개선', description=f'{count}회 발생한 실수 패턴 예방', priority='high' if count > 5 else 'medium', auto_generated=True, wisdom_hints=wisdom.get_prevention_tips(mistake_type), context_data={'mistake_type': mistake_type, 'occurrence_count': count})
            generated_tasks['wisdom'].append(task)
        large_files = analysis_result.get('largest_files', [])
        for idx, file_info in enumerate(large_files[:3]):
            if file_info['size'] > 10000:
                task = Task(id=f'auto-size-{idx + 1}', title=f"파일 분할: {file_info['file']}", description=f"{file_info['size']:,} bytes 파일을 모듈화", priority='medium', auto_generated=True, wisdom_hints=['단일 책임 원칙 적용', '관련 기능별로 분리'], context_data={'file_path': file_info['file'], 'size': file_info['size']})
                generated_tasks['analysis'].append(task)
        return generated_tasks

    def apply_wisdom_hints(self, task: Task) -> None:
        """Task에 Wisdom 시스템의 힌트 적용"""
        from project_wisdom import get_wisdom_manager
        wisdom = get_wisdom_manager()
        keywords = task.title.lower().split() + task.description.lower().split()
        best_practices = wisdom.get_best_practices()
        relevant_hints = []
        for practice in best_practices:
            if any((keyword in practice.lower() for keyword in keywords)):
                relevant_hints.append(practice)
        for mistake_type in wisdom.wisdom_data.get('common_mistakes', {}).keys():
            if any((keyword in mistake_type.lower() for keyword in keywords)):
                tips = wisdom.get_prevention_tips(mistake_type)
                relevant_hints.extend(tips)
        task.wisdom_hints = list(set(task.wisdom_hints + relevant_hints))[:5]

    def create_smart_plan(self, name: str, description: str, auto_analyze: bool=True) -> Plan:
        """ProjectAnalyzer와 Wisdom을 활용한 스마트 Plan 생성"""
        plan = Plan(name=name, description=description)
        self.context.plan = plan
        if auto_analyze:
            generated_tasks = self.analyze_and_generate_tasks()
            if generated_tasks['analysis']:
                phase1 = Phase(id='auto-phase-1', name='자동 분석 기반 개선', description='ProjectAnalyzer가 발견한 개선 사항')
                for task in generated_tasks['analysis']:
                    phase1.tasks[task.id] = task
                plan.phases['auto-phase-1'] = phase1
                plan.phase_order.append('auto-phase-1')
            if generated_tasks['wisdom']:
                phase2 = Phase(id='auto-phase-2', name='Wisdom 기반 예방', description='과거 실수 패턴 예방')
                for task in generated_tasks['wisdom']:
                    phase2.tasks[task.id] = task
                plan.phases['auto-phase-2'] = phase2
                plan.phase_order.append('auto-phase-2')
            from project_wisdom import get_wisdom_manager
            wisdom = get_wisdom_manager()
            plan.wisdom_data = {'applied_at': datetime.now().isoformat(), 'total_mistakes_tracked': sum(wisdom.wisdom_data.get('common_mistakes', {}).values()), 'best_practices_count': len(wisdom.get_best_practices())}
            plan.update_progress()
            print(f'✅ 스마트 Plan 생성 완료!')
            print(f"   - 자동 생성 Task: {len(generated_tasks['analysis']) + len(generated_tasks['wisdom'])}개")
        return plan

    @autosave
    def list_tasks(self, phase_id: Optional[str] = None) -> List[Task]:
        """현재 계획의 작업 목록을 반환"""
        if not self.context.plan:
            return []
        
        if phase_id:
            # 특정 Phase의 작업만
            phase = self.context.plan.phases.get(phase_id)
            if phase:
                return list(phase.tasks.values())
            return []
        else:
            # 전체 작업
            return self.context.get_all_tasks()
    
    @autosave
    def remove_task(self, task_id: str) -> StandardResponse:
        """작업 제거"""
        try:
            if not self.context.plan:
                return StandardResponse.error(
                    ErrorType.PLAN_ERROR,
                    "활성화된 계획이 없습니다."
                )
            
            # 작업 찾기
            for phase_id, phase in self.context.plan.phases.items():
                if task_id in phase.tasks:
                    removed_task = phase.tasks.pop(task_id)
                    # task_order에서도 제거
                    if task_id in phase.task_order:
                        phase.task_order.remove(task_id)
                    
                    self._trigger_event('task_removed', {
                        'task_id': task_id,
                        'task_name': removed_task.name,
                        'phase_id': phase_id
                    })
                    
                    print(f"✅ 작업 '{removed_task.name}'이(가) 제거되었습니다.")
                    return StandardResponse.success({
                        'removed_task': removed_task,
                        'message': f"작업 '{removed_task.name}'이(가) 제거되었습니다."
                    })
            
            return StandardResponse.error(
                ErrorType.TASK_ERROR,
                f"작업 ID '{task_id}'를 찾을 수 없습니다."
            )
            
        except Exception as e:
            return ErrorHandler.handle_exception(e, ErrorType.TASK_ERROR)
    
    @autosave
    def update_task(self, task_id: str, field: str, value: str) -> StandardResponse:
        """작업 정보 수정"""
        try:
            if not self.context.plan:
                return StandardResponse.error(
                    ErrorType.PLAN_ERROR,
                    "활성화된 계획이 없습니다."
                )
            
            # 작업 찾기
            for phase_id, phase in self.context.plan.phases.items():
                if task_id in phase.tasks:
                    task = phase.tasks[task_id]
                    
                    # 필드별 업데이트
                    if field == "name":
                        old_name = task.name
                        task.name = value
                        print(f"✅ 작업 이름 변경: '{old_name}' → '{value}'")
                    elif field == "description":
                        task.description = value
                        print(f"✅ 작업 설명이 업데이트되었습니다.")
                    elif field == "status":
                        try:
                            new_status = TaskStatus(value)
                            task.status = new_status
                            print(f"✅ 작업 상태가 '{value}'로 변경되었습니다.")
                        except ValueError:
                            return StandardResponse.error(
                                ErrorType.VALIDATION_ERROR,
                                f"올바르지 않은 상태값: {value}. 가능한 값: pending, in_progress, completed"
                            )
                    else:
                        return StandardResponse.error(
                            ErrorType.VALIDATION_ERROR,
                            f"수정할 수 없는 필드: {field}. 가능한 필드: name, description, status"
                        )
                    
                    task.updated_at = datetime.now()
                    
                    self._trigger_event('task_updated', {
                        'task_id': task_id,
                        'field': field,
                        'new_value': value
                    })
                    
                    return StandardResponse.success({
                        'task': task,
                        'message': f"작업이 성공적으로 수정되었습니다."
                    })
            
            return StandardResponse.error(
                ErrorType.TASK_ERROR,
                f"작업 ID '{task_id}'를 찾을 수 없습니다."
            )
            
        except Exception as e:
            return ErrorHandler.handle_exception(e, ErrorType.TASK_ERROR)

_workflow_manager_instance = None

def get_workflow_manager():
    """Get or create WorkflowManager singleton instance"""
    global _workflow_manager_instance
    if _workflow_manager_instance is None:
        _workflow_manager_instance = WorkflowManager()
    return _workflow_manager_instance