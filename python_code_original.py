
# 개선된 flow_project 핸들러 - 명시적 에러 처리
import sys
import os
import json
import traceback
from pathlib import Path

project_name = "${params.project_name}"
result = {
    "success": False,
    "project_name": project_name,
    "error": None,
    "details": {}
}

# 로그 출력을 억제하기 위한 설정
import logging
logging.getLogger().setLevel(logging.CRITICAL)

# stdout 캡처를 위한 설정
from io import StringIO
captured_output = StringIO()

try:
    # 1. Python 경로 설정
    current_dir = Path.cwd()
    python_dir = current_dir / 'python'
    if python_dir.exists() and str(python_dir) not in sys.path:
        sys.path.insert(0, str(python_dir))

    # 2. enhanced_flow import
    try:
        from enhanced_flow import cmd_flow_with_context
    except ImportError as e:
        result["error"] = f"enhanced_flow 모듈 import 실패: {str(e)}"
        result["details"]["import_error"] = traceback.format_exc()
        print(f"JSON_RESULT_START{json.dumps(result, ensure_ascii=False)}JSON_RESULT_END")
        sys.exit(1)

    # 3. stdout 리다이렉트
    original_stdout = sys.stdout
    sys.stdout = captured_output
    
    try:
        # 4. 프로젝트 전환 실행
        flow_result = cmd_flow_with_context(project_name)

        if flow_result and isinstance(flow_result, dict):
            result["success"] = True
            result["path"] = flow_result.get("context", {}).get("project_path", os.getcwd())
            result["git_branch"] = flow_result.get("context", {}).get("git", {}).get("branch", "unknown")
            result["workflow_status"] = flow_result.get("workflow_status", {})
            result["details"] = flow_result
        else:
            result["error"] = f"예상치 못한 반환값: {type(flow_result)}"
            result["details"]["return_value"] = str(flow_result)

    except Exception as e:
        result["error"] = f"프로젝트 전환 중 오류: {str(e)}"
        result["details"]["traceback"] = traceback.format_exc()
        result["details"]["exception_type"] = type(e).__name__
    finally:
        # stdout 복원
        sys.stdout = original_stdout
        captured_logs = captured_output.getvalue()
        result["details"]["logs"] = captured_logs

    # 5. 결과 출력 (JSON만 출력)
    print(f"JSON_RESULT_START{json.dumps(result, ensure_ascii=False)}JSON_RESULT_END")

except Exception as e:
    # 최상위 예외 처리
    result["error"] = f"치명적 오류: {str(e)}"
    result["details"]["fatal_traceback"] = traceback.format_exc()
    print(f"JSON_RESULT_START{json.dumps(result, ensure_ascii=False)}JSON_RESULT_END")
    sys.exit(1)
