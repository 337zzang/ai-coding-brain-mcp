#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NEXT Command - AI Coding Brain MCP
/next 명령어 처리

작성일: 2025-06-20
"""

import os
import json
import datetime as dt
from pathlib import Path
from typing import Dict, Any, Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.context_manager import get_context_manager
from core.config import get_paths_from_config

# ===========================================
# NEXT 명령어
# ===========================================

def cmd_next() -> None:
    """/next 명령어 - 다음 작업으로 진행"""
    if not get_context_manager().context:
        print("❌ 프로젝트가 선택되지 않았습니다.")
        return
        
    plan = get_context_manager().context.get('plan')
    if not plan:
        print("❌ 계획이 없습니다. 먼저 /plan [계획명]을 실행하세요.")
        return
    
    # 현재 작업이 있으면 완료로 표시
    current_task_id = get_context_manager().context.get('current_task')
    if current_task_id:
        work_tracking = get_context_manager().context.get('work_tracking', {})
        current_task_work = work_tracking.get('current_task_work', {})
        if current_task_work and current_task_work.get('task_id') == current_task_id:
            task_tracking = work_tracking.setdefault('task_tracking', {})
            task_tracking[current_task_id] = {
                'start_time': current_task_work.get('start_time'),
                'end_time': dt.datetime.now().isoformat(),
                'files_accessed': current_task_work.get('files_accessed', []),
                'functions_edited': current_task_work.get('functions_edited', []),
                'operations': current_task_work.get('operations', [])
            }
            
            print(f"\n📊 Task [{current_task_id}] 작업 요약:")
            print(f"   • 접근 파일: {len(current_task_work.get('files_accessed', []))}개")
            print(f"   • 수정 함수: {len(current_task_work.get('functions_edited', []))}개")
            print(f"   • 총 작업: {len(current_task_work.get('operations', []))}회")
        
        for phase_id, phase in plan['phases'].items():
            for task in phase['tasks']:
                if task['id'] == current_task_id:
                    if task['status'] != 'completed':
                        task['status'] = 'completed'
                        task['completed_at'] = dt.datetime.now().isoformat()
                        if current_task_work:
                            task['work_summary'] = {
                                'files_accessed': len(current_task_work.get('files_accessed', [])),
                                'functions_edited': len(current_task_work.get('functions_edited', [])),
                                'operations': len(current_task_work.get('operations', []))
                            }
                        print(f"✅ Task [{task['id']}] {task['title']} 완료!")
                    break
    
    # 다음 pending 작업 찾기
    next_task = None
    next_phase = None
    
    if plan.get('current_phase'):
        phase = plan['phases'].get(plan['current_phase'])
        if phase:
            for task in phase['tasks']:
                if task['status'] == 'pending':
                    next_task = task
                    next_phase = phase
                    break
    
    if not next_task:
        for phase_id, phase in plan['phases'].items():
            if phase.get('status') == 'completed':
                continue
                
            for task in phase['tasks']:
                if task['status'] == 'pending':
                    next_task = task
                    next_phase = phase
                    break
            
            if next_task:
                break
    
    if next_task:
        get_context_manager().context['current_task'] = next_task['id']
        plan['current_phase'] = next_phase['id']
        next_task['status'] = 'in_progress'
        next_task['started_at'] = dt.datetime.now().isoformat()
        next_phase['status'] = 'in_progress'
        
        get_context_manager().start_task_tracking(next_task['id'])
        
        plan['updated_at'] = dt.datetime.now().isoformat()
        
        get_context_manager()._update_progress()
        get_context_manager().save()
        
        print(f"\n🎯 다음 작업: [{next_task['id']}] {next_task['title']}")
        if next_task.get('description'):
            print(f"   📝 설명: {next_task['description']}")
        print(f"   📍 Phase: {next_phase['name']}")
        
        if next_task.get('subtasks'):
            print(f"\n   📌 서브태스크:")
            for subtask in next_task['subtasks']:
                print(f"      - {subtask}")
        
        print(f"\n💡 작업 추적이 시작되었습니다. 모든 파일 접근과 함수 수정이 자동으로 기록됩니다.")
    else:
        all_done = True
        blocked_tasks = []
        
        for phase_id, phase in plan['phases'].items():
            for task in phase['tasks']:
                if task['status'] == 'blocked':
                    blocked_tasks.append(task)
                elif task['status'] != 'completed':
                    all_done = False
        
        if all_done and not blocked_tasks:
            print("\n🎉 모든 작업이 완료되었습니다!")
            
            for phase in plan['phases'].values():
                phase['status'] = 'completed'
            
            get_context_manager()._update_progress()
            get_context_manager().save()
        else:
            if blocked_tasks:
                print(f"\n⚠️ 진행 가능한 작업이 없습니다. {len(blocked_tasks)}개의 작업이 blocked 상태입니다:")
                for task in blocked_tasks[:3]:
                    print(f"   - [{task['id']}] {task['title']}")
            else:
                print("\n⚠️ 진행 가능한 작업이 없습니다.")


