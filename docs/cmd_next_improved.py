#!/usr/bin/env python3
"""
WorkflowManager를 활용한 개선된 다음 작업(Next) 진행 명령어
단순화되고 타입 안전한 구조
"""

from typing import Optional
from core.workflow_manager import get_workflow_manager
from core.error_handler import StandardResponse


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
                print("\n🚫 차단된 작업들:")
                for b in bottlenecks[:5]:  # 최대 5개만 표시
                    if b['type'] == 'blocked_task':
                        print(f"   - [{b['task_id']}] {b['title']}")
                        print(f"     이유: {b['reason']}")
                        if b['dependencies']:
                            print(f"     대기 중: {', '.join(b['dependencies'])}")
            
        else:
            # 작업 시작 성공
            task_id = data['task_id']
            title = data['title']
            phase = data.get('phase', 'Unknown')
            
            print(f"\n🚀 작업 시작: [{task_id}] {title}")
            print(f"   Phase: {phase}")
            
            if data.get('estimated_hours'):
                print(f"   예상 시간: {data['estimated_hours']} 시간")
            
            # 작업 브리핑
            _show_task_briefing(task_id, title, phase)
            
            # 워크플로우 상태 표시
            status = wm.get_workflow_status()
            progress = status['progress']
            print(f"\n📊 전체 진행률: {progress['percentage']:.1f}% ({progress['completed_tasks']}/{progress['total_tasks']})")
            
    else:
        # 에러 처리
        error = result['error']
        print(f"\n❌ {error['message']}")
        
        if error['type'] == 'plan_error':
            print("\n💡 먼저 'plan \"계획명\"'으로 계획을 생성하세요.")
    
    return result


def _show_task_briefing(task_id: str, title: str, phase: str) -> None:
    """작업 브리핑 표시"""
    print("\n📋 작업 브리핑:")
    print(f"   1. 작업 ID: {task_id}")
    print(f"   2. 제목: {title}")
    print(f"   3. Phase: {phase}")
    print()
    print("💡 작업 완료 후 'task done'을 실행하세요.")
    
    # 작업 분석 정보 표시
    wm = get_workflow_manager()
    analytics = wm.get_task_analytics()
    
    if analytics.get('average_time_by_status'):
        avg_time = analytics['average_time_by_status'].get('in_progress', 0)
        if avg_time > 0:
            print(f"\n📊 평균 작업 시간: {avg_time:.1f} 시간")


# 기존 호환성을 위한 래퍼 (선택사항)
def cmd_next_legacy(quiet: bool = False) -> Optional[Dict[str, Any]]:
    """레거시 인터페이스 호환성 제공"""
    result = cmd_next()
    
    if not quiet:
        # 이미 cmd_next에서 출력했으므로 추가 출력 불필요
        pass
    
    # 기존 형식으로 변환
    if result['success'] and result['data'].get('task_id'):
        return {
            'task_id': result['data']['task_id'],
            'title': result['data']['title'],
            'phase': result['data'].get('phase')
        }
    
    return None


if __name__ == "__main__":
    # 직접 실행 시
    cmd_next()
