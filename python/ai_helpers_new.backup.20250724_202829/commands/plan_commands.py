"""
Plan 관련 명령어
"""
from typing import List, Dict, Any
from .router import command


@command('plan', 'p', description='Plan 추가/목록')
def plan_command(manager, args: List[str]) -> Dict[str, Any]:
    """Plan 명령어 처리"""
    current = manager.get_current_flow()
    if not current:
        return {'ok': False, 'error': 'Flow를 먼저 선택하세요'}

    if not args:
        # Plan 목록
        plans = manager.get_plans()
        if not plans:
            return {'ok': True, 'message': 'Plan이 없습니다'}

        lines = [f"📋 {current.name}의 Plan 목록:", "-" * 40]
        for i, plan in enumerate(plans, 1):
            status = "✅" if plan['status'] == 'completed' else "⏳"
            progress = f"{plan['completed_tasks']}/{plan['tasks']}"
            lines.append(f"{i}. {status} {plan['name']} ({progress} tasks)")

        return {'ok': True, 'message': '\n'.join(lines)}

    # Plan 추가
    if args[0] in ['add', 'new', 'create']:
        if len(args) < 2:
            return {'ok': False, 'error': 'Plan 이름이 필요합니다'}

        name = ' '.join(args[1:])
        plan_id = manager.add_plan(name)
        return {'ok': True, 'message': f"Plan 생성: {name}", 'plan_id': plan_id}

    # Plan 완료
    if args[0] in ['complete', 'done']:
        if len(args) < 2:
            return {'ok': False, 'error': 'Plan ID가 필요합니다'}

        plan_id = args[1]
        success = manager.complete_plan(plan_id)
        if success:
            return {'ok': True, 'message': f"Plan 완료: {plan_id}"}
        else:
            return {'ok': False, 'error': f"Plan 완료 실패: {plan_id}"}

    return {'ok': False, 'error': f"알 수 없는 Plan 명령: {args[0]}"}


@command('plans', description='전체 Plan 목록')
def list_plans(manager, args: List[str]) -> Dict[str, Any]:
    """전체 Plan 목록"""
    current = manager.get_current_flow()
    if not current:
        return {'ok': False, 'error': 'Flow를 먼저 선택하세요'}

    plans = manager.get_plans()
    if not plans:
        return {'ok': True, 'message': 'Plan이 없습니다'}

    lines = [f"📋 {current.name}의 전체 Plan", "=" * 60]

    for plan in plans:
        status = "✅ 완료" if plan['status'] == 'completed' else "⏳ 진행중"
        lines.append(f"📌 {plan['name']} [{status}]")
        lines.append(f"   ID: {plan['id']}")
        lines.append(f"   Tasks: {plan['completed_tasks']}/{plan['tasks']} 완료")
        lines.append("")

    return {'ok': True, 'message': '\n'.join(lines)}
