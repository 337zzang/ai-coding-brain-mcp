import os
import glob
import json
"""
극단순화된 Workflow 명령어 시스템
Flow 개념 없이 Plan과 Task만으로 작업 관리
"""
from typing import Optional, List, Dict, Any
from .ultra_simple_flow_manager import UltraSimpleFlowManager, Plan, Task
from .project import get_current_project
from .project import flow_project_with_workflow

# New session-based imports
from .session import get_current_session
from .contextual_flow_manager import ContextualFlowManager
from .manager_adapter import ManagerAdapter
from .flow_api import get_flow_api

# 전역 매니저 인스턴스
# DEPRECATED: These global variables are maintained for backward compatibility
# New code should use get_current_session() instead
_manager: Optional[UltraSimpleFlowManager] = None  # @deprecated - use get_current_session().flow_manager
_flow_api_instance = None  # type: Optional["FlowAPI"]

def get_flow_api_instance() -> "FlowAPI":
    """싱글톤 FlowAPI 인스턴스 반환"""
    global _flow_api_instance
    if _flow_api_instance is None:
        _flow_api_instance = FlowAPI()
    return _flow_api_instance

def get_current_plan_id() -> Optional[str]:
    """현재 선택된 Plan ID 반환 (호환성 유지)"""
    api = get_flow_api_instance()
    return api._current_plan_id

def set_current_plan_id(plan_id: Optional[str]) -> None:
    """현재 Plan ID 설정 (호환성 유지)"""
    api = get_flow_api_instance()
    api._current_plan_id = plan_id
_current_project_path: Optional[str] = None  # @deprecated - use get_current_session().project_context

def get_manager() -> UltraSimpleFlowManager:
    """현재 프로젝트의 매니저 가져오기 (Session 기반)

    이 함수는 기존 코드와의 호환성을 위해 유지됩니다.
    내부적으로는 새로운 Session 시스템을 사용하며,
    ManagerAdapter를 통해 기존 인터페이스를 제공합니다.
    """
    # Get current session
    session = get_current_session()

    # Check if session is initialized with a project
    if not session.is_initialized:
        # Initialize with current directory
        project_path = os.getcwd()
        project_name = os.path.basename(project_path)
        session.set_project(project_name, project_path)

        # Notification about .ai-brain directory
        ai_brain_path = os.path.join(project_path, '.ai-brain', 'flow')
        if not os.path.exists(ai_brain_path):
            print(f"📁 새로운 Flow 저장소 생성: {project_name}/.ai-brain/flow/")
        else:
            print(f"📁 Flow 저장소 사용: {project_name}/.ai-brain/flow/")

    # Return adapter for backward compatibility
    # The adapter makes ContextualFlowManager look like UltraSimpleFlowManager
    return ManagerAdapter(session.flow_manager)

def _show_deprecation_warning():
    """Show deprecation warning for old-style usage."""
    import warnings
    warnings.warn(
        "Direct flow() command usage is deprecated. "
        "Consider using get_flow_api() for a more Pythonic interface:\n"
        "  api = get_flow_api()\n"
        "  plan = api.create_plan('My Plan')\n"
        "  task = api.add_task('My Task')",
        DeprecationWarning,
        stacklevel=3
    )

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

def show_status(manager: UltraSimpleFlowManager) -> None:
    """현재 상태 표시"""

    print("\n📊 Flow 시스템 상태")
    print("=" * 50)
    print(f"프로젝트: {manager.project_name}")

    plans = manager.list_plans()
    print(f"\nPlan 개수: {len(plans)}개")

    # 최근 Plan 3개 표시
    if plans:
        recent_plans = sorted(plans, key=lambda p: p.created_at, reverse=True)[:3]
        print("\n📌 최근 Plan (최대 3개):")
        for i, plan in enumerate(recent_plans):
            task_count = len(plan.tasks) if hasattr(plan, 'tasks') else 0
            if i == 0:
                print(f"  • {plan.id}: {plan.name} (Task {task_count}개) 🔥 가장 최근")
            else:
                print(f"  • {plan.id}: {plan.name} (Task {task_count}개)")

    if get_current_plan_id():
        plan = manager.get_plan(get_current_plan_id())
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
    set_current_plan_id(plan.id)
    print(f"✅ 자동으로 선택됨")

def display_task_history(plan_id: str, show_all: bool = False):
    """완료된 Task들의 JSONL 전체 내역을 모두 표시"""
    plan_dir = os.path.join(
        get_manager().project_path,
        ".ai-brain", "flow", "plans", plan_id
    )

    if not os.path.exists(plan_dir):
        return

    print("\n📋 기존 Task 작업 내역 (전체):")
    print("="*80)

    jsonl_files = sorted(glob.glob(os.path.join(plan_dir, "*.jsonl")))
    
    for jsonl_file in jsonl_files:
        task_name = os.path.basename(jsonl_file).replace('.jsonl', '')
        events = []

        # JSONL 파일 읽기
        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            events.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"\n❌ 파일 읽기 오류 ({task_name}): {e}")
            continue

        # 완료된 Task만 표시 (또는 전체 표시)
        is_completed = any(
            e.get('event_type') == 'COMPLETE' or e.get('type') == 'COMPLETE' 
            for e in events
        )

        if is_completed or show_all:
            print(f"\n\n{'='*80}")
            print(f"📁 Task: {task_name}")
            print(f"📊 총 이벤트: {len(events)}개")
            print("="*80)
            
            # 모든 이벤트를 순서대로 표시
            for i, event in enumerate(events, 1):
                event_type = event.get('event_type') or event.get('type', 'UNKNOWN')
                timestamp = event.get('timestamp', event.get('ts', 'N/A'))
                
                print(f"\n[이벤트 #{i}] {event_type} - {timestamp}")
                print("-"*60)
                
                # 이벤트 타입별 전체 내용 표시
                if event_type == 'TASK_INFO':
                    print(f"  📌 제목: {event.get('title', 'N/A')}")
                    print(f"  ⏰ 예상시간: {event.get('estimate', 'N/A')}")
                    print(f"  🎯 우선순위: {event.get('priority', 'N/A')}")
                    desc = event.get('description', '')
                    if desc:
                        print(f"  📝 설명: {desc}")
                        
                elif event_type == 'DESIGN':
                    design_content = event.get('design', '')
                    if design_content:
                        print("  🏗️ 설계 내용:")
                        for line in design_content.split('\n'):
                            print(f"    {line}")
                            
                elif event_type == 'TODO':
                    todos = event.get('todos', [])
                    print(f"  📋 TODO 목록 ({len(todos)}개):")
                    for j, todo in enumerate(todos, 1):
                        print(f"    {j}. {todo}")
                        
                elif event_type == 'TODO_UPDATE':
                    completed = event.get('completed', [])
                    remaining = event.get('remaining', [])
                    new_todos = event.get('new', [])
                    blocked = event.get('blocked', [])
                    
                    if completed:
                        print(f"  ✅ 완료된 항목 ({len(completed)}개):")
                        for item in completed:
                            print(f"    - {item}")
                    if remaining:
                        print(f"  ⏳ 남은 항목 ({len(remaining)}개):")
                        for item in remaining:
                            print(f"    - {item}")
                    if new_todos:
                        print(f"  🆕 새로 추가된 항목 ({len(new_todos)}개):")
                        for item in new_todos:
                            print(f"    - {item}")
                    if blocked:
                        print(f"  🚫 블로킹된 항목 ({len(blocked)}개):")
                        for item in blocked:
                            print(f"    - {item}")
                            
                elif event_type == 'ANALYZE':
                    target = event.get('target', 'N/A')
                    result = event.get('result', '')
                    print(f"  🔍 분석 대상: {target}")
                    if result:
                        print(f"  📊 분석 결과:")
                        for line in result.split('\n'):
                            print(f"    {line}")
                            
                elif event_type == 'CODE':
                    action = event.get('action', 'N/A')
                    file_path = event.get('file', 'N/A')
                    summary = event.get('summary', '')
                    print(f"  🔧 액션: {action}")
                    print(f"  📄 파일: {file_path}")
                    if summary:
                        print(f"  📝 요약:")
                        for line in summary.split('\n'):
                            print(f"    {line}")
                            
                elif event_type == 'DECISION':
                    decision = event.get('decision', '')
                    rationale = event.get('rationale', '')
                    print(f"  🤔 결정: {decision}")
                    if rationale:
                        print(f"  💭 이유: {rationale}")
                        
                elif event_type == 'BLOCKER':
                    issue = event.get('issue', '')
                    severity = event.get('severity', 'N/A')
                    solution = event.get('solution', '')
                    print(f"  🚨 이슈: {issue}")
                    print(f"  ⚠️ 심각도: {severity}")
                    if solution:
                        print(f"  💡 해결방안: {solution}")
                        
                elif event_type == 'NOTE':
                    content = event.get('content', event.get('note', ''))
                    print(f"  📝 메모: {content}")
                    
                elif event_type == 'CONTEXT':
                    ctx_type = event.get('context_type', 'N/A')
                    ctx_data = event.get('data', '')
                    print(f"  🔗 컨텍스트 타입: {ctx_type}")
                    print(f"  📋 데이터: {ctx_data}")
                    
                elif event_type == 'COMPLETE':
                    summary = event.get('summary', '')
                    print(f"  ✅ 완료 요약:")
                    if summary:
                        for line in summary.split('\n'):
                            print(f"    {line}")
                else:
                    # 알 수 없는 이벤트 타입의 경우 전체 내용 표시
                    print(f"  📦 전체 데이터:")
                    print(json.dumps(event, indent=4, ensure_ascii=False))
            
            print(f"\n{'='*80}")
            print(f"📊 Task '{task_name}' 종료 - 총 {len(events)}개 이벤트")
            print("="*80)

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



def _show_project_summary():
    """프로젝트 문서 요약 표시"""
    try:
        # file 모듈의 read 함수 import
        from .file import read as h_read

        readme_exists = False
        file_dir_exists = False

        # readme.md 확인 및 요약
        try:
            readme = h_read('readme.md')
            if readme['ok']:
                readme_exists = True
                lines = readme['data'].split('\n')

                print("\n📄 README.md 요약")
                print("=" * 60)

                # 주요 기능 찾기
                in_features = False
                feature_count = 0
                for line in lines:
                    if '주요 기능' in line and line.startswith('#'):
                        in_features = True
                        continue
                    elif in_features and line.startswith('#'):
                        break
                    elif in_features and line.strip() and feature_count < 3:
                        print(f"  {line.strip()}")
                        feature_count += 1
        except:
            pass

        # file_directory.md 확인 및 구조 표시
        try:
            file_dir = h_read('file_directory.md')
            if file_dir['ok']:
                file_dir_exists = True
                lines = file_dir['data'].split('\n')

                # 통계 정보
                print("\n📁 파일 구조 통계")
                print("=" * 60)

                for line in lines[:20]:
                    if '총 파일 수:' in line:
                        print(f"  {line.strip()}")
                    elif '총 디렉토리 수:' in line:
                        print(f"  {line.strip()}")

                # 디렉토리 트리 표시
                print("\n📂 프로젝트 구조")
                print("=" * 60)

                tree_lines = []
                i = 0

                while i < len(lines):
                    line = lines[i]

                    # 디렉토리 트리 섹션 찾기
                    if '디렉토리 트리' in line:
                        # ``` 코드 블록 시작 찾기
                        for j in range(i+1, min(i+5, len(lines))):
                            if lines[j].strip() == '```':
                                # 코드 블록 내용 수집
                                for k in range(j+1, len(lines)):
                                    if lines[k].strip() == '```':
                                        i = k  # 루프 인덱스 업데이트
                                        break
                                    else:
                                        tree_lines.append(lines[k].rstrip())
                                break
                        break
                    i += 1

                # 트리 출력 (전체)
                for line in tree_lines:
                    print(line)

                # 주요 파일 찾기
                print("\n📌 주요 파일")
                print("-" * 60)

                # 진입점 파일 찾기
                entry_points = ['main.py', 'index.js', 'index.ts', 'app.py', 'server.js', 
                              'server.py', '__main__.py', 'run.py', 'json_repl_session.py']
                config_files = ['config.py', 'settings.py', 'package.json', 'pyproject.toml',
                              'requirements.txt', 'setup.py', 'tsconfig.json']
                important_files = ['README.md', 'readme.md', 'LICENSE', '.gitignore']

                found_files = []

                # file_directory.md에서 파일 찾기
                for line in lines:
                    # 진입점 파일
                    for entry in entry_points:
                        if entry in line and ('│' in line or '├' in line or '└' in line):
                            file_entry = f"  🎯 진입점: {entry}"
                            if file_entry not in found_files:
                                found_files.append(file_entry)

                    # 설정 파일
                    for config in config_files:
                        if config in line and ('│' in line or '├' in line or '└' in line):
                            file_entry = f"  ⚙️ 설정: {config}"
                            if file_entry not in found_files:
                                found_files.append(file_entry)

                    # 중요 파일
                    for imp_file in important_files:
                        if imp_file in line and ('│' in line or '├' in line or '└' in line):
                            file_entry = f"  📋 문서: {imp_file}"
                            if file_entry not in found_files:
                                found_files.append(file_entry)

                # 출력 (모든 찾은 파일)
                for file in found_files:
                    print(file)

            else:
                # file_directory.md가 없을 때 직접 스캔
                _show_direct_structure()

        except Exception as e:
            # 오류 시 직접 스캔
            _show_direct_structure()

        # 문서 존재 여부 표시
        if readme_exists or file_dir_exists:
            print("\n📚 프로젝트 문서:")
            if readme_exists:
                print("  - readme.md ✅")
            if file_dir_exists:
                print("  - file_directory.md ✅")
            print("  💡 팁: /a 명령어로 문서를 업데이트할 수 있습니다.")
        else:
            print("\n💡 팁: /a 명령어로 프로젝트 문서를 생성할 수 있습니다.")

    except Exception as e:
        # 조용히 실패
        pass
def _show_direct_structure():
    """file_directory.md가 없을 때 직접 디렉토리 구조 표시"""
    try:
        from pathlib import Path

        print("\n📂 프로젝트 구조")
        print("=" * 60)

        def show_tree(path, prefix="", is_last=True, level=0, max_level=3):
            """디렉토리 트리를 재귀적으로 표시"""
            if level > max_level:
                return

            # 현재 디렉토리의 항목들
            try:
                items = sorted(os.listdir(path))
                # 숨김 파일과 특정 폴더 제외
                items = [item for item in items 
                        if not item.startswith('.') 
                        and item not in ['node_modules', '__pycache__', 'venv', 'dist', 'build']]

                dirs = [item for item in items if os.path.isdir(os.path.join(path, item))]
                files = [item for item in items if os.path.isfile(os.path.join(path, item))]

                # 디렉토리 먼저, 파일 나중에
                all_items = dirs + files

                for i, item in enumerate(all_items):
                    is_last_item = (i == len(all_items) - 1)
                    item_path = os.path.join(path, item)

                    # 트리 문자 선택
                    if is_last_item:
                        print(prefix + "└── ", end="")
                        new_prefix = prefix + "    "
                    else:
                        print(prefix + "├── ", end="")
                        new_prefix = prefix + "│   "

                    # 아이템 표시
                    if os.path.isdir(item_path):
                        print(f"📂 {item}/")
                        # 재귀적으로 하위 디렉토리 표시
                        show_tree(item_path, new_prefix, is_last_item, level + 1, max_level)
                    else:
                        # 파일 아이콘 선택
                        if item.endswith('.py'):
                            icon = "🐍"
                        elif item.endswith(('.js', '.ts', '.jsx', '.tsx')):
                            icon = "📜"
                        elif item.endswith('.json'):
                            icon = "📋"
                        elif item.endswith('.md'):
                            icon = "📝"
                        else:
                            icon = "📄"
                        print(f"{icon} {item}")

            except PermissionError:
                pass

        # 프로젝트 이름 표시
        current = get_current_project()
        project_name = 'unknown'
        if current and current.get('ok'):
            project_name = current.get('data', {}).get('name', 'unknown')
        print(f"{project_name}/")

        # 트리 표시 (3단계 깊이까지)
        show_tree(".", "", True, 0, 3)

        # 주요 파일 찾기
        print("\n📌 주요 파일")
        print("-" * 60)

        # 루트 디렉토리의 주요 파일들
        entry_points = ['main.py', 'index.js', 'index.ts', 'app.py', 'server.js']
        config_files = ['package.json', 'requirements.txt', 'pyproject.toml']

        for file in entry_points:
            if os.path.exists(file):
                print(f"  🎯 진입점: {file}")

        for file in config_files:
            if os.path.exists(file):
                print(f"  ⚙️ 설정: {file}")

    except Exception as e:
        print(f"  디렉토리 구조를 읽을 수 없습니다: {e}")
def show_help() -> None:
    """도움말 표시"""
    print("""
🚀 극단순 Flow 명령어 시스템
==========================

기본 명령어:
  h.flow()                    # 현재 상태 표시
  h.flow("/list")            # Plan 목록 보기
  h.flow("/create 계획이름")  # 새 Plan 생성
  h.flow("/select plan_id")  # Plan 선택
  h.flow("/delete plan_id")  # Plan 삭제

Task 명령어:
  h.flow("/task")            # 현재 Plan의 Task 목록
  h.flow("/task add 작업명")  # Task 추가
  h.flow("/task done task_id") # Task 완료 처리
  h.flow("/task progress task_id") # Task 진행중 처리

프로젝트:
  h.flow("/project")         # 현재 프로젝트 확인
  h.flow("/project 이름")    # 프로젝트 전환

기타:
  h.flow("/help")            # 이 도움말 표시
  h.flow("/status")          # 상태 표시

팁:
- Plan을 먼저 선택해야 Task를 추가할 수 있습니다.
- 새 Plan을 생성하면 자동으로 선택됩니다.
""")

# 별칭 함수들
def help_flow() -> None:
    """도움말 표시"""
    show_help()

# __all__ export
__all__ = ['flow', 'help_flow', 'get_manager']


def show_plan_progress() -> str:
    """
    가장 최근 Plan의 진행 상황을 요약하여 표시합니다.
    
    Returns:
        진행 상황 요약 문자열. Plan이 없으면 빈 문자열을 반환합니다.
    """
    from pathlib import Path
    import json
    from datetime import datetime
    
    try:
        # 1. 가장 최근에 수정된 Plan 디렉토리 찾기
        plans_dir = Path(".ai-brain/flow/plans")
        if not plans_dir.exists():
            return ""
            
        all_plans = [d for d in plans_dir.iterdir() if d.is_dir()]
        if not all_plans:
            return ""
            
        latest_plan_dir = max(all_plans, key=lambda p: p.stat().st_mtime)
        plan_id = latest_plan_dir.name
        
        # 2. tasks.json에서 전체 Task 수와 완료된 Task 수 집계
        tasks_file = latest_plan_dir / "tasks.json"
        total_tasks = 0
        completed_tasks = 0
        if tasks_file.exists():
            with open(tasks_file, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
                total_tasks = len(tasks_data)
                completed_tasks = sum(1 for t in tasks_data.values() if t.get('status') == 'done')
        
        # 3. 모든 .jsonl 파일에서 이벤트 수집 및 파싱
        all_events = []
        for jsonl_file in latest_plan_dir.glob("*.jsonl"):
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        # 유연한 파싱: event_type/type 필드 처리
                        if 'event_type' not in event and 'type' in event:
                            event['event_type'] = event['type']
                        all_events.append(event)
                    except json.JSONDecodeError:
                        continue  # 손상된 라인은 무시
        
        # 4. 정보 추출
        # 완료 이벤트 (최신순 정렬)
        complete_events = sorted(
            [e for e in all_events if e.get('event_type') == 'COMPLETE'],
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )
        
        # 코드 수정 이벤트
        code_events = [e for e in all_events if e.get('event_type') == 'CODE']
        modified_files = sorted(list(set(
            f"{e['file']} ({e['action']})" for e in code_events if 'file' in e and 'action' in e
        )))
        
        # 5. 출력 포맷 생성
        output_lines = [
            "\n" + "📊 Plan 진행 상황" + "\n" + "=" * 60,
            f"   Plan: {plan_id}",
            f"   진행률: {completed_tasks} / {total_tasks} Tasks 완료"
        ]
        
        if complete_events:
            output_lines.append("\n✅ 최근 완료된 작업 (최대 3개):")
            for event in complete_events[:3]:
                # summary 필드 정규화
                summary = event.get('summary', '')
                if isinstance(summary, dict):
                    summary = summary.get('summary', str(summary))
                summary_text = summary.replace('\n', ' ').strip()
                if summary_text:
                    # 첫 줄만 표시
                    first_line = summary_text.split('\n')[0]
                    output_lines.append(f"  • {first_line[:80]}")
        
        if modified_files:
            output_lines.append("\n📄 최근 작업한 파일:")
            for file_info in modified_files[:5]:
                output_lines.append(f"  • {file_info}")
        
        remaining_tasks = total_tasks - completed_tasks
        if remaining_tasks > 0:
            output_lines.append("\n💡 다음 작업:")
            output_lines.append(f"   {remaining_tasks}개의 Task가 남아있습니다. h.flow('/task') 명령으로 확인하세요.")
        
        return "\n".join(output_lines)
        
    except Exception:
        # 이 함수에서 오류가 발생해도 전체 프로세스를 중단시키지 않음
        return ""



# FlowAPI 클래스 - Manager보다 풍부한 기능 제공
class FlowAPI:
    """Flow 시스템을 위한 고급 API

    Manager의 모든 기능 + 추가 기능들:
    - Context 기반 상태 관리 (전역 변수 없음)
    - 체이닝 가능한 메서드
    - 더 상세한 필터링과 검색
    """

    def __init__(self, manager: Optional[UltraSimpleFlowManager] = None):
        """FlowAPI 초기화

        Args:
            manager: 기존 매니저 인스턴스 (없으면 새로 생성)
        """
        self.manager = manager or get_manager()
        self._current_plan_id: Optional[str] = None
        self._context: Dict[str, Any] = {}

    # Plan 관리 메서드
    def create_plan(self, name: str, description: str = "") -> Dict[str, Any]:
        """새 Plan 생성"""
        plan = self.manager.create_plan(name)
        if description:
            plan.metadata["description"] = description
        self._current_plan_id = plan.id
        return _plan_to_dict(plan)

    def select_plan(self, plan_id: str) -> "FlowAPI":
        """Plan 선택 (체이닝 가능)"""
        plan = self.manager.get_plan(plan_id)
        if plan:
            self._current_plan_id = plan_id
        else:
            raise ValueError(f"Plan {plan_id} not found")
        return self

    def get_current_plan(self) -> Optional[Dict[str, Any]]:
        """현재 선택된 Plan 정보"""
        if self.get_current_plan_id():
            plan = self.manager.get_plan(self.get_current_plan_id())
            return _plan_to_dict(plan) if plan else None
        return None

    def list_plans(self, status: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Plan 목록 조회 (필터링 가능)"""
        plans = self.manager.list_plans()
        if status:
            plans = [p for p in plans if p.status == status]
        return [_plan_to_dict(p) for p in plans[:limit]]

    def update_plan(self, plan_id: str, **kwargs) -> Dict[str, Any]:
        """Plan 정보 업데이트"""
        plan = self.manager.get_plan(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")

        # 업데이트 가능한 필드들
        if "name" in kwargs:
            plan.name = kwargs["name"]
        if "description" in kwargs:
            plan.metadata["description"] = kwargs["description"]
        if "status" in kwargs:
            plan.status = kwargs["status"]

        plan.updated_at = datetime.now().isoformat()
        self.manager.save_index()
        return _plan_to_dict(plan)

    def delete_plan(self, plan_id: str) -> bool:
        """Plan 삭제"""
        return self.manager.delete_plan(plan_id)

    # Task 관리 메서드
    def add_task(self, plan_id: str, title: str, **kwargs) -> Dict[str, Any]:
        """Task 추가 (plan_id 명시적 지정)"""
        task = self.manager.create_task(plan_id, title)

        # 추가 속성 설정
        if "description" in kwargs:
            task.description = kwargs["description"]
        if "priority" in kwargs:
            task.priority = kwargs["priority"]
        if "tags" in kwargs:
            task.tags = kwargs["tags"]

        return _task_to_dict(task)

    def get_task(self, plan_id: str, task_id: str) -> Optional[Dict[str, Any]]:
        """특정 Task 조회"""
        plan = self.manager.get_plan(plan_id)
        if plan and task_id in plan.tasks:
            return _task_to_dict(plan.tasks[task_id])
        return None

    def list_tasks(self, plan_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Task 목록 조회"""
        plan = self.manager.get_plan(plan_id)
        if not plan:
            return []

        tasks = list(plan.tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]

        return [_task_to_dict(t) for t in tasks]

    def update_task(self, plan_id: str, task_id: str, **kwargs) -> Dict[str, Any]:
        """Task 정보 업데이트"""
        plan = self.manager.get_plan(plan_id)
        if not plan or task_id not in plan.tasks:
            raise ValueError(f"Task {task_id} not found in plan {plan_id}")

        task = plan.tasks[task_id]

        # 업데이트 가능한 필드들
        if "title" in kwargs:
            task.title = kwargs["title"]
        if "status" in kwargs:
            self.manager.update_task_status(plan_id, task_id, kwargs["status"])
        if "description" in kwargs:
            task.description = kwargs["description"]
        if "priority" in kwargs:
            task.priority = kwargs["priority"]

        task.updated_at = datetime.now().isoformat()
        self.manager.save_index()
        return _task_to_dict(task)

    def start_task(self, task_id: str) -> Dict[str, Any]:
        """Task 시작 (현재 Plan 컨텍스트 사용)"""
        if not self.get_current_plan_id():
            raise ValueError("No plan selected. Use select_plan() first.")
        return self.update_task(self.get_current_plan_id(), task_id, status="in_progress")

    def complete_task(self, task_id: str) -> Dict[str, Any]:
        """Task 완료 (현재 Plan 컨텍스트 사용)"""
        if not self.get_current_plan_id():
            raise ValueError("No plan selected. Use select_plan() first.")
        return self.update_task(self.get_current_plan_id(), task_id, status="done")

    # 고급 기능
    def get_stats(self) -> Dict[str, Any]:
        """전체 통계 정보"""
        plans = self.manager.list_plans()
        total_tasks = sum(len(p.tasks) for p in plans)

        task_stats = {"todo": 0, "in_progress": 0, "done": 0}
        for plan in plans:
            for task in plan.tasks.values():
                task_stats[task.status] = task_stats.get(task.status, 0) + 1

        return {
            "total_plans": len(plans),
            "active_plans": len([p for p in plans if p.status == "active"]),
            "total_tasks": total_tasks,
            "tasks_by_status": task_stats,
            "current_plan_id": self.get_current_plan_id()
        }

    def search(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """Plan과 Task 통합 검색"""
        query_lower = query.lower()

        # Plan 검색
        plans = []
        for plan in self.manager.list_plans():
            if query_lower in plan.name.lower():
                plans.append(_plan_to_dict(plan))

        # Task 검색
        tasks = []
        for plan in self.manager.list_plans():
            for task in plan.tasks.values():
                if query_lower in task.title.lower():
                    task_dict = _task_to_dict(task)
                    task_dict["plan_id"] = plan.id
                    task_dict["plan_name"] = plan.name
                    tasks.append(task_dict)

        return {"plans": plans, "tasks": tasks}

    # Context 관리
    def set_context(self, key: str, value: Any) -> "FlowAPI":
        """컨텍스트 설정 (체이닝 가능)"""
        self._context[key] = value
        return self

    def get_context(self, key: str) -> Any:
        """컨텍스트 조회"""
        return self._context.get(key)

    def clear_context(self) -> "FlowAPI":
        """컨텍스트 초기화"""
        self._context.clear()
        self._current_plan_id = None
        return self



# FlowAPI 싱글톤 인스턴스
_flow_api_instance: Optional[FlowAPI] = None

def get_flow_api() -> FlowAPI:
    """FlowAPI 싱글톤 인스턴스 반환

    Returns:
        FlowAPI: Flow 시스템 고급 API 인스턴스
    """
    global _flow_api_instance
    if _flow_api_instance is None:
        _flow_api_instance = FlowAPI()
    return _flow_api_instance

def get_flow_api() -> FlowAPI:
    """FlowAPI 인스턴스 반환

    Returns:
        FlowAPI: Flow 시스템 고급 API

# 전역 변수 제거 - FlowAPI 기반으로 전환

    """
    return FlowAPI()


# Helper 함수들
def _plan_to_dict(plan: Plan) -> Dict[str, Any]:
    """Plan 객체를 딕셔너리로 변환"""
    return {
        "id": plan.id,
        "name": plan.name,
        "status": plan.status,
        "created_at": plan.created_at,
        "updated_at": plan.updated_at,
        "task_count": len(plan.tasks),
        "metadata": plan.metadata
    }


def _task_to_dict(task: Task) -> Dict[str, Any]:
    """Task 객체를 딕셔너리로 변환"""
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "completed_at": task.completed_at,
        "tags": task.tags,
        "metadata": task.metadata
    }
