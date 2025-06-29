#!/usr/bin/env python3
"""
개선된 작업(Task) 관리 명령어
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
from plan_improved import get_plan, set_plan, plan_to_dict


def get_current_task(context) -> Optional[str]:
    """현재 작업 ID 가져오기"""
    if hasattr(context, 'current_task'):
        return context.current_task
    elif isinstance(context, dict):
        return context.get('current_task')
    return None


def set_current_task(context, task_id: Optional[str]):
    """현재 작업 설정"""
    if hasattr(context, 'current_task'):
        context.current_task = task_id
    elif isinstance(context, dict):
        context['current_task'] = task_id


def get_tasks(context) -> Dict[str, List]:
    """작업 목록 가져오기"""
    if hasattr(context, 'tasks'):
        return context.tasks
    elif isinstance(context, dict):
        return context.get('tasks', {})
    return {}


def update_plan_in_context(context, plan_dict: Dict):
    """수정된 plan을 context에 반영"""
    return set_plan(context, plan_dict)


def cmd_task(action: str, *args) -> None:
    """/task 명령어 - 작업 관리"""
    context = get_context_manager().context
    if not context:
        print("❌ 프로젝트가 선택되지 않았습니다.")
        return
    
    plan = get_plan(context)
    if not plan:
        print("❌ 계획이 없습니다. 먼저 'plan <계획명>'으로 새 계획을 생성하세요.")
        return
    
    # Plan을 dict로 변환하여 일관된 처리
    plan_dict = plan_to_dict(plan)
    
    if action == 'add':
        if len(args) < 2:
            print("사용법: task add [phase-id] [작업명] [설명(선택)]")
            return
        
        phase_id = args[0]
        task_title = args[1]
        task_desc = ' '.join(args[2:]) if len(args) > 2 else ""
        
        # Context Manager의 새로운 메서드 사용
        context_manager = get_context_manager()
        task = context_manager.add_task_to_plan(phase_id, task_title, task_desc)
        
        if task:
            print(f"✅ 작업 추가됨: [{task.id}] {task.title}")
            if task.description:
                print(f"   설명: {task.description}")
            
            # Phase 정보 표시
            phase = context_manager.context.plan.phases.get(phase_id)
            if phase:
                print(f"   Phase: {phase.name}")
                print(f"   Phase 내 작업 수: {len(phase.tasks)}")
        else:
            print(f"❌ 작업 추가 실패")
            if phase_id not in context_manager.context.plan.phases:
                print(f"   Phase '{phase_id}'를 찾을 수 없습니다.")
                print(f"   사용 가능한 Phase: {', '.join(context_manager.context.plan.phases.keys())}")
    
    elif action == 'done':
        if len(args) < 1:
            # 현재 작업을 완료
            current_task_id = get_current_task(context)
            if not current_task_id:
                print("사용법: task done [task-id]")
                print("   또는 현재 작업이 있을 때: task done")
                return
            task_id = current_task_id
        else:
            task_id = args[0]
        
        task_found = False
        for phase_id, phase in plan_dict['phases'].items():
            for task in phase['tasks']:
                if task['id'] == task_id:
                    if task['status'] == 'completed':
                        print(f"⚠️ Task [{task_id}]는 이미 완료되었습니다.")
                        return
                    
                    # 작업을 완료로 표시
                    task['status'] = 'completed'
                    task['completed_at'] = dt.datetime.now().isoformat()
                    task['updated_at'] = dt.datetime.now().isoformat()
                    
                    # 현재 작업이었다면 해제
                    if get_current_task(context) == task_id:
                        set_current_task(context, None)
                    
                    # tasks 목록 업데이트
                    tasks = get_tasks(context)
                    
                    # next에서 done으로 이동
                    if hasattr(context, 'tasks'):
                        next_tasks = context.tasks.get('next', [])
                        done_tasks = context.tasks.setdefault('done', [])
                        
                        # next에서 제거
                        context.tasks['next'] = [t for t in next_tasks if t.get('id') != task_id]
                        
                        # done에 추가
                        done_tasks.append({
                            'id': task_id,
                            'phase': phase_id,
                            'title': task['title'],
                            'completed_at': task['completed_at']
                        })
                    
                    task_found = True
                    plan_dict['updated_at'] = dt.datetime.now().isoformat()
                    
                    # 변경사항 저장
                    update_plan_in_context(context, plan_dict)
                    get_context_manager().save()
                    
                    print(f"✅ Task [{task_id}] {task['title']} 완료!")
                    
                    # Phase의 모든 작업이 완료되었는지 확인
                    all_completed = all(t['status'] == 'completed' for t in phase['tasks'])
                    if all_completed and phase['tasks']:
                        phase['status'] = 'completed'
                        print(f"🎉 {phase['name']} 완료!")
                    
                    break
            if task_found:
                break
        
        if not task_found:
            print(f"❌ Task '{task_id}'를 찾을 수 없습니다.")
    
    elif action == 'list':
        print(f"\n📋 계획: {plan_dict['name']}")
        
        # 진행률 계산
        total_tasks = sum(len(phase['tasks']) for phase in plan_dict['phases'].values())
        completed_tasks = sum(
            sum(1 for t in phase['tasks'] if t.get('status') == 'completed')
            for phase in plan_dict['phases'].values()
        )
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        print(f"진행률: {progress:.1f}% ({completed_tasks}/{total_tasks})")
        
        # 현재 작업 표시
        current_task_id = get_current_task(context)
        if current_task_id:
            print(f"현재 작업: [{current_task_id}]")
        
        print("\n전체 Task 목록:")
        
        for phase_id, phase in plan_dict['phases'].items():
            tasks = phase['tasks']
            completed = sum(1 for t in tasks if t.get('status') == 'completed')
            
            status_emoji = "✅" if phase.get('status') == 'completed' else "🔄" if phase.get('status') == 'in_progress' else "⏳"
            print(f"\n{status_emoji} {phase['name']} ({completed}/{len(tasks)} 완료)")
            
            if phase.get('description'):
                print(f"   📝 {phase['description']}")
            
            for task in tasks:
                task_emoji = "✅" if task['status'] == 'completed' else "🔄" if task['status'] == 'in_progress' else "🚫" if task['status'] == 'blocked' else "⏳"
                current = " 👈 현재" if current_task_id == task['id'] else ""
                print(f"   {task_emoji} [{task['id']}] {task['title']}{current}")
                if task.get('description'):
                    print(f"      📝 {task['description']}")
        
        # 작업 큐 상태
        tasks = get_tasks(context)
        if tasks:
            print(f"\n📊 작업 큐:")
            print(f"   - 대기: {len(tasks.get('next', []))}개")
            print(f"   - 완료: {len(tasks.get('done', []))}개")
    
    elif action == 'current':
        current_task_id = get_current_task(context)
        if not current_task_id:
            print("❌ 현재 진행 중인 작업이 없습니다.")
            return
        
        # 현재 작업 찾기
        for phase_id, phase in plan_dict['phases'].items():
            for task in phase['tasks']:
                if task['id'] == current_task_id:
                    print(f"\n🔄 현재 작업: [{task['id']}] {task['title']}")
                    print(f"   Phase: {phase['name']}")
                    if task.get('description'):
                        print(f"   설명: {task['description']}")
                    print(f"   상태: {task['status']}")
                    print(f"   시작: {task.get('created_at', 'N/A')}")
                    return
        
        print(f"⚠️ 현재 작업 ID [{current_task_id}]를 찾을 수 없습니다.")
    
    else:
        print(f"❌ 알 수 없는 액션: {action}")
        print("사용 가능한 액션: add, done, list, current")
        print("\n사용 예시:")
        print("  task add phase-1 \"작업명\" \"설명\"")
        print("  task done [task-id]")
        print("  task list")
        print("  task current")


if __name__ == "__main__":
    # 명령줄 인자 처리
    import sys
    if len(sys.argv) > 1:
        action = sys.argv[1]
        args = sys.argv[2:]
        cmd_task(action, *args)
    else:
        cmd_task('list')
