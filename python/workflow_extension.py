"""
워크플로우 확장 명령어
/start, /plan, /task, /next, /status, /focus
"""
import json
import os
from datetime import datetime

WORKFLOW_FILE = "memory/workflow.json"

def load_data():
    if os.path.exists(WORKFLOW_FILE):
        with open(WORKFLOW_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"plans": [], "active_plan_id": None}

def save_data(data):
    os.makedirs(os.path.dirname(WORKFLOW_FILE), exist_ok=True)
    with open(WORKFLOW_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_active_plan(data):
    if not data.get("active_plan_id"):
        return None
    for plan in data["plans"]:
        if plan["id"] == data["active_plan_id"]:
            return plan
    return None

def cmd_start(*args):
    """새 플랜 시작"""
    data = load_data()
    name = " ".join(args) if args else f"플랜_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    new_plan = {
        "id": f"plan_{int(datetime.now().timestamp())}",
        "name": name,
        "status": "active",
        "tasks": [],
        "created_at": datetime.now().isoformat(),
        "metadata": {"stages": ["준비", "진행", "완료"]}
    }

    data["plans"].append(new_plan)
    data["active_plan_id"] = new_plan["id"]
    save_data(data)

    return f"✅ '{name}' 시작됨"

def cmd_plan(*args):
    """단계 설정/조회"""
    data = load_data()
    plan = get_active_plan(data)
    if not plan:
        return "❌ 활성 플랜이 없습니다"

    if not args:
        stages = plan.get("metadata", {}).get("stages", [])
        return f"📋 단계: {' → '.join(stages)}"
    else:
        plan["metadata"]["stages"] = list(args)
        save_data(data)
        return f"✅ 단계 설정: {' → '.join(args)}"

def cmd_task(action, *args):
    """작업 관리"""
    data = load_data()
    plan = get_active_plan(data)
    if not plan:
        return "❌ 활성 플랜이 없습니다"

    if action == "add":
        if not args:
            return "사용: /task add [내용]"
        desc = " ".join(args)
        task = {
            "id": f"t{len(plan['tasks']) + 1}",
            "title": desc,
            "status": "준비",
            "created_at": datetime.now().isoformat()
        }
        plan["tasks"].append(task)
        save_data(data)
        return f"✅ 작업 추가: {desc}"

    elif action == "list":
        if not plan["tasks"]:
            return "작업이 없습니다"
        lines = ["📋 작업 목록:"]
        for i, task in enumerate(plan["tasks"]):
            lines.append(f"{i+1}. [{task.get('status', '?')}] {task['title']}")
        return "\n".join(lines)

    elif action == "del":
        if not args or not args[0].isdigit():
            return "사용: /task del [번호]"
        idx = int(args[0]) - 1
        if 0 <= idx < len(plan["tasks"]):
            removed = plan["tasks"].pop(idx)
            save_data(data)
            return f"✅ 삭제: {removed['title']}"
        return "❌ 잘못된 번호"

    return "사용: /task [add|list|del]"

def cmd_next():
    """다음 작업 진행"""
    data = load_data()
    plan = get_active_plan(data)
    if not plan:
        return "❌ 활성 플랜이 없습니다"

    # 준비 상태의 첫 작업을 진행으로
    for task in plan["tasks"]:
        if task.get("status") == "준비":
            task["status"] = "진행"
            save_data(data)
            return f"▶️ 진행: {task['title']}"

    return "진행할 작업이 없습니다"

def cmd_status():
    """현황 확인"""
    data = load_data()
    plan = get_active_plan(data)
    if not plan:
        return "❌ 활성 플랜이 없습니다"

    total = len(plan["tasks"])
    done = len([t for t in plan["tasks"] if t.get("status") == "완료"])

    return f"""📊 {plan['name']}
작업: {total}개 (완료: {done}개)
진행률: {done/total*100 if total else 0:.0f}%"""

def cmd_focus(*args):
    """포커스 설정"""
    data = load_data()
    plan = get_active_plan(data)
    if not plan:
        return "❌ 활성 플랜이 없습니다"

    if not args:
        focus = plan.get("metadata", {}).get("focus", "")
        return f"포커스: {focus or '없음'}"

    focus = " ".join(args)
    plan.setdefault("metadata", {})["focus"] = focus
    save_data(data)
    return f"포커스: {focus}"

def handle_workflow_ext(command):
    """워크플로우 확장 명령어 처리"""
    parts = command.strip().split()
    if not parts:
        return ""

    cmd = parts[0]
    args = parts[1:] if len(parts) > 1 else []

    handlers = {
        "/start": lambda: cmd_start(*args),
        "/plan": lambda: cmd_plan(*args),
        "/task": lambda: cmd_task(*args) if args else "사용: /task [add|list|del]",
        "/next": lambda: cmd_next(),
        "/status": lambda: cmd_status(),
        "/focus": lambda: cmd_focus(*args)
    }

    if cmd in handlers:
        try:
            return handlers[cmd]()
        except Exception as e:
            return f"오류: {str(e)}"

    return None  # 다른 명령어는 기존 시스템으로
