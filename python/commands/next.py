"""
Command: Next - 다음 작업으로 진행
리팩토링 버전: WorkflowManager 중심 아키텍처
"""

from typing import Optional
from core.workflow_manager import get_workflow_manager


def cmd_next(content: Optional[str] = None) -> None:
    """
    WorkflowManager를 호출하여 현재 계획을 다음 단계로 진행시킵니다.
    
    이 함수는 단순한 래퍼 역할만 수행하며, 모든 비즈니스 로직은
    WorkflowManager.advance_to_next_step()에 위임됩니다.
    
    Args:
        content: 현재 작업의 완료 내용/요약 (선택사항)
    """
    wm = get_workflow_manager()
    
    # WorkflowManager에 모든 로직 위임
    result = wm.advance_to_next_step(content=content)
    
    # 결과 출력
    if result.get('completed_task'):
        task_data = result['completed_task']
        print(f"✅ 작업 완료: [{task_data['task_id']}] {task_data['title']}")
        if task_data.get('content'):
            print(f"   📝 완료 내용: {task_data['content']}")
    
    if result['data']:
        # 다음 작업이 있는 경우
        task_data = result['data']
        print(f"\n✨ 새 작업: [{task_data['id']}] {task_data['title']}")
        print(f"   📌 Phase: {task_data.get('phase_name', 'N/A')}")
        if task_data.get('description'):
            print(f"   📝 설명: {task_data['description']}")
        
        # 작업 브리핑
        print("\n💡 작업 진행 가이드:")
        print("   - 작업을 완료한 후 '/next [완료 내용]'를 입력하세요")
        print("   - 완료 내용은 선택사항입니다")
    else:
        # 모든 작업이 완료된 경우
        print(f"\n🎉 {result['message']}")
        if "모든 작업이 완료" in result['message']:
            print("\n🏆 축하합니다! 현재 계획의 모든 작업을 완료했습니다.")
            print("   새로운 작업을 추가하려면 '/task add'를 사용하세요.")
