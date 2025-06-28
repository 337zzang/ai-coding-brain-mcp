#!/usr/bin/env python3
"""
개선된 다음 작업(Next) 진행 명령어
WorkflowManager 기반으로 완전히 리팩토링됨
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.workflow_manager import get_workflow_manager
from typing import Dict, Any


def cmd_next() -> Dict[str, Any]:
    """다음 작업을 시작합니다.
    
    Returns:
        Dict[str, Any]: 작업 실행 결과
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
            print(f"\n✅ 작업 시작: [{task.id}] {task.title}")
            
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
    else:
        print(f"\n❌ 오류: {result.get('message', 'Unknown error')}")
    
    return result


# 스크립트로 직접 실행 시
if __name__ == "__main__":
    result = cmd_next()
    exit(0 if result['success'] else 1)
