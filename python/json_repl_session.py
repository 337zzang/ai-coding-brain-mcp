#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
🚀 JSON REPL Session for AI Coding Brain v7.1 - Debug Version
"""

import sys
import ast
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

# === 통합 기능을 위한 추가 import (v7.2) ===
try:
    from ai_helpers_new.task_logger import EnhancedTaskLogger, create_task_logger
    TASKLOGGER_AVAILABLE = True
except ImportError:
    TASKLOGGER_AVAILABLE = False
    EnhancedTaskLogger = None

try:
    from repl_kernel.manager import WorkerManager
    WORKER_AVAILABLE = True
except ImportError:
    WORKER_AVAILABLE = False
    WorkerManager = None


# === 네임스페이스 격리를 위한 LazyHelperProxy ===
import importlib
import warnings
import types
from functools import wraps

class LazyHelperProxy(types.ModuleType):
    """지연 로딩과 캐싱을 지원하는 헬퍼 프록시

    네임스페이스 오염을 방지하면서 기존 API와 호환성 유지
    """

    def __init__(self, name='helpers'):
        super().__init__(name)
        self._module = None
        self._warned = set()
        self.__file__ = "LazyHelperProxy"
        self.__doc__ = "AI Helpers v2.0 프록시"

    def _load(self):
        """실제 모듈을 지연 로딩"""
        if self._module is None:
            try:
                self._module = importlib.import_module('ai_helpers_new')
            except ImportError as e:
                raise ImportError(f"Failed to load ai_helpers_new: {e}")

    def __getattr__(self, item):
        """속성 접근 시 실제 모듈에서 가져오고 캐싱"""
        self._load()
        try:
            attr = getattr(self._module, item)
            # 함수나 클래스인 경우만 캐싱 (변경 가능한 값은 제외)
            if callable(attr) or isinstance(attr, type):
                setattr(self, item, attr)
            return attr
        except AttributeError:
            raise AttributeError(f"'helpers' has no attribute '{item}'")

    def __setattr__(self, name, value):
        """헬퍼 함수 덮어쓰기 방지"""
        if name.startswith('_') or name in ['__file__', '__doc__']:
            super().__setattr__(name, value)
        else:
            raise AttributeError(
                f"Cannot override helper function '{name}'. "
                f"Helper functions are read-only for safety."
            )

    def __dir__(self):
        """자동완성을 위한 속성 목록"""
        self._load()
        return dir(self._module)

# 레거시 경고 추적용 전역 변수

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

# === 환경변수 기반 설정 (v7.2) ===
USE_SUBPROCESS_WORKER = os.environ.get('USE_SUBPROCESS_WORKER', '0') == '1'
FLOW_PLAN_ID = os.environ.get('FLOW_PLAN_ID', 'local')
FLOW_TASK_ID = os.environ.get('FLOW_TASK_ID', 'adhoc')
FLOW_TASK_NAME = os.environ.get('FLOW_TASK_NAME', 'repl_session')

# 디버그 모드
DEBUG_MODE = os.environ.get('DEBUG_REPL', '0') == '1'


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
    """AI Helpers v2.0과 워크플로우 시스템 로드 (레거시 제거 버전)"""
    global helpers, HELPERS_AVAILABLE
    if HELPERS_AVAILABLE:
        return True

    try:
        # LazyHelperProxy 인스턴스 생성
        h = LazyHelperProxy('helpers')

        # 전역에는 h와 helpers만 등록 (동일 객체)
        globals()['h'] = h
        globals()['helpers'] = h
        
        # repl_globals에도 helpers 업데이트
        repl_globals['helpers'] = h

        # 레거시 코드 완전 제거 - 더 이상 직접 함수 호출 불가
        # 모든 함수는 h.함수명() 형태로만 호출 가능

        HELPERS_AVAILABLE = True
        print("✅ AI Helpers v2.0 로드 완료 (순수 h.* 모드)")
        return True

    except Exception as e:
        print(f"❌ 헬퍼 로드 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
# 워크플로우 래퍼
WORKFLOW_AVAILABLE = False

try:
    WORKFLOW_AVAILABLE = True
    print("✅ Workflow 시스템 로드 완료", file=sys.stderr)
except ImportError as e:
    print(f"⚠️ Workflow 시스템 로드 실패: {e}", file=sys.stderr)

# 전역 REPL 환경
repl_globals = {
    '__name__': '__main__',
    '__builtins__': builtins,
    'helpers': None,  # 나중에 업데이트
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
# 실행 히스토리 추적 (Task 2)
EXECUTION_HISTORY = []
MAX_HISTORY_SIZE = 100

# === TaskLogger 초기화 (v7.2) ===
REPL_LOGGER = None
if TASKLOGGER_AVAILABLE:
    try:
        # Flow 시스템과 연동된 TaskLogger 생성
        task_number = int(FLOW_TASK_ID.split('-')[-1]) if FLOW_TASK_ID.startswith('T-') else 0
        REPL_LOGGER = EnhancedTaskLogger(
            plan_id=FLOW_PLAN_ID,
            task_number=task_number,
            task_name=FLOW_TASK_NAME
        )
        if DEBUG_MODE:
            print(f"✅ TaskLogger 초기화: Plan={FLOW_PLAN_ID}, Task={task_number}", file=sys.stderr)
    except Exception as e:
        if DEBUG_MODE:
            print(f"⚠️ TaskLogger 초기화 실패: {e}", file=sys.stderr)
        REPL_LOGGER = None


# === Subprocess Worker Manager (Task 3) ===
_worker_manager = None

def get_worker_manager():
    """Worker Manager 싱글톤 인스턴스 반환"""
    global _worker_manager
    if _worker_manager is None:
        if WORKER_AVAILABLE:
            try:
                from repl_kernel.manager import SubprocessWorkerManager
                _worker_manager = SubprocessWorkerManager()
                if DEBUG_MODE:
                    print("[DEBUG] SubprocessWorkerManager initialized", file=sys.stderr)
            except Exception as e:
                print(f"[ERROR] Failed to initialize SubprocessWorkerManager: {e}", file=sys.stderr)
                _worker_manager = None
    return _worker_manager

def execute_locally(code: str, repl_globals: dict) -> Dict[str, Any]:
    """로컬에서 코드 실행 (기존 exec 방식)"""
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
            'helpers_loaded': HELPERS_AVAILABLE,
            'execution_mode': 'local'
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
                    k not in ['helpers', 'sys', 'os', 'json', 'Path', 'dt', 'time', 'platform']]
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
    global execution_count, repl_globals, helpers, EXECUTION_HISTORY
    execution_count += 1


    # 실행 시작 시간 측정 (Task 2)
    exec_start_time = time.perf_counter()
    
    # 헬퍼가 로드되지 않았으면 즉시 로드
    if not HELPERS_AVAILABLE:
        if load_helpers():
            repl_globals['helpers'] = helpers
            repl_globals['h'] = helpers  # h 별칭도 추가

    # === Task 3: Subprocess Worker 분기 ===
    if USE_SUBPROCESS_WORKER and WORKER_AVAILABLE:
        if DEBUG_MODE:
            print(f"[DEBUG] Using subprocess worker for execution", file=sys.stderr)
        
        manager = get_worker_manager()
        if manager:
            try:
                # Worker에서 실행
                result = manager.execute(code, timeout=30.0)
                
                # 결과 형식 통일
                if 'success' not in result:
                    result['success'] = not result.get('error', False)
                if 'debug_info' not in result:
                    result['debug_info'] = {}
                result['debug_info']['execution_mode'] = 'worker'
                
                # Worker는 repl_globals를 직접 수정하지 않으므로 variable_count는 0
                result['variable_count'] = 0
                
            except Exception as e:
                if DEBUG_MODE:
                    print(f"[DEBUG] Worker execution failed: {e}, falling back to local", file=sys.stderr)
                # Fallback to local execution
                result = execute_locally(code, repl_globals)
        else:
            # Worker manager 초기화 실패 시 로컬 실행
            result = execute_locally(code, repl_globals)
    else:
        # 로컬 실행 (기본)
        result = execute_locally(code, repl_globals)


    # 실행 히스토리 기록 (Task 2)
    exec_end_time = time.perf_counter()
    elapsed_ms = (exec_end_time - exec_start_time) * 1000

    history_entry = {
        'timestamp': dt.datetime.utcnow().isoformat() + 'Z',
        'execution_count': execution_count,
        'code': code[:100],  # 처음 100자만
        'success': result['success'],
        'elapsed_ms': round(elapsed_ms, 2)
    }

    EXECUTION_HISTORY.append(history_entry)

    # 순환 버퍼 관리
    if len(EXECUTION_HISTORY) > MAX_HISTORY_SIZE:
        EXECUTION_HISTORY.pop(0)

    # debug_info 업데이트
    result['debug_info']['elapsed_ms'] = round(elapsed_ms, 2)
    result['debug_info']['history_size'] = len(EXECUTION_HISTORY)
    
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



# === 실행 히스토리 헬퍼 함수 (Task 2) ===
def get_recent_executions(n=10):
    """최근 n개의 실행 반환"""
    return EXECUTION_HISTORY[-n:] if n <= len(EXECUTION_HISTORY) else EXECUTION_HISTORY

def get_failed_executions():
    """실패한 실행만 반환"""
    return [e for e in EXECUTION_HISTORY if not e['success']]

def get_execution_stats():
    """실행 통계 반환"""
    if not EXECUTION_HISTORY:
        return {'total': 0, 'success': 0, 'failed': 0, 'success_rate': 0.0}

    total = len(EXECUTION_HISTORY)
    success = sum(1 for e in EXECUTION_HISTORY if e['success'])
    return {
        'total': total,
        'success': success,
        'failed': total - success,
        'success_rate': (success / total) * 100 if total > 0 else 0.0
    }

def clear_execution_history():
    """실행 히스토리 초기화"""
    global EXECUTION_HISTORY
    EXECUTION_HISTORY.clear()
    print("✅ 실행 히스토리가 초기화되었습니다.")

def main():
    """메인 실행 루프"""
    global repl_globals

    # 초기화 메시지
    print("🚀 JSON REPL Session Started", file=sys.stderr)
    print(f"📦 Available: helpers=⏳ (lazy loading), Flow API via h.get_flow_api()", file=sys.stderr)
    
    # 실행 히스토리 함수들을 repl_globals에 추가 (Task 2)
    repl_globals.update({
        'EXECUTION_HISTORY': EXECUTION_HISTORY,
        'get_recent_executions': get_recent_executions,
        'get_failed_executions': get_failed_executions,
        'get_execution_stats': get_execution_stats,
        'clear_execution_history': clear_execution_history
    })
    
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
