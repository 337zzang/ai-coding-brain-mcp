#!/usr/bin/env python3
"""
개선된 작업(Task) 관리 명령어
WorkflowManager와 완전히 통합
"""

import os
import sys
from typing import Dict, Any, Optional, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.workflow_manager import get_workflow_manager
from core.error_handler import StandardResponse, ErrorType
from core.models import TaskStatus
import logging

# 로거 설정
logger = logging.getLogger(__name__)


def cmd_task(action: str, *args) -> Dict[str, Any]:
    """작업 관리 명령어
    
    Args:
        action: 작업 동작 (list, add, done, remove, update)
        args: 추가 인자
        
    Returns:
        Dict[str, Any]: 작업 실행 결과
    """
    wm = get_workflow_manager()
    
    try:
        if action == 'list':
            # 작업 목록 표시
            if not wm.plan:
                print('❌ 설정된 계획이 없습니다. 먼저 "plan 계획명"으로 생성하세요.')
                return {"success": False, "message": "No plan set"}
                
            status = wm.get_workflow_status()
            plan = wm.plan
            
            print(f"📋 계획: {plan.name}")
            progress = status.get('progress', 0)
            completed = status.get('completed_tasks', 0)
            total = status.get('total_tasks', 0)
            print(f"진행률: {progress:.1f}% ({completed}/{total})")
            
            # Phase별 작업 표시
            if not plan.phases:
                print("\n📭 아직 Phase가 없습니다.")
            else:
                for phase_id in plan.phase_order:
                    phase = plan.phases.get(phase_id)
                    if not phase:
                        continue
                        
                    phase_tasks = list(phase.tasks.values())
                    if phase_tasks:
                        completed_count = len([t for t in phase_tasks if t.status == TaskStatus.COMPLETED])
                        icon = "✅" if completed_count == len(phase_tasks) else ("🔄" if completed_count > 0 else "⏳")
                        print(f"\n{icon} {phase.name} ({completed_count}/{len(phase_tasks)} 완료)")
                        
                        for task in phase_tasks:
                            task_icon = "✅" if task.status == TaskStatus.COMPLETED else ("🔄" if task.status == TaskStatus.IN_PROGRESS else "⏳")
                            priority_mark = "🔴" if task.priority == 'high' else ("🟡" if task.priority == 'medium' else "")
                            print(f"   {task_icon} {priority_mark} [{task.id[:8]}] {task.title}")
                            if task.description:
                                print(f"      📝 {task.description[:50]}...")
                    else:
                        print(f"\n⏳ {phase.name} (작업 없음)")
                        
            # 현재 작업 표시
            if status.get('current_task'):
                print(f"\n🎯 현재 작업: {status['current_task']}")
                
            return {"success": True, "data": status}
            
        elif action == 'add':
            if not args:
                print('❌ 사용법: task add [phase-id] "작업명" [설명]')
                return {"success": False, "message": "Invalid arguments"}
                
            # Phase ID 결정
            if len(args) >= 2 and args[0].startswith('phase-'):
                phase_id = args[0]
                task_name = args[1]
                description = ' '.join(args[2:]) if len(args) > 2 else ""
            else:
                # phase_id가 없으면 현재 phase 사용
                if not wm.plan:
                    print("❌ 계획이 설정되지 않았습니다.")
                    return {"success": False, "message": "No plan set"}
                    
                current_phase = wm.plan.current_phase
                if not current_phase:
                    # 첫 번째 phase 사용
                    if wm.plan.phase_order:
                        current_phase = wm.plan.phase_order[0]
                    else:
                        print("❌ Phase가 없습니다. 먼저 계획을 생성하세요.")
                        return {"success": False, "message": "No phases in plan"}
                        
                phase_id = current_phase
                task_name = args[0]
                description = ' '.join(args[1:]) if len(args) > 1 else ""
            
            # 작업 추가
            result = wm.add_task(
                phase_id=phase_id,
                title=task_name,
                description=description
            )
            
            if result['success']:
                task = result['data']['task']
                print(f"✅ 작업 추가됨: [{task.id[:8]}] {task.title}")
                print(f"   Phase: {phase_id}")
            else:
                print(f"❌ 작업 추가 실패: {result.get('message', 'Unknown error')}")
                
            return result
            
        elif action == 'done':
            if not args:
                print("❌ 사용법: task done <작업ID>")
                return {"success": False, "message": "Task ID required"}
                
            task_id = args[0]
            
            # 짧은 ID도 지원 (앞 8자리로 검색)
            if len(task_id) < 36:  # UUID 길이보다 짧으면
                # 모든 작업에서 검색
                found_task_id = None
                for phase in wm.plan.phases.values():
                    for full_id, task in phase.tasks.items():
                        if full_id.startswith(task_id):
                            found_task_id = full_id
                            break
                    if found_task_id:
                        break
                        
                if found_task_id:
                    task_id = found_task_id
                else:
                    print(f"❌ 작업 ID '{task_id}'를 찾을 수 없습니다.")
                    return {"success": False, "message": "Task not found"}
            
            result = wm.complete_task(task_id)
            
            if result['success']:
                task = result['data']['task']
                print(f"✅ 작업 완료: {task.title}")
                
                # 다음 작업 제안
                next_tasks = []
                for phase in wm.plan.phases.values():
                    for t in phase.tasks.values():
                        if t.status == TaskStatus.PENDING:
                            next_tasks.append(t)
                            
                if next_tasks:
                    print(f"\n💡 다음 작업 제안: [{next_tasks[0].id[:8]}] {next_tasks[0].title}")
                    print("   'next' 명령으로 시작하세요.")
            else:
                print(f"❌ 작업 완료 실패: {result.get('message', 'Unknown error')}")
                
            return result
            
        elif action == 'remove':
            if not args:
                print("❌ 사용법: task remove <작업ID>")
                return {"success": False, "message": "Task ID required"}
                
            task_id = args[0]
            
            # 작업 찾기 및 제거
            removed = False
            for phase in wm.plan.phases.values():
                if task_id in phase.tasks:
                    task = phase.tasks[task_id]
                    del phase.tasks[task_id]
                    phase.task_order.remove(task_id)
                    phase.total_tasks = len(phase.tasks)
                    removed = True
                    print(f"✅ 작업 제거됨: {task.title}")
                    break
                    
            if not removed:
                print(f"❌ 작업 ID '{task_id}'를 찾을 수 없습니다.")
                return {"success": False, "message": "Task not found"}
                
            # 컨텍스트 저장
            wm.save()
            return {"success": True, "message": "Task removed"}
            
        elif action == 'update':
            if len(args) < 2:
                print("❌ 사용법: task update <작업ID> <필드> <값>")
                return {"success": False, "message": "Invalid arguments"}
                
            task_id = args[0]
            field = args[1]
            value = ' '.join(args[2:]) if len(args) > 2 else ""
            
            # 작업 찾기
            task = None
            for phase in wm.plan.phases.values():
                if task_id in phase.tasks:
                    task = phase.tasks[task_id]
                    break
                    
            if not task:
                print(f"❌ 작업 ID '{task_id}'를 찾을 수 없습니다.")
                return {"success": False, "message": "Task not found"}
                
            # 필드 업데이트
            if field == 'title':
                task.title = value
            elif field == 'description':
                task.description = value
            elif field == 'priority':
                if value in ['high', 'medium', 'low']:
                    task.priority = value
                else:
                    print("❌ 우선순위는 high, medium, low 중 하나여야 합니다.")
                    return {"success": False, "message": "Invalid priority"}
            else:
                print(f"❌ 알 수 없는 필드: {field}")
                return {"success": False, "message": "Unknown field"}
                
            # 업데이트 시간 기록
            from datetime import datetime
            task.updated_at = datetime.now()
            
            # 저장
            wm.save()
            print(f"✅ 작업 업데이트됨: {task.title}")
            return {"success": True, "data": {"task": task}}
            
        else:
            print(f"❌ 알 수 없는 명령: {action}")
            print("사용 가능한 명령: list, add, done, remove, update")
            return {"success": False, "message": f"Unknown action: {action}"}
            
    except Exception as e:
        logger.error(f"cmd_task 오류: {str(e)}")
        print(f"❌ 작업 관리 중 오류: {str(e)}")
        return {"success": False, "message": str(e), "error": str(e)}


# 스크립트로 직접 실행 시
if __name__ == "__main__":
    if len(sys.argv) > 1:
        action = sys.argv[1]
        args = sys.argv[2:]
        result = cmd_task(action, *args)
        exit(0 if result['success'] else 1)
    else:
        result = cmd_task('list')
        exit(0 if result['success'] else 1)
