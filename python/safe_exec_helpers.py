
# safe_exec_helpers.py - JSON REPL 세션을 위한 안전한 실행 헬퍼
"""
JSON REPL 세션을 위한 안전한 코드 실행 시스템
- 실행 전 컴파일 검사
- 증분 구문 검사
- 에러 포맷팅
"""

import ast
import sys
import time
import traceback
from typing import Dict, Any, Optional, Tuple

def enhanced_safe_exec(code: str, globals_dict: dict) -> Tuple[bool, str]:
    """
    기존 safe_exec를 개선한 버전
    compile() 단계를 추가하여 구문 오류를 사전에 검출

    Returns:
        (성공 여부, 에러 메시지 또는 빈 문자열)
    """
    # 1. 들여쓰기 정리
    import textwrap
    code = textwrap.dedent(code).strip()

    # 2. 컴파일 단계 (구문 검사)
    try:
        # mode 결정 (단일 표현식 vs 문장)
        try:
            ast.parse(code, mode='eval')
            mode = 'eval'
        except:
            mode = 'exec'

        # 컴파일
        code_obj = compile(code, '<json_repl>', mode)

    except SyntaxError as e:
        # 구문 오류 포맷팅
        error_msg = f"❌ 구문 오류: {e.msg}"
        if e.lineno:
            error_msg += f" (라인 {e.lineno}"
            if e.offset:
                error_msg += f", 위치 {e.offset}"
            error_msg += ")"

        # 에러 위치 표시
        if e.text:
            error_msg += f"\n    {e.text}"
            if e.offset:
                error_msg += f"    {' ' * (e.offset - 1)}^"

        return False, error_msg

    except Exception as e:
        return False, f"❌ 컴파일 오류: {type(e).__name__}: {str(e)}"

    # 3. 실행 단계
    try:
        if mode == 'eval':
            result = eval(code_obj, globals_dict)
            # eval 결과를 출력
            if result is not None:
                print(repr(result))
        else:
            exec(code_obj, globals_dict)

        return True, ""

    except Exception as e:
        # 런타임 오류 포맷팅
        tb = traceback.format_exc()
        error_msg = f"❌ 런타임 오류: {type(e).__name__}: {str(e)}"

        # 상세 트레이스백은 디버그 모드에서만
        if globals_dict.get('DEBUG', False):
            error_msg += f"\n\n{tb}"

        return False, error_msg

# 빠른 구문 검사 (실행 없이)
def quick_syntax_check(code: str) -> Dict[str, Any]:
    """
    실행 없이 구문만 빠르게 검사
    IDE처럼 타이핑 중 실시간 피드백용
    """
    try:
        ast.parse(code)
        return {
            "valid": True,
            "mode": "exec" if '\n' in code or '=' in code else "eval"
        }
    except SyntaxError as e:
        return {
            "valid": False,
            "error": {
                "msg": e.msg,
                "lineno": e.lineno,
                "offset": e.offset,
                "text": e.text
            }
        }
    except Exception as e:
        return {
            "valid": False,
            "error": {
                "msg": str(e),
                "type": type(e).__name__
            }
        }

# JSON REPL 세션 통합 버전
def create_enhanced_json_repl_execute(original_execute):
    """
    기존 execute 함수를 래핑하여 안전한 버전으로 만들기
    """
    def enhanced_execute(request):
        # 코드 추출
        code = request.get('code', '')

        # 빈 코드 처리
        if not code.strip():
            return {
                'success': True,
                'output': '',
                'error': None,
                'variable_count': len([k for k in globals() if not k.startswith('_')])
            }

        # 구문 검사 옵션 (요청에 포함된 경우)
        if request.get('check_only', False):
            check_result = quick_syntax_check(code)
            return {
                'success': check_result['valid'],
                'syntax_check': check_result,
                'output': '',
                'error': check_result.get('error', None)
            }

        # 안전한 실행
        from io import StringIO
        from contextlib import redirect_stdout, redirect_stderr

        stdout_buffer = StringIO()
        stderr_buffer = StringIO()

        # 전역 변수 준비
        repl_globals = globals()

        # stdout/stderr 리다이렉트
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            success, error_msg = enhanced_safe_exec(code, repl_globals)

        # 결과 수집
        stdout_content = stdout_buffer.getvalue()
        stderr_content = stderr_buffer.getvalue()

        # 응답 생성
        response = {
            'success': success,
            'output': stdout_content,
            'error': error_msg if not success else None,
            'variable_count': len([k for k in repl_globals if not k.startswith('_')]),
            'note': 'Enhanced JSON REPL with compile-time checks'
        }

        # stderr가 있으면 추가
        if stderr_content:
            response['stderr'] = stderr_content

        # 디버그 정보 (옵션)
        if request.get('debug', False):
            response['debug_info'] = {
                'code_length': len(code),
                'compile_check': 'passed' if success or 'runtime' in str(error_msg) else 'failed',
                'execution_time': time.time()
            }

        return response

    return enhanced_execute

# 사용 예시
def demonstrate_enhanced_repl():
    """개선된 REPL 데모"""

    test_cases = [
        # 정상 코드
        {"code": "2 + 2", "description": "간단한 표현식"},
        {"code": "x = 10\nprint(f'x = {x}')", "description": "변수 할당과 출력"},

        # 구문 오류
        {"code": "print('Hello' ", "description": "괄호 안 닫음"},
        {"code": "def foo()\n  pass", "description": "콜론 빠짐"},

        # 런타임 오류
        {"code": "1 / 0", "description": "0으로 나누기"},
        {"code": "unknown_variable", "description": "정의되지 않은 변수"},

        # 구문 검사만
        {"code": "def hello():\n    return 'Hi'", "check_only": True, "description": "구문 검사만"}
    ]

    print("\n🧪 개선된 REPL 데모:")
    print("=" * 60)

    # 가상의 execute 함수
    def mock_original_execute(request):
        return {"output": "원본 실행"}

    # 개선된 버전 생성
    enhanced_execute = create_enhanced_json_repl_execute(mock_original_execute)

    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test.get('description', '테스트')}:")
        print(f"   코드: {repr(test['code'])}")

        # 요청 생성
        request = {"code": test['code']}
        if test.get('check_only'):
            request['check_only'] = True

        # 실행
        result = enhanced_execute(request)

        # 결과 출력
        if result['success']:
            print(f"   ✅ 성공")
            if result.get('output'):
                print(f"   출력: {result['output'].strip()}")
            if result.get('syntax_check'):
                print(f"   구문: {result['syntax_check']}")
        else:
            print(f"   ❌ 실패")
            print(f"   에러: {result['error']}")

print("\n✅ 개선된 safe_exec 시스템 준비 완료!")
print("\n통합 방법:")
print("1. safe_exec_helpers.py 파일로 저장")
print("2. json_repl_session.py에서 import")
print("3. 기존 execute 함수를 enhanced_execute로 교체")
