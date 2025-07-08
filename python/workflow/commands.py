"""
워크플로우 명령어 처리
"""
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import json
from python.workflow.workflow_manager import WorkflowManager
from python.workflow.models import ExecutionPlan, TaskStatus
from python.enhanced_flow import start_project
from python.core.context_manager import get_context_manager
from python.workflow.safety_utils import safe_get, safe_json, CommandParser

class WorkflowCommands:
    """워크플로우 명령어 처리 클래스"""
    
    def __init__(self, workflow_manager: WorkflowManager):
        self.workflow = workflow_manager
        self.context_manager = get_context_manager()
        self.commands = {
            '/plan': self.handle_plan,
            '/task': self.handle_task,
            '/approve': self.handle_approve,
            '/next': self.handle_next,
            '/status': self.handle_status,
            '/history': self.handle_history,
            '/build': self.handle_build,
            '/done': self.handle_done,
            '/complete': self.handle_done,  # alias for /done
            '/list': self.handle_list,
            '/start': self.handle_start,
            '/current': self.handle_current,
            '/tasks': self.handle_tasks,
        }
    
    def process_command(self, command: str) -> Dict[str, Any]:
        """명령어 처리"""
        # 명령어 파싱
        parts = command.strip().split(None, 1)
        if not parts:
            return {'error': '명령어를 입력하세요.'}
        
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ''
        
        if cmd in self.commands:
            try:
                return self.commands[cmd](args)
            except Exception as e:
                return {'error': f'명령어 실행 중 오류: {str(e)}'}
        else:
            return {'error': f'알 수 없는 명령어: {cmd}'}
    
    def handle_plan(self, args: str) -> Dict[str, Any]:
        """계획 생성 처리 - 안전성 강화"""
        try:
            # --reset 옵션 처리
            reset = '--reset' in args
            if reset:
                args = args.replace('--reset', '').strip()
            
            # CommandParser 사용으로 안전한 파싱
            parsed = CommandParser.parse_plan_command(args)
            name = parsed['name']
            description = parsed['description']
            
            if not name:
                return {'error': '계획 이름은 필수입니다'}
        
            plan = self.workflow.create_plan(name, description, reset)
        
            # 컨텍스트 업데이트
            self.context_manager.update_context('current_plan_id', plan.id)
            self.context_manager.update_context('current_plan_name', name)
            self.context_manager.update_context('last_workflow_action', {
                'action': 'plan_created',
                'timestamp': datetime.now().isoformat(),
                'plan_name': name
            })
            
            return {
                'success': True,
                'message': f'새 계획 생성됨: {name}',
                'plan_id': plan.id,
                'reset': reset
            }
            
        except ValueError as e:
            return {'error': str(e)}
        except Exception as e:
            return {'error': f'계획 생성 중 오류: {str(e)}'}
    
    def handle_task(self, args: str) -> Dict[str, Any]:
        """작업 추가 처리 - 안전성 강화"""
        try:
            # CommandParser 사용으로 안전한 파싱
            parsed = CommandParser.parse_task_command(args)
            title = parsed['title']
            description = parsed['description']
            
            if not title:
                return {'error': '작업 제목은 필수입니다'}
        
            task = self.workflow.add_task(title, description)
            
            # 컨텍스트 업데이트
            self.context_manager.update_context('last_added_task', {
                'id': task.id,
                'title': task.title,
                'timestamp': datetime.now().isoformat()
            })
            self.context_manager.update_context('last_workflow_action', {
                'action': 'task_added',
                'timestamp': datetime.now().isoformat(),
                'task_title': task.title
            })
            
            return {
                'success': True,
                'message': f'작업 추가됨: {title}',
                'task_id': task.id,
                'request_plan': True,  # AI가 계획을 수립하도록 요청
                'task': {
                    'id': task.id,
                    'title': title,
                    'description': description
                }
            }
        except ValueError as e:
            return {'error': str(e)}
        except Exception as e:
            return {'error': f'작업 추가 중 오류: {str(e)}'}
    
    def handle_approve(self, args: str) -> Dict[str, Any]:
        """작업 승인 처리"""
        # /approve [yes|no] [메모]
        parts = args.split(None, 1)
        if not parts:
            current_task = self.workflow.get_current_task()
            if not current_task:
                return {'error': '현재 작업이 없습니다.'}
            
            return {
                'current_task': {
                    'id': current_task.id,
                    'title': current_task.title,
                    'plan': current_task.execution_plan.to_dict() if current_task.execution_plan else None
                },
                'request_approval': True
            }
        
        approval = parts[0].lower() in ['yes', 'y', '예', '승인']
        notes = parts[1] if len(parts) > 1 else ''
        
        current_task = self.workflow.get_current_task()
        if not current_task:
            return {'error': '현재 작업이 없습니다.'}
        
        task = self.workflow.approve_task(current_task.id, approval, notes)
        
        return {
            'success': True,
            'approved': approval,
            'message': f'작업 {"승인" if approval else "거부"}됨: {task.title}',
            'notes': notes
        }
    
    def handle_done(self, args: str) -> Dict[str, Any]:
        """현재 작업 완료 처리"""
        try:
            current_task = self.workflow.get_current_task()
            if not current_task:
                return {'error': '현재 작업이 없습니다.'}

            notes = args.strip() if args else "작업 완료"
            success = self.workflow.complete_task(current_task.id, notes)

            if success:
                # 다음 태스크로 이동
                self.workflow.current_plan.move_to_next_task()
                self.workflow.save_data()

                return {
                    'success': True,
                    'message': f'✅ 작업 완료: {current_task.title}',
                    'notes': notes
                }
            return {'error': '작업 완료 처리 실패'}
        except Exception as e:
            return {'error': f'오류: {str(e)}'}

    def handle_next(self, args: str) -> Dict[str, Any]:
        """다음 작업으로 이동"""
        try:
            current_task = self.workflow.get_current_task()
            if not current_task:
                return {
                    'success': True,
                    'message': '모든 작업이 완료되었습니다!',
                    'all_completed': True
                }

            return {
                'success': True,
                'current_task': {
                    'title': current_task.title,
                    'description': current_task.description,
                    'index': self.workflow.current_plan.current_task_index + 1,
                    'total': len(self.workflow.current_plan.tasks)
                }
            }
        except Exception as e:
            return {'error': f'오류: {str(e)}'}


    def handle_tasks(self, args: str) -> Dict[str, Any]:
        """태스크 목록 조회"""
        try:
            if not self.workflow.current_plan:
                return {'error': '활성 플랜이 없습니다.'}

            plan = self.workflow.current_plan
            tasks_info = []

            for i, task in enumerate(plan.tasks):
                tasks_info.append({
                    'index': i + 1,
                    'title': task.title,
                    'description': task.description,
                    'status': getattr(task, 'status', 'todo'),
                    'is_current': i == plan.current_task_index
                })

            return {
                'success': True,
                'plan': plan.name,
                'total_tasks': len(tasks_info),
                'current_index': plan.current_task_index + 1,
                'tasks': tasks_info
            }
        except Exception as e:
            return {'error': f'오류: {str(e)}'}


    def handle_current(self, args: str) -> Dict[str, Any]:
        """현재 태스크 확인"""
        try:
            if not self.workflow.current_plan:
                return {'error': '활성 플랜이 없습니다.'}

            current_task = self.workflow.get_current_task()
            if not current_task:
                return {
                    'success': True,
                    'message': '모든 태스크가 완료되었습니다.',
                    'plan': self.workflow.current_plan.name
                }

            return {
                'success': True,
                'plan': self.workflow.current_plan.name,
                'current_task': {
                    'index': self.workflow.current_plan.current_task_index + 1,
                    'total': len(self.workflow.current_plan.tasks),
                    'title': current_task.title,
                    'description': current_task.description,
                    'status': getattr(current_task, 'status', 'todo')
                }
            }
        except Exception as e:
            return {'error': f'오류: {str(e)}'}


    def handle_status(self, args: str) -> Dict[str, Any]:
        """상태 확인"""
        try:
            current_plan = self.workflow.get_current_plan()
            current_task = self.workflow.get_current_task()

            if not current_plan:
                return {
                    'success': True,
                    'status': 'no_plan',
                    'message': '활성 계획 없음'
                }

            # 완료된 태스크 수 계산 - Enum 비교로 수정
            completed_count = 0
            for task in current_plan.tasks:
                if hasattr(task, 'status') and task.status == TaskStatus.COMPLETED:
                    completed_count += 1

            total_tasks = len(current_plan.tasks)
            progress = (completed_count / total_tasks * 100) if total_tasks > 0 else 0

            status = {
                'plan': {
                    'id': current_plan.id,
                    'name': current_plan.name,
                    'status': getattr(current_plan, 'status', 'active'),
                    'progress': progress,
                    'completed': completed_count,
                    'total': total_tasks
                }
            }

            if current_task:
                status['current_task'] = {
                    'id': current_task.id,
                    'title': current_task.title,
                    'status': getattr(current_task, 'status', 'todo'),
                    'index': current_plan.current_task_index
                }

            return {
                'success': True,
                'status': status
            }
        except Exception as e:
            return {'error': f'상태 조회 중 오류: {str(e)}'}

    def handle_history(self, args: str) -> Dict[str, Any]:
        """작업 이력 조회"""
        try:
            history = self.workflow.get_history()
            return {
                'success': True,
                'history': history,
                'count': len(history)
            }
        except Exception as e:
            return {'error': f'이력 조회 중 오류: {str(e)}'}

    def handle_build(self, args: str) -> Dict[str, Any]:
        """프로젝트 문서 빌드"""
        return {
            'success': True,
            'request_build': True,
            'message': '프로젝트 문서 빌드를 요청합니다.'
        }

    def handle_list(self, args: str) -> Dict[str, Any]:
        """플랜 목록 조회"""
        try:
            # workflow.json에서 히스토리 확인
            import json
            import os
            workflow_path = os.path.join("memory", "workflow.json")

            if os.path.exists(workflow_path):
                with open(workflow_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                plans = []
                # 현재 플랜 - 안전한 접근
                current = safe_get(data, 'current_plan')
                if current:
                    plans.append({
                        'name': current.get('name'),
                        'status': 'active',
                        'created_at': current.get('created_at', ''),
                        'tasks': len(current.get('tasks', []))
                    })

                # 히스토리
                for hist in data.get('history', []):
                    plan = safe_get(hist, 'plan')
                    if plan:
                        plans.append({
                            'name': plan.get('name'),
                            'status': 'archived',
                            'created_at': plan.get('created_at', ''),
                            'archived_at': hist.get('archived_at', ''),
                            'tasks': len(plan.get('tasks', []))
                        })

                return {
                    'success': True,
                    'plans': plans,
                    'count': len(plans)
                }
            else:
                return {'success': True, 'plans': [], 'count': 0}

        except Exception as e:
            return {'error': f'플랜 목록 조회 중 오류: {str(e)}'}

    def handle_start(self, args: str) -> Dict[str, Any]:
        """새 프로젝트 생성"""
        if not args.strip():
            return {'error': '프로젝트 이름을 입력해주세요. 사용법: /start 프로젝트명'}

        project_name = args.strip()

        try:
            # start_project 함수 호출 (ai_helpers에서)
            result = start_project(project_name)

            if result.ok:
                return {
                    'success': True,
                    'message': f'✅ 프로젝트 "{project_name}" 생성 완료!',
                    'data': result.data
                }
            else:
                return {'error': f'프로젝트 생성 실패: {result.error}'}

        except Exception as e:
            return {'error': f'프로젝트 생성 중 오류: {str(e)}'}
