"""Plan 자동 완료 기능"""
import json
from typing import Dict, Any
from datetime import datetime

def check_and_complete_plan(flow_id: str, plan_id: str) -> bool:
    """Plan의 모든 Task가 완료되었는지 확인하고 자동 완료 처리

    Args:
        flow_id: Flow ID
        plan_id: Plan ID

    Returns:
        bool: Plan이 자동 완료되었는지 여부
    """
    try:
        # flows.json 읽기
        with open(".ai-brain/flows.json", 'r') as f:
            flows_data = json.load(f)

        # Flow와 Plan 찾기
        flow = flows_data.get('flows', {}).get(flow_id)
        if not flow:
            return False

        plan = flow.get('plans', {}).get(plan_id)
        if not plan:
            return False

        # 이미 완료된 Plan은 스킵
        if plan.get('completed', False):
            return False

        # Task 목록 확인
        tasks = plan.get('tasks', {})
        if not tasks:
            return False

        # 모든 Task가 completed 상태인지 확인 (reviewing은 미완료)
        all_completed = all(
            task.get('status') == 'completed'
            for task in tasks.values()
            if isinstance(task, dict)
        )

        if all_completed:
            # Plan 완료 처리
            plan['completed'] = True
            plan['completed_at'] = datetime.now().isoformat()

            # 파일에 저장
            with open(".ai-brain/flows.json", 'w') as f:
                json.dump(flows_data, f, indent=2, default=str)

            print(f"Plan '{plan.get('name', plan_id)}' 자동 완료! 모든 Task가 완료되었습니다.")

            # Context 기록 (선택적)
            try:
                context_file = f".ai-brain/contexts/{flow_id}.json"
                import os
                if os.path.exists(context_file):
                    with open(context_file, 'r') as f:
                        context = json.load(f)

                    if 'events' not in context:
                        context['events'] = []

                    context['events'].append({
                        'type': 'plan_auto_completed',
                        'plan_id': plan_id,
                        'plan_name': plan.get('name'),
                        'timestamp': datetime.now().isoformat()
                    })

                    with open(context_file, 'w') as f:
                        json.dump(context, f, indent=2)
            except:
                pass  # Context 기록 실패는 무시

            return True

        return False

    except Exception as e:
        print(f"Plan 자동 완료 체크 중 오류: {e}")
        return False

def check_plan_after_task_complete(task_id: str) -> bool:
    """Task 완료 후 해당 Plan 자동 완료 체크

    Args:
        task_id: 완료된 Task ID

    Returns:
        bool: Plan이 자동 완료되었는지 여부
    """
    try:
        # flows.json 읽기
        with open(".ai-brain/flows.json", 'r') as f:
            flows_data = json.load(f)

        # Task가 속한 Flow와 Plan 찾기
        for flow_id, flow in flows_data.get('flows', {}).items():
            for plan_id, plan in flow.get('plans', {}).items():
                tasks = plan.get('tasks', {})
                if task_id in tasks:
                    # Task 상태가 completed인지 확인
                    task = tasks[task_id]
                    if task.get('status') == 'completed':
                        # Plan 자동 완료 체크
                        return check_and_complete_plan(flow_id, plan_id)
                    return False

        return False

    except Exception as e:
        print(f"Task 완료 후 Plan 체크 중 오류: {e}")
        return False
