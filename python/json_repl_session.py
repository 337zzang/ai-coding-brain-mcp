#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
🚀 JSON REPL Session for AI Coding Brain v7.1 - Debug Version
"""

import sys
import os
import json
import tempfile
import io
import traceback
import time
import datetime as dt
import platform
import subprocess
import builtins
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import contextmanager

# 프로젝트 경로 초기화 (o3 권장사항 반영)
from pathlib import Path

def _init_project_paths():
    """프로젝트 루트를 찾아 sys.path 설정"""
    current = Path(__file__).resolve().parent

    # 프로젝트 루트 찾기
    while current != current.parent:
        if (current / '.ai-brain.config.json').exists() or (current / '.git').exists():
            project_root = str(current)

            # sys.path 설정 (중복 방지)
            for path in [project_root, str(current / 'python')]:
                if path not in sys.path and os.path.exists(path):
                    sys.path.insert(0, path)

            # 작업 디렉토리 설정
            if os.getcwd() != project_root:
                os.chdir(project_root)

            return project_root
        current = current.parent

    return os.getcwd()

PROJECT_ROOT = _init_project_paths()


# Windows에서 UTF-8 출력 강제 설정
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Windows 코드 페이지 설정
    try:
        subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
    except:
        pass

# 기본 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# AI Helpers v2 통합 - 지연 로딩으로 변경
helpers = None
HELPERS_AVAILABLE = False

def load_helpers():
    """AI Helpers v2.0과 워크플로우 시스템 로드"""
    global helpers, HELPERS_AVAILABLE
    if HELPERS_AVAILABLE:
        return True

    try:
        # AI Helpers v2.0 import
        import ai_helpers_new as h

        # 글로벌 네임스페이스에 등록
        globals()['h'] = h
        globals()['helpers'] = h

        # 자주 사용하는 함수들을 직접 등록
        # 파일 작업
        globals()['read'] = h.read
        globals()['write'] = h.write
        globals()['append'] = h.append
        globals()['read_json'] = h.read_json
        globals()['write_json'] = h.write_json
        globals()['exists'] = h.exists

        # 코드 분석/수정
        globals()['parse'] = h.parse
        globals()['view'] = h.view
        globals()['replace'] = h.replace

        # 검색
        globals()['search_files'] = h.search_files
        globals()['search_code'] = h.search_code
        globals()['find_function'] = h.find_function
        globals()['grep'] = h.grep

        # LLM
        globals()['ask_o3_async'] = h.ask_o3_async
        globals()['check_o3_status'] = h.check_o3_status
        globals()['get_o3_result'] = h.get_o3_result

        # Git 함수들
        if hasattr(h, 'git_status'):
            globals()['git_status'] = h.git_status
            globals()['git_add'] = h.git_add
            globals()['git_commit'] = h.git_commit
            globals()['git_push'] = h.git_push
            globals()['git_pull'] = h.git_pull
            globals()['git_branch'] = h.git_branch
            globals()['git_log'] = h.git_log
            globals()['git_diff'] = h.git_diff

        # Project 함수들
        if hasattr(h, 'get_current_project'):
            globals()['get_current_project'] = h.get_current_project
            globals()['scan_directory'] = h.scan_directory
            globals()['scan_directory_dict'] = h.scan_directory_dict
            globals()['create_project_structure'] = h.create_project_structure

        # 워크플로우 시스템
        try:
            from ai_helpers_new.simple_flow_commands import flow, wf
            globals()['wf'] = wf
            globals()['workflow'] = wf
            globals()['flow'] = flow
            globals()['wf'] = wf
            print("✅ 워크플로우 시스템 로드 완료", file=sys.stderr)
        except ImportError as e:
            print(f"⚠️ 워크플로우 시스템 로드 실패: {e}", file=sys.stderr)

        # flow_project 함수
        try:
            from ai_helpers_new.project import flow_project, fp
            globals()['flow_project'] = flow_project
            globals()['fp'] = fp
        except ImportError:
            print("⚠️ flow_project 로드 실패", file=sys.stderr)

        HELPERS_AVAILABLE = True
        print("✅ AI Helpers v2.0 로드 완료", file=sys.stderr)
        return True

    except SyntaxError as e:
        # f-string 백슬래시 특별 처리
        if 'f-string expression part cannot include a backslash' in str(e):
            result['success'] = False
            result['error'] = format_fstring_error(e, code)
            result['error_type'] = 'fstring_backslash'
            result['suggestion'] = 'Use \\\\ instead of \\ in f-strings'
            return result
        else:
            # 다른 SyntaxError는 기존 방식으로 처리
            result['success'] = False
            result['error'] = f"SyntaxError: {str(e)}"
            result['traceback'] = traceback.format_exc()
            return result
    except Exception as e:
        print(f"❌ 헬퍼 로드 실패: {e}", file=sys.stderr)
        return False
# 워크플로우 래퍼
wf = None
WORKFLOW_AVAILABLE = False

try:
    from ai_helpers_new.simple_flow_commands import flow, wf
    WORKFLOW_AVAILABLE = True
    print("✅ Workflow 시스템 로드 완료", file=sys.stderr)
except ImportError as e:
    print(f"⚠️ Workflow 시스템 로드 실패: {e}", file=sys.stderr)

# 전역 REPL 환경
repl_globals = {
    '__name__': '__main__',
    '__builtins__': builtins,
    'helpers': None,  # 나중에 업데이트
    'wf': wf,
    'fp': None,  # 나중에 업데이트
    'sys': sys,
    'os': os,
    'json': json,
    'Path': Path,
    'dt': dt,
    'time': time,
    'platform': platform,
}

# 실행 카운터
execution_count = 0

@contextmanager
def capture_output():
    """출력 캡처 컨텍스트"""
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    try:
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        yield stdout_capture, stderr_capture
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def format_fstring_error(e: SyntaxError, code: str) -> str:
    """f-string 백슬래시 오류를 위한 친화적 메시지 생성"""
    lines = code.split('\n')
    line_no = e.lineno if e.lineno else 1
    problem_line = lines[line_no - 1].strip() if line_no <= len(lines) else ''

    error_msg = f"""[ERROR] f-string 백슬래시 오류

문제: f-string 내부에서 백슬래시(\\)를 직접 사용할 수 없습니다.
위치: Line {line_no}
코드: {problem_line}

[해결 방법]

1. 백슬래시 두 번 사용:
   f"{{path.replace('\\\\', '/')}}"

2. chr(92) 사용:
   f"{{path.replace(chr(92), '/')}}"

3. 변수로 분리:
   sep = "\\\\"
   f"{{path.replace(sep, '/')}}"

4. f-string 밖에서 처리:
   clean_path = path.replace("\\\\", "/")
   f"{{clean_path}}"

TIP: 가장 간단한 방법은 백슬래시를 두 번(\\\\) 쓰는 것입니다.
"""
    return error_msg

def execute_code(code: str) -> Dict[str, Any]:
    """Python 코드 실행"""
    global execution_count, repl_globals, helpers
    execution_count += 1
    
    # 헬퍼가 로드되지 않았으면 즉시 로드
    if not HELPERS_AVAILABLE:
        if load_helpers():
            repl_globals['helpers'] = helpers
            repl_globals['h'] = helpers  # h 별칭도 추가
            repl_globals['fp'] = fp if 'fp' in globals() else None
            repl_globals['flow'] = flow if 'flow' in globals() else None
            repl_globals['wf'] = wf if 'wf' in globals() else None

    result = {
        'success': True,
        'language': 'python',
        'session_mode': 'JSON_REPL',
        'stdout': '',
        'stderr': '',
        'variable_count': 0,
        'note': 'JSON REPL Session - Variables persist between executions',
        'debug_info': {
            'repl_process_active': True,
            'repl_ready': True,
            'execution': 'success',
            'helpers_loaded': HELPERS_AVAILABLE
        },
        'timestamp': dt.datetime.now().isoformat() + 'Z'
    }

    try:
        # 코드 실행
        with capture_output() as (stdout, stderr):
            exec(code, repl_globals)

        result['stdout'] = stdout.getvalue()
        result['stderr'] = stderr.getvalue()

        # 사용자 정의 변수 카운트
        user_vars = [k for k in repl_globals.keys() 
                    if not k.startswith('_') and 
                    k not in ['helpers', 'wf', 'fp', 'sys', 'os', 'json', 'Path', 'dt', 'time', 'platform']]
        result['variable_count'] = len(user_vars)

    except Exception as e:
        result['success'] = False
        result['stderr'] = f"❌ Runtime Error: {type(e).__name__}: {str(e)}"
        result['debug_info']['execution'] = 'error'

        # 상세 에러 정보는 stderr에 추가
        with io.StringIO() as error_details:
            traceback.print_exc(file=error_details)
            result['stderr'] += '\n' + error_details.getvalue()

    return result

def read_json_input():
    """JSON 입력 읽기"""
    try:
        line = sys.stdin.readline()
        if not line:
            return None
        return line.strip()
    except:
        return None

def write_json_output(response):
    """JSON 출력 쓰기"""
    json_str = json.dumps(response, ensure_ascii=False)
    sys.stdout.write(json_str + '\n')
    sys.stdout.flush()

def main():
    """메인 실행 루프"""
    global repl_globals

    # 초기화 메시지
    print("🚀 JSON REPL Session Started", file=sys.stderr)
    print(f"📦 Available: helpers=⏳, wf={'✓' if wf else '✗'}", file=sys.stderr)
    
    # 준비 완료 신호 (MCP 서버가 기다리는 신호)
    print("__READY__", flush=True)

    # 메인 루프
    while True:
        try:
            # JSON 입력 읽기
            code_input = read_json_input()
            if code_input is None:
                break

            # 요청 파싱
            request = json.loads(code_input)
            request_id = request.get('id')
            request_type = request.get('method', '').split('/')[-1]

            # execute 요청 처리
            if request_type == 'execute':
                params = request.get('params', {})
                code = params.get('code', '')

                # 코드 실행
                result = execute_code(code)

                # 응답 생성
                response = {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'result': result
                }

                # 응답 전송
                write_json_output(response)

            else:
                # 지원하지 않는 메소드
                error_response = {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'error': {
                        'code': -32601,
                        'message': f'Method not found: {request_type}'
                    }
                }
                write_json_output(error_response)

        except json.JSONDecodeError as e:
            # JSON 파싱 에러
            error_response = {
                'jsonrpc': '2.0',
                'id': None,
                'error': {
                    'code': -32700,
                    'message': f'Parse error: {str(e)}'
                }
            }
            write_json_output(error_response)

        except KeyboardInterrupt:
            break

        except Exception as e:
            # 일반 에러
            error_response = {
                'jsonrpc': '2.0',
                'id': request_id if 'request_id' in locals() else None,
                'error': {
                    'code': -32603,
                    'message': f'Internal error: {str(e)}'
                }
            }
            write_json_output(error_response)

if __name__ == '__main__':
    main()



# Global context functions removed - module does not exist
