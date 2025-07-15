"""
Improved Workflow Manager
========================
단일 workflow.json 파일을 사용하는 개선된 워크플로우 매니저
"""

import json
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from .models import WorkflowPlan, Task, TaskStatus, PlanStatus, WorkflowEvent, EventType
from .messaging.message_controller import MessageController


class ImprovedWorkflowManager:
    """개선된 워크플로우 매니저 - 단일 파일 저장 방식"""
    
    def __init__(self, project_name: str):
        self.project_name = project_name
        
        # 현재 프로젝트의 memory 폴더 사용
        self.memory_dir = os.path.join(os.getcwd(), "memory")
        os.makedirs(self.memory_dir, exist_ok=True)
        
        # 프로젝트별 파일 경로
        self.workflow_file = os.path.join(self.memory_dir, "workflow.json")
        self.events_file = os.path.join(self.memory_dir, "workflow_events.json")
        
        self.data = self._load_workflow_file()
        self._ensure_structure()
        
        # MessageController 초기화 (AI 메시지 발행용)
        self.msg_controller = MessageController()
        
    def _ensure_structure(self):
        """데이터 구조 확인 및 초기화"""
        if "plans" not in self.data:
            self.data["plans"] = []
        if "active_plan_id" not in self.data:
            self.data["active_plan_id"] = None
        # events는 별도 파일로 관리
        if "events_file" not in self.data:
            self.data["events_file"] = "workflow_events.json"
        if "version" not in self.data:
            self.data["version"] = "3.0.0"
        if "project_name" not in self.data:
            self.data["project_name"] = self.project_name
        
    def _load_workflow_file(self) -> Dict[str, Any]:
        """workflow.json 로드"""
        if os.path.exists(self.workflow_file):
            try:
                with open(self.workflow_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"워크플로우 파일 로드 오류: {e}")
                return {}
        return {}
    
    def _save_workflow_file(self):
        """workflow.json 저장"""
        self.data["last_saved"] = datetime.now().isoformat()
        
        # 디렉토리 확인
        os.makedirs(os.path.dirname(self.workflow_file), exist_ok=True)
        
        # 파일 저장
        with open(self.workflow_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def create_plan(self, name: str, description: str = "") -> str:
        """새 플랜 생성"""
        plan = WorkflowPlan(name=name, description=description)
        plan_dict = plan.to_dict()
        
        # plans 리스트에 추가
        self.data["plans"].append(plan_dict)
        self.data["active_plan_id"] = plan.id
        
        # 이벤트 기록 - 생성
        self._add_event("workflow_created", plan.id, {
            "name": name,
            "description": description
        })
        
        # 이벤트 기록 - 상태 변경 (draft → active)
        self._add_event("state_changed", plan.id, {
            "from": "draft",
            "to": "active",
            "workflow_id": plan.id
        })
        
        self._save_workflow_file()
        return plan.id
    
    def add_task(self, title: str, description: str = "") -> str:
        """현재 플랜에 태스크 추가"""
        if not self.data["active_plan_id"]:
            raise ValueError("활성 플랜이 없습니다")
        
        # 현재 플랜 찾기
        current_plan = self._get_plan(self.data["active_plan_id"])
        if not current_plan:
            raise ValueError("활성 플랜을 찾을 수 없습니다")
        
        # 태스크 생성
        task = Task(title=title, description=description)
        task_dict = task.to_dict()
        
        # 플랜에 태스크 추가
        if "tasks" not in current_plan:
            current_plan["tasks"] = []
        current_plan["tasks"].append(task_dict)
        
        # 이벤트 기록
        self._add_event("task_added", task.id, {
            "title": title,
            "workflow_id": current_plan["id"]
        })
        
        self._save_workflow_file()
        return task.id
    
    def start_task(self, task_id: str) -> bool:
        """태스크 시작"""
        task = self._find_task(task_id)
        if not task:
            return False
        
        # 이전 상태 저장
        old_status = task.get("status", TaskStatus.TODO.value)
        
        task["status"] = TaskStatus.IN_PROGRESS.value
        task["started_at"] = datetime.now().isoformat()
        task["updated_at"] = datetime.now().isoformat()
        
        # state_changed 이벤트 발행 (AI가 설계서를 작성하도록)
        self._add_event("state_changed", task_id, {
            "from": old_status,
            "to": TaskStatus.IN_PROGRESS.value,
            "task_name": task["title"],
            "task_description": task.get("description", "")
        })
        
        # task_started 이벤트도 발행 (호환성 유지)
        self._add_event("task_started", task_id, {"title": task["title"]})
        self._save_workflow_file()
        return True
    
    def complete_task(self, task_id: str, note: str = "") -> bool:
        """태스크 완료"""
        task = self._find_task(task_id)
        if not task:
            return False
        
        # 이전 상태 저장
        old_status = task.get("status", TaskStatus.IN_PROGRESS.value)
        
        task["status"] = TaskStatus.COMPLETED.value
        task["completed_at"] = datetime.now().isoformat()
        task["updated_at"] = datetime.now().isoformat()
        
        if note:
            if "notes" not in task:
                task["notes"] = []
            task["notes"].append(f"[완료] {note}")
        
        # state_changed 이벤트 발행 (AI가 완료 보고서를 작성하도록)
        self._add_event("state_changed", task_id, {
            "from": old_status,
            "to": TaskStatus.COMPLETED.value,
            "task_name": task["title"],
            "note": note,
            "duration": self._calculate_duration(task)
        })
        
        # task_completed 이벤트도 발행 (호환성 유지)
        self._add_event("task_completed", task_id, {
            "title": task["title"],
            "note": note
        })
        
        # 모든 태스크가 완료되었는지 확인
        self._check_plan_completion()
        
        self._save_workflow_file()
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """현재 상태 조회"""
        active_plan = None
        if self.data["active_plan_id"]:
            active_plan = self._get_plan(self.data["active_plan_id"])
        
        completed_tasks = 0
        if active_plan and "tasks" in active_plan:
            completed_tasks = len([t for t in active_plan["tasks"] if t.get("status") == TaskStatus.COMPLETED.value])
        
        return {
            "status": "active" if active_plan else "idle",
            "plan_id": self.data["active_plan_id"],
            "plan_name": active_plan["name"] if active_plan else None,
            "total_tasks": len(active_plan.get("tasks", [])) if active_plan else 0,
            "completed_tasks": completed_tasks,
            "current_task": self._get_current_task(active_plan) if active_plan else None,
            "progress": self._calculate_progress(active_plan) if active_plan else 0
        }
    
    def process_command(self, command: str) -> Dict[str, Any]:
        """워크플로우 명령 처리"""
        parts = command.strip().split(None, 1)
        if not parts:
            return {"success": False, "message": "빈 명령"}
        
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ''
        
        try:
            if cmd in ['/start', '/s']:
                plan_id = self.create_plan(args)
                return {"success": True, "plan_id": plan_id, "message": f"플랜 생성됨: {args}"}
            
            elif cmd in ['/task', '/t']:
                task_id = self.add_task(args)
                return {"success": True, "task_id": task_id, "message": f"태스크 추가됨: {args}"}
            
            elif cmd == '/list':
                tasks = self._list_current_tasks()
                output = "\n=== 📋 태스크 목록 ===\n"
                if tasks:
                    for i, task in enumerate(tasks, 1):
                        status_icon = "✅" if task['status'] == 'completed' else "⏳" if task['status'] == 'in_progress' else "📋"
                        output += f"{i}. {status_icon} {task['title']}\n"
                else:
                    output += "태스크가 없습니다"
                return {"success": True, "tasks": tasks, "message": output}
            
            elif cmd == '/status':
                status = self.get_status()
                # 상태를 읽기 쉬운 형태로 포맷팅
                output = f"\n=== 📊 워크플로우 상태 ===\n"
                output += f"상태: {status['status']}\n"
                if status['plan_name']:
                    output += f"플랜: {status['plan_name']}\n"
                    output += f"진행률: {status['progress']:.1f}% ({status.get('completed_tasks', 0)}/{status['total_tasks']})\n"
                    if status['current_task']:
                        output += f"현재 태스크: {status['current_task']['title']}\n"
                        output += f"태스크 상태: {status['current_task']['status']}"
                else:
                    output += "활성 플랜 없음"
                return {"success": True, "status": status, "message": output}
            
            elif cmd in ['/complete', '/c']:
                current_task = self._get_current_task_object()
                if current_task:
                    self.complete_task(current_task["id"], args)
                    return {"success": True, "message": f"태스크 완료: {current_task['title']}"}
                return {"success": False, "message": "진행 중인 태스크가 없습니다"}
            
            elif cmd == '/focus':
                task_num = int(args) if args.isdigit() else 1
                task = self._get_task_by_number(task_num)
                if task:
                    self.start_task(task["id"])
                    return {"success": True, "message": f"태스크 시작: {task['title']}"}
                return {"success": False, "message": "태스크를 찾을 수 없습니다"}
            
            elif cmd == '/next':
                # 현재 태스크가 있는지 확인
                current_task = self._get_current_task_object()
                if current_task:
                    # 태스크가 아직 시작되지 않았으면 시작만 하고 설계서 작성 대기
                    if current_task["status"] == TaskStatus.TODO.value:
                        self.start_task(current_task["id"])
                        return {"success": True, "message": f"태스크 시작됨: {current_task['title']}. 설계서 작성 후 계속 진행하세요."}
                    # 이미 진행 중이면 완료하고 다음으로
                    elif current_task["status"] == TaskStatus.IN_PROGRESS.value:
                        self.complete_task(current_task["id"], "완료")
                
                # 다음 태스크 찾기
                plan = self._get_plan(self.data["active_plan_id"])
                if plan:
                    next_task = self._get_current_task(plan)
                    if next_task:
                        self.start_task(next_task["id"])
                        return {"success": True, "message": f"다음 태스크 시작: {next_task['title']}. 설계서 작성이 필요합니다."}
                    else:
                        return {"success": True, "message": "모든 태스크가 완료되었습니다"}
                return {"success": False, "message": "활성 플랜이 없습니다"}
            
            elif cmd == '/skip':
                # 현재 태스크를 건너뛰기
                current_task = self._get_current_task_object()
                if current_task:
                    current_task["status"] = TaskStatus.SKIPPED.value
                    current_task["skipped_at"] = datetime.now().isoformat()
                    current_task["skip_reason"] = args or "사용자가 건너뜀"
                    self._add_event("task_skipped", current_task["id"], {
                        "title": current_task["title"],
                        "reason": args or "사용자가 건너뜀"
                    })
                    self._save_workflow_file()
                    return {"success": True, "message": f"태스크 건너뜀: {current_task['title']}"}
                return {"success": False, "message": "진행 중인 태스크가 없습니다"}
            
            elif cmd == '/reset':
                # 워크플로우 초기화
                if self.data["active_plan_id"]:
                    plan = self._get_plan(self.data["active_plan_id"])
                    if plan:
                        plan["status"] = PlanStatus.ARCHIVED.value
                        self._add_event("plan_archived", plan["id"], {"name": plan["name"]})
                
                self.data["active_plan_id"] = None
                self._save_workflow_file()
                return {"success": True, "message": "워크플로우가 초기화되었습니다"}
            
            elif cmd == '/error':
                # 에러 보고
                current_task = self._get_current_task_object()
                if current_task:
                    current_task["status"] = TaskStatus.ERROR.value
                    current_task["error_at"] = datetime.now().isoformat()
                    current_task["error_message"] = args
                    self._add_event("task_error", current_task["id"], {
                        "title": current_task["title"],
                        "error": args
                    })
                    self._save_workflow_file()
                    return {"success": True, "message": f"에러 보고됨: {current_task['title']}"}
                return {"success": False, "message": "진행 중인 태스크가 없습니다"}
            
            elif cmd == '/pause':
                # 현재 태스크 일시 중지
                current_task = self._get_current_task_object()
                if current_task and current_task["status"] == TaskStatus.IN_PROGRESS.value:
                    # 일시 중지 상태로 변경 (메타데이터에 저장)
                    if "metadata" not in current_task:
                        current_task["metadata"] = {}
                    current_task["metadata"]["paused"] = True
                    current_task["metadata"]["paused_at"] = datetime.now().isoformat()
                    current_task["metadata"]["pause_reason"] = args or "사용자가 일시 중지"
                    
                    self._add_event("task_paused", current_task["id"], {
                        "title": current_task["title"],
                        "reason": args or "사용자가 일시 중지"
                    })
                    self._save_workflow_file()
                    return {"success": True, "message": f"태스크 일시 중지됨: {current_task['title']}"}
                return {"success": False, "message": "진행 중인 태스크가 없습니다"}
            
            elif cmd == '/continue':
                # 일시 중지된 태스크 재개
                current_task = self._get_current_task_object()
                if current_task and current_task.get("metadata", {}).get("paused"):
                    # 일시 중지 상태 해제
                    current_task["metadata"]["paused"] = False
                    current_task["metadata"]["resumed_at"] = datetime.now().isoformat()
                    
                    self._add_event("task_resumed", current_task["id"], {
                        "title": current_task["title"]
                    })
                    self._save_workflow_file()
                    return {"success": True, "message": f"태스크 재개됨: {current_task['title']}"}
                return {"success": False, "message": "일시 중지된 태스크가 없습니다"}
            
            elif cmd == '/help':
                help_text = """사용 가능한 워크플로우 명령어:
                
/start [플랜명] - 새 워크플로우 시작
/task [태스크명] - 태스크 추가
/list - 현재 태스크 목록
/status - 워크플로우 상태 확인
/focus [번호] - 특정 태스크 시작
/complete [메모] - 현재 태스크 완료
/next - 다음 태스크로 이동
/pause [이유] - 현재 태스크 일시 중지
/continue - 일시 중지된 태스크 재개
/skip [이유] - 현재 태스크 건너뛰기
/error [메시지] - 에러 보고
/reset - 워크플로우 초기화
/help - 이 도움말 표시"""
                return {"success": True, "message": help_text}
            
            else:
                return {"success": False, "message": f"알 수 없는 명령: {cmd}"}
                
        except Exception as e:
            return {"success": False, "message": f"오류: {str(e)}"}
    
    # 헬퍼 메서드들
    def _get_plan(self, plan_id: str) -> Optional[Dict]:
        """플랜 ID로 플랜 찾기"""
        for plan in self.data["plans"]:
            if plan["id"] == plan_id:
                return plan
        return None
    
    def _find_task(self, task_id: str) -> Optional[Dict]:
        """모든 플랜에서 태스크 찾기"""
        for plan in self.data["plans"]:
            for task in plan.get("tasks", []):
                if task["id"] == task_id:
                    return task
        return None
    
    def _get_current_task(self, plan: Dict) -> Optional[Dict]:
        """현재 진행 중인 태스크 찾기"""
        if not plan:
            return None
            
        # 진행 중인 태스크 찾기
        for task in plan.get("tasks", []):
            if task["status"] == TaskStatus.IN_PROGRESS.value:
                return task
        
        # 진행 중인 태스크가 없으면 첫 번째 pending 태스크
        for task in plan.get("tasks", []):
            if task["status"] == TaskStatus.TODO.value:
                return task
        
        return None
    
    def _get_current_task_object(self) -> Optional[Dict]:
        """현재 활성 플랜의 현재 태스크"""
        if not self.data["active_plan_id"]:
            return None
        plan = self._get_plan(self.data["active_plan_id"])
        return self._get_current_task(plan) if plan else None
    
    def _get_task_by_number(self, number: int) -> Optional[Dict]:
        """번호로 태스크 찾기 (1부터 시작)"""
        if not self.data["active_plan_id"]:
            return None
        
        plan = self._get_plan(self.data["active_plan_id"])
        if not plan or "tasks" not in plan:
            return None
        
        if 1 <= number <= len(plan["tasks"]):
            return plan["tasks"][number - 1]
        
        return None
    
    def _list_current_tasks(self) -> List[Dict]:
        """현재 플랜의 태스크 목록"""
        if not self.data["active_plan_id"]:
            return []
        
        plan = self._get_plan(self.data["active_plan_id"])
        if not plan:
            return []
        
        tasks = []
        for i, task in enumerate(plan.get("tasks", []), 1):
            tasks.append({
                "number": i,
                "id": task["id"],
                "title": task["title"],
                "status": task["status"]
            })
        
        return tasks
    
    def _calculate_progress(self, plan: Dict) -> float:
        """플랜 진행률 계산"""
        if not plan or "tasks" not in plan or not plan["tasks"]:
            return 0.0
        
        completed = sum(1 for task in plan["tasks"] 
                       if task["status"] == TaskStatus.COMPLETED.value)
        total = len(plan["tasks"])
        
        return (completed / total) * 100
    
    def _check_plan_completion(self):
        """플랜 완료 여부 확인"""
        if not self.data["active_plan_id"]:
            return
        
        plan = self._get_plan(self.data["active_plan_id"])
        if not plan:
            return
        
        # 모든 태스크가 완료되었는지 확인
        all_completed = all(
            task["status"] == TaskStatus.COMPLETED.value 
            for task in plan.get("tasks", [])
        )
        
        if all_completed and plan["status"] != PlanStatus.COMPLETED.value:
            old_status = plan["status"]
            plan["status"] = PlanStatus.COMPLETED.value
            plan["completed_at"] = datetime.now().isoformat()
            
            # state_changed 이벤트 발행 (AI가 페이즈 완료 보고서를 작성하도록)
            self._add_event("state_changed", plan["id"], {
                "from": old_status,
                "to": PlanStatus.COMPLETED.value,
                "phase_name": plan["name"],
                "total_tasks": len(plan.get("tasks", [])),
                "completed_tasks": len([t for t in plan.get("tasks", []) if t["status"] == TaskStatus.COMPLETED.value])
            })
            
            # plan_completed 이벤트도 발행 (호환성 유지)
            self._add_event("plan_completed", plan["id"], {
                "name": plan["name"],
                "task_count": len(plan.get("tasks", []))
            })
    
    def _calculate_duration(self, task: Dict) -> str:
        """태스크 소요 시간 계산"""
        if not task.get("started_at"):
            return "알 수 없음"
            
        start = datetime.fromisoformat(task["started_at"].replace("Z", "+00:00"))
        
        # 완료 시간이 있으면 사용, 없으면 현재 시간
        if task.get("completed_at"):
            end = datetime.fromisoformat(task["completed_at"].replace("Z", "+00:00"))
        else:
            end = datetime.now()
            
        duration = end - start
        hours = int(duration.total_seconds() // 3600)
        minutes = int((duration.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours}시간 {minutes}분"
        else:
            return f"{minutes}분"
    
    def _add_event(self, event_type: str, entity_id: str, data: Dict):
        """이벤트 추가 및 메시지 발행"""
        event = {
            "type": event_type,
            "entity_id": entity_id,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        # 이벤트를 별도 파일에 저장
        try:
            # 기존 이벤트 로드
            events_data = {}
            if os.path.exists(self.events_file):
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    events_data = json.load(f)
            
            if "events" not in events_data:
                events_data["events"] = []
            
            events_data["events"].append(event)
            
            # 이벤트가 너무 많으면 오래된 것 제거 (최대 1000개)
            if len(events_data["events"]) > 1000:
                events_data["events"] = events_data["events"][-1000:]
            
            # 파일에 저장
            with open(self.events_file, 'w', encoding='utf-8') as f:
                json.dump(events_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"이벤트 저장 오류: {e}")
        
        # MessageController를 통해 AI용 메시지 발행
        self.msg_controller.emit(event_type, entity_id, data)