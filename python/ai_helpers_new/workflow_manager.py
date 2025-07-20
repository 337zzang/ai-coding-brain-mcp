"""
WorkflowManager V3 - 프로젝트별 독립 워크플로우 관리

각 프로젝트의 .ai-brain 폴더에 워크플로우 데이터를 저장하고 관리합니다.
"""
import os
import json
import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from .util import ok, err


# 전역 워크플로우 매니저 저장소
_workflow_managers = {}  # project_path를 키로 하는 딕셔너리

class WorkflowManager:
    """프로젝트별 워크플로우 관리자"""

    def __init__(self, project_path: str = "."):
        """
        Args:
            project_path: 프로젝트 루트 경로 (기본값: 현재 디렉토리)
        """
        self.project_path = Path(project_path).resolve()
        self.ai_brain_path = self.project_path / ".ai-brain"
        self.workflow_file = self.ai_brain_path / "workflow.json"
        self.history_file = self.ai_brain_path / "workflow_history.json"
        self.cache_path = self.ai_brain_path / "cache"

        # .ai-brain 폴더 생성
        self._ensure_directories()

        # 워크플로우 데이터 로드
        self.workflow = self._load_workflow()

    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        self.ai_brain_path.mkdir(exist_ok=True)
        self.cache_path.mkdir(exist_ok=True)
        (self.cache_path / "llm_responses").mkdir(exist_ok=True)

    def _load_workflow(self) -> Dict[str, Any]:
        """워크플로우 파일 로드 또는 초기화"""
        if self.workflow_file.exists():
            try:
                with open(self.workflow_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 워크플로우 로드 오류: {e}")

        # 기본 워크플로우 생성
        return self._create_default_workflow()

    def _create_default_workflow(self) -> Dict[str, Any]:
        """기본 워크플로우 구조 생성"""
        return {
            "version": "3.0",
            "project_name": self.project_path.name,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "tasks": [],
            "current_task": None,
            "context": {
                "last_files": [],
                "last_command": ""
            }
        }

    def save_workflow(self) -> Dict[str, Any]:
        """워크플로우 저장"""
        try:
            self.workflow["updated_at"] = datetime.datetime.now().isoformat()
            with open(self.workflow_file, 'w', encoding='utf-8') as f:
                json.dump(self.workflow, f, indent=2, ensure_ascii=False)
            return ok(True)
        except Exception as e:
            return err(f"워크플로우 저장 실패: {e}")

    def add_task(self, name: str, description: str = "") -> Dict[str, Any]:
        """새 태스크 추가"""
        task_id = f"task_{len(self.workflow['tasks']) + 1:03d}"
        task = {
            "id": task_id,
            "name": name,
            "description": description,
            "status": "todo",
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat()
        }

        self.workflow["tasks"].append(task)

        # 첫 태스크면 current로 설정
        if len(self.workflow["tasks"]) == 1:
            self.workflow["current_task"] = task_id

        self.save_workflow()
        self._add_history("task_added", {"task": task})

        return ok(task)

    def update_task(self, task_id: str, **updates) -> Dict[str, Any]:
        """태스크 업데이트"""
        for task in self.workflow["tasks"]:
            if task["id"] == task_id:
                old_status = task.get("status")
                task.update(updates)
                task["updated_at"] = datetime.datetime.now().isoformat()

                self.save_workflow()
                self._add_history("task_updated", {
                    "task_id": task_id,
                    "updates": updates,
                    "old_status": old_status
                })

                return ok(task)

        return err(f"태스크를 찾을 수 없습니다: {task_id}")

    def get_current_task(self) -> Optional[Dict[str, Any]]:
        """현재 태스크 반환"""
        if not self.workflow["current_task"]:
            return None

        for task in self.workflow["tasks"]:
            if task["id"] == self.workflow["current_task"]:
                return task
        return None

    def list_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """태스크 목록 반환"""
        tasks = self.workflow["tasks"]
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        return tasks

    def _add_history(self, action: str, data: Dict[str, Any]):
        """히스토리 항목 추가"""
        history_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action,
            "data": data
        }

        # 히스토리 파일 로드
        history = []
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                history = []

        # 새 항목 추가
        history.append(history_entry)

        # 저장
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 히스토리 저장 오류: {e}")


    def _handle_task_command(self, args: list) -> Dict[str, Any]:
        """task 하위 명령어 처리"""
        if not args:
            return err("사용법: /task [add|list|start|complete] [옵션]")

        subcmd = args[0].lower()
        subargs = args[1:]

        if subcmd == "add":
            if not subargs:
                return err("사용법: /task add [태스크 이름]")
            task_name = " ".join(subargs)
            return self.add_task(task_name)

        elif subcmd == "list":
            return self.list_tasks()

        elif subcmd == "start":
            if not subargs:
                return err("사용법: /task start [태스크 ID 또는 번호]")

            # ID 처리: 숫자만 입력하면 task_XXX 형식으로 변환
            task_id = subargs[0]
            if task_id.isdigit():
                task_id = f"task_{int(task_id):03d}"

            return self.update_task(task_id, status="in_progress")

        elif subcmd == "complete":
            if not subargs:
                return err("사용법: /task complete [태스크 ID 또는 번호] [요약(선택)]")

            # ID 처리: 숫자만 입력하면 task_XXX 형식으로 변환
            task_id = subargs[0]
            if task_id.isdigit():
                task_id = f"task_{int(task_id):03d}"

            summary = " ".join(subargs[1:]) if len(subargs) > 1 else None
            return self.update_task(task_id, status="completed", summary=summary)

        else:
            return err(f"알 수 없는 task 명령어: {subcmd}")

    def wf_command(self, command: str) -> Dict[str, Any]:
        """wf 명령어 처리"""
        parts = command.strip().split()
        if not parts:
            return self._show_help()

        cmd = parts[0].lower().lstrip('/')
        args = parts[1:]

        # 명령어 매핑
        commands = {
            "help": self._show_help,
            "status": self._show_status,
            "task": lambda: self._handle_task_command(args),
            "list": self.list_tasks,
            
            
            
            
        }

        handler = commands.get(cmd)
        if handler:
            return handler()
        else:
            return err(f"❌ 알 수 없는 명령어: {cmd}\n사용 가능한 명령어: {', '.join(commands.keys())}")

    def _show_help(self) -> str:
        """도움말 표시"""
        return """📋 워크플로우 명령어:
  /help - 이 도움말 표시
  /status - 현재 상태 표시
  /task add [이름] - 새 태스크 추가
  /task list - 태스크 목록
  /start [id] - 태스크 시작
  /done [id] - 태스크 완료
  /skip [id] - 태스크 건너뛰기
  /report - 전체 리포트"""

    def _show_status(self) -> str:
        """워크플로우 상태 표시"""
        # self._ensure_workflow_exists()  # 제거: __init__에서 이미 워크플로우 로드됨

        done = len(self.workflow.get("completed_tasks", []))
        total = len(self.workflow.get("tasks", {}))
        progress = (done / total * 100) if total > 0 else 0

        current_task = self.workflow.get("current_task")
        current_info = f"\n\n현재 태스크: {current_task}" if current_task else "\n\n현재 태스크 없음"

        return f"""📊 워크플로우 상태
프로젝트: {self.workflow['project_name']}
진행률: {done}/{total} ({progress:.0f}%)
{current_info}"""
def get_workflow_manager(project_path: str = ".") -> WorkflowManager:
    """프로젝트별 WorkflowManager 인스턴스 반환"""
    path = str(Path(project_path).resolve())
    if path not in _workflow_managers:
        _workflow_managers[path] = WorkflowManager(path)
    return _workflow_managers[path]

# wf 함수 래퍼
def wf(command: str) -> str:
    """워크플로우 명령어 처리"""
    manager = get_workflow_manager()
    return manager.wf_command(command)
