"""
FlowManagerUnified - 통합 워크플로우 매니저
Flow Project v2 + 기존 WorkflowManager 기능 통합
"""
import os
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Flow Project v2 import 시도
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

class FlowManagerUnified(FlowManagerWithContext):
    """통합된 Flow + Workflow 매니저"""

    def __init__(self, project_root: str = None):
        """초기화"""
        # 기본 속성 초기화
        self.current_flow = None
        self.context_manager = None
        self.flows = []
        self._has_flow_v2 = _has_flow_v2

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

        # 기본 flow가 없으면 생성
        if self._has_flow_v2 and not self.current_flow:
            self._create_default_flow()

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
        name = args.strip() if args else 'New Task'

        try:
            if self._has_flow_v2:
                # Flow v2 방식
                if not self.current_flow:
                    self._create_default_flow()

                # Plan이 없으면 생성
                if not self.current_flow.get('plans'):
                    if hasattr(self, 'create_plan'):
                        self.create_plan('Default Plan')

                # 태스크 생성
                if hasattr(self, 'create_task'):
                    task = self.create_task(name)
                    return {'ok': True, 'data': {
                        'id': task.get('id'),
                        'name': task.get('name'),
                        'message': f'태스크 추가됨: {name}'
                    }}
            else:
                # 기본 모드 (Flow v2 없을 때)
                task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                return {'ok': True, 'data': {
                    'id': task_id,
                    'name': name,
                    'message': f'태스크 추가됨: {name} (기본 모드)'
                }}

        except Exception as e:
            return {'ok': False, 'error': f'태스크 추가 실패: {str(e)}'}

    def _list_tasks(self, args: str) -> Dict[str, Any]:
        """태스크 목록 표시"""
        try:
            tasks = []

            if self._has_flow_v2 and self.current_flow:
                # Flow v2에서 태스크 가져오기
                for plan in self.current_flow.get('plans', []):
                    for task in plan.get('tasks', []):
                        tasks.append({
                            'id': task['id'],
                            'name': task['name'],
                            'status': task.get('status', 'todo'),
                            'plan': plan['name']
                        })

            if not tasks:
                return {'ok': True, 'data': '태스크가 없습니다.'}

            return {'ok': True, 'data': tasks}

        except Exception as e:
            return {'ok': False, 'error': f'태스크 목록 조회 실패: {str(e)}'}

    def _start_task(self, args: str) -> Dict[str, Any]:
        """태스크 시작"""
        if not args:
            return {'ok': False, 'error': 'Usage: /start <task_id>'}

        task_id = args.strip()

        try:
            if self._has_flow_v2 and hasattr(self, 'update_task_status'):
                self.update_task_status(task_id, 'in_progress')
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
                self.update_task_status(task_id, 'completed')

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
                return {'ok': True, 'data': f'태스크 {task_id} 완료됨 (기본 모드)'}

        except Exception as e:
            return {'ok': False, 'error': f'태스크 완료 실패: {str(e)}'}

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

        flow_handlers = {
            'list': self._list_flows,
            'create': lambda: self._create_flow(flow_args),
            'switch': lambda: self._switch_flow(flow_args),
            'delete': lambda: self._delete_flow(flow_args),
            'status': lambda: self._handle_flow_command(''),  # 현재 flow 정보
        }

        handler = flow_handlers.get(subcmd)
        if handler:
            return handler()

        return {'ok': False, 'error': f'Unknown flow command: {subcmd}'}

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
            return {'ok': False, 'error': 'Usage: /plan <add|list>'}

        parts = args.split(maxsplit=1)
        subcmd = parts[0].lower()
        plan_args = parts[1] if len(parts) > 1 else ''

        if subcmd == 'add':
            return self._add_plan(plan_args)
        elif subcmd == 'list':
            return self._list_plans()
        else:
            return {'ok': False, 'error': f'Unknown plan command: {subcmd}'}

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


# 클래스 종료
