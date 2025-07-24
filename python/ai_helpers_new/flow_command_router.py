"""
Flow 중심 명령어 라우터
"""
from typing import Dict, Any, List, Optional, Tuple
import re
import os
import json
from datetime import datetime
from ai_helpers_new.util import ok, err

class FlowCommandRouter:
    """Flow 중심의 통합 명령어 라우터"""

    def __init__(self, unified_manager):
        self.manager = unified_manager
        self.command_map = {
            # 기본 명령어
            'flow': self.handle_flow,
            'flows': self.handle_flows,
            'f': self.handle_flow,  # 단축키
            'fs': self.handle_flows,  # 단축키

            # Task 관련 명령어
            'task': self.handle_task,
            'task_list': self.handle_task_list,

            # 기존 명령어 호환성
            'project': self.handle_flow,  # 리다이렉트
            'projects': self.handle_flows,  # 리다이렉트
            'fp': self.handle_flow,  # 기존 fp 명령
        
            # 새로운 명령어 (v31.0)
            'plans': self.handle_plans,
            'start': self.handle_start,
            'complete': self.handle_complete,
            'status': self.handle_status,
            'tasks': self.handle_tasks,

            # Plan 관련 명령어 (v31.0)
            'plan': self.handle_plans,  # plan 단독 명령어
}

        # 서브 명령어
        self.flow_subcommands = {
            'create': self.handle_flow_create,
            'list': self.handle_flow_list,
            'status': self.handle_flow_status,
            'delete': self.handle_flow_delete,
            'archive': self.handle_flow_archive,
            'restore': self.handle_flow_restore,
        }

    def route(self, command: str) -> Dict[str, Any]:
        """명령어 라우팅"""
        parts = command.strip().split()
        if not parts:
            return {'ok': False, 'error': '명령어가 비어있습니다'}

        # 명령어 파싱
        cmd = parts[0].lstrip('/')
        args = parts[1:] if len(parts) > 1 else []

        # 메인 명령어 처리
        if cmd in self.command_map:
            return self.command_map[cmd](args)

        # v30.0: 숫자 입력으로 Plan 선택
        if cmd.isdigit():
            return self.handle_plan_select(int(cmd))

        # "Plan X 선택" 형식 처리
        if cmd.lower() == 'plan' and len(args) >= 2 and args[1] == '선택':
            if args[0].isdigit():
                return self.handle_plan_select(int(args[0]))

        return {'ok': False, 'error': f'알 수 없는 명령어: {cmd}'}

    def handle_flow(self, args: List[str]) -> Dict[str, Any]:
        """flow 명령어 처리"""
        if not args:
            # /flow만 입력한 경우 - v30.0: Plan 리스트 표시
            return self.handle_flow_status([])

        # 서브 명령어 확인
        if args[0] in self.flow_subcommands:
            return self.flow_subcommands[args[0]](args[1:])

        # Flow 이름으로 전환
        flow_name = args[0]

        # 특수 명령어
        if flow_name == '-':
            # 이전 Flow로 전환
            return self.manager.switch_to_previous()

        # 일반 Flow 전환
        result = self.manager.switch_project(flow_name)
        if result['ok']:
            # Flow 전환 성공 시 Plan 리스트도 표시
            status_result = self.handle_flow_status([])
            if status_result['ok']:
                # 전환 메시지와 Plan 리스트 결합
                switch_msg = f"✅ Flow '{flow_name}'로 전환됨"
                combined_data = f"{switch_msg}\n\n{status_result['data']}"
                return {'ok': True, 'data': combined_data}
        return result

    def handle_flows(self, args: List[str]) -> Dict[str, Any]:
        """flows 목록 명령어"""
        filters = {
            'active': '--active' in args,
            'recent': '--recent' in args,
            'archived': '--archived' in args,
        }

        # 검색어 추출
        search_term = None
        for arg in args:
            if not arg.startswith('--'):
                search_term = arg
                break

        # Flow 목록 가져오기
        flows = self.manager.list_flows(
            search=search_term,
            include_archived=filters['archived'],
            sort_by='recent' if filters['recent'] else 'name'
        )

        # 포맷팅
        return self._format_flow_list(flows)

    def handle_flow_create(self, args: List[str]) -> Dict[str, Any]:
        """flow create 명령어"""
        if not args:
            return {'ok': False, 'error': 'Flow 이름을 지정하세요'}

        name = args[0]
        template = 'default'

        # 템플릿 옵션 파싱
        for arg in args[1:]:
            if arg.startswith('--template='):
                template = arg.split('=')[1]

        return self.manager.create_project(name, template)

    def handle_flow_status(self, args: List[str]) -> Dict[str, Any]:
        """flow status 명령어 - v30.0 Plan 리스트 표시"""
        status = self.manager.get_status()

        if not status['ok']:
            return status

        # 상태 포맷팅
        data = status['data']
        
        # v30.0 - Plan 리스트 표시
        output = [
            f"🌊 Flow: {data['project']['name']}",
            f"📋 Plans ({data['flow']['plans']} 개):",
            ""
        ]
        
        # Plan 리스트 가져오기
        try:
            # FlowManager를 직접 가져와서 사용
            from .flow_manager import FlowManager
            fm = FlowManager()
            
            # 현재 프로젝트 이름으로 Flow 찾기
            flow_name = data['project']['name']
            flows = fm.list_flows()
            
            current_flow = None
            for flow in flows:
                if flow.name == flow_name:
                    current_flow = flow
                    break
            
            if current_flow and current_flow.plans:
                for i, (plan_id, plan) in enumerate(current_flow.plans.items(), 1):
                        # Plan 상태 아이콘
                        if plan.completed:
                            status_icon = "✅"
                        else:
                            # 모든 Task 완료했는지 확인
                            all_tasks_done = all(
                                task.status in ['completed', 'reviewing', 'approved'] 
                                for task in plan.tasks.values()
                            ) if plan.tasks else False
                            
                            if all_tasks_done and plan.tasks:
                                status_icon = "🔄"  # 모든 Task 완료했지만 Plan은 미완료
                            else:
                                status_icon = "⏳"
                        
                        # Plan 정보 표시
                        plan_line = f"{i}. {status_icon} {plan.name}"
                        if plan.tasks:
                            completed_tasks = sum(1 for t in plan.tasks.values() 
                                                if t.status in ['completed', 'approved'])
                            plan_line += f" ({completed_tasks}/{len(plan.tasks)} tasks)"
                        
                        output.append(plan_line)
            else:
                output.append("Plan이 없습니다. /plan add [이름]으로 추가하세요.")
                
        except Exception as e:
            output.append(f"Plan 목록 로드 중 오류: {str(e)}")
        
        output.extend([
            "",
            "사용법:",
            "  - Plan 선택: '2' 또는 'Plan 2 선택'",
            "  - 새 Plan 추가: /plan add [이름]",
            "  - Plan 상태 확인: /plan status"
        ])

        return {'ok': True, 'data': '\n'.join(output)}


    def handle_flow_list(self, args: List[str]) -> Dict[str, Any]:
        """Flow 목록 표시"""
        flows = self.manager.list_flows()

        if not flows:
            return ok("생성된 Flow가 없습니다. '/flow create [name]'으로 새 Flow를 생성하세요.")

        # Flow 목록 생성
        flow_list = []
        for i, flow in enumerate(flows):
            # flow가 dict인지 객체인지 확인
            if isinstance(flow, dict):
                flow_id = flow.get('id', 'unknown')
                flow_name = flow.get('name', 'unknown')
                plans_count = len(flow.get('plans', {}))
            else:
                flow_id = getattr(flow, 'id', 'unknown')
                flow_name = getattr(flow, 'name', 'unknown')
                plans_count = len(getattr(flow, 'plans', {}))

            flow_list.append(f"{i+1}. {flow_name} (ID: {flow_id}, Plans: {plans_count})")

        result = "📋 Flow 목록:\n" + "\n".join(flow_list)
        return ok(result)

    def handle_task(self, args: List[str]) -> Dict[str, Any]:
        """task 명령어 처리"""
        if not args:
            return self.handle_task_list([])

        # 서브 명령어 확인
        subcommand = args[0]

        if subcommand == 'list':
            return self.handle_task_list(args[1:])
        elif subcommand == 'start':
            if len(args) < 2:
                return err("Task ID를 지정하세요. 예: /task start task_id")
            return self.manager.start_task(args[1])
        elif subcommand == 'complete':
            if len(args) < 2:
                return err("Task ID를 지정하세요. 예: /task complete task_id [메시지]")
            task_id = args[1]
            message = ' '.join(args[2:]) if len(args) > 2 else "작업 완료"
            return self.manager.complete_task(task_id, message)
        elif subcommand == 'status':
            if len(args) < 2:
                return err("Task ID를 지정하세요. 예: /task status task_id")
            return self.manager.get_task_status(args[1])
        else:
            return err(f"알 수 없는 task 서브커맨드: {subcommand}")

    def handle_task_list(self, args: List[str]) -> Dict[str, Any]:
        """Task 목록 표시"""
        # 현재 flow_id 가져오기
        flow_id = self._get_current_flow_id()
        if not flow_id:
            return {'ok': False, 'error': '활성 Flow가 없습니다. /flow [name]으로 Flow를 선택하세요.'}

        # flows에서 직접 가져오기
        if hasattr(self.manager, 'flows') and flow_id in self.manager.flows:
            flow_data = self.manager.flows[flow_id]
        else:
            # 또는 list_flows에서 찾기
            flows = self.manager.list_flows()
            flow_data = None
            for flow in flows:
                if isinstance(flow, dict) and flow.get('id') == flow_id:
                    flow_data = flow
                    break

            if not flow_data:
                return {'ok': False, 'error': f'Flow {flow_id}를 찾을 수 없습니다'}

        plans = flow_data.get('plans', {})

        if not plans:
            return {'ok': True, 'data': '📋 Task가 없습니다. Plan을 먼저 생성하세요.'}

        # 특정 plan_id가 제공된 경우
        if args and len(args) > 0:
            plan_id = args[0]
            if plan_id in plans:
                plan = plans[plan_id]
                tasks = plan.get('tasks', {})
                if not tasks:
                    return {'ok': True, 'data': f'📋 Plan {plan_id}에 Task가 없습니다.'}

                lines = [f"📋 Plan '{plan['name']}'의 Task 목록:"]
                for task_id, task in tasks.items():
                    status_icon = self._get_task_status_icon(task.get('status', 'todo'))
                    lines.append(f"  - {status_icon} [{task_id}] {task['name']}")
                return {'ok': True, 'data': '\n'.join(lines)}
            else:
                return {'ok': False, 'error': f'Plan {plan_id}를 찾을 수 없습니다'}

        # 모든 Plan의 Task 표시
        lines = [f"📋 {flow_id}의 전체 Task 목록:"]
        lines.append("")

        for plan_id, plan in plans.items():
            tasks = plan.get('tasks', {})
            if tasks:
                lines.append(f"Plan: {plan['name']} ({plan_id})")
                for task_id, task in tasks.items():
                    status_icon = self._get_task_status_icon(task.get('status', 'todo'))
                    lines.append(f"  - {status_icon} [{task_id}] {task['name']}")
                lines.append("")

        return {'ok': True, 'data': '\n'.join(lines)}
    def handle_flow_delete(self, args: List[str]) -> Dict[str, Any]:
        """flow delete 명령어"""
        if not args:
            return {'ok': False, 'error': 'Flow 이름을 지정하세요'}

        name = args[0]
        force = '--force' in args

        if not force:
            # 확인 프롬프트
            print(f"⚠️  Flow '{name}'을(를) 삭제하시겠습니까? (아카이브됩니다)")
            print("   완전 삭제하려면 --force 옵션을 사용하세요")
            confirm = input("계속하시겠습니까? (y/N): ")
            if confirm.lower() != 'y':
                return {'ok': False, 'data': '취소되었습니다'}

        return self.manager.delete_flow(name, force=force)

    def handle_flow_archive(self, args: List[str]) -> Dict[str, Any]:
        """flow archive 명령어"""
        if not args:
            return {'ok': False, 'error': 'Flow 이름을 지정하세요'}

        return self.manager.archive_flow(args[0])

    def handle_flow_restore(self, args: List[str]) -> Dict[str, Any]:
        """flow restore 명령어"""
        if not args:
            return {'ok': False, 'error': 'Flow 이름을 지정하세요'}

        return self.manager.restore_flow(args[0])

    def _format_flow_list(self, flows: List[Dict]) -> Dict[str, Any]:
        """Flow 목록 포맷팅"""
        if not flows:
            return {'ok': True, 'data': '🌊 Flow가 없습니다'}

        # 테이블 헤더
        output = ["🌊 Flow 목록:"]
        output.append("┌─────────────────────────┬──────────┬─────────┬─────────┐")
        output.append("│ Flow Name               │ Status   │ Plans   │ Tasks   │")
        output.append("├─────────────────────────┼──────────┼─────────┼─────────┤")

        # Flow 정보
        for flow in flows:
            status_icon = "🟢" if flow.get('active') else "⚪"
            if flow.get('archived'):
                status_icon = "🔵"

            name = f"{status_icon} {flow['name'][:20]:20}"
            status = flow.get('status', 'Inactive')[:8]
            plans = str(flow.get('plans', 0))[:7]
            tasks = str(flow.get('tasks', 0))[:7]

            output.append(f"│ {name} │ {status:8} │ {plans:7} │ {tasks:7} │")

        output.append("└─────────────────────────┴──────────┴─────────┴─────────┘")

        return {'ok': True, 'data': '\n'.join(output)}
    def handle_plan_select(self, plan_number: int) -> Dict[str, Any]:
        """Plan 선택 시 Context 읽기 (v30.0)"""
        from .context_integration import ContextIntegration
        from .flow_manager import FlowManager

        try:
            # 현재 Flow 정보 가져오기
            fm = FlowManager()

            # 현재 Flow ID 가져오기
            try:
                with open('.ai-brain/current_flow.txt', 'r') as f:
                    current_flow_id = f.read().strip()
            except:
                return {'ok': False, 'error': '활성 Flow가 없습니다'}
            flows = fm.list_flows()
            current_flow = None

            for flow in flows:
                if flow.id == current_flow_id:
                    current_flow = flow
                    break

            if not current_flow:
                return {'ok': False, 'error': f'Flow를 찾을 수 없습니다: {current_flow_id}'}

            # Plan 찾기
            if not current_flow.plans:
                return {'ok': False, 'error': 'Plan이 없습니다'}

            plan_list = list(current_flow.plans.items())
            if plan_number < 1 or plan_number > len(plan_list):
                return {'ok': False, 'error': f'잘못된 Plan 번호입니다. 1-{len(plan_list)} 사이를 선택하세요'}

            plan_id, selected_plan = plan_list[plan_number - 1]

            # Context 읽기
            context_integration = ContextIntegration()

            # Flow의 Context 파일 직접 읽기
            context_file = f'.ai-brain/contexts/flow_{current_flow.id}/context.json'
            flow_context = None

            if os.path.exists(context_file):
                with open(context_file, 'r') as f:
                    import json
                    flow_context = json.load(f)

            # 분석 결과 생성
            output = [
                f"📊 Plan '{selected_plan.name}' 분석 결과",
                ""
            ]

            # 완료된 Task 분석
            completed_tasks = []
            pending_tasks = []

            for task_id, task in selected_plan.tasks.items():
                if task.status in ['completed', 'approved']:
                    completed_tasks.append(task)
                else:
                    pending_tasks.append(task)

            if completed_tasks:
                output.append("## ✅ 완료된 작업 요약")
                for task in completed_tasks:
                    output.append(f"- {task.name}: {task.status}")
                output.append("")

            # Context 기반 현재 상태 분석
            output.append("## 🔍 Context 기반 현재 상태 분석")
            output.append(f"- Plan 진행률: {len(completed_tasks)}/{len(selected_plan.tasks)} Tasks 완료")

            if flow_context and 'actions' in flow_context:
                # 최근 작업 분석
                recent_actions = flow_context.get('actions', [])[-5:]
                if recent_actions:
                    output.append("- 최근 작업:")
                    for action in recent_actions:
                        output.append(f"  - {action.get('type', 'unknown')}")

            # 다음 단계 권장사항
            output.append("")
            output.append("## 💡 다음 단계 권장사항")

            if pending_tasks:
                output.append(f"1. **최우선**: {pending_tasks[0].name}")
                output.append(f"   - 상태: {pending_tasks[0].status}")
                output.append(f"   - Task ID: {pending_tasks[0].id}")
            else:
                output.append("✅ 모든 Task가 완료되었습니다!")
                output.append("- Plan 완료: `/plan complete {}`".format(plan_id))

            output.append("")
            output.append("## 🚀 시작하려면")
            if pending_tasks:
                output.append(f"- Task 시작: `/start {pending_tasks[0].id}`")
            output.append("- 새 Task 추가: `/task add {} 작업명`".format(plan_id))

            return {'ok': True, 'data': '\n'.join(output)}

        except Exception as e:
            return {'ok': False, 'error': f'Plan 선택 중 오류 발생: {str(e)}'}



    # === 새로 추가되는 명령어 핸들러 (v31.0) ===

    def handle_plans(self, args: List[str]) -> Dict[str, Any]:
        """현재 Flow의 Plan 목록 표시"""
        flow_id = self._get_current_flow_id()
        if not flow_id:
            return {'ok': False, 'error': '활성 Flow가 없습니다'}

        result = self.manager.list_plans(flow_id)
        if not result['ok']:
            return result

        plans = result['data']
        if not plans:
            return {'ok': True, 'data': '📋 생성된 Plan이 없습니다'}

        # Plan 목록 포맷팅
        lines = [f"📋 {flow_id}의 Plan 목록:"]
        lines.append("")

        for i, plan in enumerate(plans, 1):
            status_icon = "✅" if plan.get('completed') else "⏳"
            lines.append(f"{i}. {status_icon} {plan['name']} ({plan['id']})")
            lines.append(f"   Tasks: {plan.get('task_count', 0)}개")
            if plan.get('description'):
                lines.append(f"   설명: {plan['description']}")
            lines.append("")

        return {'ok': True, 'data': '\n'.join(lines)}

    def handle_start(self, args: List[str]) -> Dict[str, Any]:
        """Task 시작 (상태를 in_progress로 변경)"""
        if not args:
            return {'ok': False, 'error': 'Task ID를 지정하세요. 예: /start task_001_01'}

        task_id = args[0]

        # Task ID에서 plan_id 추출
        plan_id, flow_id = self._extract_ids_from_task(task_id)
        if not plan_id or not flow_id:
            return {'ok': False, 'error': 'Task ID 형식이 올바르지 않습니다'}

        result = self.manager.start_task(flow_id, plan_id, task_id)
        if result['ok']:
            return {'ok': True, 'data': f"✅ Task '{task_id}' 시작됨 (상태: in_progress)"}
        return result

    def handle_complete(self, args: List[str]) -> Dict[str, Any]:
        """Task 완료 (상태를 completed로 변경)"""
        if not args:
            return {'ok': False, 'error': 'Task ID를 지정하세요. 예: /complete task_001_01'}

        task_id = args[0]

        # Task ID에서 plan_id 추출
        plan_id, flow_id = self._extract_ids_from_task(task_id)
        if not plan_id or not flow_id:
            return {'ok': False, 'error': 'Task ID 형식이 올바르지 않습니다'}

        result = self.manager.complete_task(flow_id, plan_id, task_id)
        if result['ok']:
            return {'ok': True, 'data': f"✅ Task '{task_id}' 완료됨 (상태: completed)"}
        return result

    def handle_status(self, args: List[str]) -> Dict[str, Any]:
        """Task 상태 조회"""
        if not args:
            # 인자가 없으면 현재 Flow 상태 표시
            return self.handle_flow_status([])

        task_id = args[0]

        # Task ID에서 plan_id 추출
        plan_id, flow_id = self._extract_ids_from_task(task_id)
        if not plan_id or not flow_id:
            return {'ok': False, 'error': 'Task ID 형식이 올바르지 않습니다'}

        result = self.manager.get_task_status(flow_id, plan_id, task_id)
        if not result['ok']:
            return result

        task_data = result['data']
        lines = [
            f"📊 Task 상태: {task_id}",
            f"상태: {task_data.get('status', 'unknown')}",
            f"이름: {task_data.get('name', '')}",
            f"생성: {task_data.get('created_at', 'N/A')}",
            f"시작: {task_data.get('started_at', 'N/A')}",
            f"완료: {task_data.get('completed_at', 'N/A')}"
        ]

        return {'ok': True, 'data': '\n'.join(lines)}

    def handle_tasks(self, args: List[str]) -> Dict[str, Any]:
        """특정 Plan의 Task 목록 조회"""
        if not args:
            return {'ok': False, 'error': 'Plan ID를 지정하세요. 예: /tasks plan_001_flow'}

        plan_id = args[0]
        flow_id = self._get_current_flow_id()
        if not flow_id:
            return {'ok': False, 'error': '활성 Flow가 없습니다'}

        result = self.manager.list_tasks(flow_id, plan_id)
        if not result['ok']:
            return result

        tasks = result['data']
        if not tasks:
            return {'ok': True, 'data': f'📋 Plan {plan_id}에 Task가 없습니다'}

        # Task 목록 포맷팅
        lines = [f"📋 Plan {plan_id}의 Task 목록:"]
        lines.append("")

        for i, task in enumerate(tasks, 1):
            status_icons = {
                'todo': '📝',
                'in_progress': '🔄',
                'completed': '✅',
                'reviewing': '🔍',
                'error': '❌'
            }
            icon = status_icons.get(task.get('status', 'todo'), '❓')

            lines.append(f"{i}. {icon} {task['name']} ({task['id']})")
            lines.append(f"   상태: {task.get('status', 'todo')}")
            if task.get('started_at'):
                lines.append(f"   시작: {task['started_at']}")
            if task.get('completed_at'):
                lines.append(f"   완료: {task['completed_at']}")
            lines.append("")

        return {'ok': True, 'data': '\n'.join(lines)}

    # === 헬퍼 메서드 ===

    def _get_current_flow_id(self) -> Optional[str]:
        """현재 활성 Flow ID 가져오기"""
        try:
            # current_flow.txt에서 읽기
            with open('.ai-brain/current_flow.txt', 'r') as f:
                return f.read().strip()
        except:
            # 또는 manager에서 가져오기
            if hasattr(self.manager, 'current_flow'):
                flow = self.manager.current_flow
                if flow and hasattr(flow, 'id'):
                    return flow.id
                elif isinstance(flow, dict) and 'id' in flow:
                    return flow['id']
        return None

    def _get_task_status_icon(self, status: str) -> str:
        """Task 상태에 따른 아이콘 반환"""
        status_icons = {
            'todo': '⏳',
            'planning': '📐',
            'in_progress': '🔄',
            'reviewing': '🔍',
            'completed': '✅',
            'error': '❌',
            'blocked': '🚫'
        }
        return status_icons.get(status, '❓')

    def _extract_ids_from_task(self, task_id: str) -> Tuple[Optional[str], Optional[str]]:
        """Task ID에서 plan_id와 flow_id 추출"""
        # task_001_01 형식에서 plan_id 추출
        import re
        match = re.match(r'task_(\d{3})_(\d{2})', task_id)
        if match:
            plan_number = int(match.group(1))
            # 현재 Flow에서 해당 번호의 Plan 찾기
            flow_id = self._get_current_flow_id()
            if flow_id:
                result = self.manager.list_plans(flow_id)
                if result['ok']:
                    plans = result['data']
                    # plan_number에 해당하는 plan 찾기
                    for plan in plans:
                        # plan_001_xxx 형식에서 번호 추출
                        plan_match = re.match(r'plan_(\d{3})', plan['id'])
                        if plan_match and int(plan_match.group(1)) == plan_number:
                            return plan['id'], flow_id
        return None, None
