"""Flow 시스템 에러 메시지 정의"""

def get_error_message(error_type: str, **kwargs) -> str:
    """구체적이고 도움이 되는 에러 메시지 반환

    Args:
        error_type: 에러 타입
        **kwargs: 에러 메시지에 포함할 추가 정보

    Returns:
        str: 상세한 에러 메시지
    """

    error_messages = {
        # Flow 관련 에러
        "no_current_flow": "현재 활성화된 Flow가 없습니다. /flow list로 Flow 목록을 확인하고 /flow switch <flow_id>로 전환하세요.",

        "flow_not_found": f"Flow '{kwargs.get('flow_id', '')}' 를 찾을 수 없습니다. /flow list 명령으로 존재하는 Flow를 확인하세요.",

        "flow_already_exists": f"Flow '{kwargs.get('flow_name', '')}' 가 이미 존재합니다. 다른 이름을 사용하거나 기존 Flow로 전환하세요.",

        # Plan 관련 에러
        "plan_not_found": f"Plan ID '{kwargs.get('plan_id', '')}' 를 찾을 수 없습니다. /plan 명령으로 올바른 Plan ID를 확인하세요.",

        "plan_creation_failed": f"Plan 생성 실패: {kwargs.get('reason', '알 수 없는 오류')}. Plan 이름이 비어있지 않은지 확인하세요.",

        # Task 관련 에러
        "task_not_found": f"Task ID '{kwargs.get('task_id', '')}' 를 찾을 수 없습니다. /task 명령으로 Task 목록을 확인하세요.",

        "task_creation_failed": f"Task 생성 실패: Plan ID '{kwargs.get('plan_id', '')}' 가 올바른지 확인하세요. /plan 명령으로 정확한 Plan ID를 복사하여 사용하세요.",

        "invalid_task_status": f"잘못된 Task 상태 '{kwargs.get('status', '')}'. 사용 가능한 상태: todo, planning, in_progress, reviewing, completed, skip, error",

        "task_already_completed": f"Task '{kwargs.get('task_id', '')}' 는 이미 완료되었습니다. 다시 시작하려면 먼저 상태를 변경하세요.",

        # 명령어 관련 에러
        "unknown_command": f"알 수 없는 명령어: '{kwargs.get('command', '')}'. /help 명령으로 사용 가능한 명령어를 확인하세요.",

        "invalid_arguments": f"잘못된 인자: {kwargs.get('details', '')}. 올바른 사용법: {kwargs.get('usage', '')}",

        "missing_required_argument": f"필수 인자가 누락되었습니다: {kwargs.get('argument', '')}. 사용법: {kwargs.get('usage', '')}",

        # 백업 관련 에러
        "backup_not_found": f"백업 파일 '{kwargs.get('filename', '')}' 를 찾을 수 없습니다. /backup 명령으로 백업 목록을 확인하세요.",

        "backup_restore_failed": f"백업 복구 실패: {kwargs.get('reason', '파일을 읽을 수 없습니다')}. 백업 파일이 손상되지 않았는지 확인하세요.",

        # 일반 에러
        "permission_denied": "권한이 없습니다. 파일이나 디렉토리에 대한 접근 권한을 확인하세요.",

        "file_not_found": f"파일을 찾을 수 없습니다: {kwargs.get('filepath', '')}",

        "invalid_json": "잘못된 JSON 형식입니다. 데이터 구조를 확인하세요.",

        "unexpected_error": f"예상치 못한 오류가 발생했습니다: {kwargs.get('error', '')}. 문제가 지속되면 로그를 확인하세요."
    }

    return error_messages.get(error_type, f"오류 발생: {error_type}")

def format_error_response(error_type: str, **kwargs) -> dict:
    """에러 응답 형식 생성

    Args:
        error_type: 에러 타입
        **kwargs: 에러 메시지에 포함할 추가 정보

    Returns:
        dict: {"ok": False, "error": "상세 메시지"}
    """
    return {
        "ok": False,
        "error": get_error_message(error_type, **kwargs)
    }
