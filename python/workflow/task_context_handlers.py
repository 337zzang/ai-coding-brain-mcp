from .task_context_manager import TaskContextManager
from .event_types import EventType

class TaskContextEventHandlers:
    """이벤트를 받아 TaskContextManager를 통해 처리하는 핸들러"""
    
    def __init__(self, task_context_manager: TaskContextManager):
        self.tcm = task_context_manager
    
    def register_all(self, event_bus):
        """모든 핸들러 등록"""
        event_bus.subscribe(EventType.PLAN_CREATED, self.on_plan_created)
        event_bus.subscribe(EventType.PLAN_STARTED, self.on_plan_started)
        event_bus.subscribe(EventType.TASK_ADDED, self.on_task_added)
        event_bus.subscribe(EventType.TASK_STARTED, self.on_task_started)
        event_bus.subscribe(EventType.TASK_COMPLETED, self.on_task_completed)
        event_bus.subscribe(EventType.TASK_UPDATED, self.on_task_updated)
        event_bus.subscribe(EventType.PLAN_COMPLETED, self.on_plan_completed)
    
    def on_plan_created(self, event):
        """플랜 생성 시"""
        plan_id = event.data.get("plan_id")
        plan_name = event.data.get("plan_name", event.data.get("plan_title", "Unknown"))
        description = event.data.get("description", "")
        
        if plan_id and plan_name:
            self.tcm.on_plan_created(plan_id, plan_name, description)
    
    def on_plan_started(self, event):
        """플랜 시작 시"""
        plan_id = event.data.get("plan_id")
        if plan_id:
            self.tcm.on_plan_started(plan_id)
    
    def on_task_added(self, event):
        """태스크 추가 시"""
        plan_id = event.data.get("plan_id")
        task_id = event.data.get("task_id")
        task_title = event.data.get("task_title", event.data.get("title", "Unknown"))
        description = event.data.get("description", "")
        
        if plan_id and task_id and task_title:
            self.tcm.on_task_added(plan_id, task_id, task_title, description)
    
    def on_task_started(self, event):
        """태스크 시작 시"""
        task_id = event.data.get("task_id")
        if task_id:
            self.tcm.on_task_started(task_id)
    
    def on_task_completed(self, event):
        """태스크 완료 시"""
        task_id = event.data.get("task_id")
        notes = event.data.get("notes", "")
        
        # 추가 데이터가 있으면 처리
        if "additional_data" in event.data:
            additional = event.data["additional_data"]
            if "notes" in additional:
                notes = additional["notes"]
            
            # 작업 결과가 있으면 업데이트
            if "work_results" in additional:
                work_results = additional["work_results"]
                # 작업 결과를 task_context에 반영
                self.tcm.on_task_updated(task_id, {
                    "files_created": work_results.get("files_created", []),
                    "files_modified": work_results.get("files_modified", []),
                    "git_commits": work_results.get("git_commits", [])
                })
        
        if task_id:
            self.tcm.on_task_completed(task_id, notes)
    
    def on_task_updated(self, event):
        """태스크 업데이트 시"""
        task_id = event.data.get("task_id")
        
        # update_data 찾기
        update_data = {}
        if "update_data" in event.data:
            update_data = event.data["update_data"]
        elif "additional_data" in event.data and "update_data" in event.data["additional_data"]:
            update_data = event.data["additional_data"]["update_data"]
        
        if task_id and update_data:
            self.tcm.on_task_updated(task_id, update_data)
    
    def on_plan_completed(self, event):
        """플랜 완료 시"""
        plan_id = event.data.get("plan_id")
        if plan_id:
            self.tcm.on_plan_completed(plan_id)
