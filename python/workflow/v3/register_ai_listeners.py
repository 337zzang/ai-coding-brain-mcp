"""
양방향 통신 리스너 등록 헬퍼
"""
from python.workflow.v3.manager import WorkflowManager
from python.workflow.v3.listeners.task_completion_instructor import TaskCompletionInstructor
from python.workflow.v3.listeners.error_instructor import ErrorInstructor
from python.workflow.v3.listeners.workflow_instructor import WorkflowInstructor
import logging

logger = logging.getLogger(__name__)

def register_ai_instructors(project_name: str):
    """AI 지시 리스너들을 등록"""
    try:
        wm = WorkflowManager.get_instance(project_name)
        
        # 기존 리스너 제거 (중복 방지)
        if hasattr(wm, 'listener_manager') and wm.listener_manager:
            # listener_manager가 있는 경우
            existing_listeners = wm.listener_manager.get_listeners()
            for listener in existing_listeners:
                if isinstance(listener, (TaskCompletionInstructor, ErrorInstructor, WorkflowInstructor)):
                    wm.listener_manager.unregister_listener(listener)
        
        # 새 리스너 생성 및 등록
        instructors = [
            TaskCompletionInstructor(wm),
            ErrorInstructor(wm),
            WorkflowInstructor(wm)
        ]
        
        registered = 0
        for instructor in instructors:
            if hasattr(wm, 'listener_manager') and wm.listener_manager:
                wm.listener_manager.register_listener(instructor)
                logger.info(f"✅ 등록됨: {instructor.__class__.__name__}")
                registered += 1
            else:
                logger.warning(f"❌ listener_manager 없음: {instructor.__class__.__name__} 등록 실패")
        
        print(f"\n🎯 AI 지시 리스너 등록 완료!")
        print(f"프로젝트: {project_name}")
        print(f"등록된 리스너: {registered}개")
        
        if registered > 0:
            print("\n이제 워크플로우 이벤트가 AI 지시서로 변환됩니다.")
        else:
            print("\n⚠️ 리스너가 등록되지 않았습니다. WorkflowManager 설정을 확인하세요.")
        
        return registered > 0
        
    except Exception as e:
        logger.error(f"리스너 등록 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_instruction_system(project_name: str):
    """AI 지시 시스템 테스트"""
    print("\n🧪 AI 지시 시스템 테스트")
    print("="*60)
    
    # 1. 리스너 등록
    if register_ai_instructors(project_name):
        print("✅ 리스너 등록 성공")
    else:
        print("❌ 리스너 등록 실패")
        return
    
    # 2. 테스트 이벤트 발생
    wm = WorkflowManager.get_instance(project_name)
    
    # 태스크 완료 이벤트 시뮬레이션
    print("\n📌 태스크 완료 이벤트 발생...")
    # 실제로는 helpers.workflow("/next") 등으로 발생
    
    # 3. 지시서 확인
    from python.workflow.v3.ai_instruction_executor import check_ai_instructions
    
    import time
    time.sleep(1)  # 파일 쓰기 대기
    
    summary = check_ai_instructions()
    
    print("\n✅ 테스트 완료!")
    print(f"생성된 지시서: {summary.get('pending', 0)}개")