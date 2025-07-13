#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🚀 JSON REPL Session for AI Coding Brain v5.0
==============================================

Claude Desktop과 통신하는 간소화된 JSON REPL 세션
- claude_code_ai_brain과 직접 통합
- 네임스페이스 보호 (AIHelpers 클래스)
- 최소 의존성, 핵심 기능만 유지
- Wisdom 시스템 통합

작성일: 2025-06-14
"""

import sys
import os
import json
import io
import traceback
import time
import datetime as dt
import platform
import subprocess
import builtins
from pathlib import Path
from typing import Dict, Any, Optional
from contextlib import redirect_stdout, redirect_stderr

# 기본 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Wisdom 시스템 제거됨 (2025-06-30 리팩토링)

# ============================================================================
# 🌟 전역 변수 초기화
# ============================================================================
repl_globals = {}  # REPL 전역 네임스페이스
execution_count = 0  # 실행 카운터

# ============================================================================
# 🛡️ AIHelpers - 네임스페이스 보호된 헬퍼 함수 모음
# ============================================================================

# API 모듈 import (절대 임포트 사용 - 독립 실행 파일)
try:
    from ai_helpers.api import toggle_api as api_toggle_api, list_apis as api_list_apis, check_api_enabled
    from ai_helpers.api import ImageAPI
except ImportError as e:
    print(f"WARNING: API 모듈 로드 실패: {e}")
    api_toggle_api = None
    api_list_apis = None
    check_api_enabled = None
    ImageAPI = None

class AIHelpers:
    """AI Coding Brain 헬퍼 함수 네임스페이스"""
    
    def __init__(self):
        self._load_helpers()
        self._bind_modular_methods()
    
    def _bind_modular_methods(self):
        """모듈화된 메서드들을 바인딩"""
        # Git 메서드들 (절대 임포트 사용)
        from ai_helpers import git
        self.git_status = git.git_status
        self.git_add = git.git_add
        self.git_commit = git.git_commit
        self.git_branch = git.git_branch
        self.git_stash = git.git_stash
        self.git_stash_pop = git.git_stash_pop
        self.git_log = git.git_log
        
        # Build 메서드들 - build 모듈이 없으므로 주석 처리
        # try:
        #     from ai_helpers import build
        #     self.find_executable = build.find_executable
        #     self.detect_project_type = build.detect_project_type
        #     self.run_command = build.run_command
        #     self.build_project = build.build_project
        #     self.install_dependencies = build.install_dependencies
        # except ImportError:
        #     pass
        
        # Context 메서드들
        from ai_helpers import context
        self.get_context = context.get_context
        self.get_value = context.get_value
        self.initialize_context = context.initialize_context
        self.update_cache = context.update_cache
        
        # Project 메서드들 (프로젝트 관리)
        from ai_helpers.project import (
            get_current_project, list_tasks, quick_task, get_project_progress,
            create_standard_phases, get_current_phase, complete_current_phase,
            get_system_summary, get_pending_tasks, get_event_history,
            project, task, progress, complete, reset_project
        )
        # 프로젝트 관리
        self.get_current_project = get_current_project
        self.list_tasks = list_tasks
        self.quick_task = quick_task
        self.get_project_progress = get_project_progress
        # Phase 관리
        self.create_standard_phases = create_standard_phases
        self.get_current_phase = get_current_phase
        self.complete_current_phase = complete_current_phase
        # 상태 조회
        self.get_system_summary = get_system_summary
        self.get_pending_tasks = get_pending_tasks
        self.get_event_history = get_event_history
        # 간편 명령
        self.project = project
        self.task = task
        self.progress = progress
        self.complete = complete
        self.reset_project = reset_project
        
        # File 메서드들
        from ai_helpers import file
        self.create_file = file.create_file
        self.read_file = file.read_file
        self.write_file = file.write_file
        self.append_to_file = file.append_to_file
        
        # Code 메서드들
        from ai_helpers import code
        self.replace_block = code.replace_block
        self.insert_block = code.insert_block
        self.parse_code = code.parse_code
        
        # Search 메서드들
        from ai_helpers.search import (
            scan_directory_dict, search_files_advanced, search_code_content
        )
        from ai_helpers import search_code, find_class, find_function, find_import
        self.scan_directory_dict = scan_directory_dict
        self.search_files_advanced = search_files_advanced
        self.search_code_content = search_code_content
        # 새로운 search wrapper 함수들
        self.search_code = search_code
        self.find_class = find_class
        self.find_function = find_function
        self.find_import = find_import
        
        # Utils 메서드들
        from ai_helpers import utils
        # list_functions는 self를 인자로 받아야 하므로 래핑
        self.list_functions = lambda: utils.list_functions(self)

        # Workflow 메서드들
        try:
            from ai_helpers.workflow import workflow, get_workflow_status
            self.workflow = workflow
            self.get_workflow_status = get_workflow_status
            logger.info("✅ Workflow 메서드 바인딩 완료")
        except ImportError as e:
            logger.warning(f"⚠️ Workflow 메서드 바인딩 실패: {e}")
            # Fallback
            self.workflow = lambda cmd: {"ok": False, "error": "Workflow module not available"}
            self.get_workflow_status = lambda: {"ok": False, "error": "Workflow module not available"}
    
    def _bind_workflow_methods(self):
        """Workflow 관련 메서드 바인딩"""
        try:
            from workflow_integration import (
                workflow_command, workflow_plan, workflow_complete,
                get_workflow_status, get_current_task_info
            )
            
            self.workflow = workflow_command
            self.workflow_plan = workflow_plan
            self.workflow_complete = workflow_complete
            self.workflow_status = get_workflow_status
            self.workflow_current_task = get_current_task_info
            
            # print("✅ Workflow 메서드 바인딩 완료")  # MCP JSON 응답 오염 방지
        except ImportError as e:
            # print(f"⚠️ Workflow 메서드 바인딩 실패: {e}")  # MCP JSON 응답 오염 방지
            pass

    def _load_helpers(self):
        """auto_tracking_wrapper 및 지연 로딩 함수들을 로드"""
        # context manager 초기화
        try:
            from core.context_manager import get_context_manager
            self._context_manager = get_context_manager()
        except:
            self._context_manager = None
        
        # 지연 로딩 함수들 (claude_code_ai_brain에서)
        from ai_helpers import cmd_flow, track_file_access, track_function_edit, get_work_tracking_summary
        from ai_helpers.context import save_context  # context 모듈에서 직접 import
        self.cmd_flow = cmd_flow
        self.save_context = save_context  # lazy_import 대신 직접 할당
        self.track_file_access = track_file_access
        self.track_function_edit = track_function_edit
        self.get_work_tracking_summary = get_work_tracking_summary
        
        try:
            # cmd_flow_with_context 추가 - 더 견고한 방식으로
            import sys
            import os
            # Python 경로 확실히 추가
            current_dir = os.path.dirname(os.path.abspath(__file__))
            commands_dir = os.path.join(current_dir, 'commands')
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            if commands_dir not in sys.path:
                sys.path.insert(0, commands_dir)
                
            # 직접 함수 정의 - import 실패에 대비
            def robust_flow_project(project_name):
                """견고한 flow_project 구현"""
                try:
                    # enhanced_flow 모듈 동적 import
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(
                        "enhanced_flow", 
                        os.path.join(current_dir, "enhanced_flow.py")
                    )
                    module = importlib.util.module_from_spec(spec)
                    # helpers 전달
                    module.global_helpers = self
                    spec.loader.exec_module(module)
                    
                    # flow_project 함수 호출
                    if hasattr(module, 'flow_project'):
                        return module.flow_project(project_name)
                    else:
                        return {'success': False, 'error': 'flow_project 함수를 찾을 수 없습니다'}
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    return {'success': False, 'error': str(e)}
                    
            self.cmd_flow_with_context = robust_flow_project
            
        except Exception as e:
            # print(f"⚠️ cmd_flow_with_context 설정 실패: {e}")  # MCP JSON 응답 오염 방지
            # 최소한의 기능이라도 제공
            def minimal_flow_project(project_name):
                # 프로젝트 디렉토리 찾기
                from pathlib import Path
                try:
                    # OS 독립적인 Desktop 경로 찾기
                    desktop_paths = [
                        Path.home() / "Desktop",  # 영문 Windows/Mac/Linux
                        Path.home() / "바탕화면",  # 한글 Windows
                        Path.home() / "桌面",      # 중국어
                        Path.home() / "デスクトップ"  # 일본어
                    ]
                    
                    project_path = None
                    
                    # Desktop에서 프로젝트 찾기
                    for desktop in desktop_paths:
                        if desktop.exists():
                            test_path = desktop / project_name
                            if test_path.exists():
                                project_path = test_path
                                break
                    
                    # Desktop에 없으면 다른 일반적인 위치에서 찾기
                    if not project_path:
                        other_locations = [
                            Path.home() / "Documents",
                            Path.home() / "Projects",
                            Path("/Projects"),  # 루트의 Projects
                            Path("D:/Projects") if os.name == 'nt' else None  # Windows D드라이브
                        ]
                        
                        for location in other_locations:
                            if location and location.exists():
                                test_path = location / project_name
                                if test_path.exists():
                                    project_path = test_path
                                    break
                    
                    if project_path:
                        os.chdir(str(project_path))
                        return {'success': True, 'path': str(project_path)}
                    else:
                        return {'success': False, 'error': f'프로젝트 디렉토리를 찾을 수 없음: {project_name}'}
                except Exception as e:
                    return {'success': False, 'error': str(e)}
            self.cmd_flow_with_context = minimal_flow_project
        
        try:
            # 파일 작업 및 코드 분석은 이미 _bind_modular_methods에서 처리됨
            # parse_with_snippets와 get_snippet_preview 추가 바인딩
            from ai_helpers import code
            self.parse_with_snippets = code.parse_with_snippets
            self.get_snippet_preview = code.get_snippet_preview
        except ImportError as e:
            print(f"⚠️ ai_helpers code 모듈 로드 실패: {e}")
            
            # 폴더 구조 캐싱 함수들은 search 모듈에서 처리
            try:
                from ai_helpers import search, search_code, find_class, find_function, find_import
                # cache_project_structure 등은 아직 구현 필요
                print("✅ ai_helpers 모듈 로드 성공")
            except ImportError as e:
                print(f"⚠️ 폴더 구조 캐싱 함수 로드 실패: {e}")
        
        except ImportError as e:
            print(f"⚠️ auto_tracking_wrapper 로드 실패: {e}")
    
    def list_functions(self):
        """사용 가능한 함수 목록 표시"""
        funcs = [attr for attr in dir(self) 
                if not attr.startswith('_') and callable(getattr(self, attr))]
        print(f"🔧 사용 가능한 헬퍼 함수 ({len(funcs)}개):")
        for func in sorted(funcs):
            print(f"  • helpers.{func}()")
        return funcs

        # Workflow 관련 메서드 바인딩
        try:
            from workflow_integration import (
                workflow_command, workflow_plan, workflow_complete,
                get_workflow_status, get_current_task_info
            )
            
            self.workflow = workflow_command
            self.workflow_plan = workflow_plan
            self.workflow_complete = workflow_complete
            self.workflow_status = get_workflow_status
            self.workflow_current_task = get_current_task_info
            
            logger.info("✅ Workflow 메서드 바인딩 완료")
        except ImportError as e:
            logger.warning(f"⚠️ Workflow 메서드 바인딩 실패: {e}")


def ensure_helpers_loaded_old():
    """helpers 모듈이 제대로 로드되었는지 확인하고 필요시 재로드"""
    global repl_globals
    
    try:
        # helpers가 전역 변수에 있는지 확인
        if 'helpers' not in repl_globals:
            print("📋 helpers 로드 중...")
            
            # sys.path 설정 확인
            import sys
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # AIHelpers import
            try:
                from ai_helpers import AIHelpers
                ai_helpers = AIHelpers()
            except ImportError:
                print("⚠️ AIHelpers import 실패 - 기본 헬퍼 사용")
                ai_helpers = None
            
            # HelpersWrapper로 감싸기
            from helpers_wrapper import HelpersWrapper
            if ai_helpers:
                repl_globals['helpers'] = HelpersWrapper(ai_helpers)
                print("✅ helpers 로드 완료!")
            else:
                print("❌ helpers 로드 실패")
                
        # workflow 메서드 확인
        if 'helpers' in repl_globals:
            helpers = repl_globals['helpers']
            if not hasattr(helpers, 'workflow'):
                print("⚠️ workflow 메서드 없음 - helpers 재로드 필요")
                # 재로드 시도
                import importlib
                if 'python.helpers_wrapper' in sys.modules:
                    importlib.reload(sys.modules['python.helpers_wrapper'])
                    from helpers_wrapper import HelpersWrapper
                    if hasattr(helpers, 'helpers'):
                        repl_globals['helpers'] = HelpersWrapper(helpers.helpers)
                        print("✅ helpers 재로드 완료!")
                        
    except Exception as e:
        print(f"❌ ensure_helpers_loaded 오류: {e}")
        import traceback
        traceback.print_exc()


def ensure_helpers_loaded():
    """helpers 모듈을 안전하게 로드하고 래핑"""
    import importlib
    import sys
    import pathlib
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # 프로젝트 루트를 sys.path에 추가
        project_root = pathlib.Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        # ai_helpers 모듈 import
        raw = importlib.import_module("ai_helpers")
        
        # HelpersWrapper 적용
        from helpers_wrapper import HelpersWrapper
        wrapped_helpers = HelpersWrapper(raw)
        
        # 전역 변수에 설정
        globals()["helpers"] = wrapped_helpers
        globals()["helpers_original"] = raw
        
        logger.info("✅ helpers 로딩·래핑 완료")
        return wrapped_helpers
        
    except Exception as e:
        logger.error("❌ helpers 로딩 실패: %s", e)
        return None
def initialize_repl():
    """REPL 환경 초기화"""
    global repl_globals, wisdom, hooks
    
    # print("🚀 JSON REPL Session v5.0 초기화 중...")  # MCP JSON 응답 오염 방지
    
    # 1. helpers 객체 생성
    helpers = ensure_helpers_loaded()
    if helpers:
        repl_globals['helpers'] = helpers
        repl_globals['h'] = helpers
        builtins.helpers = helpers
    else:
        sys.stderr.write('⚠️ helpers 로딩 실패\n')

        # 실패해도 원본 helpers는 사용 가능
    
    # 2. 자주 사용하는 함수들을 전역에도 노출 (선택적)
    critical_funcs = {}
    
    # 필수 함수들
    if hasattr(helpers, 'create_file'):
        critical_funcs['create_file'] = helpers.create_file
    if hasattr(helpers, 'read_file'):
        critical_funcs['read_file'] = helpers.read_file
    if hasattr(helpers, 'backup_file'):
        critical_funcs['backup_file'] = helpers.backup_file
    if hasattr(helpers, 'replace_block'):
        critical_funcs['replace_block'] = helpers.replace_block
    
    # 명령어 함수들
    if hasattr(helpers, 'cmd_flow'):
        critical_funcs['cmd_flow'] = helpers.cmd_flow
    if hasattr(helpers, 'cmd_plan'):
        critical_funcs['cmd_plan'] = helpers.cmd_plan
    if hasattr(helpers, 'cmd_task'):
        critical_funcs['cmd_task'] = helpers.cmd_task
    if hasattr(helpers, 'cmd_next'):
        critical_funcs['cmd_next'] = helpers.cmd_next
    if hasattr(helpers, 'cmd_flow_with_context'):
        critical_funcs['cmd_flow_with_context'] = helpers.cmd_flow_with_context
    elif hasattr(helpers, 'cmd_flow'):
        critical_funcs['cmd_flow_with_context'] = helpers.cmd_flow
    
    # save_context가 있는 경우에만 추가
    if hasattr(helpers, 'save_context'):
        critical_funcs['save_context'] = helpers.save_context
    
    for name, func in critical_funcs.items():
        if callable(func):
            repl_globals[name] = func
    
    # 3. 기본 모듈들
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
    
    # 4. context 연결 (optional)
    try:
        if hasattr(helpers, 'get_context'):
            context = helpers.get_context()
            if context:
                repl_globals['context'] = context
    except Exception:
        pass  # context 로드 실패 시 무시
    
    # 5. 프로젝트 자동 초기화 (현재 디렉토리)
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
        if hasattr(helpers, 'initialize_context'):
            context = helpers.initialize_context(str(project_path))
            repl_globals['context'] = context
            # print(f"✅ 프로젝트 '{project_name}' 자동 초기화")  # MCP JSON 응답 오염 방지
    except Exception as e:
        # print(f"⚠️ 프로젝트 자동 초기화 건너뜀: {e}")  # MCP JSON 응답 오염 방지
        pass
    
    # 6. Git Version Manager 초기화
    try:
        from git_version_manager import GitVersionManager
        git_manager = GitVersionManager()
        repl_globals['git_manager'] = git_manager
        # print("✅ Git Version Manager 초기화 완료")  # MCP JSON 응답 오염 방지
        
        # Git 상태 확인
        status = git_manager.status()
        # print(f"  - 브랜치: {status.get('branch', 'unknown')}")  # MCP JSON 응답 오염 방지
        # print(f"  - 수정된 파일: {len(status.get('modified', []))}개")  # MCP JSON 응답 오염 방지
    except Exception as e:
        sys.stderr.write(f"⚠️ Git Manager 초기화 실패: {e}\n")
        git_manager = None
    
    
    # helpers 로드 확인
    ensure_helpers_loaded()
    
    # print("✅ REPL 초기화 완료!")  # MCP JSON 응답 오염 방지
    # print("💡 사용법: helpers.create_file('test.py') 또는 h.read_file('test.py')")  # MCP JSON 응답 오염 방지
    # print("📋 함수 목록: helpers.list_functions()")  # MCP JSON 응답 오염 방지

# ============================================================================
# 💻 코드 실행
# ============================================================================

def safe_exec(code: str, globals_dict: dict) -> tuple[bool, str]:
    """안전한 코드 실행 - 들여쓰기 오류 시 자동 재시도
    
    Returns:
        (성공 여부, 오류 메시지)
    """
    from textwrap import dedent
    
    try:
        # 1차 시도: 원본 코드 그대로 실행
        exec(compile(code, '<repl>', 'exec'), globals_dict)
        return True, ''
    except IndentationError as e:
        # 2차 시도: 자동 dedent 후 재시도
        try:
            dedented_code = dedent(code)
            exec(compile(dedented_code, '<repl>', 'exec'), globals_dict)
            print("ℹ️ 들여쓰기 자동 정리 후 실행 성공")
            return True, ''
        except Exception as e2:
            return False, f'{type(e2).__name__}: {e2}'
    except Exception as e:
        return False, f'{type(e).__name__}: {e}'


def execute_code(code: str) -> Dict[str, Any]:
    """Python 코드 실행"""
    global execution_count
    
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    start_time = time.time()
    
    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            # safe_exec를 사용하여 코드 실행
            success, error_msg = safe_exec(code, repl_globals)
            if not success:
                # 오류를 stderr에 기록
                print(error_msg, file=stderr_capture)
            
        execution_count += 1
        
        # 자동 저장 (10회마다)
        if execution_count % 10 == 0 and 'save_context' in repl_globals:
            try:
                repl_globals['save_context']()
            except Exception:
                # 컨텍스트 저장 실패는 무시 (세션 유지를 위해)
                pass
        
        # 변수 개수 계산
        user_vars = [k for k in repl_globals.keys() 
                    if not k.startswith('_') and k not in ['__builtins__']]
        
        return {
            "success": True,
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "execution_time": time.time() - start_time,
            "variable_count": len(user_vars),
            "execution_count": execution_count,
            "session_mode": "JSON_REPL",
            "note": "JSON REPL Session - Variables persist"
        }
        
    except Exception as e:
        execution_count += 1
        
        return {
            "success": False,
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue() + f"\n{type(e).__name__}: {str(e)}\n{traceback.format_exc()}",
            "execution_time": time.time() - start_time,
            "variable_count": len(repl_globals),
            "execution_count": execution_count,
            "error": str(e),
            "error_type": type(e).__name__,
            "session_mode": "JSON_REPL"
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
    
    # Windows UTF-8 설정
    if platform.system() == 'Windows':
        try:
            subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
        except subprocess.SubprocessError:
            # Windows 코드페이지 설정 실패 무시
            pass
    
    # 스트림 인코딩 설정
    if hasattr(sys.stdout, 'reconfigure'):
        # Python 3.7+ 
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    else:
        # 구버전 Python을 위한 대체 방법
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
    
    if hasattr(sys.stderr, 'reconfigure'):
        # Python 3.7+
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    else:
        # 구버전 Python을 위한 대체 방법
        import codecs
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')
    
    # 기본 작업 디렉토리 설정 (MCP 시작 시 Claude 앱 디렉토리 문제 해결)
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
        pass  # 실패해도 계속 진행
    
    # 초기화
    initialize_repl()
    
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
            # 종료 시 저장 실패는 무시
            pass


# ============================================================================
# [TARGET] 실행
# ============================================================================

if __name__ == "__main__":
    # 이미지 생성 관련 모듈은 helpers를 통해 사용
    ImageGenerator = None
    generate_ai_image = None
    
    main()
