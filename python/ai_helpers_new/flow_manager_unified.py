"""
FlowManagerUnified - 통합 워크플로우 매니저
Flow Project v2 + 기존 WorkflowManager 기능 통합
"""
import os
import json
import sys
import copy
from datetime import datetime
import time
import uuid
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any

# Flow Project v2 import 시도
from enum import Enum
_has_flow_v2 = False
try:
    # 경로 추가
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    from flow_project_v2.flow_manager_integrated import FlowManagerWithContext
    _has_flow_v2 = True
except ImportError as e:
    print(f"⚠️ Flow v2 import 실패: {e}")
    # Fallback 베이스 클래스
    class FlowManagerWithContext:
        def __init__(self):
            pass

# Task context 기본 구조

class TaskStatus(Enum):
    """Task 상태 정의"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

    @classmethod
    def from_string(cls, status_str: str):
        """문자열에서 TaskStatus로 변환"""
        status_map = {
            'todo': cls.TODO,
            'in_progress': cls.IN_PROGRESS,
            'in-progress': cls.IN_PROGRESS,
            'reviewing': cls.REVIEWING,
            'approved': cls.APPROVED,
            'completed': cls.COMPLETED,
            'done': cls.COMPLETED,
            'blocked': cls.BLOCKED,
            'cancelled': cls.CANCELLED,
            'canceled': cls.CANCELLED,
        }
        return status_map.get(status_str.lower(), cls.TODO)

    def __str__(self):
        return self.value

# Task 상태 전환 규칙
TASK_TRANSITIONS = {
    TaskStatus.TODO: {
        TaskStatus.IN_PROGRESS,
        TaskStatus.CANCELLED
    },
    TaskStatus.IN_PROGRESS: {
        TaskStatus.REVIEWING,
        TaskStatus.BLOCKED,
        TaskStatus.TODO,
        TaskStatus.CANCELLED
    },
    TaskStatus.REVIEWING: {
        TaskStatus.APPROVED,
        TaskStatus.IN_PROGRESS,
        TaskStatus.BLOCKED
    },
    TaskStatus.APPROVED: {
        TaskStatus.COMPLETED
    },
    TaskStatus.BLOCKED: {
        TaskStatus.IN_PROGRESS,
        TaskStatus.TODO,
        TaskStatus.CANCELLED
    },
    TaskStatus.COMPLETED: set(),
    TaskStatus.CANCELLED: set(),
}

DEFAULT_CONTEXT = {
    "plan": "",
    "actions": [],     # 작업 이력: [{"time": ISO8601, "action": str, "result": str}]
    "results": {},     # 결과 데이터: 자유 형식
    "docs": [],        # 관련 문서: 파일명 리스트
    "files": {         # 파일 작업 내역
        "analyzed": [],
        "created": [],
        "modified": []
    },
    "errors": []       # 오류 내역
}

class FlowManagerUnified(FlowManagerWithContext):
    """통합된 Flow + Workflow 매니저"""

    def __init__(self, project_root: str = None):
        """초기화"""
        # 기본 속성 초기화
        self.current_flow = None
        self.context_manager = None
        self.flows = []
        self._has_flow_v2 = _has_flow_v2
        self.debug = False  # 디버그 모드 (기본값: False)

        # Flow v2 초기화 시도
        if self._has_flow_v2:
            try:
                super().__init__()
                print("✅ Flow v2 기능 활성화됨")
            except Exception as e:
                print(f"⚠️ Flow v2 초기화 부분 실패: {e}")
                self._has_flow_v2 = False

        # 프로젝트 설정
        self.project_root = project_root or os.getcwd()
        self.data_dir = os.path.join(self.project_root, '.ai-brain')
        self._ensure_directories()

        # 명령어 핸들러 초기화
        self._command_handlers = self._init_command_handlers()

        # 레거시 데이터 마이그레이션
        self._migrate_legacy_data()
        # Flow 데이터 로드
        self._load_flows()

        # 기본 flow가 없으면 생성
        if self._has_flow_v2 and not self.current_flow:
            self._create_default_flow()

    def _generate_unique_id(self, prefix: str) -> str:
        """
        나노초 타임스탬프 + UUID 기반 고유 ID 생성

        Args:
            prefix: ID 접두사 (예: 'plan', 'task')

        Returns:
            str: 고유 ID (예: 'plan_1753143613422185100_eac7a3')
        """
        ns = time.time_ns()  # 나노초 타임스탬프
        rand = uuid.uuid4().hex[:6]  # 6자리 랜덤 문자열
        return f"{prefix}_{ns}_{rand}"

    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, 'backups'), exist_ok=True)

    def _create_default_flow(self):
        """기본 flow 생성"""
        try:
            if hasattr(self, 'create_flow') and callable(self.create_flow):
                # Flow 데이터 구조 직접 생성 (FlowManagerWithContext가 없을 경우)
                if not self.current_flow:
                    self.current_flow = {
                        'id': f'flow_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                        'name': 'default',
                        'plans': [],
                        'created_at': datetime.now().isoformat()
                    }
                    if hasattr(self, 'flows'):
                        self.flows.append(self.current_flow)
                    print("✅ 기본 flow 생성됨")
        except Exception as e:
            print(f"⚠️ 기본 flow 생성 실패: {e}")

    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(os.path.join(self.data_dir, 'backups'), exist_ok=True)

    def _create_default_flow(self):
        """기본 flow 생성"""
        try:
            if hasattr(self, 'create_flow'):
                self.create_flow('default')
        except Exception as e:
            print(f"⚠️ 기본 flow 생성 실패: {e}")

    def _migrate_legacy_data(self):
        """기존 workflow.json을 flow 구조로 마이그레이션"""
        legacy_path = os.path.join(self.data_dir, 'workflow.json')
        if not os.path.exists(legacy_path):
            return

        try:
            with open(legacy_path, 'r', encoding='utf-8') as f:
                legacy_data = json.load(f)

            print("📦 레거시 데이터 마이그레이션 시작...")

            # 백업
            backup_path = os.path.join(self.data_dir, 'backups', 
                                     f'workflow_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(legacy_data, f, indent=2)

            # Flow v2가 활성화되어 있으면 마이그레이션
            if self._has_flow_v2:
                # 기본 flow 확인
                if not self.current_flow:
                    self._create_default_flow()

                # 태스크 마이그레이션
                migrated_count = 0
                for task in legacy_data.get('tasks', []):
                    try:
                        # Plan이 없으면 기본 plan 생성
                        if not self.current_flow.get('plans'):
                            if hasattr(self, 'create_plan'):
                                self.create_plan('Default Plan')

                        # 첫 번째 plan에 태스크 추가
                        if hasattr(self, 'create_task'):
                            self.create_task(
                                name=task.get('name', 'Unnamed Task'),
                                description=task.get('description', '')
                            )
                            migrated_count += 1
                    except Exception as e:
                        print(f"⚠️ 태스크 마이그레이션 실패: {e}")

                print(f"✅ {migrated_count}개 태스크 마이그레이션 완료")

            # 레거시 파일 이름 변경
            os.rename(legacy_path, legacy_path + '.migrated')

        except Exception as e:
            print(f"⚠️ 마이그레이션 중 오류: {e}")

    def _init_command_handlers(self) -> Dict[str, Any]:
        """명령어 핸들러 초기화"""
        return {
            # 기본 명령어
            'help': self._show_help,
            'status': self._show_status,
            'list': self._list_tasks,

            # 태스크 관리
            'task': self._handle_task_command,
            'start': self._start_task,
            'done': self._complete_task,
            'complete': self._complete_task,
            'skip': self._skip_task,

            # Flow v2 명령어
            'flow': self._handle_flow_command,
            'plan': self._handle_plan_command,

            # Context 명령어
            'context': self._handle_context_command,
            'session': self._handle_session_command,
            'history': self._show_history,
            'stats': self._show_stats,

            # 리포트
            'report': self._show_report,
        }

    def process_command(self, command: str) -> Dict[str, Any]:
        """통합 명령어 처리"""
        if not command.startswith('/'):
            return {'ok': False, 'error': 'Commands must start with /'}

        # 명령어 파싱
        parts = command[1:].split(maxsplit=1)
        if not parts:
            return {'ok': False, 'error': 'Empty command'}

        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ''

        # 핸들러 찾기
        handler = self._command_handlers.get(cmd)
        if handler:
            try:
                return handler(args)
            except Exception as e:
                return {'ok': False, 'error': f'Command failed: {str(e)}'}

        # 알 수 없는 명령어
        similar = self._find_similar_commands(cmd)
        error_msg = f"Unknown command: {cmd}"
        if similar:
            error_msg += f"\nDid you mean: {', '.join(similar)}?"
        return {'ok': False, 'error': error_msg}

    def _find_similar_commands(self, cmd: str) -> List[str]:
        """유사한 명령어 찾기"""
        similar = []
        for command in self._command_handlers.keys():
            if cmd in command or command.startswith(cmd):
                similar.append(command)
        return similar[:3]

    # === 도움말 및 상태 ===

    def _show_help(self, args: str) -> Dict[str, Any]:
        """도움말 표시"""
        help_text = """📋 통합 워크플로우 명령어

기본 명령어:
  /help              - 이 도움말 표시
  /status            - 현재 상태 표시
  /list              - 태스크 목록
  /report            - 전체 리포트

태스크 관리:
  /task add [이름]   - 새 태스크 추가
  /task list         - 태스크 목록
  /start [id]        - 태스크 시작
  /done [id]         - 태스크 완료
  /skip [id]         - 태스크 건너뛰기

Flow 관리:
  /flow              - 현재 flow 정보
  /flow list         - 모든 flow 목록
  /flow create [이름] - 새 flow 생성
  /flow switch [id]  - flow 전환
  /plan add [이름]   - 새 plan 추가
  /plan list         - plan 목록

Context 시스템:
  /context           - 현재 컨텍스트
  /session save [이름] - 세션 저장
  /session list      - 세션 목록
  /history [n]       - 최근 히스토리
  /stats             - 통계 정보"""

        return {'ok': True, 'data': help_text.strip()}

    def _show_status(self, args: str) -> Dict[str, Any]:
        """현재 상태 표시"""
        status_lines = []

        # Flow 정보
        if self._has_flow_v2 and self.current_flow:
            status_lines.append(f"📊 Flow: {self.current_flow.get('name', 'Unknown')}")
            status_lines.append(f"ID: {self.current_flow.get('id', 'N/A')}")

            # Plan 정보
            plans = self.current_flow.get('plans', [])
            status_lines.append(f"\nPlans: {len(plans)}")

            # 태스크 통계
            total_tasks = 0
            completed_tasks = 0
            in_progress = 0

            for plan in plans:
                for task in plan.get('tasks', []):
                    total_tasks += 1
                    status = task.get('status', 'todo')
                    if status in ['done', 'completed']:
                        completed_tasks += 1
                    elif status == 'in_progress':
                        in_progress += 1

            progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            status_lines.append(f"\n태스크: {total_tasks}개")
            status_lines.append(f"  - 완료: {completed_tasks}")
            status_lines.append(f"  - 진행중: {in_progress}")
            status_lines.append(f"  - 대기: {total_tasks - completed_tasks - in_progress}")
            status_lines.append(f"\n진행률: {progress:.1f}%")

            # 현재 진행 중인 태스크
            if in_progress > 0:
                status_lines.append("\n🔄 진행 중인 태스크:")
                for plan in plans:
                    for task in plan.get('tasks', []):
                        if task.get('status') == 'in_progress':
                            status_lines.append(f"  - [{task['id']}] {task['name']}")
        else:
            status_lines.append("📊 워크플로우 상태")
            status_lines.append("Flow v2: 비활성화")
            status_lines.append("기본 모드로 실행 중")

        # Context 정보
        if self.context_manager:
            try:
                stats = self.context_manager.get_stats()
                status_lines.append(f"\nContext: 활성화")
                status_lines.append(f"  세션: {stats.get('session_id', 'N/A')}")
            except:
                pass

        return {'ok': True, 'data': '\n'.join(status_lines)}

    def _show_report(self, args: str) -> Dict[str, Any]:
        """전체 리포트 생성"""
        report_lines = ["📊 워크플로우 리포트", "=" * 50]

        # 상태 정보 추가
        status = self._show_status('')
        if status['ok']:
            report_lines.append(status['data'])

        # 태스크 목록 추가
        report_lines.append("\n" + "=" * 50)
        report_lines.append("📋 태스크 목록")

        tasks = self._list_tasks('')
        if tasks['ok']:
            task_list = tasks['data']
            if isinstance(task_list, list):
                for task in task_list:
                    status_emoji = {
                        'todo': '⚪',
                        'in_progress': '🔵',
                        'done': '✅',
                        'completed': '✅',
                        'skipped': '⏭️'
                    }.get(task.get('status', 'todo'), '❓')

                    report_lines.append(f"{status_emoji} [{task['id']}] {task['name']}")
            else:
                report_lines.append(str(task_list))

        return {'ok': True, 'data': '\n'.join(report_lines)}

    # === 태스크 관리 ===

    def _handle_task_command(self, args: str) -> Dict[str, Any]:
        """태스크 명령어 처리"""
        if not args:
            return {'ok': False, 'error': 'Usage: /task <add|list>'}

        parts = args.split(maxsplit=1)
        subcmd = parts[0].lower()
        task_args = parts[1] if len(parts) > 1 else ''

        if subcmd == 'add':
            return self._add_task(task_args)
        elif subcmd == 'list':
            return self._list_tasks('')
        else:
            return {'ok': False, 'error': f'Unknown task command: {subcmd}'}

    def _add_task(self, args: str) -> Dict[str, Any]:
        """태스크 추가"""
        # args 파싱: plan_id name 형식 지원
        parts = args.strip().split(maxsplit=1) if args else []

        # plan_id가 있는지 확인
        plan_id = None
        name = 'New Task'

        if len(parts) >= 2 and parts[0].startswith('plan_'):
            # plan_id name 형식
            plan_id = parts[0]
            name = parts[1]
        elif len(parts) == 1:
            # name만 있는 경우
            name = parts[0]
        elif args:
            # 전체를 name으로 사용
            name = args.strip()

        try:
            if self._has_flow_v2:
                # Flow v2 방식
                if not self.current_flow:
                    self._create_default_flow()

                # Plan이 없으면 생성
                if not self.current_flow.get('plans'):
                    if hasattr(self, 'create_plan'):
                        self.create_plan('Default Plan')

                # 태스크 생성 (plan_id 전달)
                if hasattr(self, 'create_task'):
                    task = self.create_task(name, plan_id=plan_id)
                    return {'ok': True, 'data': {
                        'id': task.get('id'),
                        'name': task.get('name'),
                        'message': f'태스크 추가됨: {name}'
                    }}
            else:
                # 기본 모드 (Flow v2 없을 때)
                task_id = self._generate_unique_id("task")
                return {'ok': True, 'data': {
                    'id': task_id,
                    'name': name,
                    'message': f'태스크 추가됨: {name} (기본 모드)'
                }}

        except Exception as e:
            return {'ok': False, 'error': f'태스크 추가 실패: {str(e)}'}

    def _list_tasks(self, args: str) -> Dict[str, Any]:
        """태스크 목록 표시 (context 정보 포함)"""
        try:
            if self._has_flow_v2 and self.current_flow:
                lines = ['📌 Task 목록:\\n']
                
                for plan in self.current_flow.get('plans', []):
                    lines.append(f"\\nPlan: {plan['name']}")
                    tasks = plan.get('tasks', [])
                    
                    if not tasks:
                        lines.append("  (No tasks)")
                        continue
                    
                    for task in tasks:
                        # 상태 이모지
                        status_emoji = {
                            'todo': '⏳',
                            'in_progress': '🔄',
                            'completed': '✅',
                            'skipped': '⏭️',
                            'error': '❌'
                        }.get(task.get('status', 'todo'), '❓')
                        
                        # 기본 정보
                        lines.append(f"  {status_emoji} {task['id']}: {task['name']}")
                        
                        # Description
                        if task.get('description'):
                            lines.append(f"     📝 {task['description']}")
                        
                        # Context 정보가 있으면 표시
                        if 'context' in task:
                            ctx = task['context']
                            
                            # 계획 (첫 줄만)
                            if ctx.get('plan'):
                                plan_first_line = ctx['plan'].split('\\n')[0]
                                if len(plan_first_line) > 50:
                                    plan_first_line = plan_first_line[:50] + '...'
                                lines.append(f"     📋 계획: {plan_first_line}")
                            
                            # 최근 작업
                            if ctx.get('actions'):
                                last_action = ctx['actions'][-1]
                                action_text = f"{last_action['action']}"
                                if last_action.get('result'):
                                    action_text += f" → {last_action['result']}"
                                lines.append(f"     🔧 최근: {action_text}")
                            
                            # 진행률
                            if ctx.get('results', {}).get('progress'):
                                progress = ctx['results']['progress']
                                lines.append(f"     📊 진행률: {progress}%")
                
                return {'ok': True, 'data': '\\n'.join(lines)}
            else:
                # 기본 모드
                return {'ok': True, 'data': '태스크 목록이 비어있습니다.'}
                
        except Exception as e:
            return {'ok': False, 'error': f'태스크 목록 표시 실패: {str(e)}'}
    def _start_task(self, args: str) -> Dict[str, Any]:
        """태스크 시작"""
        if not args:
            return {'ok': False, 'error': 'Usage: /start <task_id>'}

        task_id = args.strip()

        try:
            if self._has_flow_v2 and hasattr(self, 'update_task_status'):
                self.update_task_status(task_id, 'planning')
                return {'ok': True, 'data': f'태스크 {task_id} 시작됨'}
            else:
                return {'ok': True, 'data': f'태스크 {task_id} 시작됨 (기본 모드)'}

        except Exception as e:
            return {'ok': False, 'error': f'태스크 시작 실패: {str(e)}'}

    def _complete_task(self, args: str) -> Dict[str, Any]:
        """태스크 완료"""
        if not args:
            return {'ok': False, 'error': 'Usage: /done <task_id>'}

        task_id = args.strip()

        try:
            if self._has_flow_v2 and hasattr(self, 'update_task_status'):
                self.update_task_status(task_id, 'reviewing')

                # Context에 완료 기록
                if self.context_manager:
                    try:
                        self.context_manager.add_event('task_completed', {
                            'task_id': task_id,
                            'timestamp': datetime.now().isoformat()
                        })
                    except:
                        pass

                return {'ok': True, 'data': f'태스크 {task_id} 완료됨'}
            else:

                # Plan 자동 완료 체크
                try:
                    # Task가 속한 Plan 찾기
                    for plan in self.current_flow.get("plans", []):
                        for task in plan.get("tasks", []):
                            if task.get("id") == task_id:
                                self._check_plan_auto_complete(plan["id"])
                                break
                except:
                    pass  # 자동 완료 체크 실패는 무시

                return {'ok': True, 'data': f'태스크 {task_id} 완료됨 (기본 모드)'}

        except Exception as e:
            return {'ok': False, 'error': f'태스크 완료 실패: {str(e)}'}



    def _complete_plan(self, plan_id: str) -> Dict[str, Any]:
        """Plan을 완료 상태로 변경"""
        try:
            # 현재 Flow 확인
            if not self.current_flow:
                return {'ok': False, 'error': '활성 Flow가 없습니다'}

            # Plan 존재 확인
            plan_found = False
            for plan in self.current_flow['plans']:
                if plan['id'] == plan_id:
                    plan_found = True
                    # completed 필드 업데이트
                    plan['completed'] = True
                    plan['completed_at'] = datetime.now().isoformat()

                    # 모든 하위 Task도 완료 처리
                    if 'tasks' in plan:
                        for task in plan['tasks']:
                            if task.get('status') != 'completed':
                                task['status'] = 'completed'
                                task['completed_at'] = datetime.now().isoformat()

                    # 저장
                    self._save_flows()

                    # Context Manager에 이벤트 기록
                    if self.context_manager:
                        try:
                            self.context_manager.add_event('plan_completed', {
                                'plan_id': plan_id,
                                'plan_name': plan['name'],
                                'task_count': len(plan.get('tasks', [])),
                                'completed_at': plan.get('completed_at', ''),
                                'auto_completed_tasks': True
                            })
                        except:
                            pass  # Context Manager 오류는 무시

                    # 알림 메시지
                    task_count = len(plan.get('tasks', []))
                    return {
                        'ok': True, 
                        'data': f"✅ Plan '{plan['name']}' 완료! (하위 {task_count}개 Task 모두 완료 처리)"
                    }

            if not plan_found:
                return {'ok': False, 'error': f'Plan을 찾을 수 없습니다: {plan_id}'}

        except Exception as e:
            return {'ok': False, 'error': f'Plan 완료 처리 중 오류: {str(e)}'}



    def _reopen_plan(self, plan_id: str) -> Dict[str, Any]:
        """Plan을 다시 열기 (완료 상태 취소)"""
        try:
            # 현재 Flow 확인
            if not self.current_flow:
                return {'ok': False, 'error': '활성 Flow가 없습니다'}

            # Plan 찾기
            plan_found = False
            for plan in self.current_flow['plans']:
                if plan['id'] == plan_id:
                    plan_found = True
                    # completed 필드 업데이트
                    plan['completed'] = False
                    if 'completed_at' in plan:
                        del plan['completed_at']

                    # 저장
                    self._save_flows()

                    # 알림 메시지 (Task 상태는 유지)
                    return {
                        'ok': True, 
                        'data': f"📂 Plan '{plan['name']}' 다시 열림 (Task 상태는 유지됨)"
                    }

            if not plan_found:
                return {'ok': False, 'error': f'Plan을 찾을 수 없습니다: {plan_id}'}

        except Exception as e:
            return {'ok': False, 'error': f'Plan 재오픈 중 오류: {str(e)}'}



    def _check_plan_auto_complete(self, plan_id: str) -> bool:
        """모든 Task가 완료되면 Plan 자동 완료"""
        try:
            if not self.current_flow:
                return False

            for plan in self.current_flow['plans']:
                if plan['id'] == plan_id:
                    # 이미 완료된 Plan은 건너뛰기
                    if plan.get('completed', False):
                        return False

                    # 모든 Task가 완료되었는지 확인
                    tasks = plan.get('tasks', [])
                    if not tasks:  # Task가 없으면 자동 완료하지 않음
                        return False

                    all_completed = all(
                        task.get('status') in ['completed', 'reviewing'] 
                        for task in tasks
                    )

                    if all_completed:
                        # Plan 자동 완료
                        result = self._complete_plan(plan_id)
                        if result['ok']:
                            print(f"🎉 모든 Task 완료! {result['data']}")

                            # Context Manager에 자동 완료 이벤트 기록
                            if self.context_manager:
                                try:
                                    self.context_manager.add_event('plan_auto_completed', {
                                        'plan_id': plan_id,
                                        'plan_name': plan['name'],
                                        'trigger': 'all_tasks_completed',
                                        'task_count': len(tasks)
                                    })
                                except:
                                    pass

                            return True

                    return False

            return False

        except Exception as e:
            print(f"자동 완료 체크 중 오류: {e}")
            return False

    def _skip_task(self, args: str) -> Dict[str, Any]:
        """태스크 건너뛰기"""
        if not args:
            return {'ok': False, 'error': 'Usage: /skip <task_id>'}

        task_id = args.strip()

        try:
            if self._has_flow_v2 and hasattr(self, 'update_task_status'):
                self.update_task_status(task_id, 'skipped')
                return {'ok': True, 'data': f'태스크 {task_id} 건너뛰기'}
            else:
                return {'ok': True, 'data': f'태스크 {task_id} 건너뛰기 (기본 모드)'}

        except Exception as e:
            return {'ok': False, 'error': f'태스크 건너뛰기 실패: {str(e)}'}

    # === Flow v2 명령어 ===

    def _handle_flow_command(self, args: str) -> Dict[str, Any]:
        """Flow 명령어 처리"""
        if not self._has_flow_v2:
            return {'ok': False, 'error': 'Flow v2가 활성화되지 않았습니다'}

        if not args:
            # 현재 flow 정보 표시
            if self.current_flow:
                info = f"📁 현재 Flow: {self.current_flow.get('name', 'Unknown')}\n"
                info += f"ID: {self.current_flow.get('id', 'N/A')}\n"
                info += f"Plans: {len(self.current_flow.get('plans', []))}개"
                return {'ok': True, 'data': info}
            else:
                return {'ok': True, 'data': 'Flow가 선택되지 않았습니다'}

        parts = args.split(maxsplit=1)
        subcmd = parts[0].lower()
        flow_args = parts[1] if len(parts) > 1 else ''

        # ✨ 새로운 기능: 직접 프로젝트명으로 전환
        # subcmd가 명령어가 아닌 경우 프로젝트명으로 간주
        known_commands = ['list', 'create', 'switch', 'delete', 'status', 
                         'plan', 'task', 'summary', 'export']
        if subcmd not in known_commands:
            # 프로젝트명으로 직접 전환 시도
            return self._switch_to_project(subcmd)

        flow_handlers = {
            'list': self._list_flows,
            'create': lambda: self._create_flow(flow_args),
            'switch': lambda: self._switch_flow(flow_args),
            'delete': lambda: self._delete_flow(flow_args),
            'status': lambda: self._handle_flow_command(''),  # 현재 flow 정보
            'plan': lambda: self._handle_plan_subcommand(flow_args),
            'task': lambda: self._handle_task_subcommand(flow_args),
            'summary': lambda: self.get_summary(),
            'export': lambda: self._export_flow_data(),
        }

        handler = flow_handlers.get(subcmd)
        if handler:
            return handler()

        return {'ok': False, 'error': f'Unknown flow command: {subcmd}'}

    def _switch_to_project(self, project_name: str) -> Dict[str, Any]:
        """프로젝트명으로 직접 전환하고 관련 작업 수행"""
        import os

        # 1. Flow 찾기 (이름으로, 플랜이 있는 것 우선)
        flow_id = None
        matching_flows = []

        # 이름이 일치하는 모든 Flow 찾기
        for flow in self.flows:
            if flow['name'].lower() == project_name.lower():
                matching_flows.append(flow)

        if not matching_flows:
            return {'ok': False, 'error': f"프로젝트 '{project_name}'를 찾을 수 없습니다"}

                # 플랜이 있는 Flow 우선, 그 다음 최신 Flow 선택
        matching_flows.sort(key=lambda f: (
            len(f.get('plans', [])),    # 플랜 수가 많은 것 우선
            f.get('created_at', '')      # 그 다음 최신 것
        ), reverse=True)

        flow_id = matching_flows[0]['id']

        # 여러 개가 있으면 알림
        if len(matching_flows) > 1:
            plans_count = len(matching_flows[0].get('plans', []))
            print(f"ℹ️ '{project_name}' Flow가 {len(matching_flows)}개 있습니다. Plans {plans_count}개인 {flow_id} 선택")

        if not flow_id:
            return {'ok': False, 'error': f"프로젝트 '{project_name}'를 찾을 수 없습니다"}

        # 2. Flow 전환
        try:
            self.switch_flow(flow_id)
        except Exception as e:
            return {'ok': False, 'error': f'Flow 전환 실패: {str(e)}'}

        # 3. 작업 디렉토리 변경
        # Windows의 경우 Desktop 경로 확인
        desktop_path = os.path.join(os.environ['USERPROFILE'], 'Desktop') if os.name == 'nt' else os.path.expanduser("~/Desktop")
        project_path = os.path.join(desktop_path, project_name)

        result_lines = []
        result_lines.append(f"✅ 프로젝트 '{project_name}' 전환 완료")
        result_lines.append(f"📁 Flow ID: {flow_id}")

        if os.path.exists(project_path):
            try:
                os.chdir(project_path)
                result_lines.append(f"📂 작업 디렉토리: {project_path}")
            except Exception as e:
                result_lines.append(f"⚠️ 디렉토리 변경 실패: {str(e)}")

            # 4. README.md 읽기
            readme_path = os.path.join(project_path, "README.md")
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        readme_content = f.read()
                        # 첫 10줄 또는 500자 중 더 짧은 것
                        readme_lines = readme_content.split('\n')[:10]
                        readme_preview = '\n'.join(readme_lines)
                        if len(readme_preview) > 500:
                            readme_preview = readme_preview[:500] + "..."
                        result_lines.append(f"\n📄 README.md:")
                        result_lines.append(readme_preview)
                except Exception as e:
                    result_lines.append(f"⚠️ README.md 읽기 실패: {str(e)}")

            # 5. filedirectory.md 읽기
            filedir_path = os.path.join(project_path, "filedirectory.md")
            if os.path.exists(filedir_path):
                try:
                    with open(filedir_path, 'r', encoding='utf-8') as f:
                        filedir_content = f.read()
                        filedir_lines = filedir_content.split('\n')[:20]
                        filedir_preview = '\n'.join(filedir_lines)
                        if len(filedir_preview) > 500:
                            filedir_preview = filedir_preview[:500] + "..."
                        result_lines.append(f"\n📁 File Directory:")
                        result_lines.append(filedir_preview)
                except Exception as e:
                    result_lines.append(f"⚠️ filedirectory.md 읽기 실패: {str(e)}")
        else:
            result_lines.append(f"⚠️ 프로젝트 디렉토리를 찾을 수 없습니다: {project_path}")

        # 6. 모든 Plan 리스트 표시
        if self.current_flow.get('plans'):
            result_lines.append(f"\n📋 Plans ({len(self.current_flow['plans'])}개):")
            result_lines.append("-" * 50)

            for i, plan in enumerate(self.current_flow['plans']):
                # Task 집계
                tasks = plan.get('tasks', [])
                total_tasks = len(tasks)
                completed_tasks = sum(1 for t in tasks if t.get('status') in ['completed', 'reviewing'])

                # 완료 상태 아이콘 결정
                if plan.get('completed', False):
                    status_icon = "✅"  # Plan 완료됨
                elif total_tasks == 0:
                    status_icon = "📋"  # Task가 없음
                elif completed_tasks == total_tasks and total_tasks > 0:
                    status_icon = "🔄"  # 모든 Task 완료했지만 Plan은 미완료
                elif completed_tasks > 0:
                    status_icon = "⏳"  # 진행중
                else:
                    status_icon = "📝"  # 시작 전

                # Plan 정보 출력
                result_lines.append(f"\n{i+1}. {status_icon} {plan['name']}")
                result_lines.append(f"   ID: {plan['id']}")
                result_lines.append(f"   Tasks: {total_tasks}개 (완료: {completed_tasks}개)")
                if total_tasks > 0:
                    progress = (completed_tasks / total_tasks) * 100
                    result_lines.append(f"   진행률: {completed_tasks}/{total_tasks} ({progress:.0f}%)")
                result_lines.append(f"   설명: {plan.get('description', '설명 없음')}")

        # 7. 최근 Task context 확인
        recent_tasks_with_context = []
        for plan in self.current_flow.get('plans', []):
            for task in plan.get('tasks', []):
                if task.get('context') and task['context'].get('actions'):
                    recent_tasks_with_context.append(task)

        if recent_tasks_with_context:
            latest_task = recent_tasks_with_context[-1]
            result_lines.append(f"\n🔄 최근 작업 Task: {latest_task.get('description', '')}")
            if latest_task.get('context', {}).get('actions'):
                result_lines.append("   최근 작업 내역:")
                for action in latest_task['context']['actions'][-3:]:
                    result_lines.append(f"   - {action.get('action', 'No action')}")
                    if action.get('result'):
                        result_lines.append(f"     → {action['result']}")

        # Plan 선택 안내 추가
        if self.current_flow.get('plans'):
            result_lines.append("")
            result_lines.append("-" * 50)
            result_lines.append("💡 Plan을 선택하려면 번호를 입력하거나 'Plan 2 선택' 형식으로 입력해주세요.")
            result_lines.append("   예: '2' 또는 'Plan 2 선택' 또는 '2번 Plan'")

        return {'ok': True, 'data': '\n'.join(result_lines)}

    def _handle_plan_subcommand(self, args: str) -> Dict[str, Any]:
        """Plan 하위 명령어 처리"""
        if not self.current_flow:
            return {'ok': False, 'error': '현재 flow가 선택되지 않았습니다'}

        if not args:
            return {'ok': False, 'error': 'Plan 명령어가 필요합니다. 예: /flow plan add <name>'}

        parts = args.split(maxsplit=1)
        action = parts[0].lower()
        plan_args = parts[1] if len(parts) > 1 else ''

        if action == 'add':
            if not plan_args:
                return {'ok': False, 'error': 'Plan 이름이 필요합니다'}
            plan = self.create_plan(plan_args)
            if 'id' in plan:
                return {'ok': True, 'data': f'Plan 생성됨: {plan["id"]} - {plan["name"]}'}
            return {'ok': False, 'error': 'Plan 생성 실패'}

        elif action == 'list':
            plans = self.current_flow.get('plans', [])
            if not plans:
                return {'ok': True, 'data': 'Plan이 없습니다'}

            result = "📋 Plan 목록:\n"
            for plan in plans:
                task_count = len(plan.get('tasks', []))
                result += f"- {plan['id']}: {plan['name']} ({task_count} tasks)\n"
            return {'ok': True, 'data': result.strip()}

        return {'ok': False, 'error': f'Unknown plan action: {action}'}

    def _handle_task_subcommand(self, args: str) -> Dict[str, Any]:
        """Task 하위 명령어 처리"""
        if not self.current_flow:
            return {'ok': False, 'error': '현재 flow가 선택되지 않았습니다'}

        if not args:
            return {'ok': False, 'error': 'Task 명령어가 필요합니다. 예: /flow task add <plan_id> <name>'}

        parts = args.split(maxsplit=2)
        action = parts[0].lower()

        if action == 'add':
            if len(parts) < 3:
                return {'ok': False, 'error': 'Usage: /flow task add <plan_id> <task_name>'}

            plan_id = parts[1]
            # parts[2:]를 join하여 전체 task 이름 가져오기
            task_name = ' '.join(parts[2:])

            task = self.create_task(plan_id, task_name)
            if 'id' in task:
                return {'ok': True, 'data': f'Task 생성됨: {task["id"]} - {task["name"]}'}
            return {'ok': False, 'error': 'Task 생성 실패'}

        elif action == 'list':
            result = "📌 Task 목록:\n"
            plans = self.current_flow.get('plans', [])
            for plan in plans:
                result += f"\nPlan: {plan['name']}\n"
                tasks = plan.get('tasks', [])
                if tasks:
                    for task in tasks:
                        status = task.get('status', 'todo')
                        icon = '✅' if status == 'completed' else '🔄' if status == 'in_progress' else '⏳'
                        result += f"  {icon} {task['id']}: {task['name']}\n"
                else:
                    result += "  (No tasks)\n"
            return {'ok': True, 'data': result.strip()}

        return {'ok': False, 'error': f'Unknown task action: {action}'}

    def _export_flow_data(self) -> Dict[str, Any]:
        """현재 flow 데이터 내보내기"""
        if not self.current_flow:
            return {'ok': False, 'error': '현재 flow가 선택되지 않았습니다'}

        import json
        try:
            export_data = {
                'flow': self.current_flow,
                'exported_at': datetime.now().isoformat(),
                'stats': self.get_current_flow_status()
            }

            # 파일로 저장
            filename = f"flow_export_{self.current_flow['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            export_path = os.path.join(self.data_dir, 'exports', filename)

            # exports 디렉토리 생성
            os.makedirs(os.path.dirname(export_path), exist_ok=True)

            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            return {'ok': True, 'data': f'Flow exported to: {filename}'}

        except Exception as e:
            return {'ok': False, 'error': f'Export failed: {str(e)}'}
    def _list_flows(self) -> Dict[str, Any]:
        """Flow 목록 표시"""
        try:
            if hasattr(self, 'list_flows'):
                flows = self.list_flows()
                if not flows:
                    return {'ok': True, 'data': 'Flow가 없습니다'}

                lines = ["📁 Flow 목록:"]
                for flow in flows:
                    marker = "▶" if flow.get('id') == self.current_flow.get('id') else " "
                    lines.append(f"{marker} [{flow['id']}] {flow['name']}")

                return {'ok': True, 'data': '\n'.join(lines)}
            else:
                return {'ok': False, 'error': 'Flow 목록 조회 기능 없음'}
        except Exception as e:
            return {'ok': False, 'error': f'Flow 목록 조회 실패: {str(e)}'}

    def _create_flow(self, name: str) -> Dict[str, Any]:
        """새 Flow 생성"""
        if not name:
            name = f"Flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            if hasattr(self, 'create_flow'):
                flow = self.create_flow(name)
                return {'ok': True, 'data': f'Flow 생성됨: {name}'}
            else:
                return {'ok': False, 'error': 'Flow 생성 기능 없음'}
        except Exception as e:
            return {'ok': False, 'error': f'Flow 생성 실패: {str(e)}'}

    def _switch_flow(self, flow_id: str) -> Dict[str, Any]:
        """Flow 전환"""
        if not flow_id:
            return {'ok': False, 'error': 'Usage: /flow switch <flow_id>'}

        try:
            if hasattr(self, 'switch_flow'):
                self.switch_flow(flow_id)
                return {'ok': True, 'data': f'Flow 전환됨: {flow_id}'}
            else:
                return {'ok': False, 'error': 'Flow 전환 기능 없음'}
        except Exception as e:
            return {'ok': False, 'error': f'Flow 전환 실패: {str(e)}'}

    def _delete_flow(self, flow_id: str) -> Dict[str, Any]:
        """Flow 삭제"""
        if not flow_id:
            return {'ok': False, 'error': 'Usage: /flow delete <flow_id>'}

        try:
            if hasattr(self, 'delete_flow'):
                self.delete_flow(flow_id)
                return {'ok': True, 'data': f'Flow 삭제됨: {flow_id}'}
            else:
                return {'ok': False, 'error': 'Flow 삭제 기능 없음'}
        except Exception as e:
            return {'ok': False, 'error': f'Flow 삭제 실패: {str(e)}'}

    def _handle_plan_command(self, args: str) -> Dict[str, Any]:
        """Plan 명령어 처리"""
        if not self._has_flow_v2:
            return {'ok': False, 'error': 'Flow v2가 활성화되지 않았습니다'}

        if not args:
            return {'ok': False, 'error': 'Usage: /plan <add|list|complete|reopen|status>'}

        parts = args.split(maxsplit=1)
        subcmd = parts[0].lower()
        plan_args = parts[1] if len(parts) > 1 else ''

        if subcmd == 'add':
            return self._add_plan(plan_args)
        elif subcmd == 'list':
            return self._list_plans()
        elif subcmd == 'complete':
            if not plan_args:
                return {'ok': False, 'error': 'Usage: /plan complete <plan_id>'}
            return self._complete_plan(plan_args.strip())
        elif subcmd == 'reopen':
            if not plan_args:
                return {'ok': False, 'error': 'Usage: /plan reopen <plan_id>'}
            return self._reopen_plan(plan_args.strip())
        elif subcmd == 'status':
            return self._show_plan_status()
        else:
            return {'ok': False, 'error': f'Unknown plan command: {subcmd}. Available: add, list, complete, reopen, status'}

    def _add_plan(self, name: str) -> Dict[str, Any]:
        """Plan 추가"""
        if not name:
            name = f"Plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            if hasattr(self, 'create_plan'):
                plan = self.create_plan(name)
                return {'ok': True, 'data': f'Plan 생성됨: {name}'}
            else:
                return {'ok': False, 'error': 'Plan 생성 기능 없음'}
        except Exception as e:
            return {'ok': False, 'error': f'Plan 생성 실패: {str(e)}'}

    def _list_plans(self) -> Dict[str, Any]:
        """Plan 목록 표시"""
        try:
            if not self.current_flow:
                return {'ok': False, 'error': 'Flow가 선택되지 않았습니다'}

            plans = self.current_flow.get('plans', [])
            if not plans:
                return {'ok': True, 'data': 'Plan이 없습니다'}

            lines = ["📋 Plan 목록:"]
            for plan in plans:
                task_count = len(plan.get('tasks', []))
                lines.append(f"- [{plan['id']}] {plan['name']} ({task_count}개 태스크)")

            return {'ok': True, 'data': '\n'.join(lines)}

        except Exception as e:
            return {'ok': False, 'error': f'Plan 목록 조회 실패: {str(e)}'}

    # === Context 명령어 ===



    def _show_plan_status(self) -> Dict[str, Any]:
        """모든 Plan의 완료 상태 표시"""
        try:
            if not self.current_flow:
                return {'ok': False, 'error': '활성 Flow가 없습니다'}

            plans = self.current_flow.get('plans', [])
            if not plans:
                return {'ok': True, 'data': 'Plan이 없습니다'}

            output = ['📊 Plan 완료 상태:\n']
            total_plans = len(plans)
            completed_plans = 0

            for plan in plans:
                plan_id = plan['id']
                plan_name = plan['name']
                is_completed = plan.get('completed', False)
                tasks = plan.get('tasks', [])

                # Task 완료 상태 계산
                if tasks:
                    completed_tasks = sum(1 for task in tasks if task.get('status') == 'completed')
                    total_tasks = len(tasks)
                else:
                    completed_tasks = 0
                    total_tasks = 0

                # 아이콘 설정
                if is_completed:
                    icon = '✅'
                    completed_plans += 1
                elif total_tasks > 0 and completed_tasks == total_tasks:
                    icon = '🔄'  # 모든 Task 완료했지만 Plan은 미완료
                else:
                    icon = '⏳'

                output.append(f'{icon} {plan_name}')
                output.append(f'   ID: {plan_id[:30]}...')
                output.append(f'   Tasks: {completed_tasks}/{total_tasks} 완료')
                output.append('')

            # 전체 통계
            output.append(f'\n📈 전체 진행률: {completed_plans}/{total_plans} Plans 완료 ({completed_plans/total_plans*100:.1f}%)')

            return {'ok': True, 'data': '\n'.join(output)}

        except Exception as e:
            return {'ok': False, 'error': f'Plan 상태 표시 중 오류: {str(e)}'}

    def _handle_context_command(self, args: str) -> Dict[str, Any]:
        """Context 명령어 처리"""
        if not self.context_manager:
            return {'ok': False, 'error': 'Context 시스템이 활성화되지 않았습니다'}

        try:
            if args:
                if args.startswith('show'):
                    parts = args.split()
                    format_type = parts[1] if len(parts) > 1 else 'brief'
                    return {'ok': True, 'data': self.context_manager.get_summary(format_type)}

            # 기본: brief 요약
            return {'ok': True, 'data': self.context_manager.get_summary('brief')}

        except Exception as e:
            return {'ok': False, 'error': f'Context 조회 실패: {str(e)}'}

    def _handle_session_command(self, args: str) -> Dict[str, Any]:
        """Session 명령어 처리"""
        if not self.context_manager:
            return {'ok': False, 'error': 'Context 시스템이 활성화되지 않았습니다'}

        if not args:
            return {'ok': False, 'error': 'Usage: /session <save|list|restore>'}

        parts = args.split(maxsplit=1)
        subcmd = parts[0].lower()
        session_args = parts[1] if len(parts) > 1 else ''

        try:
            if subcmd == 'save':
                name = session_args or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                if hasattr(self, 'save_checkpoint'):
                    self.save_checkpoint(name)
                return {'ok': True, 'data': f'세션 저장됨: {name}'}

            elif subcmd == 'list':
                if hasattr(self, 'list_sessions'):
                    sessions = self.list_sessions()
                    if not sessions:
                        return {'ok': True, 'data': '저장된 세션이 없습니다'}

                    lines = ["💾 저장된 세션:"]
                    for session in sessions:
                        lines.append(f"- {session}")
                    return {'ok': True, 'data': '\n'.join(lines)}

            elif subcmd == 'restore':
                if not session_args:
                    return {'ok': False, 'error': 'Usage: /session restore <session_name>'}
                if hasattr(self, 'restore_session'):
                    self.restore_session(session_args)
                    return {'ok': True, 'data': f'세션 복원됨: {session_args}'}

            else:
                return {'ok': False, 'error': f'Unknown session command: {subcmd}'}

        except Exception as e:
            return {'ok': False, 'error': f'Session 명령 실패: {str(e)}'}

    def _show_history(self, args: str) -> Dict[str, Any]:
        """히스토리 표시"""
        if not self.context_manager:
            return {'ok': False, 'error': 'Context 시스템이 활성화되지 않았습니다'}

        try:
            count = int(args) if args else 10
            history = self.context_manager.get_history(count)

            if not history:
                return {'ok': True, 'data': '히스토리가 없습니다'}

            lines = [f"📜 최근 {count}개 히스토리:"]
            for i, item in enumerate(history, 1):
                lines.append(f"{i}. {item}")

            return {'ok': True, 'data': '\n'.join(lines)}

        except Exception as e:
            return {'ok': False, 'error': f'히스토리 조회 실패: {str(e)}'}

    def _show_stats(self, args: str) -> Dict[str, Any]:
        """통계 정보 표시"""
        if not self.context_manager:
            return {'ok': False, 'error': 'Context 시스템이 활성화되지 않았습니다'}

        try:
            stats = self.context_manager.get_stats()

            lines = ["📊 통계 정보:"]
            for key, value in stats.items():
                lines.append(f"{key}: {value}")

            return {'ok': True, 'data': '\n'.join(lines)}

        except Exception as e:
            return {'ok': False, 'error': f'통계 조회 실패: {str(e)}'}

    # === 호환성 메서드 ===

    def wf_command(self, command: str, verbose: bool = False) -> Dict[str, Any]:
        """기존 WorkflowManager와의 호환성을 위한 메서드"""
        return self.process_command(command)

    # === Flow v2 핵심 메서드 직접 구현 ===

    def create_flow(self, name: str) -> Dict[str, Any]:
        """새 Flow 생성"""
        flow_id = self._generate_unique_id("flow")
        new_flow = {
            'id': flow_id,
            'name': name,
            'plans': [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        if not hasattr(self, 'flows'):
            self.flows = []

        self.flows.append(new_flow)
        self.current_flow = new_flow

        # 저장
        self._save_flows()

        return new_flow

    def list_flows(self) -> List[Dict[str, Any]]:
        """모든 Flow 목록 반환"""
        if not hasattr(self, 'flows'):
            self.flows = []
            self._load_flows()

        return self.flows

    def switch_flow(self, flow_id: str) -> bool:
        """Flow 전환"""
        for flow in self.flows:
            if flow['id'] == flow_id:
                self.current_flow = flow
                self._save_current_flow_id(flow_id)
                return True

        raise ValueError(f"Flow not found: {flow_id}")

    def delete_flow(self, flow_id: str) -> bool:
        """Flow 삭제"""
        if self.current_flow and self.current_flow['id'] == flow_id:
            raise ValueError("Cannot delete current flow")

        # Flow 존재 여부 확인
        flow_exists = any(f['id'] == flow_id for f in self.flows)
        if not flow_exists:
            return False  # Flow가 없으면 False 반환

        self.flows = [f for f in self.flows if f['id'] != flow_id]
        self._save_flows()
        return True
    def create_plan(self, name: str, flow_id: str = None) -> Dict[str, Any]:
        """Plan 생성"""
        if not self.current_flow and not flow_id:
            self._create_default_flow()

        target_flow = self.current_flow
        if flow_id:
            target_flow = next((f for f in self.flows if f['id'] == flow_id), None)
            if not target_flow:
                raise ValueError(f"Flow not found: {flow_id}")

        plan_id = self._generate_unique_id("plan")
        new_plan = {
            'id': plan_id,
            'name': name,
            'tasks': [],
            'created_at': datetime.now().isoformat(),
            'completed': False
        }

        if 'plans' not in target_flow:
            target_flow['plans'] = []

        target_flow['plans'].append(new_plan)
        self._save_flows()

        return new_plan

    def create_task(self, name: str, description: str = '', plan_id: str = None) -> Dict[str, Any]:
        """Task 생성"""
        if not self.current_flow:
            self._create_default_flow()

        # Plan이 없으면 첫 번째 plan 사용 또는 생성
        if not plan_id:
            if not self.current_flow.get('plans'):
                self.create_plan('Default Plan')
            plan_id = self.current_flow['plans'][0]['id']

        # Plan 찾기
        target_plan = None
        for plan in self.current_flow.get('plans', []):
            if plan['id'] == plan_id:
                target_plan = plan
                break

        if not target_plan:
            # Plan ID 없이 첫 번째 plan 사용
            if self.current_flow.get('plans'):
                target_plan = self.current_flow['plans'][0]
            else:
                raise ValueError("No plan available")

        task_id = self._generate_unique_id("task")
        new_task = {
            'id': task_id,
            'name': name,
            'description': description,
            'status': 'todo',
            'context': copy.deepcopy(DEFAULT_CONTEXT),  # 컨텍스트 추가
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'started_at': None,
            'completed_at': None
        }

        if 'tasks' not in target_plan:
            target_plan['tasks'] = []

        target_plan['tasks'].append(new_task)
        self._save_flows()

        return new_task

    def update_task_context(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """Task의 context 업데이트 (deep merge)"""
        if not self.current_flow:
            return {'ok': False, 'error': 'No active flow'}

        # Task 찾기
        target_task = None
        target_plan = None

        for plan in self.current_flow.get('plans', []):
            for task in plan.get('tasks', []):
                if task['id'] == task_id:
                    target_task = task
                    target_plan = plan
                    break
            if target_task:
                break

        if not target_task:
            return {'ok': False, 'error': f'Task not found: {task_id}'}

        # Context 가져오기 (없으면 기본값)
        if 'context' not in target_task:
            target_task['context'] = copy.deepcopy(DEFAULT_CONTEXT)

        context = target_task['context']

        # Deep merge 함수
        def deep_merge(base, update):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    deep_merge(base[key], value)
                else:
                    base[key] = value

        # Context 업데이트
        deep_merge(context, kwargs)

        # 타임스탬프 업데이트
        target_task['updated_at'] = datetime.now().isoformat()

        # 저장
        self._save_flows()

        return {'ok': True, 'data': target_task}

    def add_task_action(self, task_id: str, action: str, result: str = '', **meta) -> Dict[str, Any]:
        """Task에 작업 내역 추가"""
        if not self.current_flow:
            return {'ok': False, 'error': 'No active flow'}

        # Task 찾기
        target_task = None

        for plan in self.current_flow.get('plans', []):
            for task in plan.get('tasks', []):
                if task['id'] == task_id:
                    target_task = task
                    break
            if target_task:
                break

        if not target_task:
            return {'ok': False, 'error': f'Task not found: {task_id}'}

        # Context 확인
        if 'context' not in target_task:
            target_task['context'] = copy.deepcopy(DEFAULT_CONTEXT)

        # Action 추가
        action_entry = {
            'time': datetime.now().isoformat(),
            'action': action,
            'result': result
        }

        # meta 데이터가 있으면 추가
        if meta:
            action_entry['meta'] = meta

        target_task['context']['actions'].append(action_entry)
        target_task['updated_at'] = datetime.now().isoformat()

        # 저장
        self._save_flows()

        return {'ok': True, 'data': action_entry}

    def _validate_task_transition(self, current_status: TaskStatus, new_status: TaskStatus) -> bool:
        """Task 상태 전환이 유효한지 검증"""
        if current_status == new_status:
            return True
        allowed_transitions = TASK_TRANSITIONS.get(current_status, set())
        return new_status in allowed_transitions

    def update_task_status_validated(self, task_id: str, new_status: str, force: bool = False) -> Dict[str, Any]:
        """검증된 Task 상태 업데이트"""
        if not self.current_flow:
            return {'ok': False, 'error': 'No active flow'}

        # 새 상태를 TaskStatus로 변환
        try:
            new_status_enum = TaskStatus.from_string(new_status)
        except:
            return {'ok': False, 'error': f'Invalid status: {new_status}'}

        # Task 찾기 및 처리
        for plan in self.current_flow.get('plans', []):
            for task in plan.get('tasks', []):
                if task['id'] == task_id:
                    current_status_str = task.get('status', 'todo')
                    current_status_enum = TaskStatus.from_string(current_status_str)

                    # 전환 검증
                    if not force and not self._validate_task_transition(current_status_enum, new_status_enum):
                        allowed = [s.value for s in TASK_TRANSITIONS.get(current_status_enum, set())]
                        return {'ok': False, 'error': f'Invalid transition', 'allowed': allowed}

                    # 상태 업데이트
                    task['status'] = new_status_enum.value
                    task['updated_at'] = datetime.now().isoformat()
                    self._save_flows()

                    return {'ok': True, 'data': {'task_id': task_id, 'new_status': new_status_enum.value}}

        return {'ok': False, 'error': f'Task not found: {task_id}'}

    def update_task_status(self, task_id: str, status: str) -> bool:
        """Task 상태 업데이트"""
        if not self.current_flow:
            return False

        for plan in self.current_flow.get('plans', []):
            for task in plan.get('tasks', []):
                if task['id'] == task_id:
                    task['status'] = status
                    task['updated_at'] = datetime.now().isoformat()
                    self._save_flows()
                    return True

        return False



    def update_plan_status(self, plan_id: str, completed: bool = True) -> Dict[str, Any]:
        """Plan 상태 업데이트 (public API)"""
        if completed:
            return self._complete_plan(plan_id)
        else:
            return self._reopen_plan(plan_id)

    def get_current_flow_status(self) -> Dict[str, Any]:
        """현재 Flow 상태 반환"""
        if not self.current_flow:
            return {'error': 'No active flow'}

        total_tasks = 0
        completed_tasks = 0

        for plan in self.current_flow.get('plans', []):
            for task in plan.get('tasks', []):
                total_tasks += 1
                if task['status'] in ['done', 'completed']:
                    completed_tasks += 1

        return {
            'flow': self.current_flow['name'],
            'plans': len(self.current_flow.get('plans', [])),
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'progress': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        }

    # === 저장/로드 메서드 ===

    def _load_flows(self):
        """
        flows.json에서 flow 데이터 로드

        flows.json 구조:
        {
            "flows": [...],
            "current_flow_id": "...",
            "last_saved": "...",
            "version": "2.0"
        }
        """
        flows_path = os.path.join(self.data_dir, 'flows.json')

        if os.path.exists(flows_path):
            try:
                with open(flows_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.flows = data.get('flows', [])

                    # current_flow_id가 있으면 해당 flow 찾기
                    current_id = data.get('current_flow_id')
                    if current_id:
                        for flow in self.flows:
                            if flow['id'] == current_id:
                                self.current_flow = flow
                                break

                    # Debug 로그 (debug 속성 확인)
                    if hasattr(self, 'debug') and self.debug:
                        print(f"✅ Flow 데이터 로드 완료: {len(self.flows)}개 flow")

            except Exception as e:
                if hasattr(self, 'debug') and self.debug:
                    print(f'❌ Flow 데이터 로드 실패: {e}')
                self.flows = []
        else:
            # flows.json이 없으면 빈 리스트로 초기화
            self.flows = []
            if hasattr(self, 'debug') and self.debug:
                print("📝 flows.json 파일이 없습니다. 새로 생성됩니다.")


    def _save_current_flow_id(self, flow_id: str) -> bool:
        """
        현재 flow ID를 flows.json에 저장

        Args:
            flow_id: 저장할 flow ID

        Returns:
            bool: 저장 성공 여부
        """
        try:
            flows_path = os.path.join(self.data_dir, 'flows.json')

            # 기존 데이터 읽기
            if os.path.exists(flows_path):
                with open(flows_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {'flows': self.flows}

            # current_flow_id 업데이트
            data['current_flow_id'] = flow_id
            data['last_saved'] = datetime.now().isoformat()

            # 저장
            with open(flows_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            if hasattr(self, 'debug') and self.debug:
                print(f"❌ current_flow_id 저장 실패: {e}")
            return False




    def _save_flows(self, force: bool = False) -> bool:
        """
        Flow 데이터 저장 (개선된 버전)

        Args:
            force: 강제 저장 여부

        Returns:
            bool: 저장 성공 여부
        """
        flows_path = os.path.join(self.data_dir, 'flows.json')

        try:
            # 저장할 데이터 준비
            save_data = {
                'flows': self.flows,
                'current_flow_id': self.current_flow['id'] if self.current_flow else None,
                'last_saved': datetime.now().isoformat(),
                'version': '2.0'
            }

            # 임시 파일에 먼저 저장
            temp_path = flows_path + '.tmp'
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            # 원자적 이동
            shutil.move(temp_path, flows_path)

            # 로깅
            if hasattr(self, '_last_save_time'):
                elapsed = (datetime.now() - self._last_save_time).total_seconds()
                if elapsed > 60:
                    print(f"💾 Flows 자동 저장 ({len(self.flows)} flows)")

            self._last_save_time = datetime.now()
            self._save_error_count = 0
            return True

        except Exception as e:
            if not hasattr(self, '_save_error_count'):
                self._save_error_count = 0
            self._save_error_count += 1

            if self._save_error_count <= 3:
                print(f"⚠️ Flow 저장 실패 ({self._save_error_count}회): {e}")

            return False
# 클래스 종료
