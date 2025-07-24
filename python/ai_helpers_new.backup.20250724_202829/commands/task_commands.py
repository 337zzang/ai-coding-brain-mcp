"""
Task 관련 명령어
"""
from typing import List, Dict, Any
from .router import command


@command('task', 't', description='Task 추가')
def task_command(manager, args: List[str]) -> Dict[str, Any]:
    """Task 추가"""
    if len(args) < 2:
        return {'ok': False, 'error': '사용법: task <plan_id> <task_name>'}

    plan_id = args[0]
    task_name = ' '.join(args[1:])

    try:
        task_id = manager.add_task(plan_id, task_name)
        return {'ok': True, 'message': f"Task 생성: {task_name}", 'task_id': task_id}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


@command('start', description='Task 시작')
def start_task(manager, args: List[str]) -> Dict[str, Any]:
    """Task 시작"""
    if not args:
        return {'ok': False, 'error': 'Task ID가 필요합니다'}

    task_id = args[0]
    success = manager.start_task(task_id)

    if success:
        return {'ok': True, 'message': f"Task 시작: {task_id}"}
    else:
        return {'ok': False, 'error': f"Task를 찾을 수 없습니다: {task_id}"}


@command('complete', 'done', description='Task 완료')
def complete_task(manager, args: List[str]) -> Dict[str, Any]:
    """Task 완료"""
    if not args:
        return {'ok': False, 'error': 'Task ID가 필요합니다'}

    task_id = args[0]
    message = ' '.join(args[1:]) if len(args) > 1 else ""

    success = manager.complete_task(task_id, message)

    if success:
        msg = f"Task 완료: {task_id}"
        if message:
            msg += f" ({message})"
        return {'ok': True, 'message': msg}
    else:
        return {'ok': False, 'error': f"Task를 찾을 수 없습니다: {task_id}"}


@command('tasks', description='Task 목록')
def list_tasks(manager, args: List[str]) -> Dict[str, Any]:
    """Task 목록"""
    if not args:
        # 전체 Task 목록
        current = manager.get_current_flow()
        if not current:
            return {'ok': False, 'error': 'Flow를 먼저 선택하세요'}

        lines = [f"📋 {current.name}의 전체 Task", "=" * 60]

        plans = manager.get_plans()
        for plan in plans:
            lines.append(f"\n📌 Plan: {plan['name']}")
            tasks = manager.get_tasks(plan['id'])

            if not tasks:
                lines.append("   (Task 없음)")
            else:
                for task in tasks:
                    status_icon = {
                        'todo': '⬜',
                        'doing': '🔄',
                        'done': '✅'
                    }.get(task['status'], '❓')

                    lines.append(f"   {status_icon} {task['name']}")
                    lines.append(f"      ID: {task['id']}")
                    if task['started']:
                        lines.append(f"      시작: {task['started'][:19]}")
                    if task['completed']:
                        lines.append(f"      완료: {task['completed'][:19]}")

        return {'ok': True, 'message': '\n'.join(lines)}

    else:
        # 특정 Plan의 Task 목록
        plan_id = args[0]
        tasks = manager.get_tasks(plan_id)

        if not tasks:
            return {'ok': True, 'message': f"Plan {plan_id}에 Task가 없습니다"}

        lines = [f"Plan {plan_id}의 Task 목록:", "-" * 40]

        for i, task in enumerate(tasks, 1):
            status_icon = {
                'todo': '⬜',
                'doing': '🔄', 
                'done': '✅'
            }.get(task['status'], '❓')

            lines.append(f"{i}. {status_icon} {task['name']}")
            lines.append(f"   ID: {task['id']}")

        return {'ok': True, 'message': '\n'.join(lines)}


@command('note', description='Task에 노트 추가')
def add_note(manager, args: List[str]) -> Dict[str, Any]:
    """Task에 노트 추가"""
    if len(args) < 2:
        return {'ok': False, 'error': '사용법: note <task_id> <note_content>'}

    task_id = args[0]
    note = ' '.join(args[1:])

    success = manager.add_task_note(task_id, note)

    if success:
        return {'ok': True, 'message': f"노트 추가됨: {task_id}"}
    else:
        return {'ok': False, 'error': f"Task를 찾을 수 없습니다: {task_id}"}


@command('search', description='Task 검색')
def search_tasks(manager, args: List[str]) -> Dict[str, Any]:
    """Task 검색"""
    if not args:
        return {'ok': False, 'error': '검색어가 필요합니다'}

    query = ' '.join(args)
    results = manager.search_tasks(query)

    if not results:
        return {'ok': True, 'message': f"'{query}'에 대한 검색 결과가 없습니다"}

    lines = [f"🔍 '{query}' 검색 결과: {len(results)}개", "=" * 60]

    for flow_id, plan_id, task in results:
        status_icon = {
            'todo': '⬜',
            'doing': '🔄',
            'done': '✅'
        }.get(task.status.value, '❓')

        lines.append(f"{status_icon} {task.name}")
        lines.append(f"   Task ID: {task.id}")
        lines.append(f"   Flow: {flow_id}")
        lines.append(f"   Plan: {plan_id}")
        lines.append("")

    return {'ok': True, 'message': '\n'.join(lines)}
