#!/usr/bin/env python3
"""
개선된 다음 작업(Next) 진행 명령어
WorkflowManager 기반으로 완전히 리팩토링됨
- content 기능 추가로 투명성 강화
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.workflow_manager import get_workflow_manager
from core.error_handler import StandardResponse


def cmd_next(content: str = None) -> StandardResponse:
    """다음 작업을 시작하거나 현재 작업을 완료하고 다음으로 진행
    
    Args:
        content: 현재 작업 완료 시 수행한 내용 (선택사항)
        
    Returns:
        StandardResponse: 표준 응답 형식
    """
    wm = get_workflow_manager()
    
    # 현재 진행 중인 작업이 있는지 확인
    current_task_id = wm.context.current_task
    if current_task_id:
        current_task = wm.plan.get_task_by_id(current_task_id)
        if current_task and current_task.status == 'in_progress':
            # content가 없으면 자동 생성
            if not content:
                content = input(f"\n📝 '{current_task.title}' 작업에서 수행한 내용을 입력하세요: ")
            
            # 현재 작업 완료
            print(f"\n🔄 현재 작업 완료 중...")
            wm.complete_task(current_task_id, content)
    
    # 다음 작업 시작
    result = wm.start_next_task()
    
    if result['success']:
        data = result['data']
        
        # 상태별 처리
        if data.get('status') == 'no_tasks':
            print("\n📋 대기 중인 작업이 없습니다.")
            print("\n💡 다음 옵션:")
            print("   1. 'task add phase-id \"작업명\"'으로 새 작업 추가")
            print("   2. 'plan'으로 전체 계획 확인")
            print("   3. 'flow'로 전체 진행 히스토리 확인")
            
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
            print(f"\n✅ 작업 시작: [{task.id}] {task.title}")
            
            if task.description:
                print(f"\n📝 설명: {task.description}")
                
            # 이전 작업 결과 반영
            previous_tasks = [t for t in wm.plan.get_all_tasks() if t.status == 'completed' and t.content]
            if previous_tasks:
                recent_task = previous_tasks[-1]
                print(f"\n📌 이전 작업 결과: {recent_task.content}")
                print("   (이전 작업 결과를 참고하여 진행하세요)")
                
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
