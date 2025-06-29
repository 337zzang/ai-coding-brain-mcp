"""
Command: Plan - 계획 관리
WorkflowManager 중심 아키텍처 버전
"""
from typing import Optional
from core.workflow_manager import get_workflow_manager


def cmd_plan(action: str = "show", name: Optional[str] = None, 
             description: Optional[str] = None) -> None:
    """
    계획 관리 명령어 - WorkflowManager에 모든 로직 위임
    
    Args:
        action: 액션 (create, update, show)
        name: 계획 이름
        description: 계획 설명
    """
    wm = get_workflow_manager()
    
    if action == "create":
        if not name:
            print("❌ 계획 이름을 입력해주세요")
            return
        
        result = wm.create_plan(name=name, description=description)
        
        if result['success']:
            print(f"✅ {result['message']}")
            print(f"   📋 ID: {result['data']['id']}")
            print(f"   📌 이름: {result['data']['name']}")
            if result['data']['description']:
                print(f"   📝 설명: {result['data']['description']}")
        else:
            print(f"❌ {result['message']}")
    
    elif action == "update":
        result = wm.update_plan(name=name, description=description)
        
        if result['success']:
            print(f"✅ {result['message']}")
            print(f"   📌 이름: {result['data']['name']}")
            if result['data']['description']:
                print(f"   📝 설명: {result['data']['description']}")
        else:
            print(f"❌ {result['message']}")
    
    elif action == "show":
        plan = wm.get_plan()
        
        if plan:
            print(f"📋 현재 계획: {plan.name}")
            if plan.description:
                print(f"   📝 설명: {plan.description}")
            
            # 통계 정보
            stats = wm.get_statistics()
            print(f"\n📊 진행 상황:")
            print(f"   • Phase: {stats['completed_phases']}/{stats['total_phases']} 완료")
            print(f"   • 작업: {stats['completed_tasks']}/{stats['total_tasks']} 완료")
            print(f"   • 진행률: {stats['progress']:.1f}%")
            
            # Phase 목록
            if plan.phases:
                print(f"\n📂 Phase 목록:")
                for phase in plan.phases:
                    status_icon = "✅" if phase.status.value == "completed" else "🔄" if phase.status.value == "in_progress" else "⏳"
                    print(f"   {status_icon} {phase.name} ({len(phase.tasks)}개 작업)")
                    if phase.description:
                        print(f"      └─ {phase.description}")
        else:
            print("📋 활성화된 계획이 없습니다")
            print("   '/plan create [이름]'으로 새 계획을 생성하세요")
    
    else:
        print(f"❌ 알 수 없는 액션: {action}")
        print("   사용 가능한 액션: create, update, show")
