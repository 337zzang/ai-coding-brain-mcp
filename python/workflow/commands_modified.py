"""
워크플로우 명령어 처리
"""
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from workflow.workflow_manager import WorkflowManager
from workflow.models import ExecutionPlan, TaskStatus
from enhanced_flow import start_project

from core.context_manager import ContextManager

class WorkflowCommands:
    """워크플로우 명령어 처리 클래스"""
    
    def __init__(self, workflow_manager: WorkflowManager):
        self.workflow = workflow_manager
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
        """계획 생성 처리"""
        # /plan 이름 | 설명 [--reset]
        reset = '--reset' in args
        if reset:
            args = args.replace('--reset', '').strip()
        
        parts = args.split('|', 1)
        if len(parts) != 2:
            return {'error': '형식: /plan 계획이름 | 설명 [--reset]'}
        
        name = parts[0].strip()
        description = parts[1].strip()
        
        plan = self.workflow.create_plan(name, description, reset)
        
        return {
            'success': True,
            'message': f'새 계획 생성됨: {name}',
            'plan_id': plan.id,
            'reset': reset
        }
    
    def handle_task(self, args: str) -> Dict[str, Any]:
        """작업 추가 처리"""
        # /task 제목 | 설명
        parts = args.split('|', 1)
        if len(parts) != 2:
            return {'error': '형식: /task 작업제목 | 설명'}
        
        title = parts[0].strip()
        description = parts[1].strip()
        
        try:
            task = self.workflow.add_task(title, description)
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
        """
        현재 작업 완료 처리
        사용법: /done 요약 | 세부내용1;세부내용2 | 산출물경로
        """
        current_task = self.workflow.get_current_task()
        if not current_task:
            return {'error': '현재 작업이 없습니다.'}
        
        # 승인되지 않은 작업은 완료할 수 없음
        if current_task.status != TaskStatus.APPROVED:
            return {'error': f'작업이 승인되지 않았습니다. 현재 상태: {current_task.status.value}'}
        
        # 인자 파싱
        parts = [p.strip() for p in args.split('|')] + [''] * 3
        summary = parts[0] or "작업 완료"
        details_raw = parts[1]
        outputs_raw = parts[2]
        
        # 세부사항 파싱
        details = []
        if details_raw:
            details = [d.strip() for d in details_raw.split(';') if d.strip()]
        
        # 산출물 파싱
        outputs = {}
        if outputs_raw:
            outputs = {'paths': [p.strip() for p in outputs_raw.split(',') if p.strip()]}
        
        # 작업 완료 처리
        return self.complete_current_task(
            summary=summary,
            details=details,
            outputs=outputs
        )
    

    def handle_list(self, args: str) -> Dict[str, Any]:
        """플랜 목록 조회"""
        try:
            # workflow.json 읽기
            workflow_data = self._load_workflow_data()

            if not workflow_data.get('plans'):
                return {
                    'status': 'info',
                    'message': '생성된 플랜이 없습니다.',
                    'plans': []
                }

            plans_info = []
            for plan in workflow_data['plans']:
                plan_info = {
                    'name': plan.get('name', 'Unnamed'),
                    'description': plan.get('description', ''),
                    'created_at': plan.get('created_at', ''),
                    'total_tasks': len(plan.get('tasks', [])),
                    'completed_tasks': plan.get('completed_tasks', 0),
                    'progress': f"{plan.get('completed_tasks', 0)}/{len(plan.get('tasks', []))}"
                }
                plans_info.append(plan_info)

            return {
                'status': 'success',
                'message': f'{len(plans_info)}개의 플랜이 있습니다.',
                'plans': plans_info
            }

        except Exception as e:
            return {'error': f'플랜 목록 조회 중 오류: {str(e)}'}

    def handle_current(self, args: str) -> Dict[str, Any]:
        """현재 태스크 확인"""
        try:
            # 워크플로우 데이터 로드
            workflow_data = self._load_workflow_data()

            # 활성 플랜 찾기
            active_plan = None
            for plan in workflow_data.get('plans', []):
                if plan.get('status') == 'active':
                    active_plan = plan
                    break

            if not active_plan:
                return {
                    'status': 'info',
                    'message': '활성 플랜이 없습니다.',
                    'current_task': None
                }

            # 현재 태스크 찾기
            current_index = active_plan.get('current_task_index', 0)
            tasks = active_plan.get('tasks', [])

            if current_index >= len(tasks):
                return {
                    'status': 'info',
                    'message': '모든 태스크가 완료되었습니다.',
                    'current_task': None,
                    'plan': active_plan.get('name')
                }

            current_task = tasks[current_index]

            return {
                'status': 'success',
                'message': '현재 태스크',
                'plan': active_plan.get('name'),
                'current_task': {
                    'index': current_index + 1,
                    'total': len(tasks),
                    'title': current_task.get('title', 'Untitled'),
                    'description': current_task.get('description', ''),
                    'status': current_task.get('status', 'todo'),
                    'approval': current_task.get('approval', 'none')
                }
            }

        except Exception as e:
            return {'error': f'현재 태스크 확인 중 오류: {str(e)}'}

    def handle_tasks(self, args: str) -> Dict[str, Any]:
        """태스크 목록 조회"""
        try:
            # 워크플로우 데이터 로드
            workflow_data = self._load_workflow_data()

            # 활성 플랜 찾기
            active_plan = None
            for plan in workflow_data.get('plans', []):
                if plan.get('status') == 'active':
                    active_plan = plan
                    break

            if not active_plan:
                return {
                    'status': 'info',
                    'message': '활성 플랜이 없습니다.',
                    'tasks': []
                }

            # 태스크 목록 구성
            tasks_info = []
            current_index = active_plan.get('current_task_index', 0)

            for i, task in enumerate(active_plan.get('tasks', [])):
                task_info = {
                    'index': i + 1,
                    'title': task.get('title', 'Untitled'),
                    'description': task.get('description', ''),
                    'status': task.get('status', 'todo'),
                    'is_current': i == current_index,
                    'completed_at': task.get('completed_at', '')
                }
                tasks_info.append(task_info)

            return {
                'status': 'success',
                'message': f"{active_plan.get('name')} 플랜의 태스크 목록",
                'plan': active_plan.get('name'),
                'total_tasks': len(tasks_info),
                'completed_tasks': active_plan.get('completed_tasks', 0),
                'tasks': tasks_info
            }

        except Exception as e:
            return {'error': f'태스크 목록 조회 중 오류: {str(e)}'}

    def handle_next(self, args: str) -> Dict[str, Any]:
        """다음 작업으로 이동"""
        current_task = self.workflow.get_current_task()
        if not current_task:
            return {
                'success': True,
                'message': '모든 작업이 완료되었습니다!',
                'all_completed': True
            }
        
        # 현재 작업이 완료되지 않았다면 결과 요청
        if current_task.status != TaskStatus.COMPLETED:
            return {
                'current_task': {
                    'id': current_task.id,
                    'title': current_task.title,
                    'status': current_task.status.value
                },
                'request_result': True,
                'completion_note': args.strip() if args else None
            }
        
        # 다음 작업 정보 반환
        next_task = self.workflow.current_plan.get_next_task() if self.workflow.current_plan else None
        
        return {
            'success': True,
            'message': '다음 작업으로 이동',
            'completed_task': {
                'title': current_task.title,
                'summary': current_task.result.summary if current_task.result else ''
            },
            'next_task': {
                'title': next_task.title,
                'description': next_task.description
            } if next_task else None
        }
    
    def handle_status(self, args: str) -> Dict[str, Any]:
        """상태 확인"""
        status = self.workflow.get_status()
        return {
            'success': True,
            'status': status
        }
    
    def handle_history(self, args: str) -> Dict[str, Any]:
        """작업 이력 조회"""
        history = self.workflow.get_history()
        return {
            'success': True,
            'history': history,
            'count': len(history)
        }
    
    def handle_build(self, args: str) -> Dict[str, Any]:
        """프로젝트 문서 빌드"""
        return {
            'success': True,
            'request_build': True,
            'message': '프로젝트 문서 빌드를 요청합니다.'
        }
    
    def create_task_plan(self, task_id: str, steps: list, estimated_time: str = None,
                        tools: list = None, risks: list = None, criteria: list = None) -> Dict[str, Any]:
        """작업 계획 생성"""
        plan = ExecutionPlan(
            steps=steps,
            estimated_time=estimated_time,
            tools=tools or [],
            risks=risks or [],
            success_criteria=criteria or []
        )
        
        try:
            task = self.workflow.create_task_plan(task_id, plan)
            return {
                'success': True,
                'message': f'작업 계획 수립됨: {task.title}',
                'task_id': task.id,
                'plan': plan.to_dict()
            }
        except ValueError as e:
            return {'error': str(e)}
    
    def complete_current_task(self, summary: str, details: list = None, 
                            outputs: dict = None, issues: list = None, 
                            next_steps: list = None) -> Dict[str, Any]:
        """현재 작업 완료"""
        current_task = self.workflow.get_current_task()
        if not current_task:
            return {'error': '현재 작업이 없습니다.'}
        
        result = dict(
            summary=summary,
            details=details or [],
            outputs=outputs or {},
            issues=issues or [],
            next_steps=next_steps or []
        )
        
        try:
            # 작업이 진행 중이 아니면 시작
            if current_task.status != TaskStatus.IN_PROGRESS:
                self.workflow.start_task(current_task.id)
            
            # 작업 완료
            task = self.workflow.complete_task(current_task.id, result)
            
            # 자동 Git 커밋/푸시 (환경변수 확인)
            auto_commit = os.getenv('AUTO_GIT_COMMIT', 'false').lower() == 'true'
            if auto_commit:
                try:
                    # Git 유틸리티를 사용한 커밋
                    from utils.git_utils import git_commit_with_id, git_push
                    
                    # 커밋 메시지 생성 (Task ID 포함)
                    task_id_short = task.id[:8] if len(task.id) > 8 else task.id
                    commit_message = f"task({task_id_short}): {task.title}\n\n- Summary: {summary}\n- Status: Completed\n- Time: {datetime.now().isoformat()}"
                    
                    # Git 커밋 수행
                    commit_result = git_commit_with_id(commit_message)
                    
                    if commit_result['success']:
                        # Task 결과에 Git 정보 저장
                        if 'git_info' not in task.result:
                            task.result['git_info'] = {}
                        
                        task.result['git_info'] = {
                            'commit_id': commit_result['commit_id'],
                            'commit_id_short': commit_result['commit_id_short'],
                            'branch': commit_result['branch'],
                            'author': commit_result['author'],
                            'email': commit_result['email'],
                            'timestamp': commit_result['timestamp'],
                            'files_changed': commit_result['files_changed']
                        }
                        
                        # workflow.json 다시 저장 (Git 정보 포함)
                        self.workflow.save_data()
                        
                        print(f"✅ Git 커밋 성공: {commit_result['commit_id_short']}")
                        
                        # 자동 푸시 (환경변수 확인)
                        auto_push = os.getenv('AUTO_GIT_PUSH', 'false').lower() == 'true'
                        if auto_push:
                            push_result = git_push()
                            if push_result['success']:
                                print("✅ Git 푸시 성공!")
                                task.result['git_info']['pushed'] = True
                            else:
                                print(f"⚠️ Git 푸시 실패: {push_result.get('error', 'Unknown error')}")
                                task.result['git_info']['pushed'] = False
                        else:
                            task.result['git_info']['pushed'] = False
                            # workflow.json 한 번 더 저장
                            self.workflow.save_data()
                            
                    else:
                        error_msg = commit_result.get('error', 'Unknown error')
                        if 'No changes to commit' in error_msg:
                            print("ℹ️ 커밋할 변경사항이 없습니다")
                        else:
                            print(f"⚠️ Git 커밋 실패: {error_msg}")
                        
                except Exception as e:
                    print(f"❌ Git 작업 중 오류: {str(e)}")
            
            # 다음 작업 정보
            next_task = self.workflow.current_plan.get_next_task() if self.workflow.current_plan else None
            
            return {
                'success': True,
                'message': f'작업 완료: {task.title}',
                'completed_task': {
                    'title': task.title,
                    'summary': summary
                },
                'next_task': {
                    'title': next_task.title,
                    'description': next_task.description
                } if next_task else None
            }
        except ValueError as e:
            return {'error': str(e)}


    def handle_start(self, args: str) -> Dict[str, Any]:
        """
        새 프로젝트 생성
        사용법: /start 프로젝트명
        """
        if not args.strip():
            return {
                'status': 'error',
                'message': '프로젝트 이름을 입력해주세요. 사용법: /start 프로젝트명'
            }

        project_name = args.strip()

        try:
            # start_project 함수 호출
            result = start_project(project_name)

            if result.ok:
                return {
                    'status': 'success',
                    'message': f'✅ 프로젝트 "{project_name}" 생성 완료!',
                    'data': result.data
                }
            else:
                return {
                    'status': 'error',
                    'message': f'프로젝트 생성 실패: {result.error}'
                }

        except Exception as e:
            return {
                'status': 'error',
                'message': f'프로젝트 생성 중 오류: {str(e)}'
            }