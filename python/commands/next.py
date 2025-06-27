#!/usr/bin/env python3
"""
개선된 다음 작업(Next) 진행 명령어
ProjectContext와 dict 모두 지원하는 유연한 구조
"""

import os
import json
import datetime as dt
from pathlib import Path
from typing import Dict, Any, Optional, List

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.context_manager import get_context_manager
from commands.plan import get_plan, plan_to_dict
from commands.task import get_current_task, set_current_task, get_tasks
from core.workflow_manager import get_workflow_manager
from core.error_handler import StandardResponse


def sync_task_queue_with_plan(context, plan_dict: Dict) -> None:
    """작업 큐를 현재 계획과 동기화"""
    tasks = get_tasks(context)
    if not tasks or 'next' not in tasks:
        return
    
    # 현재 계획의 모든 작업 ID 수집
    valid_task_ids = set()
    for phase_id, phase in plan_dict.get('phases', {}).items():
        for task in phase.get('tasks', []):
            if task.get('status') in ['pending', 'blocked']:
                valid_task_ids.add(task['id'])
    
    # 작업 큐 정리 - 현재 계획에 없는 작업 제거
    if hasattr(context, 'tasks'):
        old_count = len(context.tasks.get('next', []))
        context.tasks['next'] = [
            task for task in context.tasks.get('next', [])
            if task.get('id') in valid_task_ids
        ]
        removed = old_count - len(context.tasks.get('next', []))
        if removed > 0:
            print(f"  🧹 현재 계획과 맞지 않는 작업 {removed}개 제거")
    elif isinstance(context, dict) and 'tasks' in context:
        old_count = len(context['tasks'].get('next', []))
        context['tasks']['next'] = [
            task for task in context['tasks'].get('next', [])
            if task.get('id') in valid_task_ids
        ]
        removed = old_count - len(context['tasks'].get('next', []))
        if removed > 0:
            print(f"  🧹 현재 계획과 맞지 않는 작업 {removed}개 제거")


def sort_tasks_by_priority_and_dependencies(tasks: List[Dict], plan_dict: Dict) -> List[Dict]:
    """작업을 우선순위와 의존성에 따라 정렬"""
    # 작업 정보를 Plan에서 가져와 우선순위 정보 추가
    enriched_tasks = []
    for task_info in tasks:
        task_id = task_info['id']
        phase_id = task_info.get('phase')
        
        # Plan에서 작업 찾기
        task_data = None
        if phase_id and phase_id in plan_dict.get('phases', {}):
            phase = plan_dict['phases'][phase_id]
            for t in phase.get('tasks', []):
                if t['id'] == task_id:
                    task_data = t
                    break
        
        if task_data:
            # 우선순위와 의존성 정보 추가
            priority = task_data.get('priority', 'medium')
            dependencies = task_data.get('dependencies', [])
            
            # 의존성 체크 - 모든 의존 작업이 완료되었는지 확인
            blocked = False
            if dependencies:
                for dep_id in dependencies:
                    # 의존 작업이 완료되지 않았는지 확인
                    dep_completed = False
                    for p_id, p in plan_dict.get('phases', {}).items():
                        for t in p.get('tasks', []):
                            if t['id'] == dep_id and t.get('status') == 'completed':
                                dep_completed = True
                                break
                        if dep_completed:
                            break
                    
                    if not dep_completed:
                        blocked = True
                        break
            
            enriched_tasks.append({
                **task_info,
                'priority': priority,
                'priority_value': {'high': 3, 'medium': 2, 'low': 1}.get(priority, 2),
                'dependencies': dependencies,
                'blocked': blocked
            })
        else:
            # 기본값 사용
            enriched_tasks.append({
                **task_info,
                'priority': 'medium',
                'priority_value': 2,
                'dependencies': [],
                'blocked': False
            })
    
    # 정렬: 1) blocked 여부, 2) 우선순위, 3) 생성 시간
    sorted_tasks = sorted(
        enriched_tasks,
        key=lambda x: (x['blocked'], -x['priority_value'])
    )
    
    return sorted_tasks


def cmd_next() -> StandardResponse:
    """다음 작업을 시작합니다.
    
    Returns:
        StandardResponse: 표준 응답 형식
    """
    wm = get_workflow_manager()
    
    # WorkflowManager가 모든 복잡한 로직을 처리
    result = wm.start_next_task()
    
    if result['success']:
        data = result['data']
        
        # 상태별 처리
        if data.get('status') == 'no_tasks':
            print("\n📋 대기 중인 작업이 없습니다.")
            print("\n💡 다음 옵션:")
            print("   1. 'task add phase-id \"작업명\"'으로 새 작업 추가")
            print("   2. 'plan'으로 전체 계획 확인")
            
        elif data.get('status') == 'blocked':
            print(f"\n⚠️  {data['message']}")
            
            # 차단된 작업 상세 정보 표시
            bottlenecks = wm.get_bottlenecks()
            if bottlenecks:
                print("\n🔒 차단된 작업들:")
                for task_id, deps in bottlenecks.items():
                    print(f"   - [{task_id}]: {', '.join(deps)} 완료 대기 중")
                    
        elif data.get('status') == 'started':
            task = data['task']
            print(f"\n✅ 작업 시작: [{task.task_id}] {task.name}")
            
            if task.description:
                print(f"\n📝 설명: {task.description}")
                
            # 작업 브리핑 표시
            briefing = data.get('briefing', {})
            if briefing:
                print("\n" + "="*60)
                print("📋 작업 브리핑")
                print("="*60)
                
                for key, value in briefing.items():
                    if value:
                        print(f"\n{key}:")
                        print(value)
                        
            # 워크플로우 상태 표시
            status = wm.get_workflow_status()
            print(f"\n📊 전체 진행률: {status['progress']:.1f}%")
            print(f"   Phase {status['current_phase']}: {status['phase_progress']:.1f}% 완료")
    
    return result
if __name__ == "__main__":
    cmd_next()
