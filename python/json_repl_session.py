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

# Stdout Protocol v3.0 import (선택적)
try:
    pass  # Protocol import removed
    # [REMOVED] from ai_helpers.protocols import (
        # [REMOVED] get_protocol, get_id_generator, get_tracker,
        # [REMOVED] StdoutProtocol, ExecutionTracker, IDGenerator
    # [REMOVED] )
    # [REMOVED] PROTOCOL_AVAILABLE = True
    # [REMOVED] print("✅ Stdout Protocol v3.0 loaded successfully")
except ImportError as e:
    print(f"⚠️  Stdout Protocol not available: {e}")
    # [REMOVED] PROTOCOL_AVAILABLE = False
    # [REMOVED] get_protocol = None
    # [REMOVED] get_id_generator = None
    # [REMOVED] get_tracker = None

# ============================================================================
# 🌟 전역 변수 초기화
# ============================================================================
repl_globals = {}  # REPL 전역 네임스페이스
execution_count = 0  # 실행 카운터

try:
    from ai_helpers.api import toggle_api as api_toggle_api, list_apis as api_list_apis, check_api_enabled
    from ai_helpers.api import ImageAPI
except ImportError as e:
    print(f"WARNING: API 모듈 로드 실패: {e}")
    api_toggle_api = None
    api_list_apis = None
    check_api_enabled = None
    ImageAPI = None

class AIHelpersV2:
    """AI Helpers v2 통합 래퍼"""
    
    def __init__(self):
        """AI Helpers v2 메서드들을 통합"""
        if not AI_HELPERS_V2_LOADED:
            print("⚠️ AI Helpers v2가 로드되지 않았습니다. 기능이 제한될 수 있습니다.")
            return
            
        # File operations
        self.read_file = read_file
        self.write_file = write_file
        self.create_file = create_file
        self.file_exists = file_exists
        self.exists = file_exists  # 별칭
        self.append_to_file = append_to_file
        self.read_json = read_json
        self.write_json = write_json
        
        # Search operations
        self.search_code = search_code
        self.search_files = search_files
        self.search_in_files = search_code  # 별칭
        self.grep = grep
        self.find_function = find_function
        self.find_class = find_class
        
        # Code operations
        self.parse_with_snippets = parse_with_snippets
        self.insert_block = insert_block
        self.replace_block = replace_block
        
        # Git operations
        self.git_status = git_status
        self.git_add = git_add
        self.git_commit = git_commit
        self.git_branch = git_branch
        self.git_push = git_push
        self.git_pull = git_pull
        
        # Project operations
        self.get_current_project = get_current_project
        self.scan_directory_dict = scan_directory_dict
        self.create_project_structure = create_project_structure
        
        # Core operations
        self.get_metrics = get_metrics
        self.clear_cache = clear_cache
        self.get_execution_history = get_execution_history
        
        # flow_project 구현
        self.flow_project = self._flow_project
        self.cmd_flow_with_context = self._flow_project  # 별칭
        
        # API 기능 (호환성)
        self.toggle_api = api_toggle_api if api_toggle_api else self._not_implemented
        self.list_apis = api_list_apis if api_list_apis else self._not_implemented

        # LLM operations (llm_ops)
        try:
            from ai_helpers_v2.llm_ops import (
                ask_o3, analyze_code, explain_error, generate_docstring
            )
            self.ask_o3 = ask_o3
            self.analyze_code = analyze_code
            self.explain_error = explain_error
            self.generate_docstring = generate_docstring
        except ImportError:
            pass
        
    def _flow_project(self, project_name, auto_proceed=True):
        """프로젝트 전환 및 컨텍스트 로드"""
        import json
        from datetime import datetime
        
        try:
            # 프로젝트 디렉토리 생성
            projects_dir = "projects"
            if not os.path.exists(projects_dir):
                os.makedirs(projects_dir)
            
            project_path = os.path.join(projects_dir, project_name)
            if not os.path.exists(project_path):
                os.makedirs(project_path)
                print(f"✅ 새 프로젝트 디렉토리 생성: {project_path}")
            
            # 컨텍스트 업데이트
            context_file = os.path.join(project_path, "context.json")
            context = {
                "project_name": project_name,
                "switched_at": datetime.now().isoformat(),
                "status": "active",
                "workflow_status": {
                    "phase": "initialized",
                    "tasks": []
                }
            }
            
            if os.path.exists(context_file):
                with open(context_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                    context.update(existing)
                    context["switched_at"] = datetime.now().isoformat()
            
            with open(context_file, 'w', encoding='utf-8') as f:
                json.dump(context, f, indent=2)
            
            # README 생성
            readme_file = os.path.join(project_path, "README.md")
            if not os.path.exists(readme_file):
                with open(readme_file, 'w', encoding='utf-8') as f:
                    f.write(f"# {project_name}\n\n프로젝트 생성일: {datetime.now()}\n")
            
            print(f"\n✅ 프로젝트 '{project_name}'로 전환 완료!")
            return {
                "success": True,
                "project_name": project_name,
                "path": os.path.abspath(project_path),
                "context": context
            }
            
        except Exception as e:
            print(f"❌ flow_project 오류: {e}")
            return {"success": False, "error": str(e)}
    
    def _not_implemented(self, *args, **kwargs):
        """구현되지 않은 메서드"""
        return None
    
    def __getattr__(self, name):
        """동적 속성 접근 - 호환성을 위해"""
        if AI_HELPERS_V2_LOADED:
            # v2 모듈에서 찾기
            for module in ['file_ops', 'search_ops', 'code_ops', 'git_ops', 'project_ops', 'core']:
                module_name = f'ai_helpers_v2.{module}'
                if module_name in sys.modules:
                    module_obj = sys.modules[module_name]
                    if hasattr(module_obj, name):
                        return getattr(module_obj, name)
        
        # 기본 동작
        def not_implemented(*args, **kwargs):
            print(f"⚠️ {name} 메서드는 아직 구현되지 않았습니다")
            return None
        return not_implemented
    
    def __dir__(self):
        """사용 가능한 메서드 목록"""
        base_attrs = list(self.__dict__.keys())
        if AI_HELPERS_V2_LOADED:
            # v2 모듈의 모든 공개 함수 추가
            for module in ['file_ops', 'search_ops', 'code_ops', 'git_ops', 'project_ops', 'core']:
                module_name = f'ai_helpers_v2.{module}'
                if module_name in sys.modules:
                    module_obj = sys.modules[module_name]
                    base_attrs.extend([
                        attr for attr in dir(module_obj) 
                        if not attr.startswith('_') and callable(getattr(module_obj, attr))
                    ])
        return sorted(set(base_attrs))

 


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
