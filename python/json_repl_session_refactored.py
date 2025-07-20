#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
🚀 JSON REPL Session for AI Coding Brain v6.0
==============================================
"""

# 안전한 실행 헬퍼 (구문 검사 포함)
try:
    from safe_exec_helpers import enhanced_safe_exec, quick_syntax_check
from json_utils import safe_json_write
    SAFE_EXEC_AVAILABLE = True
except ImportError:
    enhanced_safe_exec = None
    quick_syntax_check = None

    SAFE_EXEC_AVAILABLE = False

import sys
import os



# Windows에서 UTF-8 출력 강제 설정

if sys.platform == 'win32':

    import locale

    sys.stdout.reconfigure(encoding='utf-8')

    sys.stderr.reconfigure(encoding='utf-8')

    os.environ['PYTHONIOENCODING'] = 'utf-8'



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



# 기본 경로 설정





# Enhanced Safe Execution v2 - f-string 및 정규식 안전성 검사

try:

    from safe_execution_v2 import (

        safe_exec as safe_exec_v2,

        check_regex,

        benchmark_regex_safety

    )

    SAFE_EXEC_V2_AVAILABLE = True

except ImportError:

    SAFE_EXEC_V2_AVAILABLE = False

current_dir = os.path.dirname(os.path.abspath(__file__))

if current_dir not in sys.path:

    sys.path.insert(0, current_dir)



# AI Helpers v2 통합

try:

    from ai_helpers_v2 import (

        # File operations

        read_file, write_file, create_file, file_exists, append_to_file,

        read_json, write_json,

        # Search operations

        search_code, search_files, grep, find_function, find_class,

        # Code operations

        parse_with_snippets, insert_block, replace_block,

        # Git operations

        git_status, git_add, git_commit, git_branch, git_push, git_pull,

        # Project operations

        get_current_project, scan_directory_dict, create_project_structure,

        # Core operations

        get_metrics, clear_cache, get_execution_history

    )

    AI_HELPERS_V2_LOADED = True

    print("✅ AI Helpers v2 로드 성공")

except ImportError as e:

    print(f"⚠️ AI Helpers v2 로드 실패: {e}")

    AI_HELPERS_V2_LOADED = False







# 실행 설정

CONFIG = {

    'use_safe_exec_v2': True,      # Enhanced Safe Execution v2 사용

    'fstring_check': True,         # f-string 미정의 변수 검사

    'regex_check': True,           # 정규식 안전성 검사

    'redos_protection': True,      # ReDoS 패턴 경고

    'show_warnings': True,         # 경고 메시지 표시

}



# ============================================================================

# 🌟 전역 변수 초기화

# ============================================================================

repl_globals = {}  # REPL 전역 네임스페이스

execution_count = 0  # 실행 카운터



class AIHelpersV2:

    """AI Helpers v2 통합 래퍼 - Workflow 시스템 포함"""



    def __init__(self):

        """모든 helper 함수를 메서드로 동적 로드"""

        # 전역 네임스페이스에서 helper 함수들 가져오기

        import_names = [

            # File operations

            'read_file', 'write_file', 'create_file', 'file_exists', 'append_to_file',

            'read_json', 'write_json',

            # Search operations

            'search_code', 'search_files', 'grep', 'find_function', 'find_class',

            # Code operations

            'parse_with_snippets', 'parse_file', 'insert_block', 'replace_block',

            'extract_functions', 'extract_code_elements',

            # Git operations

            'git_status', 'git_add', 'git_commit', 'git_branch', 'git_push', 'git_pull',

            # Project operations

            'get_current_project', 'scan_directory_dict', 'create_project_structure',

            'fp', 'flow_project', 'scan_directory',

            # Workflow

            'workflow',

            # Core operations

            'get_metrics', 'clear_cache', 'get_execution_history'

        ]



        # 각 함수를 메서드로 추가

        for name in import_names:

            if name in globals():

                setattr(self, name, globals()[name])

            else:

                # 없는 함수는 더미로 생성

                setattr(self, name, lambda *args, **kwargs: f"{name} not implemented")



        # 추가 메서드들

        self.parse_file = self.parse_with_snippets if hasattr(self, 'parse_with_snippets') else lambda x: {}

        self.extract_functions = self.parse_file

        self.extract_code_elements = self.parse_file





        # 워크플로우 캐시 추가 (o3 조언)
        self._wm_cache = {}

        # flow_project 실제 구현 연결
        self.flow_project = self._flow_project
        self.fp = self._flow_project





# Windows에서 UTF-8 출력 강제 설정

if sys.platform == 'win32':

    import locale

    sys.stdout.reconfigure(encoding='utf-8')

    sys.stderr.reconfigure(encoding='utf-8')

    os.environ['PYTHONIOENCODING'] = 'utf-8'



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



# 기본 경로 설정





# Enhanced Safe Execution v2 - f-string 및 정규식 안전성 검사

try:

    from safe_execution_v2 import (

        safe_exec as safe_exec_v2,

        check_regex,

        benchmark_regex_safety

    )

    SAFE_EXEC_V2_AVAILABLE = True

except ImportError:

    SAFE_EXEC_V2_AVAILABLE = False

current_dir = os.path.dirname(os.path.abspath(__file__))

if current_dir not in sys.path:

    sys.path.insert(0, current_dir)



# AI Helpers v2 통합

try:

    from ai_helpers_v2 import (

        # File operations

        read_file, write_file, create_file, file_exists, append_to_file,

        read_json, write_json,

        # Search operations

        search_code, search_files, grep, find_function, find_class,

        # Code operations

        parse_with_snippets, insert_block, replace_block,

        # Git operations

        git_status, git_add, git_commit, git_branch, git_push, git_pull,

        # Project operations

        get_current_project, scan_directory_dict, create_project_structure,

        # Core operations

        get_metrics, clear_cache, get_execution_history

    )

    AI_HELPERS_V2_LOADED = True

    print("✅ AI Helpers v2 로드 성공")

except ImportError as e:

    print(f"⚠️ AI Helpers v2 로드 실패: {e}")

    AI_HELPERS_V2_LOADED = False







# 실행 설정

CONFIG = {

    'use_safe_exec_v2': True,      # Enhanced Safe Execution v2 사용

    'fstring_check': True,         # f-string 미정의 변수 검사

    'regex_check': True,           # 정규식 안전성 검사

    'redos_protection': True,      # ReDoS 패턴 경고

    'show_warnings': True,         # 경고 메시지 표시

}



# ============================================================================

# 🌟 전역 변수 초기화

# ============================================================================

repl_globals = {}  # REPL 전역 네임스페이스

execution_count = 0  # 실행 카운터



class AIHelpersV2:

    """AI Helpers v2 통합 래퍼 - Workflow 시스템 포함"""



    def __init__(self):

        """모든 helper 함수를 메서드로 동적 로드"""

        # 전역 네임스페이스에서 helper 함수들 가져오기

        import_names = [

            # File operations

            'read_file', 'write_file', 'create_file', 'file_exists', 'append_to_file',

            'read_json', 'write_json',

            # Search operations

            'search_code', 'search_files', 'grep', 'find_function', 'find_class',

            # Code operations

            'parse_with_snippets', 'parse_file', 'insert_block', 'replace_block',

            'extract_functions', 'extract_code_elements',

            # Git operations

            'git_status', 'git_add', 'git_commit', 'git_branch', 'git_push', 'git_pull',

            # Project operations

            'get_current_project', 'scan_directory_dict', 'create_project_structure',

            'fp', 'flow_project', 'scan_directory',

            # Workflow

            'workflow',

            # Core operations

            'get_metrics', 'clear_cache', 'get_execution_history'

        ]



        # 각 함수를 메서드로 추가

        for name in import_names:

            if name in globals():

                setattr(self, name, globals()[name])

            else:

                # 없는 함수는 더미로 생성

                setattr(self, name, lambda *args, **kwargs: f"{name} not implemented")



        # 추가 메서드들

        self.parse_file = self.parse_with_snippets if hasattr(self, 'parse_with_snippets') else lambda x: {}

        self.extract_functions = self.parse_file

        self.extract_code_elements = self.parse_file





def ensure_helpers_loaded():

    """AI Helpers v2를 안전하게 로드"""

    import sys

    import pathlib

    

    try:

        # 프로젝트 루트를 sys.path에 추가

        project_root = pathlib.Path(__file__).parent.parent

        if str(project_root) not in sys.path:

            sys.path.insert(0, str(project_root))

        

        # AI Helpers v2 사용

        if AI_HELPERS_V2_LOADED:

            helpers = AIHelpersV2()

            print("✅ AI Helpers v2 로드 완료!")

            return helpers

        else:

            print("⚠️ AI Helpers v2 로드 실패 - 기능이 제한될 수 있습니다")

            # 빈 helpers 객체 반환

            return AIHelpersV2()

    

    except Exception as e:

        print(f"❌ helpers 로딩 실패: {e}")

        import traceback

        traceback.print_exc()

        return None

    

def initialize_repl():

    """REPL 환경 초기화"""

    global repl_globals

    

    # 1. helpers 객체 생성

    helpers = ensure_helpers_loaded()

    if helpers:

        repl_globals['helpers'] = helpers

        repl_globals['h'] = helpers

        builtins.helpers = helpers

    else:

        sys.stderr.write('⚠️ helpers 로딩 실패\n')

    

    # 2. 핵심 기능들만 전역에 노출 (q_tools와 중복 제거)

    essential_funcs = {}

    

    # 워크플로우 관리 (최우선 - q_tools에 없음)

    if hasattr(helpers, 'execute_workflow_command'):

        essential_funcs['workflow'] = helpers.execute_workflow_command

        essential_funcs['wf'] = helpers.execute_workflow_command

    

    # 프로젝트 관리 (최우선 - q_tools에 없음)

    if hasattr(helpers, 'flow_project'):

        essential_funcs['flow_project'] = helpers.flow_project

        essential_funcs['fp'] = helpers.flow_project

    

    if hasattr(helpers, 'list_desktop_projects'):

        essential_funcs['list_projects'] = helpers.list_desktop_projects

        essential_funcs['lp'] = helpers.list_desktop_projects

    

    if hasattr(helpers, 'get_project_info'):

        essential_funcs['project_info'] = helpers.get_project_info

        essential_funcs['pi'] = helpers.get_project_info

    

    # 히스토리 관리 (최우선 - q_tools에 없음)

    if hasattr(helpers, 'add_history_action'):

        essential_funcs['add_history_action'] = helpers.add_history_action

        essential_funcs['add_history'] = helpers.add_history_action

        essential_funcs['show_history'] = helpers.show_history

        essential_funcs['continue_from_last'] = helpers.continue_from_last

        essential_funcs['get_history'] = helpers.get_history

    

    # Git 고급 기능 (q_tools에 없는 것들)

    if hasattr(helpers, 'git_add'):

        essential_funcs['git_add'] = helpers.git_add

    if hasattr(helpers, 'git_push'):

        essential_funcs['git_push'] = helpers.git_push

    if hasattr(helpers, 'git_pull'):

        essential_funcs['git_pull'] = helpers.git_pull

    

    # 고급 파일 관리 (q_tools에 없는 것들)

    if hasattr(helpers, 'scan_directory_dict'):

        essential_funcs['scan_directory_dict'] = helpers.scan_directory_dict

    if hasattr(helpers, 'get_file_info'):

        essential_funcs['get_file_info'] = helpers.get_file_info

    if hasattr(helpers, 'create_directory'):

        essential_funcs['create_directory'] = helpers.create_directory

    if hasattr(helpers, 'move_file'):

        essential_funcs['move_file'] = helpers.move_file

    if hasattr(helpers, 'insert_block'):

        essential_funcs['insert_block'] = helpers.insert_block

    

    # 전역에 추가

    for name, func in essential_funcs.items():

        if callable(func):

            repl_globals[name] = func

    

    print(f"✅ 핵심 helpers 기능 로드 완료: {len(essential_funcs)}개 (중복 제거)")

    

    # 3. 기본 모듈들

    import os

    import sys

    import json

    import time

    from pathlib import Path

    import datetime as dt

    import numpy as np

    import pandas as pd

    

    repl_globals.update({

        'os': os,

        'sys': sys,

        'json': json,

        'Path': Path,

        'datetime': dt,

        'np': np,

        'pd': pd,

        'time': time,

    })

    

    # 4. 프로젝트 자동 초기화 (현재 디렉토리)

    try:

        # 기본적으로 ai-coding-brain-mcp 프로젝트로 설정

        default_project = "ai-coding-brain-mcp"

        

        # OS 독립적인 Desktop 경로 찾기

        desktop_paths = [

            Path.home() / "Desktop",  # 영문 Windows/Mac/Linux

            Path.home() / "바탕화면",  # 한글 Windows

            Path.home() / "桌面",      # 중국어

            Path.home() / "デスクトップ"  # 일본어

        ]

        

        project_path = None

        for desktop in desktop_paths:

            if desktop.exists():

                test_path = desktop / default_project

                if test_path.exists():

                    project_path = test_path

                    os.chdir(str(project_path))

                    project_name = default_project

                    break

        

        # 프로젝트를 찾지 못한 경우 현재 디렉토리 사용

        if not project_path:

            project_path = Path.cwd()

            project_name = project_path.name

    except Exception as e:

        pass

    

    # 5. Git Version Manager (제거됨 - 파일이 존재하지 않음)

    # git_version_manager 모듈이 프로젝트에 없어 제거

    git_manager = None



    # 6. q_tools 자동 로드 (추가됨)

    try:

        import sys

        import os

        

        # q_tools 경로 추가

        current_dir = os.getcwd()

        python_path = os.path.join(current_dir, "python")

        if python_path not in sys.path:

            sys.path.insert(0, python_path)

        

        # q_tools 모든 함수 로드

        q_functions = {}

        for name in dir(q_tools):

            if not name.startswith('_') and callable(getattr(q_tools, name)):

                q_functions[name] = getattr(q_tools, name)

        

        # repl_globals에 q_tools 함수들 추가

        repl_globals.update(q_functions)

        

        # builtins에도 추가 (글로벌 접근 가능)

        for name, func in q_functions.items():

            setattr(builtins, name, func)

        

        print(f"✅ q_tools 로드 완료! {len(q_functions)}개 함수 사용 가능")

        

    except Exception as e:

        pass

    

    # 7. AST 기반 코드 도구 자동 로드 (추가됨)

    try:

        # ai_helpers_v2 경로 추가

        ai_helpers_path = os.path.join(python_path, "ai_helpers_v2")

        if ai_helpers_path not in sys.path:

            sys.path.insert(0, ai_helpers_path)



        # 1. ez_code 개선된 함수들

        try:

            from ez_code import ez_parse, ez_replace, ez_view, ez_replace_safe

            repl_globals.update({

                'ez_parse': ez_parse,

                'ez_replace': ez_replace,

                'ez_view': ez_view,

                'ez_replace_safe': ez_replace_safe,

                # 짧은 별칭 추가

                'ezp': ez_parse,      # 파싱

                'ezr': ez_replace,    # 교체

                'ezv': ez_view,       # 보기

                'ezrs': ez_replace_safe  # 안전한 교체

            })

            print("  ✅ ez_code 함수 로드: ez_parse(ezp), ez_replace(ezr), ez_view(ezv), ez_replace_safe(ezrs)")

        except Exception as e:

            print(f"  ❌ ez_code 로드 실패: {e}")



        # 2. 개선된 AST 파서

        try:

            from improved_ast_parser import ez_parse_advanced, ez_parse_cached, ImprovedASTParser

            repl_globals.update({

                'ez_parse_advanced': ez_parse_advanced,

                'ez_parse_cached': ez_parse_cached,

                'ImprovedASTParser': ImprovedASTParser,

                # 짧은 별칭

                'ezpa': ez_parse_advanced,  # 고급 파싱

                'ezpc': ez_parse_cached     # 캐시된 파싱

            })

            print("  ✅ 개선된 AST 파서 로드: ez_parse_advanced(ezpa), ez_parse_cached(ezpc)")

        except Exception as e:

            print(f"  ❌ improved_ast_parser 로드 실패: {e}")



        # 3. 안전한 코드 수정 도구

        try:

            from safe_code_modifier import SafeCodeModifier

            repl_globals.update({

                'SafeCodeModifier': SafeCodeModifier

            })

            # 간편한 인스턴스 생성

            safe_modifier = SafeCodeModifier()

            repl_globals['safe_modifier'] = safe_modifier

            repl_globals['safe_replace'] = safe_modifier.safe_replace

            repl_globals['sr'] = safe_modifier.safe_replace  # 짧은 별칭

            print("  ✅ 안전한 코드 수정 도구 로드: SafeCodeModifier, safe_replace(sr)")

        except Exception as e:

            print(f"  ❌ safe_code_modifier 로드 실패: {e}")



        print("✅ AST 기반 코드 도구 로드 완료!")



        # 사용 가이드 출력

        print("""

📚 AST 코드 도구 사용법:

  • ezp('file.py') - 파일 구조 파싱

  • ezv('file.py', 'function_name') - 함수 코드 보기

  • ezr('file.py', 'function_name', new_code) - 함수 교체

  • ezrs('file.py', 'function_name', new_code) - 안전한 교체 (문법 검증)

  • ezpa('file.py', include_docstrings=True) - 고급 파싱

  • sr('file.py', 'function_name', new_code) - 안전한 교체 (별칭)

        """)



    except Exception as e:

        print(f"❌ AST 기반 코드 도구 로드 실패: {e}")



    except Exception as e:

        print(f"❌ AST 기반 코드 도구 로드 실패: {e}")







    # 7. AST 기반 코드 도구 자동 로드 (추가됨)

    try:

        # ai_helpers_v2 경로 추가

        ai_helpers_path = os.path.join(python_path, "ai_helpers_v2")

        if ai_helpers_path not in sys.path:

            sys.path.insert(0, ai_helpers_path)



        # 1. ez_code 개선된 함수들

        try:

            from ez_code import ez_parse, ez_replace, ez_view, ez_replace_safe

            repl_globals.update({

                'ez_parse': ez_parse,

                'ez_replace': ez_replace,

                'ez_view': ez_view,

                'ez_replace_safe': ez_replace_safe

            })

            print("  ✅ ez_code 함수 로드: ez_parse, ez_replace, ez_view, ez_replace_safe")

        except Exception as e:

            print(f"  ❌ ez_code 로드 실패: {e}")



        # 2. 개선된 AST 파서

        try:

            from improved_ast_parser import ez_parse_advanced, ez_parse_cached, ImprovedASTParser

            repl_globals.update({

                'ez_parse_advanced': ez_parse_advanced,

                'ez_parse_cached': ez_parse_cached,

                'ImprovedASTParser': ImprovedASTParser

            })

            print("  ✅ 개선된 AST 파서 로드: ez_parse_advanced, ez_parse_cached")

        except Exception as e:

            print(f"  ❌ improved_ast_parser 로드 실패: {e}")



        # 3. 안전한 코드 수정 도구

        try:

            from safe_code_modifier import SafeCodeModifier

            repl_globals.update({

                'SafeCodeModifier': SafeCodeModifier

            })

            # 간편한 인스턴스 생성

            safe_modifier = SafeCodeModifier()

            repl_globals['safe_modifier'] = safe_modifier

            repl_globals['safe_replace'] = safe_modifier.safe_replace

            print("  ✅ 안전한 코드 수정 도구 로드: SafeCodeModifier, safe_replace")

        except Exception as e:

            print(f"  ❌ safe_code_modifier 로드 실패: {e}")



        print("✅ AST 기반 코드 도구 로드 완료!")



    except Exception as e:

        print(f"❌ AST 기반 코드 도구 로드 실패: {e}")





        print(f"❌ q_tools 로드 실패: {e}")



# ============================================================================

# 💻 코드 실행

# ============================================================================



def safe_exec(code: str, globals_dict: dict) -> tuple[bool, str]:

    """

    안전한 코드 실행 - Enhanced v2 통합



    v2가 사용 가능하고 설정이 활성화되어 있으면 v2 사용,

    그렇지 않으면 기존 방식 사용

    """

    # Enhanced Safe Execution v2 사용 (가능한 경우)

    if SAFE_EXEC_V2_AVAILABLE and CONFIG.get('use_safe_exec_v2', True):

        try:

            success, output = safe_exec_v2(code, globals_dict)

            return success, output

        except Exception as e:

            # v2 실패 시 기존 방식으로 폴백

            print(f"⚠️ Safe Execution v2 오류, 기본 모드로 전환: {e}")



    # 기존 방식 (enhanced_safe_exec 또는 기본)

    try:

        return enhanced_safe_exec(code, globals_dict)

    except NameError:

        # enhanced_safe_exec가 import되지 않은 경우 계속 진행

        pass



    # 최종 폴백 - 기본 실행

    from textwrap import dedent



    try:

        # 들여쓰기 정리

        dedented_code = dedent(code).strip()



        # 컴파일 단계 (구문 검사)

        try:

            compiled_code = compile(dedented_code, '<json_repl>', 'exec')

        except SyntaxError as e:

            error_msg = f"❌ 구문 오류: {e.msg}"

            if e.lineno:

                error_msg += f" (라인 {e.lineno})"

            return False, error_msg



        # 실행

        exec(compiled_code, globals_dict)

        return True, ""



    except Exception as e:

        return False, f"❌ 런타임 오류: {type(e).__name__}: {str(e)}"

def execute_code(code: str) -> Dict[str, Any]:

    """Python 코드 실행"""

    global execution_count

    

    start_time = time.time()

    

    try:

        # safe_exec를 사용하여 코드 실행

        # safe_exec는 이미 stdout을 캡처하여 반환함

        success, output_or_error = safe_exec(code, repl_globals)

        

        if success:

            stdout_output = output_or_error

            stderr_output = ""

        else:

            stdout_output = ""

            stderr_output = output_or_error

            

        execution_count += 1

        

        # 자동 저장 (10회마다)

        if execution_count % 10 == 0 and 'save_context' in repl_globals:

            try:

                repl_globals['save_context']()

            except Exception:

                pass

        

        # 변수 개수 계산

        user_vars = [k for k in repl_globals.keys() 

                    if not k.startswith('_') and k not in ['__builtins__']]

        

        return {

            "success": True,

            "stdout": stdout_output,

            "stderr": stderr_output,

            "execution_time": time.time() - start_time,

            "variable_count": len(user_vars),

            "execution_count": execution_count,

            "session_mode": "JSON_REPL",

            "note": "JSON REPL Session - Variables persist between executions",

            "debug_info": {

                "repl_process_active": True,

                "repl_ready": True,

                "execution": "success"

            }

        }

        

    except Exception as e:

        execution_count += 1

        

        return {

            "success": False,

            "stdout": "",

            "stderr": f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",

            "execution_time": time.time() - start_time,

            "variable_count": len(repl_globals),

            "execution_count": execution_count,

            "error": str(e),

            "error_type": type(e).__name__,

            "session_mode": "JSON_REPL",

            "debug_info": {

                "repl_process_active": True,

                "repl_ready": True,

                "execution": "error"

            }

        }



# ============================================================================

# 🔌 JSON 통신

# ============================================================================



def read_json_input() -> Optional[str]:

    """EOT 문자로 종료되는 JSON 입력 읽기"""

    try:

        input_data = ""

        while True:

            char = sys.stdin.read(1)

            if not char:  # EOF

                return None

            if char == '\x04':  # EOT

                break

            input_data += char

        

        return input_data.strip()

    except Exception:

        return None



def send_json_response(response: Dict[str, Any]):

    """JSON 응답 전송 (EOT 문자로 종료)"""

    try:

        response['timestamp'] = dt.datetime.now().isoformat()

        response_json = json.dumps(response, ensure_ascii=False)

        # 프로토콜 태그로 감싸서 안전하게 전송

        sys.stdout.write("__JSON_START__" + response_json + "__JSON_END__\x04")

        sys.stdout.flush()

    except Exception as e:

        error_response = {

            "success": False,

            "error": f"Response encoding error: {str(e)}",

            "error_type": "ResponseError"

        }

        sys.stdout.write("__JSON_START__" + json.dumps(error_response) + "__JSON_END__\x04")

        sys.stdout.flush()



# ============================================================================

# 🔄 메인 루프

# ============================================================================



def main():

    """메인 실행 루프"""

    global repl_globals

    

    # 필요한 모듈 import

    import sys

    import platform

    import subprocess

    import os

    

    # Windows UTF-8 설정

    if platform.system() == 'Windows':

        try:

            subprocess.run(['chcp', '65001'], shell=True, capture_output=True)

        except subprocess.SubprocessError:

            pass

    

    # 스트림 인코딩 설정

    if hasattr(sys.stdout, 'reconfigure'):

        sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    else:

        import codecs

        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')

    

    if hasattr(sys.stderr, 'reconfigure'):

        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    else:

        import codecs

        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')

    

    # 기본 작업 디렉토리 설정

    try:

        from pathlib import Path

        

        # OS 독립적인 Desktop 경로 찾기

        desktop_paths = [

            Path.home() / "Desktop",  # 영문 Windows/Mac/Linux

            Path.home() / "바탕화면",  # 한글 Windows

            Path.home() / "桌面",      # 중국어

            Path.home() / "デスクトップ"  # 일본어

        ]

        

        for desktop in desktop_paths:

            if desktop.exists():

                default_project_path = desktop / "ai-coding-brain-mcp"

                if default_project_path.exists():

                    os.chdir(str(default_project_path))

                    break

    except Exception:

        pass

    

    # 초기화

    initialize_repl()

    

    # ============================================================================

    # 🛡️ Safe Wrapper 자동 로드

    # ============================================================================

    try:

        # safe_wrapper 모듈 import

        import sys

        import os

        

        # 프로젝트 루트의 python 디렉토리를 경로에 추가  

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        python_dir = os.path.join(project_root, 'python')

        if python_dir not in sys.path:

            sys.path.insert(0, python_dir)

        

        from safe_wrapper import register_safe_helpers

        

        # helpers가 repl_globals에 있는지 확인

        if 'helpers' in repl_globals:

            # 안전한 헬퍼 함수들을 전역에 등록

            register_safe_helpers(repl_globals['helpers'], repl_globals)

            print("✅ Safe Helper 함수 로드 완료", file=sys.stderr)

        else:

            print("⚠️ helpers를 찾을 수 없어 Safe Helper 로드 건너뜀", file=sys.stderr)

            

    except Exception as e:

        print(f"❌ Safe Helper 로드 실패: {e}", file=sys.stderr)

        import traceback

        traceback.print_exc(file=sys.stderr)

    

    # 이전 세션 정보 표시

    try:

        from persistent_history import PersistentHistoryManager

        history_manager = PersistentHistoryManager()

        sync_data = history_manager.get_workflow_sync_data()

        

        if sync_data['total_actions'] > 0:

            print("\n📊 이전 세션 정보:")

            print(f"   총 작업: {sync_data['total_actions']}개")

            print(f"   대화 수: {sync_data['conversations']}개")

            if sync_data['last_action']:

                print(f"   마지막 작업: {sync_data['last_action']['action']} ({sync_data['last_action']['timestamp']})")

            print("\n💡 continue_from_last()로 이전 작업을 이어갈 수 있습니다.")

    except Exception:

        pass

    

    # 준비 완료 신호

    print("__READY__", flush=True)

    

    # 메인 루프

    try:

        while True:

            # JSON 입력 읽기

            code_input = read_json_input()

            if code_input is None:

                break

            

            try:

                # 요청 파싱

                request = json.loads(code_input)

                request_id = request.get('id')

                code = request.get('code', '')

                language = request.get('language', 'python')

                

                if language != 'python':

                    response = {

                        "success": False,

                        "error": f"Unsupported language: {language}",

                        "error_type": "LanguageError"

                    }

                else:

                    # 코드 실행

                    response = execute_code(code)

                    response['language'] = language

                

                # 요청 ID 유지

                if request_id:

                    response['id'] = request_id

                    

            except json.JSONDecodeError as e:

                response = {

                    "success": False,

                    "error": f"Invalid JSON: {str(e)}",

                    "error_type": "JSONDecodeError"

                }

            

            # 응답 전송

            send_json_response(response)

    

    except KeyboardInterrupt:

        print("\n👋 JSON REPL Session 종료", file=sys.stderr)

    except Exception as e:

        print(f"\n❌ 치명적 오류: {e}", file=sys.stderr)

        traceback.print_exc(file=sys.stderr)

    finally:

        # 종료 시 컨텍스트 저장

        try:

            if 'save_context' in repl_globals:

                repl_globals['save_context']()

                print("✅ 최종 컨텍스트 저장", file=sys.stderr)

        except Exception:

            pass





# ============================================================================

# 실행

# ============================================================================



if __name__ == "__main__":

    main()