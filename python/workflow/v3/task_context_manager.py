import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TaskContextManager:
    """워크플로우 사이클에 맞춰 task_context를 관리하는 매니저"""
    
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.context_file = self.memory_dir / "task_context.json"
        self.archive_dir = self.memory_dir / "task_context_archive"
        self.realtime_file = self.memory_dir / "task_context_realtime.json"
        
        # 디렉토리 생성
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # 초기 컨텍스트 로드
        self.context = self._load_context()
        
    def _load_context(self) -> Dict[str, Any]:
        """컨텍스트 파일 로드"""
        if self.context_file.exists():
            try:
                with open(self.context_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load task context: {e}")
                return self._get_default_context()
        else:
            return self._get_default_context()
    
    def _get_default_context(self) -> Dict[str, Any]:
        """기본 컨텍스트 구조"""
        return {
            "current_plan": None,
            "current_task": None,
            "plans": {},
            "tasks": {},
            "events": [],
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_context(self) -> bool:
        """컨텍스트 저장"""
        try:
            self.context["last_updated"] = datetime.now().isoformat()
            with open(self.context_file, 'w', encoding='utf-8') as f:
                json.dump(self.context, f, indent=2, ensure_ascii=False)
            
            # realtime 파일도 업데이트
            self._update_realtime()
            return True
        except Exception as e:
            logger.error(f"Failed to save task context: {e}")
            return False
    
    def _update_realtime(self):
        """실시간 파일 업데이트 (현재 상태만)"""
        try:
            realtime_data = {
                "current_plan": self.context.get("current_plan"),
                "current_task": self.context.get("current_task"),
                "last_event": self.context["events"][-1] if self.context["events"] else None,
                "updated_at": datetime.now().isoformat()
            }
            with open(self.realtime_file, 'w', encoding='utf-8') as f:
                json.dump(realtime_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to update realtime file: {e}")
    
    def _add_event(self, event_type: str, data: Dict[str, Any]):
        """이벤트 기록"""
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.context["events"].append(event)
        
        # 이벤트가 너무 많으면 오래된 것 제거 (최대 1000개)
        if len(self.context["events"]) > 1000:
            self.context["events"] = self.context["events"][-1000:]
    
    # === 플랜 관련 메서드 ===
    
    def on_plan_created(self, plan_id: str, plan_name: str, description: str = ""):
        """플랜 생성 시"""
        plan_data = {
            "id": plan_id,
            "name": plan_name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "status": "created",
            "tasks": []
        }
        
        self.context["plans"][plan_id] = plan_data
        self._add_event("plan_created", {
            "plan_id": plan_id,
            "plan_name": plan_name
        })
        self._save_context()
        logger.info(f"Plan created: {plan_name} ({plan_id})")
    
    def on_plan_started(self, plan_id: str):
        """플랜 시작 시"""
        if plan_id in self.context["plans"]:
            self.context["plans"][plan_id]["status"] = "active"
            self.context["plans"][plan_id]["started_at"] = datetime.now().isoformat()
            self.context["current_plan"] = plan_id
            
            self._add_event("plan_started", {"plan_id": plan_id})
            self._save_context()
            logger.info(f"Plan started: {plan_id}")
    
    def on_plan_completed(self, plan_id: str):
        """플랜 완료 시"""
        if plan_id in self.context["plans"]:
            self.context["plans"][plan_id]["status"] = "completed"
            self.context["plans"][plan_id]["completed_at"] = datetime.now().isoformat()
            
            # 완료된 플랜 아카이브
            self._archive_plan(plan_id)
            
            # 현재 플랜 초기화
            if self.context["current_plan"] == plan_id:
                self.context["current_plan"] = None
                self.context["current_task"] = None
            
            self._add_event("plan_completed", {"plan_id": plan_id})
            self._save_context()
            logger.info(f"Plan completed: {plan_id}")
    
    def _archive_plan(self, plan_id: str):
        """플랜 아카이브"""
        try:
            if plan_id not in self.context["plans"]:
                return
                
            plan_data = self.context["plans"][plan_id]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_file = self.archive_dir / f"plan_{timestamp}_{plan_id[:8]}.json"
            
            # 관련 태스크 수집
            plan_tasks = []
            for task_id in plan_data.get("tasks", []):
                if task_id in self.context["tasks"]:
                    plan_tasks.append(self.context["tasks"][task_id])
            
            # 아카이브 데이터
            archive_data = {
                "plan": plan_data,
                "tasks": plan_tasks,
                "archived_at": datetime.now().isoformat()
            }
            
            with open(archive_file, 'w', encoding='utf-8') as f:
                json.dump(archive_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Plan archived: {archive_file}")
            
        except Exception as e:
            logger.error(f"Failed to archive plan: {e}")
    
    # === 태스크 관련 메서드 ===
    
    def on_task_added(self, plan_id: str, task_id: str, task_title: str, description: str = ""):
        """태스크 추가 시"""
        task_data = {
            "id": task_id,
            "title": task_title,
            "description": description,
            "plan_id": plan_id,
            "created_at": datetime.now().isoformat(),
            "status": "todo",
            "notes": [],
            "outputs": []
        }
        
        self.context["tasks"][task_id] = task_data
        
        # 플랜에 태스크 ID 추가
        if plan_id in self.context["plans"]:
            self.context["plans"][plan_id]["tasks"].append(task_id)
        
        self._add_event("task_added", {
            "plan_id": plan_id,
            "task_id": task_id,
            "task_title": task_title
        })
        self._save_context()
        logger.info(f"Task added: {task_title} ({task_id})")
    
    def on_task_started(self, task_id: str):
        """태스크 시작 시"""
        if task_id in self.context["tasks"]:
            self.context["tasks"][task_id]["status"] = "in_progress"
            self.context["tasks"][task_id]["started_at"] = datetime.now().isoformat()
            self.context["current_task"] = task_id
            
            # 태스크 작업 컨텍스트 초기화
            self.context["tasks"][task_id]["work_context"] = {
                "files_created": [],
                "files_modified": [],
                "commands_executed": [],
                "errors": [],
                "metrics": {}
            }
            
            self._add_event("task_started", {"task_id": task_id})
            self._save_context()
            logger.info(f"Task started: {task_id}")
    
    def on_task_completed(self, task_id: str, note: str = ""):
        """태스크 완료 시"""
        if task_id in self.context["tasks"]:
            task = self.context["tasks"][task_id]
            task["status"] = "completed"
            task["completed_at"] = datetime.now().isoformat()
            
            # 소요 시간 계산
            if "started_at" in task:
                start_time = datetime.fromisoformat(task["started_at"])
                end_time = datetime.now()
                duration = end_time - start_time
                task["duration"] = str(duration)
            
            # 완료 노트 추가
            if note:
                task["notes"].append({
                    "type": "completion",
                    "content": note,
                    "timestamp": datetime.now().isoformat()
                })
            
            # 현재 태스크 초기화
            if self.context["current_task"] == task_id:
                self.context["current_task"] = None
            
            self._add_event("task_completed", {
                "task_id": task_id,
                "note": note
            })
            self._save_context()
            logger.info(f"Task completed: {task_id}")
    
    def on_task_updated(self, task_id: str, updates: Dict[str, Any]):
        """태스크 업데이트 시"""
        if task_id in self.context["tasks"]:
            task = self.context["tasks"][task_id]
            
            # 업데이트 적용
            for key, value in updates.items():
                if key == "note":
                    # 노트는 추가
                    task["notes"].append({
                        "type": "update",
                        "content": value,
                        "timestamp": datetime.now().isoformat()
                    })
                elif key == "output":
                    # 출력물 추가
                    task["outputs"].append({
                        "content": value,
                        "timestamp": datetime.now().isoformat()
                    })
                elif key in ["files_created", "files_modified", "commands_executed"]:
                    # 작업 컨텍스트 업데이트
                    if "work_context" not in task:
                        task["work_context"] = {
                            "files_created": [],
                            "files_modified": [],
                            "commands_executed": [],
                            "errors": [],
                            "metrics": {}
                        }
                    if isinstance(value, list):
                        task["work_context"][key].extend(value)
                    else:
                        task["work_context"][key].append(value)
                else:
                    task[key] = value
            
            task["updated_at"] = datetime.now().isoformat()
            
            self._add_event("task_updated", {
                "task_id": task_id,
                "updates": list(updates.keys())
            })
            self._save_context()
    
    # === 조회 메서드 ===
    
    def get_current_context(self) -> Dict[str, Any]:
        """현재 컨텍스트 반환"""
        return {
            "current_plan": self.context.get("current_plan"),
            "current_task": self.context.get("current_task"),
            "plan_data": self.context["plans"].get(self.context["current_plan"]) if self.context["current_plan"] else None,
            "task_data": self.context["tasks"].get(self.context["current_task"]) if self.context["current_task"] else None
        }
    
    def get_plan_context(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """특정 플랜의 컨텍스트"""
        if plan_id not in self.context["plans"]:
            return None
            
        plan = self.context["plans"][plan_id]
        tasks = []
        for task_id in plan.get("tasks", []):
            if task_id in self.context["tasks"]:
                tasks.append(self.context["tasks"][task_id])
                
        return {
            "plan": plan,
            "tasks": tasks
        }
    
    def get_task_context(self, task_id: str) -> Optional[Dict[str, Any]]:
        """특정 태스크의 컨텍스트"""
        return self.context["tasks"].get(task_id)
    
    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 이벤트 반환"""
        return self.context["events"][-limit:]
    
    def clear_old_events(self, keep_days: int = 30):
        """오래된 이벤트 정리"""
        cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        
        new_events = []
        for event in self.context["events"]:
            try:
                event_time = datetime.fromisoformat(event["timestamp"]).timestamp()
                if event_time > cutoff_date:
                    new_events.append(event)
            except:
                # 파싱 실패한 이벤트는 유지
                new_events.append(event)
        
        self.context["events"] = new_events
        self._save_context()
        logger.info(f"Cleared old events, kept {len(new_events)} events")
    
    def export_current_state(self) -> Dict[str, Any]:
        """현재 상태 내보내기"""
        return {
            "context": self.get_current_context(),
            "recent_events": self.get_recent_events(20),
            "timestamp": datetime.now().isoformat()
        }
