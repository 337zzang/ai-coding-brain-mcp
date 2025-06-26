#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TASK Command - AI Coding Brain MCP
/task 명령어 처리

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
# TASK 명령어
# ===========================================

def cmd_task(action: str, *args) -> None:
    """/task 명령어 - 작업 관리"""
    if not get_context_manager().context:
        print("❌ 프로젝트가 선택되지 않았습니다.")
        return
        
    context = get_context_manager().context
    if hasattr(context, 'plan'):
        plan = context.plan
    else:
        plan = context.get('plan')
    if not plan:
        print("❌ 계획이 없습니다. 먼저 /plan [계획명]을 실행하세요.")
        return
    
    if action == 'add':
        if len(args) < 2:
            print("사용법: /task add [phase-id] [작업명] [설명(선택)]")
            return
            
        phase_id = args[0]
        task_title = args[1]
        task_desc = ' '.join(args[2:]) if len(args) > 2 else ""
        
        # Plan 객체와 dict 모두 지원
        if hasattr(plan, 'phases'):  # Plan 객체
            phase = plan.phases.get(phase_id)
        else:  # dict
            phase = plan['phases'].get(phase_id)
        if not phase:
            print(f"❌ Phase '{phase_id}'를 찾을 수 없습니다.")
            print(f"   사용 가능한 Phase: {', '.join(plan['phases'].keys())}")
            return
        
        phase_num = phase_id.split('-')[1]
        task_num = len(phase['tasks']) + 1
        new_task = {
            'id': f'{phase_num}-{task_num}',
            'title': task_title,
            'description': task_desc,
            'status': 'pending',
            'created_at': dt.datetime.now().isoformat(),
            'subtasks': []
        }
        
        phase['tasks'].append(new_task)
        plan['updated_at'] = dt.datetime.now().isoformat()
        
        get_context_manager()._update_progress()
        get_context_manager().save()
        
        print(f"✅ Task 추가됨: [{new_task['id']}] {task_title}")
        print(f"   Phase: {phase['name']}")
        
    elif action == 'edit':
        if len(args) < 3:
            print("사용법: /task edit [task-id] status|title|desc [새값]")
            print("   status 값: pending, in_progress, completed, blocked")
            return
            
        task_id = args[0]
        field = args[1]
        new_value = ' '.join(args[2:])
        
        task_found = False
        for phase_id, phase in plan['phases'].items():
            for task in phase['tasks']:
                if task['id'] == task_id:
                    if field == 'status':
                        if new_value not in ['pending', 'in_progress', 'completed', 'blocked']:
                            print(f"❌ 잘못된 상태값: {new_value}")
                            print("   가능한 값: pending, in_progress, completed, blocked")
                            return
                        task['status'] = new_value
                        
                        if new_value == 'in_progress':
                            context = get_context_manager().context
            if hasattr(context, 'current_task'):
                context.current_task = task_id
            else:
                context['current_task'] = task_id
                            plan['current_phase'] = phase_id
                            phase['status'] = 'in_progress'
                        elif new_value == 'completed' and get_context_manager().context.get('current_task') == task_id:
                            context = get_context_manager().context
            if hasattr(context, 'current_task'):
                context.current_task = None
            else:
                context['current_task'] = None
                            
                    elif field == 'title':
                        task['title'] = new_value
                    elif field in ['desc', 'description']:
                        task['description'] = new_value
                    else:
                        print(f"❌ 알 수 없는 필드: {field}")
                        return
                    
                    task['updated_at'] = dt.datetime.now().isoformat()
                    task_found = True
                    plan['updated_at'] = dt.datetime.now().isoformat()
                    
                    get_context_manager()._update_progress()
                    get_context_manager().save()
                    
                    print(f"✅ Task [{task_id}] {field} 수정됨")
                    break
            if task_found:
                break
        
        if not task_found:
            print(f"❌ Task '{task_id}'를 찾을 수 없습니다.")
    
    elif action == 'done':
        if len(args) < 1:
            print("사용법: /task done [task-id]")
            return
            
        task_id = args[0]
        
        task_found = False
        for phase_id, phase in plan['phases'].items():
            for task in phase['tasks']:
                if task['id'] == task_id:
                    if task['status'] == 'completed':
                        print(f"⚠️ Task [{task_id}]는 이미 완료되었습니다.")
                        return
                    
                    # 작업을 완료로 표시
                    task['status'] = 'completed'
                    task['completed_at'] = dt.datetime.now().isoformat()
                    
                    # 현재 작업이었다면 current_task 해제
                    if get_context_manager().context.get('current_task') == task_id:
                        context = get_context_manager().context
            if hasattr(context, 'current_task'):
                context.current_task = None
            else:
                context['current_task'] = None
                        
                        # 작업 추적 정보 저장
                        work_tracking = get_context_manager().context.get('work_tracking', {})
                        current_task_work = work_tracking.get('current_task_work', {})
                        if current_task_work and current_task_work.get('task_id') == task_id:
                            task_tracking = work_tracking.setdefault('task_tracking', {})
                            task_tracking[task_id] = {
                                'start_time': current_task_work.get('start_time'),
                                'end_time': dt.datetime.now().isoformat(),
                                'files_accessed': current_task_work.get('files_accessed', []),
                                'functions_edited': current_task_work.get('functions_edited', []),
                                'operations': current_task_work.get('operations', [])
                            }
                            
                            # 작업 요약 저장
                            task['work_summary'] = {
                                'files_accessed': len(current_task_work.get('files_accessed', [])),
                                'functions_edited': len(current_task_work.get('functions_edited', [])),
                                'operations': len(current_task_work.get('operations', []))
                            }
                    
                    task['updated_at'] = dt.datetime.now().isoformat()
                    task_found = True
                    plan['updated_at'] = dt.datetime.now().isoformat()
                    
                    get_context_manager()._update_progress()
                    get_context_manager().save()
                    
                    print(f"✅ Task [{task_id}] {task['title']} 완료!")
                    
                    # 작업 요약 표시
                    if task.get('work_summary'):
                        summary = task['work_summary']
                        print(f"   📊 작업 요약:")
                        print(f"      • 접근 파일: {summary['files_accessed']}개")
                        print(f"      • 수정 함수: {summary['functions_edited']}개")
                        print(f"      • 총 작업: {summary['operations']}회")
                    break
            if task_found:
                break
        
        if not task_found:
            print(f"❌ Task '{task_id}'를 찾을 수 없습니다.")
    
    elif action == 'list':
        print(f"\n📋 계획: {plan['name']}")
        print(f"진행률: {(get_context_manager().context.progress.percentage if hasattr(get_context_manager().context, 'progress') else helpers.get_value('progress.percentage', 0)):.1f}%")
        print("\n전체 Task 목록:")
        
        for phase_id, phase in plan['phases'].items():
            tasks = phase['tasks']
            completed = sum(1 for t in tasks if t.get('status') == 'completed')
            
            status_emoji = "✅" if phase.get('status') == 'completed' else "🔄" if phase.get('status') == 'in_progress' else "⏳"
            print(f"\n{status_emoji} {phase['name']} ({completed}/{len(tasks)} 완료)")
            
            if phase.get('description'):
                print(f"   📝 {phase['description']}")
            
            for task in tasks:
                task_emoji = "✅" if task['status'] == 'completed' else "🔄" if task['status'] == 'in_progress' else "🚫" if task['status'] == 'blocked' else "⏳"
                current = " 👈 현재" if get_context_manager().context.get('current_task') == task['id'] else ""
                print(f"   {task_emoji} [{task['id']}] {task['title']}{current}")
                if task.get('description'):
                    print(f"      📝 {task['description']}")
    
    else:
        print(f"❌ 알 수 없는 액션: {action}")
        print("사용 가능한 액션: add, edit, done, list")


