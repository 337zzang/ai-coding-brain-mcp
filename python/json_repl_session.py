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
            from workflow_wrapper import wf
            globals()['wf'] = wf
            globals()['workflow'] = wf
        except ImportError:
            print("⚠️ 워크플로우 시스템 로드 실패", file=sys.stderr)

        # flow_project 함수
        try:
            from flow_project_wrapper import flow_project, fp
            globals()['flow_project'] = flow_project
            globals()['fp'] = fp
        except ImportError:
            print("⚠️ flow_project 로드 실패", file=sys.stderr)

        HELPERS_AVAILABLE = True
        print("✅ AI Helpers v2.0 로드 완료", file=sys.stderr)
        return True

    except Exception as e:
        print(f"❌ 헬퍼 로드 실패: {e}", file=sys.stderr)
        return False
# 워크플로우 래퍼
wf = None
WORKFLOW_AVAILABLE = False

try:
    from workflow_wrapper import wf
    WORKFLOW_AVAILABLE = True
except ImportError:
    print("⚠️ Workflow wrapper 로드 실패", file=sys.stderr)

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

def execute_code(code: str) -> Dict[str, Any]:
    """Python 코드 실행"""
    global execution_count, repl_globals, helpers
    execution_count += 1
    
    # 첫 실행 시 helpers 로드 시도
    if execution_count == 1 and not HELPERS_AVAILABLE:
        if load_helpers():
            repl_globals['helpers'] = helpers
            repl_globals['fp'] = helpers.fp if helpers and hasattr(helpers, 'fp') else None

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



def load_global_context_on_start():
    """새 세션 시작 시 글로벌 컨텍스트 확인"""
    try:
        from workflow.global_context import get_global_context_manager
        ctx = get_global_context_manager()
        summary = ctx.get_all_projects_summary()

        if summary:
            print("\n" + "="*60)
            print("🔄 이전 작업 히스토리")
            print("="*60)

            # 최근 프로젝트 순으로 표시
            recent = ctx.get_recent_projects(5)
            for proj_name in recent:
                if proj_name in summary:
                    info = summary[proj_name]
                    print(f"📂 {proj_name}")
                    print(f"   최종: {info.get('last_opened', 'Unknown')[:19]}")  # 날짜 시간만
                    print(f"   태스크: {info.get('tasks_count', 0)}개")

            # 현재 프로젝트 확인
            current_project = ctx.global_context.get('current_project')
            if current_project:
                print(f"\n💡 마지막 작업: {current_project}")
                print(f"   계속하려면: fp('{current_project}')")

            print("="*60)
    except Exception as e:
        pass  # 조용히 무시



# 글로벌 컨텍스트 명령어
def gc():
    """모든 프로젝트 컨텍스트 표시"""
    from workflow.global_context import get_global_context_manager
    ctx = get_global_context_manager()
    summary = ctx.get_all_projects_summary()

    print("\n🌍 글로벌 프로젝트 컨텍스트")
    print("="*60)

    if not summary:
        print("아직 저장된 프로젝트가 없습니다.")
        return

    # 최근 프로젝트 순으로 정렬
    recent = ctx.get_recent_projects(10)
    for proj_name in recent:
        if proj_name in summary:
            info = summary[proj_name]
            print(f"\n📂 {proj_name}")
            print(f"   경로: {info.get('path', 'Unknown')}")
            print(f"   최종: {info.get('last_opened', 'Unknown')[:19]}")
            print(f"   태스크: {info.get('tasks_count', 0)}개")
            print(f"   최근: {info.get('recent_work', '')}")

def project_history(limit=10):
    """최근 프로젝트 이동 히스토리"""
    from workflow.global_context import get_global_context_manager
    ctx = get_global_context_manager()
    history = ctx.get_project_history(limit)

    print(f"\n📜 최근 프로젝트 이동 (최근 {limit}개)")
    print("="*60)

    if not history:
        print("이동 히스토리가 없습니다.")
        return

    for item in history:
        timestamp = item['timestamp'][:19]  # 날짜 시간만
        print(f"{timestamp}: {item['project']}")
        print(f"   경로: {item['path']}")


# REPL 초기화 시 글로벌 컨텍스트 로드
load_global_context_on_start()
