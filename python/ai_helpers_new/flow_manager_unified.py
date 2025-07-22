"""
FlowManagerUnified - Facade Pattern Implementation
기존 API를 유지하면서 내부적으로 새로운 서비스 구조 사용
"""
import os
import json
import sys
import re
from datetime import datetime
import shutil
from typing import Dict, List, Optional, Any
from enum import Enum
from pathlib import Path

# 새로운 도메인 모델 및 서비스 import
from .domain.models import Flow, Plan, Task, TaskStatus
from .infrastructure.flow_repository import JsonFlowRepository
from .service.flow_service import FlowService
from .service.plan_service import PlanService
from .service.task_service import TaskService

# 기존 FlowManagerWithContext import (호환성)
# FlowManagerWithContext가 없는 경우 기본 클래스 정의
class FlowManagerWithContext:
    def __init__(self):
        self.context_manager = None


class FlowManagerUnified(FlowManagerWithContext):
    """
    통합 Flow 매니저 - Facade Pattern
    
    기존 API를 유지하면서 내부적으로 새로운 서비스 아키텍처 사용
    """
    
    def __init__(self, storage_path: str = None, context_manager=None):
        """초기화"""
        super().__init__()
        
        # Context Manager 설정
        self.context_manager = context_manager
        
        # 새로운 서비스 초기화 - 프로젝트별 관리
        if storage_path is None:
            # 현재 프로젝트의 .ai-brain/flows.json 사용
            storage_path = os.path.join(os.getcwd(), ".ai-brain", "flows.json")
        
        self.repository = JsonFlowRepository(storage_path=storage_path)
        self.flow_service = FlowService(self.repository)
        self.plan_service = PlanService(self.flow_service)
        self.task_service = TaskService(self.plan_service)
        
        # 명령어 핸들러 초기화
        self._init_command_handlers()
        
        # 레거시 호환성을 위한 속성
        self._flows = {}  # 내부 캐시
        self._current_flow = None
        
        # 초기 로드
        self._sync_flows_from_service()
    
    # === 레거시 속성 접근자 (호환성) ===
    
    @property
    def flows(self):
        """레거시 flows 속성 (딕셔너리)"""
        self._sync_flows_from_service()
        return self._flows
    
    @flows.setter
    def flows(self, value):
        """레거시 flows setter"""
        if isinstance(value, dict):
            # 딕셔너리를 Flow 객체로 변환하여 저장
            flows_dict = {}
            for flow_id, flow_data in value.items():
                if isinstance(flow_data, dict):
                    flows_dict[flow_id] = Flow.from_dict(flow_data)
                else:
                    flows_dict[flow_id] = flow_data
            self.repository.save_all(flows_dict)
            self._sync_flows_from_service()
    
    @property
    def current_flow(self):
        """현재 활성 Flow (레거시 호환)"""
        flow = self.flow_service.get_current_flow()
        if flow:
            return flow.to_dict()
        return None
    
    @current_flow.setter
    def current_flow(self, value):
        """현재 Flow 설정 (레거시 호환)"""
        if isinstance(value, dict) and 'id' in value:
            self.flow_service.set_current_flow(value['id'])
            self._current_flow = value
    
    # === 명령어 처리 (기존 API 유지) ===
    
    def process_command(self, command: str) -> Dict[str, Any]:
        """통합 명령어 처리 - 기존 API 유지"""
        
        # Plan 선택 패턴 (숫자 입력)
        plan_select_patterns = [
            (r'^(\d+)$', 'number'),
            (r'^[Pp]lan\s+(\d+)$', 'plan_num'),
            (r'^[Pp]lan\s+(\d+)\s*선택', 'plan_select'),
            (r'^(\d+)번\s*[Pp]lan', 'num_plan')
        ]
        
        command_stripped = command.strip()
        for pattern, pattern_type in plan_select_patterns:
            match = re.match(pattern, command_stripped)
            if match:
                plan_number = match.group(1)
                return self._handle_plan_select(plan_number)
        
        # 기존 명령어 처리
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
        
        return {'ok': False, 'error': f'Unknown command: {cmd}'}
    
    def wf_command(self, command: str, verbose: bool = False) -> Dict[str, Any]:
        """WorkflowManager 호환 메서드"""
        return self.process_command(command)
    
    # === Flow 관리 (새 서비스 사용) ===
    
    def create_flow(self, name: str) -> Dict[str, Any]:
        """새 Flow 생성"""
        flow = self.flow_service.create_flow(name)
        self._sync_flows_from_service()
        
        if self.context_manager:
            self.context_manager.add_event('flow_created', {
                'flow_id': flow.id,
                'name': name
            })
        
        return flow.to_dict()
    
    def list_flows(self) -> List[Dict[str, Any]]:
        """모든 Flow 목록"""
        flows = self.flow_service.list_flows()
        return [flow.to_dict() for flow in flows]
    
    def switch_flow(self, flow_id: str) -> Dict[str, Any]:
        """Flow 전환"""
        if self.flow_service.set_current_flow(flow_id):
            self._sync_flows_from_service()
            flow = self.flow_service.get_current_flow()
            
            if self.context_manager:
                self.context_manager.add_event('flow_switched', {
                    'flow_id': flow_id
                })
            
            return {
                'ok': True,
                'data': f"Switched to flow: {flow.name}",
                'flow': flow.to_dict()
            }
        
        return {'ok': False, 'error': f'Flow {flow_id} not found'}
    
    def delete_flow(self, flow_id: str) -> Dict[str, Any]:
        """Flow 삭제"""
        flow = self.flow_service.get_flow(flow_id)
        if not flow:
            return {'ok': False, 'error': f'Flow {flow_id} not found'}
        
        if self.flow_service.delete_flow(flow_id):
            self._sync_flows_from_service()
            
            if self.context_manager:
                self.context_manager.add_event('flow_deleted', {
                    'flow_id': flow_id
                })
            
            return {'ok': True, 'data': f'Flow {flow.name} deleted'}
        
        return {'ok': False, 'error': 'Failed to delete flow'}
    
    # === Plan 관리 ===
    
    def create_plan(self, flow_id: str, name: str) -> Dict[str, Any]:
        """Plan 생성"""
        plan = self.plan_service.create_plan(flow_id, name)
        if plan:
            self._sync_flows_from_service()
            return plan.to_dict()
        return None
    
    def update_plan_status(self, plan_id: str, completed: bool = True) -> Dict[str, Any]:
        """Plan 상태 업데이트"""
        current_flow = self.flow_service.get_current_flow()
        if not current_flow:
            return {'ok': False, 'error': 'No current flow'}
        
        if completed:
            if self.plan_service.complete_plan(current_flow.id, plan_id):
                self._sync_flows_from_service()
                return {'ok': True, 'data': 'Plan completed'}
        else:
            if self.plan_service.reopen_plan(current_flow.id, plan_id):
                self._sync_flows_from_service()
                return {'ok': True, 'data': 'Plan reopened'}
        
        return {'ok': False, 'error': 'Failed to update plan status'}
    

    def _check_and_complete_plan(self, flow_id: str, plan_id: str) -> bool:
        """Plan의 모든 Task가 완료되었는지 확인하고 자동 완료 처리

        Args:
            flow_id: Flow ID
            plan_id: Plan ID

        Returns:
            bool: Plan이 자동 완료되었는지 여부
        """
        try:
            # Flow와 Plan 가져오기
            flow = self.flows.get(flow_id)
            if not flow:
                return False

            plan = flow.get('plans', {}).get(plan_id)
            if not plan:
                return False

            # 이미 완료된 Plan은 스킵
            if plan.get('completed', False):
                return False

            # Task 목록 가져오기
            tasks = self.task_service.list_tasks(plan_id)
            if not tasks:
                return False

            # 모든 Task가 completed 상태인지 확인 (reviewing은 미완료로 처리)
            all_completed = all(
                task.status == TaskStatus.COMPLETED 
                for task in tasks
            )

            if all_completed:
                # Plan 완료 처리
                self.update_plan_status(plan_id, completed=True)

                # Context에 이벤트 기록
                if hasattr(self, 'context_manager'):
                    self.context_manager.add_event(
                        "plan_auto_completed",
                        {
                            "flow_id": flow_id,
                            "plan_id": plan_id,
                            "plan_name": plan.get('name', 'Unknown'),
                            "task_count": len(tasks),
                            "timestamp": datetime.now().isoformat()
                        }
                    )

                print(f"Plan '{plan.get('name', plan_id)}' 자동 완료! 모든 Task가 완료되었습니다.")
                return True

            return False

        except Exception as e:
            print(f"Plan 자동 완료 체크 중 오류: {e}")
            return False

    def delete_plan(self, flow_id: str, plan_id: str) -> bool:
        """Plan 삭제"""
        result = self.plan_service.delete_plan(flow_id, plan_id)
        if result:
            self._sync_flows_from_service()
        return result
    
    # === Task 관리 ===
    
    def create_task(self, flow_id: str, plan_id: str, name: str) -> Dict[str, Any]:
        """Task 생성"""
        task = self.task_service.create_task(flow_id, plan_id, name)
        if task:
            self._sync_flows_from_service()
            return task.to_dict()
        return None
    
    def update_task_status(self, task_id: str, status: str) -> Dict[str, Any]:
        """Task 상태 업데이트 - 개선된 버전"""
        current_flow = self.flow_service.get_current_flow()
        if not current_flow:
            return {'ok': False, 'error': 'No current flow'}

        # 모든 Plan에서 Task 검색
        for plan_id, plan in current_flow.plans.items():
            for tid, task in plan.tasks.items():
                if tid == task_id:
                    # 상태 문자열을 Enum으로 변환
                    try:
                        status_enum = TaskStatus(status)
                    except ValueError:
                        return {'ok': False, 'error': f'Invalid status: {status}'}

                    if self.task_service.update_task_status(
                        current_flow.id, plan_id, task_id, status_enum
                    ):
                        self._sync_flows_from_service()
                        return {'ok': True, 'data': f'Task status updated to {status}'}

        return {'ok': False, 'error': 'Task not found'}
    
    def update_task_context(self, task_id: str, context: Dict) -> Dict[str, Any]:
        """Task 컨텍스트 업데이트"""
        current_flow = self.flow_service.get_current_flow()
        if not current_flow:
            return {'ok': False, 'error': 'No current flow'}
        
        # Task가 속한 Plan 찾기
        for plan in current_flow.plans.values():
            if task_id in plan.tasks:
                if self.task_service.update_task_context(
                    current_flow.id, plan.id, task_id, context
                ):
                    self._sync_flows_from_service()
                    return {'ok': True, 'data': 'Context updated'}
        
        return {'ok': False, 'error': 'Task not found'}
    
    def add_task_action(self, task_id: str, action: str) -> Dict[str, Any]:
        """Task 액션 추가"""
        current_flow = self.flow_service.get_current_flow()
        if not current_flow:
            return {'ok': False, 'error': 'No current flow'}
        
        # Task가 속한 Plan 찾기
        for plan in current_flow.plans.values():
            if task_id in plan.tasks:
                if self.task_service.add_task_action(
                    current_flow.id, plan.id, task_id, action
                ):
                    self._sync_flows_from_service()
                    return {'ok': True, 'data': 'Action added'}
        
        return {'ok': False, 'error': 'Task not found'}
    
    # === 내부 헬퍼 메서드 ===
    
    def _sync_flows_from_service(self):
        """서비스에서 flows 동기화"""
        flows = self.flow_service.list_flows()
        self._flows = {flow.id: flow.to_dict() for flow in flows}
        
        # 현재 flow도 동기화
        current = self.flow_service.get_current_flow()
        if current:
            self._current_flow = current.to_dict()
    
    def _init_command_handlers(self):
        """명령어 핸들러 초기화"""
        self._command_handlers = {
            'flow': self._handle_flow_command,
            'plan': self._handle_plan_command,
            'task': self._handle_task_command,
            'start': self._handle_start_command,
            'complete': self._handle_complete_command,
            'skip': self._handle_skip_command,
            'status': self._handle_status_command,
            'help': self._handle_help_command
        }
    
    def _handle_flow_command(self, args: str) -> Dict[str, Any]:
        """flow 명령어 처리"""
        if not args:
            return self._show_flows()
        
        parts = args.split(maxsplit=1)
        sub_cmd = parts[0]
        
        if sub_cmd == 'create':
            name = parts[1] if len(parts) > 1 else 'New Flow'
            flow = self.create_flow(name)
            return {'ok': True, 'data': f"Created flow: {name}", 'flow': flow}
        
        elif sub_cmd == 'switch':
            if len(parts) < 2:
                return {'ok': False, 'error': 'Flow ID required'}
            return self.switch_flow(parts[1])
        
        elif sub_cmd == 'delete':
            if len(parts) < 2:
                return {'ok': False, 'error': 'Flow ID required'}
            return self.delete_flow(parts[1])
        
        elif sub_cmd == 'list':
            return self._show_flows()
        
        # Flow name으로 switch 시도
        return self._switch_to_flow_by_name(args)
    
    def _handle_plan_command(self, args: str) -> Dict[str, Any]:
        """plan 명령어 처리"""
        if not args:
            return self._show_plans()
        
        parts = args.split(maxsplit=1)
        sub_cmd = parts[0]
        
        if sub_cmd == 'add':
            name = parts[1] if len(parts) > 1 else 'New Plan'
            current_flow = self.flow_service.get_current_flow()
            if not current_flow:
                return {'ok': False, 'error': 'No current flow'}
            
            plan = self.create_plan(current_flow.id, name)
            return {'ok': True, 'data': f"Created plan: {name}", 'plan': plan}
        
        elif sub_cmd == 'complete':
            if len(parts) < 2:
                return {'ok': False, 'error': 'Plan ID required'}
            return self.update_plan_status(parts[1], completed=True)
        
        elif sub_cmd == 'reopen':
            if len(parts) < 2:
                return {'ok': False, 'error': 'Plan ID required'}
            return self.update_plan_status(parts[1], completed=False)
        
        return {'ok': False, 'error': f'Unknown plan subcommand: {sub_cmd}'}
    
    def _handle_task_command(self, args: str) -> Dict[str, Any]:
        """task 명령어 처리"""
        if not args:
            return self._show_tasks()
        
        parts = args.split(maxsplit=2)
        if len(parts) < 2:
            return {'ok': False, 'error': 'Usage: /task add <plan_id> <name>'}
        
        sub_cmd = parts[0]
        
        if sub_cmd == 'add':
            plan_id = parts[1]
            name = parts[2] if len(parts) > 2 else 'New Task'
            
            current_flow = self.flow_service.get_current_flow()
            if not current_flow:
                return {'ok': False, 'error': 'No current flow'}
            
            task = self.create_task(current_flow.id, plan_id, name)
            if task:
                return {'ok': True, 'data': f"Created task: {name}", 'task': task}
            
            return {'ok': False, 'error': 'Failed to create task'}
        
        return {'ok': False, 'error': f'Unknown task subcommand: {sub_cmd}'}
    
    def _handle_start_command(self, args: str) -> Dict[str, Any]:
        """start 명령어 처리"""
        if not args:
            return {'ok': False, 'error': 'Task ID required'}
        
        task_id = args.strip()
        return self.update_task_status(task_id, 'in_progress')
    
    def _handle_complete_command(self, args: str) -> Dict[str, Any]:
        """complete 명령어 처리"""
        if not args:
            return {'ok': False, 'error': 'Task ID required'}
        
        task_id = args.strip()
        return self.update_task_status(task_id, 'completed')
    
    def _handle_skip_command(self, args: str) -> Dict[str, Any]:
        """skip 명령어 처리"""
        if not args:
            return {'ok': False, 'error': 'Task ID required'}
        
        task_id = args.strip()
        return self.update_task_status(task_id, 'skip')
    
    def _handle_status_command(self, args: str) -> Dict[str, Any]:
        """status 명령어 처리"""
        return self._show_status()
    
    def _handle_help_command(self, args: str) -> Dict[str, Any]:
        """help 명령어 처리"""
        help_text = """
Flow Commands:
  /flow                    - Show current flow
  /flow create <name>      - Create new flow
  /flow switch <id>        - Switch to flow
  /flow delete <id>        - Delete flow
  /flow list              - List all flows

Plan Commands:
  /plan                    - Show plans
  /plan add <name>         - Add plan
  /plan complete <id>      - Complete plan
  /plan reopen <id>        - Reopen plan

Task Commands:
  /task                    - Show tasks
  /task add <plan_id> <name> - Add task
  /start <task_id>         - Start task
  /complete <task_id>      - Complete task
  /skip <task_id>          - Skip task

Other Commands:
  /status                  - Show status
  /help                    - Show this help
"""
        return {'ok': True, 'data': help_text}
    
    def _handle_plan_select(self, plan_number: str) -> Dict[str, Any]:
        """Plan 선택 처리"""
        try:
            current_flow = self.flow_service.get_current_flow()
            if not current_flow:
                return {'ok': False, 'error': '현재 활성화된 Flow가 없습니다'}
            
            # Plan 목록 가져오기
            plans_list = list(current_flow.plans.values())
            if not plans_list:
                return {'ok': False, 'error': '현재 Flow에 Plan이 없습니다'}
            
            # Plan 번호로 선택
            plan_idx = int(plan_number) - 1
            if plan_idx < 0 or plan_idx >= len(plans_list):
                return {'ok': False, 'error': f'잘못된 Plan 번호입니다. 1-{len(plans_list)} 범위에서 선택하세요.'}
            
            selected_plan = plans_list[plan_idx]
            
            # Plan 정보 표시
            return self._show_plan_details(selected_plan)
            
        except ValueError:
            return {'ok': False, 'error': '올바른 Plan 번호를 입력하세요'}
        except Exception as e:
            return {'ok': False, 'error': f'Plan 선택 중 오류: {str(e)}'}
    
    def _show_flows(self) -> Dict[str, Any]:
        """Flow 목록 표시"""
        flows = self.flow_service.list_flows()
        current = self.flow_service.get_current_flow()
        
        if not flows:
            return {'ok': True, 'data': 'No flows found'}
        
        result = "📁 Flows:\n"
        for flow in flows:
            is_current = current and flow.id == current.id
            marker = "▶ " if is_current else "  "
            result += f"{marker}{flow.name} (ID: {flow.id})\n"
            result += f"   Plans: {len(flow.plans)}, Created: {flow.created_at.strftime('%Y-%m-%d')}\n"
        
        return {'ok': True, 'data': result}
    
    def _show_plans(self) -> Dict[str, Any]:
        """Plan 목록 표시"""
        current_flow = self.flow_service.get_current_flow()
        if not current_flow:
            return {'ok': False, 'error': 'No current flow'}
        
        if not current_flow.plans:
            return {'ok': True, 'data': 'No plans in current flow'}
        
        result = f"📋 Plans in '{current_flow.name}':\n"
        for i, (plan_id, plan) in enumerate(current_flow.plans.items(), 1):
            status = "✅" if plan.completed else "⏳"
            task_count = len(plan.tasks)
            completed_tasks = sum(1 for t in plan.tasks.values() 
                                if t.status in [TaskStatus.COMPLETED, TaskStatus.REVIEWING])
            
            result += f"{i}. {status} {plan.name}\n"
            result += f"   ID: {plan_id}\n"
            result += f"   Tasks: {completed_tasks}/{task_count}\n"
        
        return {'ok': True, 'data': result}
    
    def _show_tasks(self) -> Dict[str, Any]:
        """Task 목록 표시"""
        current_flow = self.flow_service.get_current_flow()
        if not current_flow:
            return {'ok': False, 'error': 'No current flow'}
        
        result = f"📝 Tasks in '{current_flow.name}':\n\n"
        
        for plan in current_flow.plans.values():
            if not plan.tasks:
                continue
            
            result += f"Plan: {plan.name}\n"
            for task in plan.tasks.values():
                status_icon = {
                    TaskStatus.TODO: "⬜",
                    TaskStatus.PLANNING: "📋",
                    TaskStatus.IN_PROGRESS: "🔄",
                    TaskStatus.REVIEWING: "👀",
                    TaskStatus.COMPLETED: "✅",
                    TaskStatus.SKIP: "⏭️",
                    TaskStatus.ERROR: "❌"
                }.get(task.status, "❓")
                
                result += f"  {status_icon} {task.name} ({task.id})\n"
            result += "\n"
        
        return {'ok': True, 'data': result}
    
    def _show_status(self) -> Dict[str, Any]:
        """전체 상태 표시"""
        current_flow = self.flow_service.get_current_flow()
        if not current_flow:
            return {'ok': True, 'data': 'No current flow'}
        
        total_plans = len(current_flow.plans)
        completed_plans = sum(1 for p in current_flow.plans.values() if p.completed)
        
        total_tasks = sum(len(p.tasks) for p in current_flow.plans.values())
        completed_tasks = sum(
            1 for p in current_flow.plans.values()
            for t in p.tasks.values()
            if t.status in [TaskStatus.COMPLETED, TaskStatus.REVIEWING]
        )
        
        progress = completed_tasks/total_tasks*100 if total_tasks > 0 else 0
        
        result = f"""📊 Status Report
        
Flow: {current_flow.name}
Plans: {completed_plans}/{total_plans} completed
Tasks: {completed_tasks}/{total_tasks} completed
Progress: {progress:.1f}%"""
        
        return {'ok': True, 'data': result}
    
    def _show_plan_details(self, plan: Plan) -> Dict[str, Any]:
        """Plan 상세 정보 표시"""
        completed_tasks = [t for t in plan.tasks.values() 
                          if t.status in [TaskStatus.COMPLETED, TaskStatus.REVIEWING]]
        
        result = f"""📊 Plan '{plan.name}' 분석 결과

## ✅ 완료된 작업 요약
"""
        
        if completed_tasks:
            for task in completed_tasks:
                result += f"- {task.name}: 완료\n"
        else:
            result += "아직 완료된 작업이 없습니다.\n"
        
        result += f"""
## 🔍 현재 상태 분석
- Plan 진행률: {len(completed_tasks)}/{len(plan.tasks)} Tasks 완료
- Plan 상태: {"✅ 완료" if plan.completed else "⏳ 진행중"}

## 🚀 시작하려면
- 특정 Task 시작: `/start task_xxx`
- 새 Task 추가: `/task add {plan.id} 작업명`
"""
        
        return {'ok': True, 'data': result}
    
    def _switch_to_flow_by_name(self, name: str) -> Dict[str, Any]:
        """이름으로 Flow 전환"""
        flows = self.flow_service.list_flows()
        
        # 정확한 이름 매치 먼저 시도
        for flow in flows:
            if flow.name.lower() == name.lower():
                return self.switch_flow(flow.id)
        
        # 부분 매치 시도
        matches = [f for f in flows if name.lower() in f.name.lower()]
        if len(matches) == 1:
            return self.switch_flow(matches[0].id)
        elif len(matches) > 1:
            result = f"Multiple flows found matching '{name}':\n"
            for flow in matches:
                result += f"  - {flow.name} (ID: {flow.id})\n"
            return {'ok': False, 'error': result}
        
        return {'ok': False, 'error': f"No flow found matching '{name}'"}
    
    # === 추가 레거시 메서드들 (필요시 구현) ===
    
    def get_current_flow_status(self) -> Dict[str, Any]:
        """현재 Flow 상태 (레거시 호환)"""
        return self._show_status()
    
    def update_task_status_validated(self, task_id: str, new_status: str,
                                    valid_transitions: Dict = None) -> Dict[str, Any]:
        """검증된 Task 상태 업데이트 (레거시 호환)"""
        # 새 서비스는 이미 내부적으로 검증하므로 그대로 전달
        return self.update_task_status(task_id, new_status)
