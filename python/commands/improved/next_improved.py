#!/usr/bin/env python3
"""
개선된 다음 작업(Next) 진행 명령어
ProjectContext와 dict 모두 지원하는 유연한 구조
"""

import os
import json
import datetime as dt
from pathlib import Path
from typing import Dict, Any, Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from core.context_manager import get_context_manager
from plan_improved import get_plan, plan_to_dict
from task_improved import get_current_task, set_current_task, get_tasks


def cmd_next() -> None:
    """/next 명령어 - 다음 작업으로 진행"""
    context = get_context_manager().context
    if not context:
        print("❌ 프로젝트가 선택되지 않았습니다.")
        return
    
    # 현재 작업 확인
    current_task_id = get_current_task(context)
    if current_task_id:
        print(f"⚠️ 현재 작업 [{current_task_id}]이 진행 중입니다.")
        print("   먼저 'task done'으로 현재 작업을 완료하세요.")
        return
    
    # 계획 확인
    plan = get_plan(context)
    if not plan:
        print("❌ 계획이 없습니다. 먼저 'plan <계획명>'으로 새 계획을 생성하세요.")
        return
    
    plan_dict = plan_to_dict(plan)
    
    # 작업 큐 확인
    tasks = get_tasks(context)
    next_tasks = []
    
    if hasattr(context, 'tasks') and 'next' in context.tasks:
        next_tasks = context.tasks['next']
    elif isinstance(context, dict) and 'tasks' in context and 'next' in context['tasks']:
        next_tasks = context['tasks']['next']
    
    if not next_tasks:
        print("❌ 대기 중인 작업이 없습니다.")
        print("   'task add phase-id \"작업명\"'으로 새 작업을 추가하세요.")
        
        # 미완료 작업 찾기
        pending_tasks = []
        for phase_id, phase in plan_dict['phases'].items():
            for task in phase['tasks']:
                if task['status'] in ['pending', 'blocked']:
                    pending_tasks.append({
                        'id': task['id'],
                        'phase': phase_id,
                        'title': task['title'],
                        'status': task['status']
                    })
        
        if pending_tasks:
            print("\n📋 미완료 작업 목록:")
            for task in pending_tasks:
                status = "🚫" if task['status'] == 'blocked' else "⏳"
                print(f"   {status} [{task['id']}] {task['title']}")
        
        return
    
    # 다음 작업 선택
    next_task_info = next_tasks[0]
    task_id = next_task_info['id']
    phase_id = next_task_info['phase']
    
    # Plan에서 작업 찾기
    task_found = False
    for p_id, phase in plan_dict['phases'].items():
        if p_id == phase_id:
            for task in phase['tasks']:
                if task['id'] == task_id:
                    # 작업 상태 업데이트
                    task['status'] = 'in_progress'
                    task['started_at'] = dt.datetime.now().isoformat()
                    task['updated_at'] = dt.datetime.now().isoformat()
                    
                    # Phase 상태 업데이트
                    if phase['status'] == 'pending':
                        phase['status'] = 'in_progress'
                    
                    # 현재 작업 설정
                    set_current_task(context, task_id)
                    
                    # 현재 phase 업데이트
                    plan_dict['current_phase'] = phase_id
                    plan_dict['current_task'] = task_id
                    plan_dict['updated_at'] = dt.datetime.now().isoformat()
                    
                    task_found = True
                    
                    print(f"\n🚀 작업 시작: [{task['id']}] {task['title']}")
                    print(f"   Phase: {phase['name']}")
                    if task.get('description'):
                        print(f"   설명: {task['description']}")
                    
                    # 작업 브리핑
                    print("\n📋 작업 브리핑:")
                    print(f"   1. 작업 ID: {task['id']}")
                    print(f"   2. 제목: {task['title']}")
                    print(f"   3. Phase: {phase['name']}")
                    
                    # 관련 파일 표시 (있을 경우)
                    if task.get('related_files'):
                        print(f"\n📁 관련 파일:")
                        for file in task['related_files']:
                            print(f"   - {file}")
                    
                    # 서브태스크 표시 (있을 경우)
                    if task.get('subtasks'):
                        print(f"\n📌 서브태스크:")
                        for i, subtask in enumerate(task['subtasks'], 1):
                            print(f"   {i}. {subtask}")
                    
                    print("\n💡 작업 완료 후 'task done'을 실행하세요.")
                    
                    break
            if task_found:
                break
    
    if not task_found:
        print(f"❌ 작업 [{task_id}]를 계획에서 찾을 수 없습니다.")
        # next 큐에서 제거
        if hasattr(context, 'tasks'):
            context.tasks['next'] = next_tasks[1:]
        elif isinstance(context, dict):
            context['tasks']['next'] = next_tasks[1:]
        print("   작업 큐에서 제거하고 다음 작업을 확인하세요.")
        return
    
    # 변경사항 저장
    from plan_improved import set_plan
    set_plan(context, plan_dict)
    
    # Phase 변경 (metadata 사용)
    if hasattr(context, 'metadata'):
        if not context.metadata:
            context.metadata = {}
        context.metadata['phase'] = 'development'
    
    # 작업 추적 시작
    if hasattr(context, 'work_tracking'):
        if hasattr(context.work_tracking, 'current_task_work'):
            context.work_tracking.current_task_work = {
                'task_id': task_id,
                'start_time': dt.datetime.now().isoformat(),
                'files_accessed': [],
                'functions_edited': [],
                'operations': []
            }
    elif isinstance(context, dict):
        if 'work_tracking' not in context:
            context['work_tracking'] = {}
        context['work_tracking']['current_task_work'] = {
            'task_id': task_id,
            'start_time': dt.datetime.now().isoformat(),
            'files_accessed': [],
            'functions_edited': [],
            'operations': []
        }
    
    get_context_manager().save()
    
    # 남은 작업 수 표시
    remaining_tasks = len(next_tasks) - 1
    if remaining_tasks > 0:
        print(f"\n📊 대기 중인 작업: {remaining_tasks}개")


if __name__ == "__main__":
    cmd_next()
