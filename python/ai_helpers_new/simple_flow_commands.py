"""
극단순화된 Workflow 명령어 시스템
Flow 개념 없이 Plan과 Task만으로 작업 관리
"""
from typing import Optional, List, Dict, Any
from .ultra_simple_flow_manager import UltraSimpleFlowManager
from .project import get_current_project

# 전역 매니저 인스턴스
_manager: Optional[UltraSimpleFlowManager] = None
_current_plan_id: Optional[str] = None

def get_manager() -> UltraSimpleFlowManager:
    """현재 프로젝트의 매니저 가져오기"""
    global _manager
    if _manager is None:
        _manager = UltraSimpleFlowManager()
    return _manager

def flow(command: str = "") -> None:
    """
    극단순 Flow 명령어 처리

    사용법:
        flow()                    # 현재 상태 표시
        flow("/list")            # Plan 목록
        flow("/create 계획이름")  # 새 Plan 생성
        flow("/select plan_id")  # Plan 선택
        flow("/task add 작업명")  # Task 추가
        flow("/task done task_id") # Task 완료
        flow("/delete plan_id")  # Plan 삭제
        flow("/project 프로젝트명") # 프로젝트 전환
        flow("/help")            # 도움말
    """
    manager = get_manager()
    parts = command.strip().split(maxsplit=2)

    if not parts or not command:
        # 현재 상태 표시
        show_status(manager)
        return

    cmd = parts[0].lower()

    # 명령어 매핑
    commands = {
        "/list": lambda: show_plans(manager),
        "/create": lambda: create_plan(manager, parts[1] if len(parts) > 1 else None),
        "/select": lambda: select_plan(parts[1] if len(parts) > 1 else None),
        "/task": lambda: handle_task_command(manager, parts[1:] if len(parts) > 1 else []),
        "/delete": lambda: delete_plan(manager, parts[1] if len(parts) > 1 else None),
        "/project": lambda: switch_project(parts[1] if len(parts) > 1 else None),
        "/help": lambda: show_help(),
        "/status": lambda: show_status(manager),
    }

    if cmd in commands:
        commands[cmd]()
    else:
        print(f"❌ 알 수 없는 명령어: {cmd}")
        show_help()

def show_status(manager: UltraSimpleFlowManager) -> None:
    """현재 상태 표시"""
    global _current_plan_id

    print("\n📊 Flow 시스템 상태")
    print("=" * 50)
    print(f"프로젝트: {manager.project_name}")

    plans = manager.list_plans()
    print(f"\nPlan 개수: {len(plans)}개")

    if _current_plan_id:
        plan = manager.get_plan(_current_plan_id)
        if plan:
            print(f"\n현재 선택된 Plan: {plan.name}")
            print(f"Task 개수: {len(plan.tasks)}개")

            # Task 상태별 개수
            todo = sum(1 for t in plan.tasks.values() if str(t.status).endswith("TODO"))
            in_progress = sum(1 for t in plan.tasks.values() if str(t.status).endswith("IN_PROGRESS"))
            done = sum(1 for t in plan.tasks.values() if str(t.status).endswith("DONE"))

            print(f"  - 할 일: {todo}개")
            print(f"  - 진행중: {in_progress}개")
            print(f"  - 완료: {done}개")
    else:
        print("\n선택된 Plan이 없습니다. /select [plan_id]로 선택하세요.")

def show_plans(manager: UltraSimpleFlowManager) -> None:
    """Plan 목록 표시"""
    plans = manager.list_plans()

    if not plans:
        print("\n📋 Plan이 없습니다. /create [이름]으로 생성하세요.")
        return

    print(f"\n📋 Plan 목록 ({len(plans)}개)")
    print("=" * 60)

    for plan in plans:
        task_count = len(plan.tasks) if hasattr(plan, 'tasks') else 0
        print(f"\n{plan.id}")
        print(f"  이름: {plan.name}")
        print(f"  상태: {plan.status}")
        print(f"  Task: {task_count}개")
        print(f"  생성: {str(plan.created_at)[:19]}")

def create_plan(manager: UltraSimpleFlowManager, name: Optional[str]) -> None:
    """새 Plan 생성"""
    if not name:
        print("❌ Plan 이름을 입력하세요: /create [이름]")
        return

    plan = manager.create_plan(name)
    print(f"✅ Plan 생성 완료: {plan.name} ({plan.id})")

    # 자동으로 선택
    global _current_plan_id
    _current_plan_id = plan.id
    print(f"✅ 자동으로 선택됨")

def select_plan(plan_id: Optional[str]) -> None:
    """Plan 선택"""
    global _current_plan_id

    if not plan_id:
        print("❌ Plan ID를 입력하세요: /select [plan_id]")
        return

    manager = get_manager()
    plan = manager.get_plan(plan_id)

    if not plan:
        print(f"❌ Plan을 찾을 수 없습니다: {plan_id}")
        return

    _current_plan_id = plan_id
    print(f"✅ Plan 선택됨: {plan.name}")

def handle_task_command(manager: UltraSimpleFlowManager, args: List[str]) -> None:
    """Task 관련 명령어 처리"""
    global _current_plan_id

    if not _current_plan_id:
        print("❌ 먼저 Plan을 선택하세요: /select [plan_id]")
        return

    if not args:
        # 현재 Plan의 Task 목록 표시
        show_tasks(manager, _current_plan_id)
        return

    subcmd = args[0].lower()

    if subcmd == "add" and len(args) > 1:
        # Task 추가
        title = " ".join(args[1:])
        task = manager.create_task(_current_plan_id, title)
        print(f"✅ Task 추가됨: {task.title} ({task.id})")

    elif subcmd == "done" and len(args) > 1:
        # Task 완료
        task_id = args[1]
        result = manager.update_task_status(_current_plan_id, task_id, "done")
        if result:
            print(f"✅ Task 완료 처리됨: {task_id}")
        else:
            print(f"❌ Task 업데이트 실패: {task_id}")

    elif subcmd == "progress" and len(args) > 1:
        # Task 진행중
        task_id = args[1]
        result = manager.update_task_status(_current_plan_id, task_id, "in_progress")
        if result:
            print(f"✅ Task 진행중 처리됨: {task_id}")
        else:
            print(f"❌ Task 업데이트 실패: {task_id}")

    else:
        print("❌ 올바른 Task 명령어:")
        print("  /task add [제목] - Task 추가")
        print("  /task done [task_id] - Task 완료")
        print("  /task progress [task_id] - Task 진행중")

def show_tasks(manager: UltraSimpleFlowManager, plan_id: str) -> None:
    """Task 목록 표시"""
    plan = manager.get_plan(plan_id)
    if not plan:
        return

    if not plan.tasks:
        print(f"\n📝 {plan.name}에 Task가 없습니다.")
        print("  /task add [제목]으로 추가하세요.")
        return

    print(f"\n📝 {plan.name}의 Task 목록")
    print("=" * 60)

    for task in plan.tasks.values():
        status_emoji = {
            "TODO": "⬜",
            "IN_PROGRESS": "🟨", 
            "DONE": "✅"
        }
        status_str = str(task.status).split(".")[-1]
        emoji = status_emoji.get(status_str, "❓")

        print(f"\n{emoji} {task.id}")
        print(f"   {task.title}")
        print(f"   상태: {status_str}")

def delete_plan(manager: UltraSimpleFlowManager, plan_id: Optional[str]) -> None:
    """Plan 삭제"""
    global _current_plan_id

    if not plan_id:
        print("❌ Plan ID를 입력하세요: /delete [plan_id]")
        return

    plan = manager.get_plan(plan_id)
    if not plan:
        print(f"❌ Plan을 찾을 수 없습니다: {plan_id}")
        return

    # 확인
    print(f"⚠️  '{plan.name}' Plan을 삭제하시겠습니까?")
    print(f"   Task {len(plan.tasks)}개도 함께 삭제됩니다.")
    response = input("   삭제하려면 'yes'를 입력하세요: ")

    if response.lower() == 'yes':
        result = manager.delete_plan(plan_id)
        if result:
            print(f"✅ Plan 삭제 완료: {plan.name}")
            if _current_plan_id == plan_id:
                _current_plan_id = None
        else:
            print(f"❌ Plan 삭제 실패")

def switch_project(project_name: Optional[str]) -> None:
    """프로젝트 전환"""
    global _manager, _current_plan_id

    if not project_name:
        # 현재 프로젝트 표시
        current = get_current_project()
        print(f"\n현재 프로젝트: {current['name']}")
        return

    # 프로젝트 전환 (디렉토리 변경 방식)
    try:
        if os.path.exists(project_name):
            os.chdir(project_name)
            _manager = None  # 매니저 재생성 필요
            _current_plan_id = None
            print(f"✅ 프로젝트 전환: {os.path.basename(project_name)}")
        else:
            print(f"❌ 프로젝트 경로를 찾을 수 없습니다: {project_name}")
    except Exception as e:
        print(f"❌ 프로젝트 전환 실패: {e}")

def show_help() -> None:
    """도움말 표시"""
    print("""
🚀 극단순 Flow 명령어 시스템
==========================

기본 명령어:
  flow()                    # 현재 상태 표시
  flow("/list")            # Plan 목록 보기
  flow("/create 계획이름")  # 새 Plan 생성
  flow("/select plan_id")  # Plan 선택
  flow("/delete plan_id")  # Plan 삭제

Task 명령어:
  flow("/task")            # 현재 Plan의 Task 목록
  flow("/task add 작업명")  # Task 추가
  flow("/task done task_id") # Task 완료 처리
  flow("/task progress task_id") # Task 진행중 처리

프로젝트:
  flow("/project")         # 현재 프로젝트 확인
  flow("/project 이름")    # 프로젝트 전환

기타:
  flow("/help")            # 이 도움말 표시
  flow("/status")          # 상태 표시

팁:
- Plan을 먼저 선택해야 Task를 추가할 수 있습니다.
- 새 Plan을 생성하면 자동으로 선택됩니다.
""")

# 별칭 함수들
def wf(command: str = "") -> None:
    """flow()의 짧은 별칭"""
    flow(command)

def help_flow() -> None:
    """도움말 표시"""
    show_help()

# __all__ export
__all__ = ['flow', 'wf', 'help_flow', 'get_manager']
