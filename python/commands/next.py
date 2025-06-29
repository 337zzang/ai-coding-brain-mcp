"""
Command: Next - 다음 작업으로 진행
WorkflowManager 중심 아키텍처 버전
"""
from typing import Optional
from core.workflow_manager import get_workflow_manager


def cmd_next(content: Optional[str] = None) -> None:
    """
    다음 작업으로 진행 - WorkflowManager에 모든 로직 위임
    
    Args:
        content: 현재 작업의 완료 내용 (선택사항)
    """
    wm = get_workflow_manager()
    
    # WorkflowManager의 advance_to_next_step 호출
    result = wm.advance_to_next_step(content=content)
    
    # 완료된 작업 표시
    if result.get('completed_task'):
        task_data = result['completed_task']
        print(f"✅ 작업 완료: {task_data['title']}")
        if task_data.get('content'):
            print(f"   📝 완료 내용: {task_data['content']}")
    
    # 다음 작업 표시
    if result.get('next_task'):
        task_data = result['next_task']
        print(f"\n✨ 새 작업 시작: {task_data['title']}")
        print(f"   🚀 상태: {task_data['status']}")
        
        # 진행 가이드
        print("\n💡 작업 진행 가이드:")
        print("   • 작업 완료 후 '/next [완료 내용]' 입력")
        print("   • 완료 내용은 선택사항입니다")
    else:
        # 모든 작업 완료
        print(f"\n🎉 {result['message']}")
        
        # 통계 표시
        stats = wm.get_statistics()
        if stats['total_tasks'] > 0:
            print(f"\n📊 최종 통계:")
            print(f"   • 완료된 작업: {stats['completed_tasks']}/{stats['total_tasks']}")
            print(f"   • 완료된 Phase: {stats['completed_phases']}/{stats['total_phases']}")
            print(f"   • 전체 진행률: {stats['progress']:.1f}%")
        
        print("\n🏆 축하합니다! 모든 작업을 완료했습니다.")
        print("   새로운 작업을 추가하려면 '/task add'를 사용하세요.")
