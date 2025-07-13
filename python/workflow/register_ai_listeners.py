"""
양방향 통신 리스너 등록 헬퍼
"""
from python.workflow.manager import WorkflowManager
from python.workflow.listeners.task_completion_instructor import TaskCompletionInstructor
from python.workflow.listeners.error_instructor import ErrorInstructor
from python.workflow.listeners.workflow_instructor import WorkflowInstructor
import logging

logger = logging.getLogger(__name__)

def register_ai_instructors(project_name: str):
    """AI 지시 리스너들을 등록"""
    try:
        wm = WorkflowManager.get_instance(project_name)
        
        # 기존 리스너 제거 (중복 방지)
        if hasattr(wm, 'listener_manager') and wm.listener_manager:
            # listener_manager가 있는 경우
            # listeners 딕셔너리 직접 확인
            if hasattr(wm.listener_manager, 'listeners'):
                existing_listeners = list(wm.listener_manager.listeners.values())
                for listener in existing_listeners:
                    if listener.__class__.__name__ in ['TaskCompletionInstructor', 'ErrorInstructor', 'WorkflowInstructor']:
                        # listener의 name을 찾아서 unregister
                        for name, l in wm.listener_manager.listeners.items():
                            if l == listener:
                                wm.listener_manager.unregister_listener(name)
                                break
        
        # 새 리스너 생성 및 등록
        instructors = [
            ('task_completion_instructor', TaskCompletionInstructor()),
            ('error_instructor', ErrorInstructor()),
            ('workflow_instructor', WorkflowInstructor())
        ]
        
        registered = 0
        for name, instructor in instructors:
            if hasattr(wm, 'listener_manager') and wm.listener_manager:
                wm.listener_manager.register_listener(name, instructor)
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
    try:
        from python.workflow.ai_instruction_executor import check_ai_instructions
    except ImportError:
        # check_ai_instructions가 없으면 로컬 함수 사용
        def check_ai_instructions():
            import os
            import json
            instruction_file = "memory/ai_instructions.json"
            
            if os.path.exists(instruction_file):
                with open(instruction_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        'pending': len(data.get('pending', [])),
                        'completed': len(data.get('completed', []))
                    }
            return {'pending': 0, 'completed': 0}
    
    import time
    time.sleep(1)  # 파일 쓰기 대기
    
    summary = check_ai_instructions()
    
    print("\n✅ 테스트 완료!")
    print(f"생성된 지시서: {summary.get('pending', 0)}개")