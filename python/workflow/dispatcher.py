"""
워크플로우 명령어 디스패처
AI helpers에서 워크플로우 명령을 실행하기 위한 인터페이스
"""

from .improved_manager import ImprovedWorkflowManager

# 전역 매니저 인스턴스
_manager_instance = None

def get_manager():
    """워크플로우 매니저 싱글톤 인스턴스 반환"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ImprovedWorkflowManager()
    return _manager_instance

def execute_workflow_command(command: str):
    """워크플로우 명령 실행"""
    try:
        manager = get_manager()
        result = manager.process_command(command)

        # 성공 시 문자열 반환
        if result.get('success'):
            return result.get('message', '완료')
        else:
            # 실패 시 Error: 접두사 추가
            return f"Error: {result.get('message', '알 수 없는 오류')}"

    except Exception as e:
        return f"Error: {str(e)}"

# 추가 헬퍼 함수들
def get_workflow_status():
    """워크플로우 상태 조회"""
    manager = get_manager()
    return manager.get_status()

def reset_workflow():
    """워크플로우 초기화"""
    global _manager_instance
    _manager_instance = None
    return "워크플로우가 초기화되었습니다"
