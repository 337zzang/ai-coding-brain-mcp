"""
Flow CLI - 명령어 인터페이스
분리일: 2025-08-03
원본: simple_flow_commands.py
"""

from typing import Dict, Any, Optional

from .flow_api import FlowAPI
from .flow_manager_utils import get_manager
from .flow_views import (
    show_status, show_plans, show_tasks, 
    display_task_history, _show_project_summary
)
# Response helpers
def ok_response(data=None, message=None):
    response = {'ok': True}
    if data is not None: response['data'] = data
    if message: response['message'] = message
    return response

def error_response(error, data=None):
    response = {'ok': False, 'error': error}
    if data is not None: response['data'] = data
    return response
from .project import switch_project as _switch_project

# 전역 변수 (레거시 호환성)
_flow_api_instance = None


def get_flow_api_instance() -> FlowAPI:
    """FlowAPI 인스턴스 반환 (싱글톤)"""
    global _flow_api_instance
    if _flow_api_instance is None:
        _flow_api_instance = FlowAPI(get_manager())
    return _flow_api_instance


def flow(command: str = "") -> Dict[str, Any]:
    """
    극단순 Flow 명령어 처리

    이 함수는 명령어 기반 인터페이스를 제공합니다.
    프로그래밍 방식의 접근을 원한다면 get_flow_api()를 사용하세요.

    사용법:
        h.flow()                    # 현재 상태 표시
        h.flow("/list")            # Plan 목록
        h.flow("/create 계획이름")  # 새 Plan 생성
        h.flow("/select plan_id")  # Plan 선택
        h.flow("/task add 작업명")  # Task 추가
        h.flow("/task done task_id") # Task 완료
        h.flow("/delete plan_id")  # Plan 삭제
        h.flow("/project 프로젝트명") # 프로젝트 전환
        h.flow("/help")            # 도움말
    """
    manager = get_manager()
    parts = command.strip().split(maxsplit=2)

    if not parts or not command:
        # 현재 상태 표시
        show_status(manager)
        plans = manager.list_plans()
        return {
            "ok": True,
            "data": {
                "plan_count": len(plans),
                "current_plan": get_current_plan_id(),
                "recent_plans": [plan.to_dict() for plan in plans[-3:]]
            }
        }

    cmd = parts[0].lower()

    # 명령어 매핑
    commands = {
        "/list": lambda: show_plans(manager),
        "/create": lambda: create_plan(manager, " ".join(parts[1:]) if len(parts) > 1 else None),
        "/select": lambda: select_plan(parts[1] if len(parts) > 1 else None),
        "/task": lambda: handle_task_command(manager, parts[1:] if len(parts) > 1 else []),
        "/delete": lambda: delete_plan(manager, parts[1] if len(parts) > 1 else None),
        "/project": lambda: switch_project(parts[1] if len(parts) > 1 else None),
        "/help": lambda: show_help(),
        "/status": lambda: show_status(manager),
    }

    if cmd in commands:
        commands[cmd]()
        
        # 각 명령어에 따른 데이터 반환
        if cmd == "/list":
            plans = manager.list_plans()
            return {
                "ok": True,
                "data": {
                    "plans": [plan.to_dict() for plan in plans]
                }
            }
        elif cmd == "/status":
            plans = manager.list_plans()
            return {
                "ok": True,
                "data": {
                    "plan_count": len(plans),
                    "current_plan": get_current_plan_id(),
                    "recent_plans": [plan.to_dict() for plan in plans[-3:]]
                }
            }
        elif cmd == "/project":
            # 프로젝트 전환은 flow_project_with_workflow가 이미 dict 반환
            return {"ok": True, "message": "Project command executed"}
        else:
            return {"ok": True, "message": f"Command {cmd} executed"}
    else:
        print(f"❌ 알 수 없는 명령어: {cmd}")
        show_help()
        return {"ok": False, "error": f"Unknown command: {cmd}"}

def handle_task_command(manager: UltraSimpleFlowManager, args: List[str]) -> None:
    """Task 관련 명령어 처리"""

    if not get_current_plan_id():
        print("❌ 먼저 Plan을 선택하세요: /select [plan_id]")
        return

    if not args:
        # 현재 Plan의 Task 목록 표시
        show_tasks(manager, get_current_plan_id())
        return

    subcmd = args[0].lower()

    if subcmd == "add" and len(args) > 1:
        # Task 추가
        title = " ".join(args[1:])
        task = manager.create_task(get_current_plan_id(), title)
        if task:
            print(f"✅ Task 추가됨: {task.title} ({task.id})")
        else:
            print(f"❌ Task 추가 실패: Plan '{get_current_plan_id()}'을 찾을 수 없습니다.")
            print("   💡 Plan 목록 확인: /list")
            print("   💡 Plan 선택: /select [plan_id]")

    elif subcmd == "done" and len(args) > 1:
        # Task 완료
        task_id = args[1]
        result = manager.update_task_status(get_current_plan_id(), task_id, "done")
        if result:
            print(f"✅ Task 완료 처리됨: {task_id}")
        else:
            print(f"❌ Task 업데이트 실패: {task_id}")

    elif subcmd == "progress" and len(args) > 1:
        # Task 진행중
        task_id = args[1]
        result = manager.update_task_status(get_current_plan_id(), task_id, "in_progress")
        if result:
            print(f"✅ Task 진행중 처리됨: {task_id}")
        else:
            print(f"❌ Task 업데이트 실패: {task_id}")

    else:
        print("❌ 올바른 Task 명령어:")
        print("  /task add [제목] - Task 추가")
        print("  /task done [task_id] - Task 완료")
        print("  /task progress [task_id] - Task 진행중")

def select_plan(plan_id: Optional[str]) -> None:
    """Plan 선택 - 순번, 부분 매칭, 인덱스 모두 지원"""

    if not plan_id:
        print("❌ Plan ID를 입력하세요: /select [plan_id]")
        return

    manager = get_manager()

    # 1. 정확한 매칭 시도 (기존 로직)
    plan = manager.get_plan(plan_id)
    if plan:
        set_current_plan_id(plan_id)
        print(f"✅ Plan 선택됨: {plan.name}")
        display_task_history(plan_id)
        return

    # 2. 순번 매칭 (o3 권장 방식)
    if plan_id.isdigit() and len(plan_id) <= 3:
        seq = plan_id.zfill(3)  # 10 → 010
        matches = []

        for plan in manager.list_plans():
            parts = plan.id.split('_')
            if len(parts) >= 3 and parts[2] == seq:
                matches.append(plan)

        if len(matches) == 1:
            set_current_plan_id(matches[0].id)
            print(f"✅ Plan 선택됨: {matches[0].name}")
            print(f"   (순번 매칭: {plan_id} → {matches[0].id})")
            display_task_history(matches[0].id)
            return
        elif len(matches) > 1:
            # 가장 최근 것 선택 (날짜 역순)
            matches.sort(key=lambda p: p.created_at, reverse=True)
            set_current_plan_id(matches[0].id)
            print(f"✅ Plan 선택됨: {matches[0].name}")
            print(f"   (순번 {plan_id} 중복 → 가장 최근 선택)")
            display_task_history(matches[0].id)
            if len(matches) > 1:
                print(f"   💡 동일 순번 {len(matches)}개 존재")
            return

    # 3. 부분 매칭 시도
    all_plans = manager.list_plans()
    matches = [p for p in all_plans if plan_id in p.id or plan_id in p.name]

    if len(matches) == 0:
        print(f"❌ Plan을 찾을 수 없습니다: {plan_id}")

        # 유사한 순번 제안
        if plan_id.isdigit():
            similar_seq = []
            target = int(plan_id)
            for p in all_plans:
                parts = p.id.split('_')
                if len(parts) >= 3 and parts[2].isdigit():
                    seq_num = int(parts[2])
                    if abs(seq_num - target) <= 2:  # ±2 범위
                        similar_seq.append((seq_num, p))

            if similar_seq:
                print("\n💡 유사한 순번:")
                for seq, p in sorted(similar_seq, key=lambda x: x[0])[:3]:
                    print(f"  - {seq:03d}: {p.name}")

    elif len(matches) == 1:
        set_current_plan_id(matches[0].id)
        print(f"✅ Plan 선택됨: {matches[0].name}")
        print(f"   (부분 매칭: {plan_id} → {matches[0].id})")
        display_task_history(matches[0].id)
    else:
        print(f"🔍 여러 Plan이 '{plan_id}'와 일치합니다:")
        for i, p in enumerate(matches[:5], 1):
            parts = p.id.split('_')
            seq = parts[2] if len(parts) >= 3 else "???"
            print(f"  [{seq}] {p.id}")
            print(f"       이름: {p.name}")
        print("\n순번이나 전체 ID를 입력하여 선택하세요.")

def create_plan(manager: UltraSimpleFlowManager, name: Optional[str]) -> None:
    """새 Plan 생성"""
    if not name:
        print("❌ Plan 이름을 입력하세요: /create [이름]")
        return

    plan = manager.create_plan(name)
    print(f"✅ Plan 생성 완료: {plan.name} ({plan.id})")

    # 자동으로 선택
    set_current_plan_id(plan.id)
    print(f"✅ 자동으로 선택됨")

def delete_plan(manager: UltraSimpleFlowManager, plan_id: Optional[str]) -> None:
    """Plan 삭제"""

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
            if get_current_plan_id() == plan_id:
                set_current_plan_id(None)
        else:
            print(f"❌ Plan 삭제 실패")



def switch_project(project_name: Optional[str]) -> None:
    """프로젝트 전환 - flow_project_with_workflow 사용"""
    global _manager

    if not project_name:
        # 현재 프로젝트 표시
        current = get_current_project()
        if current and current.get('ok'):
            project_data = current.get('data', {})
            print(f"\n현재 프로젝트: {project_data.get('name', 'Unknown')}")
            print(f"경로: {project_data.get('path', '.')}")
        else:
            print(f"\n현재 프로젝트 확인 실패")
        return

    # 안전한 프로젝트 전환
    try:
        # flow_project_with_workflow 사용 - dict 반환
        result = flow_project_with_workflow(project_name)

        # 전환 성공 확인
        if isinstance(result, dict) and result.get('ok'):
            # Flow 매니저 재초기화
            _manager = None
            set_current_plan_id(None)

            project_info = result.get('data', {}).get('project', {})
            print(f"✅ 프로젝트 전환 완료: {project_name}")
            print(f"   경로: {project_info.get('path', '')}")

            # ========== 개선된 부분 ==========
            # 프로젝트 문서 요약 표시
            _show_project_summary()

            # Flow Plan 목록 표시
            print("")  # 빈 줄
            manager = get_manager()
            show_plans(manager)
            
            # ========== 💡 신규 기능 통합 부분 💡 ==========
            try:
                # Plan 진행 상황 자동 표시
                progress_summary = show_plan_progress()
                if progress_summary:
                    print(progress_summary)
            except Exception:
                # 이 기능에서 오류가 발생해도 프로젝트 전환은 정상 처리됨
                pass
            # ============================================
            # ========== 개선 끝 ==========
        else:
            print(f"❌ 프로젝트 전환 실패: {project_name}")
            if isinstance(result, dict):
                print(f"   오류: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ 프로젝트 전환 중 오류: {e}")

