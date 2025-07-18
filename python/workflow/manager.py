"""
워크플로우 v2.0 매니저 - 새로운 독립 시스템
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import uuid

from .schema import (
    Task, TaskStatus, WorkflowV2, WorkflowEvent, 
    Artifact, ArtifactType
)

class WorkflowV2Manager:
    """워크플로우 v2.0 관리 클래스"""

    def __init__(self, project_name: str = None):
        self.project_name = project_name or self._get_current_project()
        self.workflow_path = self._get_workflow_path()
        self.workflow: WorkflowV2 = self._load_or_create()

    def _get_current_project(self) -> str:
        """현재 프로젝트 이름 가져오기"""
        try:
            # 기존 시스템의 프로젝트 정보 활용
            context_path = "memory/context.json"
            if os.path.exists(context_path):
                with open(context_path, 'r', encoding='utf-8') as f:
                    context = json.load(f)
                    return context.get("project", "default")
        except:
            pass
        return "default"

    def _get_workflow_path(self) -> Path:
        """v2 워크플로우 파일 경로"""
        # v2는 memory 폴더에 단순하게 저장
        memory_dir = Path("memory")
        memory_dir.mkdir(parents=True, exist_ok=True)
        return memory_dir / "workflow_v2.json"

    def _load_or_create(self) -> WorkflowV2:
        """워크플로우 로드 또는 생성"""
        if self.workflow_path.exists():
            try:
                with open(self.workflow_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return self._dict_to_workflow(data)
            except Exception as e:
                print(f"⚠️ 워크플로우 로드 실패: {e}")

        # 새 워크플로우 생성
        return WorkflowV2(project=self.project_name)

    def _dict_to_workflow(self, data: Dict[str, Any]) -> WorkflowV2:
        """딕셔너리를 WorkflowV2 객체로 변환"""
        workflow = WorkflowV2(
            version=data.get("version", "2.0"),
            project=data.get("project", self.project_name),
            status=data.get("status", "active"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            focus_task_id=data.get("focus_task_id"),
            metadata=data.get("metadata", {})
        )

        # Tasks 복원
        for task_data in data.get("tasks", []):
            workflow.tasks.append(Task.from_dict(task_data))

        # Events 복원
        for event_data in data.get("events", []):
            event = WorkflowEvent(
                id=event_data["id"],
                type=event_data["type"],
                timestamp=event_data["timestamp"],
                task_id=event_data.get("task_id"),
                user=event_data.get("user"),
                data=event_data.get("data", {}),
                before_state=event_data.get("before_state"),
                after_state=event_data.get("after_state")
            )
            workflow.events.append(event)

        return workflow

    def save(self):
        """워크플로우 저장"""
        self.workflow.updated_at = datetime.now().isoformat()
        with open(self.workflow_path, 'w', encoding='utf-8') as f:
            json.dump(self.workflow.to_dict(), f, indent=2, ensure_ascii=False)

    def add_task(self, name: str, tags: List[str] = None, 
                 priority: int = 3, dependencies: List[int] = None) -> Task:
        """새 태스크 추가"""
        # ID 생성
        task_id = max([t.id for t in self.workflow.tasks], default=0) + 1

        # Task 생성
        task = Task(
            id=task_id,
            name=name,
            tags=tags or [],
            priority=priority,
            dependencies=dependencies or []
        )

        # 이벤트 기록
        self._add_event("task_created", task_id=task_id, data={
            "name": name,
            "tags": tags,
            "priority": priority
        })

        self.workflow.tasks.append(task)
        self.save()

        return task

    def start_task(self, task_id: int) -> Optional[Task]:
        """태스크 시작"""
        task = self.get_task(task_id)
        if not task:
            return None

        # 의존성 체크
        for dep_id in task.dependencies:
            dep_task = self.get_task(dep_id)
            if dep_task and dep_task.status != TaskStatus.DONE:
                print(f"⚠️ 의존성 태스크 #{dep_id}가 완료되지 않았습니다.")
                task.status = TaskStatus.BLOCKED
                self._add_event("task_blocked", task_id=task_id, data={
                    "reason": f"Waiting for task #{dep_id}"
                })
                self.save()
                return task

        # 상태 변경
        before_state = task.to_dict()
        task.status = TaskStatus.DOING
        task.started_at = datetime.now().isoformat()
        self.workflow.focus_task_id = task_id

        # 이벤트 기록
        self._add_event("task_started", task_id=task_id,
                       before_state=before_state,
                       after_state=task.to_dict())

        self.save()
        return task

    def complete_task(self, task_id: int, summary: str = None) -> Optional[Task]:
        """태스크 완료"""
        task = self.get_task(task_id)
        if not task:
            return None

        # 완료 처리
        before_state = task.to_dict()
        task.status = TaskStatus.DONE
        task.completed_at = datetime.now().isoformat()
        task.summary = summary

        # 소요 시간 계산
        if task.started_at:
            start = datetime.fromisoformat(task.started_at)
            end = datetime.fromisoformat(task.completed_at)
            task.duration_minutes = int((end - start).total_seconds() / 60)

        # 자동으로 생성된 파일들 추적 (간단한 예시)
        # 실제로는 더 정교한 추적 필요
        self._track_artifacts(task)

        # 이벤트 기록
        self._add_event("task_completed", task_id=task_id,
                       before_state=before_state,
                       after_state=task.to_dict())

        # 다음 태스크로 포커스 이동
        self._update_focus()

        self.save()
        return task

    def add_artifact(self, task_id: int, artifact_type: str, 
                    path: str = None, content: str = None, 
                    description: str = None) -> bool:
        """태스크에 산출물 추가"""
        task = self.get_task(task_id)
        if not task:
            return False

        artifact = Artifact(
            type=ArtifactType(artifact_type),
            path=path,
            content=content,
            description=description
        )

        task.artifacts.append(artifact)

        self._add_event("artifact_added", task_id=task_id, data={
            "type": artifact_type,
            "path": path,
            "description": description
        })

        self.save()
        return True

    def get_task(self, task_id: int) -> Optional[Task]:
        """태스크 조회"""
        for task in self.workflow.tasks:
            if task.id == task_id:
                return task
        return None

    def get_status(self) -> Dict[str, Any]:
        """워크플로우 상태 조회"""
        total_tasks = len(self.workflow.tasks)
        completed_tasks = len([t for t in self.workflow.tasks 
                              if t.status == TaskStatus.DONE])

        current_task = None
        if self.workflow.focus_task_id:
            current_task = self.get_task(self.workflow.focus_task_id)

        return {
            "project": self.workflow.project,
            "version": self.workflow.version,
            "status": self.workflow.status,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "progress": f"{completed_tasks}/{total_tasks} ({completed_tasks/total_tasks*100:.1f}%)" if total_tasks > 0 else "0%",
            "current_task": current_task.name if current_task else None,
            "created_at": self.workflow.created_at,
            "updated_at": self.workflow.updated_at
        }

    def _add_event(self, event_type: str, task_id: Optional[int] = None, 
                   data: Dict[str, Any] = None, before_state: Dict[str, Any] = None,
                   after_state: Dict[str, Any] = None):
        """이벤트 추가"""
        event = WorkflowEvent(
            id=str(uuid.uuid4()),
            type=event_type,
            timestamp=datetime.now().isoformat(),
            task_id=task_id,
            user=os.environ.get("USER", "system"),
            data=data or {},
            before_state=before_state,
            after_state=after_state
        )
        self.workflow.events.append(event)

    def _track_artifacts(self, task: Task):
        """작업 중 생성된 산출물 자동 추적 (간단한 예시)"""
        # 실제로는 Git diff, 파일 시스템 모니터링 등 필요
        # 여기서는 예시로 간단히 구현
        pass

    def _update_focus(self):
        """포커스 업데이트"""
        # 다음 미완료 태스크로 포커스 이동
        for task in self.workflow.tasks:
            if task.status in [TaskStatus.TODO, TaskStatus.DOING]:
                self.workflow.focus_task_id = task.id
                return

        # 모든 태스크 완료 시
        self.workflow.focus_task_id = None
        if all(t.status == TaskStatus.DONE for t in self.workflow.tasks):
            self.workflow.status = "completed"

    def search_tasks(self, query: str = None, tags: List[str] = None, 
                    status: str = None) -> List[Task]:
        """태스크 검색"""
        results = self.workflow.tasks

        if query:
            query_lower = query.lower()
            results = [t for t in results 
                      if query_lower in t.name.lower() 
                      or (t.summary and query_lower in t.summary.lower())]

        if tags:
            results = [t for t in results 
                      if any(tag in t.tags for tag in tags)]

        if status:
            results = [t for t in results 
                      if t.status.value == status]

        return results

    def get_report(self) -> str:
        """워크플로우 리포트 생성"""
        status = self.get_status()

        report = f"""
# 워크플로우 리포트

**프로젝트**: {status['project']}
**상태**: {status['status']}
**진행률**: {status['progress']}
**현재 작업**: {status['current_task'] or '없음'}

## 태스크 목록

"""
        for task in self.workflow.tasks:
            status_icon = "✅" if task.status == TaskStatus.DONE else "⏳" if task.status == TaskStatus.DOING else "📋"
            report += f"{status_icon} **{task.name}** (#{task.id})\n"

            if task.summary:
                report += f"   요약: {task.summary}\n"

            if task.artifacts:
                report += f"   산출물: {len(task.artifacts)}개\n"
                for artifact in task.artifacts:
                    report += f"     - {artifact.type.value}: {artifact.path or artifact.description}\n"

            if task.duration_minutes:
                report += f"   소요시간: {task.duration_minutes}분\n"

            report += "\n"

        return report
