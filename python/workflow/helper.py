"""
WorkflowV2 헬퍼 - 간편한 사용을 위한 래퍼
"""
from .manager import WorkflowV2Manager
from .schema import TaskStatus, ArtifactType
from typing import Optional, List, Dict, Any
import os
import json
from datetime import datetime

# 전역 매니저 인스턴스
_manager: Optional[WorkflowV2Manager] = None

def init_workflow_v2(project_name: str = None) -> WorkflowV2Manager:
    """워크플로우 v2 초기화"""
    global _manager
    _manager = WorkflowV2Manager(project_name)
    return _manager

def get_manager() -> WorkflowV2Manager:
    """현재 매니저 가져오기"""
    global _manager
    if _manager is None:
        _manager = init_workflow_v2()
    return _manager

def workflow_v2(command: str) -> str:
    """워크플로우 v2 명령어 처리"""
    manager = get_manager()
    parts = command.split()

    if not parts:
        return "❌ 명령어를 입력하세요"

    cmd = parts[0].lower()

    # /v2 status - 상태 확인
    if cmd in ["status", "st"]:
        status = manager.get_status()
        return f"""
📊 워크플로우 v2 상태
프로젝트: {status['project']}
진행률: {status['progress']}
현재 작업: {status['current_task'] or '없음'}
생성일: {status['created_at'][:19]}
"""

    # /v2 task add [name] - 태스크 추가
    elif cmd == "task" and len(parts) > 2 and parts[1] == "add":
        task_name = " ".join(parts[2:])

        # 태그 추출 (예: #backend #api)
        tags = []
        words = task_name.split()
        clean_words = []
        for word in words:
            if word.startswith("#"):
                tags.append(word[1:])
            else:
                clean_words.append(word)
        task_name = " ".join(clean_words)

        task = manager.add_task(task_name, tags=tags)
        return f"✅ 태스크 추가: {task.name} (#{task.id})"

    # /v2 task list - 태스크 목록
    elif cmd == "task" and len(parts) > 1 and parts[1] == "list":
        tasks = manager.workflow.tasks
        if not tasks:
            return "📋 태스크가 없습니다"

        lines = ["📋 태스크 목록:"]
        for task in tasks:
            status_icon = "✅" if task.status == TaskStatus.DONE else "🔄" if task.status == TaskStatus.DOING else "⏳"
            line = f"{status_icon} #{task.id} {task.name}"
            if task.tags:
                line += f" [{', '.join(task.tags)}]"
            lines.append(line)

        return "\n".join(lines)

    # /v2 start [id] - 태스크 시작
    elif cmd == "start" and len(parts) > 1:
        try:
            task_id = int(parts[1])
            task = manager.start_task(task_id)
            if task:
                return f"🚀 태스크 시작: {task.name} (#{task.id})"
            else:
                return f"❌ 태스크 #{task_id}를 찾을 수 없습니다"
        except ValueError:
            return "❌ 올바른 태스크 ID를 입력하세요"

    # /v2 complete [id] [summary] - 태스크 완료
    elif cmd == "complete" and len(parts) > 1:
        try:
            task_id = int(parts[1])
            summary = " ".join(parts[2:]) if len(parts) > 2 else None

            task = manager.complete_task(task_id, summary)
            if task:
                msg = f"✅ 태스크 완료: {task.name} (#{task.id})"
                if task.duration_minutes:
                    msg += f"\n⏱️ 소요시간: {task.duration_minutes}분"
                return msg
            else:
                return f"❌ 태스크 #{task_id}를 찾을 수 없습니다"
        except ValueError:
            return "❌ 올바른 태스크 ID를 입력하세요"

    # /v2 artifact [task_id] [type] [path] - 산출물 추가
    elif cmd == "artifact" and len(parts) > 3:
        try:
            task_id = int(parts[1])
            artifact_type = parts[2]
            path = parts[3]
            description = " ".join(parts[4:]) if len(parts) > 4 else None

            if manager.add_artifact(task_id, artifact_type, path=path, description=description):
                return f"📎 산출물 추가: {artifact_type} - {path}"
            else:
                return f"❌ 태스크 #{task_id}를 찾을 수 없습니다"
        except (ValueError, KeyError):
            return "❌ 사용법: /v2 artifact [task_id] [file|commit|url|document] [path]"

    # /v2 search [query] - 검색
    elif cmd == "search" and len(parts) > 1:
        query = " ".join(parts[1:])
        results = manager.search_tasks(query=query)

        if not results:
            return "🔍 검색 결과가 없습니다"

        lines = [f"🔍 검색 결과 ({len(results)}개):"]
        for task in results:
            status_icon = "✅" if task.status == TaskStatus.DONE else "🔄" if task.status == TaskStatus.DOING else "⏳"
            lines.append(f"{status_icon} #{task.id} {task.name}")

        return "\n".join(lines)

    # /v2 report - 리포트 생성
    elif cmd == "report":
        return manager.get_report()

    # /v2 help - 도움말
    elif cmd == "help":
        return """
📚 WorkflowV2 명령어:
/v2 status - 상태 확인
/v2 task add [이름] #태그1 #태그2 - 태스크 추가
/v2 task list - 태스크 목록
/v2 start [id] - 태스크 시작
/v2 complete [id] [요약] - 태스크 완료
/v2 artifact [id] [type] [path] - 산출물 추가
/v2 search [검색어] - 태스크 검색
/v2 report - 전체 리포트
/v2 help - 도움말
"""

    else:
        return f"❌ 알 수 없는 명령어: {cmd}\n/v2 help로 도움말을 확인하세요"

# 자동 추적 헬퍼들
def track_file_artifact(task_id: int, file_path: str, description: str = None):
    """파일 산출물 자동 추적"""
    manager = get_manager()
    manager.add_artifact(task_id, "file", path=file_path, description=description)

def track_commit_artifact(task_id: int, commit_hash: str, message: str):
    """Git 커밋 산출물 자동 추적"""
    manager = get_manager()
    artifact = {
        "type": "commit",
        "commit_hash": commit_hash,
        "commit_message": message
    }
    # 실제로는 add_artifact 메서드 확장 필요
    manager.add_artifact(task_id, "commit", description=message)

def auto_track_current_task():
    """현재 포커스 태스크의 산출물 자동 추적"""
    manager = get_manager()
    if not manager.workflow.focus_task_id:
        return

    # 현재 태스크
    task = manager.get_task(manager.workflow.focus_task_id)
    if not task or task.status != TaskStatus.DOING:
        return

    # Git 상태 확인 (helpers가 있다고 가정)
    try:
        # 실제로는 helpers.git_status() 등 사용
        # 여기서는 예시로만
        pass
    except:
        pass

# 초기화
init_workflow_v2()
