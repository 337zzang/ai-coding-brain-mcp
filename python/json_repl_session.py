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

class AIHelpers:
    """AI Coding Brain 헬퍼 함수 네임스페이스"""
    
    def __init__(self):
        self._load_helpers()
        self._bind_modular_methods()
        self._enabled_apis = {}  # API 활성화 상태 관리
    
    def _bind_modular_methods(self):
        """모듈화된 메서드들을 바인딩"""
        # Git 메서드들
        from ai_helpers import git
        self.git_status = git.git_status
        self.git_add = git.git_add
        self.git_commit = git.git_commit
        self.git_branch = git.git_branch
        self.git_stash = git.git_stash
        self.git_stash_pop = git.git_stash_pop
        self.git_log = git.git_log
        
        # Build 메서드들
        from ai_helpers import build
        self.find_executable = build.find_executable
        self.detect_project_type = build.detect_project_type
        self.run_command = build.run_command
        self.build_project = build.build_project
        self.install_dependencies = build.install_dependencies
        
        # Context 메서드들
        from ai_helpers import context
        self.get_context = context.get_context
        self.get_value = context.get_value
        self.initialize_context = context.initialize_context
        self.update_cache = context.update_cache
        
        # Command 메서드들
        from ai_helpers import command
        self.cmd_plan = command.cmd_plan
        self.cmd_task = command.cmd_task
        self.cmd_next = command.cmd_next
        
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
        from ai_helpers import search
        self.scan_directory_dict = search.scan_directory_dict
        self.search_files_advanced = search.search_files_advanced
        self.search_code_content = search.search_code_content
        
        # Utils 메서드들
        from ai_helpers import utils
        # list_functions는 self를 인자로 받아야 하므로 래핑
        self.list_functions = lambda: utils.list_functions(self)
    def _load_helpers(self):
        """auto_tracking_wrapper 및 지연 로딩 함수들을 로드"""
        # context manager 초기화
        try:
            from core.context_manager import get_context_manager
            self._context_manager = get_context_manager()
        except:
            self._context_manager = None
        
        # 지연 로딩 함수들 (claude_code_ai_brain에서)
        from ai_helpers import command
        self.cmd_flow = command.cmd_flow
        self.save_context = lambda *args, **kwargs: command.lazy_import('claude_code_ai_brain', 'save_context')(*args, **kwargs)
        self.track_file_access = command.track_file_access
        self.track_function_edit = command.track_function_edit
        self.get_work_tracking_summary = command.get_work_tracking_summary
        
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
                        os.path.join(current_dir, "commands", "enhanced_flow.py")
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
            print(f"⚠️ cmd_flow_with_context 설정 실패: {e}")
            # 최소한의 기능이라도 제공
            def minimal_flow_project(project_name):
                os.chdir(os.path.dirname(os.path.abspath(__file__)).replace('\\python', ''))
                print(f"✅ 프로젝트 '{project_name}'로 디렉토리 변경 완료 (최소 모드)")
                return {'success': True, 'context': {}}
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
                from ai_helpers import search
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
    




    # ==================== 이미지 생성 관련 메서드 ====================
    
    def generate_image(self, prompt: str, filename: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """AI를 사용하여 이미지 생성
        
        Args:
            prompt: 이미지 생성 프롬프트
            filename: 저장할 파일명 (선택사항)
            **kwargs: 추가 옵션 (model, size, quality, style)
        
        Returns:
            생성 결과 딕셔너리
        """
        if not self._check_api_enabled('image'):
            return {
                "success": False,
                "error": "Image API가 비활성화되어 있습니다. helpers.toggle_api('image', True)로 활성화하세요."
            }
            
        try:
            from api.image_generator import generate_ai_image
            result = generate_ai_image(prompt, filename, **kwargs)
            
            if result.get("success"):
                print(f"✅ 이미지 생성 성공: {result['filename']}")
                print(f"📍 저장 위치: {result['filepath']}")
                if result.get('revised_prompt') and result.get('revised_prompt') != prompt:
                    print(f"📝 수정된 프롬프트: {result['revised_prompt']}")
            else:
                print(f"❌ 이미지 생성 실패: {result.get('error')}")
            
            return result
        except Exception as e:
            error_msg = f"이미지 생성 중 오류 발생: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}
    def list_generated_images(self) -> list:
        """생성된 이미지 목록 조회
        
        Returns:
            이미지 정보 리스트
        """
        try:
            from api.image_generator import list_ai_images
            images = list_ai_images()
            print(f"📸 총 {len(images)}개의 이미지가 생성되었습니다.")
            for i, img in enumerate(images[-5:], 1):  # 최근 5개만 표시
                print(f"  {i}. {img['filename']} - {img['created_at']}")
            if len(images) > 5:
                print(f"  ... 그리고 {len(images) - 5}개 더")
            return images
        except Exception as e:
            print(f"❌ 이미지 목록 조회 실패: {e}")
            return []
    
    def search_generated_images(self, keyword: str) -> list:
        """키워드로 생성된 이미지 검색
        
        Args:
            keyword: 검색할 키워드
        
        Returns:
            검색된 이미지 정보 리스트
        """
        try:
            from api.image_generator import search_ai_images
            results = search_ai_images(keyword)
            print(f"🔍 '{keyword}' 검색 결과: {len(results)}개의 이미지")
            for i, img in enumerate(results[:5], 1):
                print(f"  {i}. {img['filename']} - {img['prompt'][:50]}...")
            if len(results) > 5:
                print(f"  ... 그리고 {len(results) - 5}개 더")
            return results
        except Exception as e:
            print(f"❌ 이미지 검색 실패: {e}")
            return []
    
    def get_image_base64(self, filename: str) -> Optional[str]:
        """이미지를 base64로 인코딩하여 반환
        
        Args:
            filename: 이미지 파일명
        
        Returns:
            base64 인코딩된 문자열 또는 None
        """
        try:
            from api.image_generator import get_image_base64
            base64_data = get_image_base64(filename)
            if base64_data:
                print(f"✅ 이미지 base64 인코딩 성공: {filename}")
            else:
                print(f"❌ 이미지를 찾을 수 없습니다: {filename}")
            return base64_data
        except Exception as e:
            print(f"❌ base64 인코딩 실패: {e}")
            return None

    def toggle_api(self, api_name: str, enabled: bool = True) -> Dict[str, Any]:
        """API 활성화/비활성화 토글
        
        Args:
            api_name: API 이름 (예: 'image', 'translator', 'voice' 등)
            enabled: 활성화 여부
        
        Returns:
            상태 정보 딕셔너리
        """
        self._enabled_apis[api_name] = enabled
        
        if enabled:
            # API 모듈 동적 로드 시도
            try:
                module = __import__(f'api.{api_name}_generator', fromlist=[''])
                print(f"✅ {api_name} API 활성화됨")
                return {
                    "success": True,
                    "api": api_name,
                    "status": "enabled",
                    "module": str(module)
                }
            except ImportError:
                # api_name_generator가 없으면 다른 패턴 시도
                try:
                    module = __import__(f'api.{api_name}', fromlist=[''])
                    print(f"✅ {api_name} API 활성화됨")
                    return {
                        "success": True,
                        "api": api_name,
                        "status": "enabled",
                        "module": str(module)
                    }
                except ImportError as e:
                    print(f"⚠️ {api_name} API 모듈을 찾을 수 없음: {e}")
                    self._enabled_apis[api_name] = False
                    return {
                        "success": False,
                        "api": api_name,
                        "error": str(e)
                    }
        else:
            print(f"🔴 {api_name} API 비활성화됨")
            return {
                "success": True,
                "api": api_name,
                "status": "disabled"
            }
    
    def list_apis(self) -> Dict[str, bool]:
        """활성화된 API 목록 반환"""
        # 사용 가능한 API 확인
        api_path = os.path.join(os.path.dirname(__file__), 'api')
        available_apis = []
        
        if os.path.exists(api_path):
            for file in os.listdir(api_path):
                if file.endswith('.py') and not file.startswith('__'):
                    api_name = file.replace('.py', '').replace('_generator', '')
                    available_apis.append(api_name)
        
        # 활성화 상태와 함께 반환
        api_status = {}
        for api in available_apis:
            api_status[api] = self._enabled_apis.get(api, False)
        
        print(f"📊 API 상태:")
        for api, enabled in api_status.items():
            status = "✅ 활성" if enabled else "⭕ 비활성"
            print(f"  - {api}: {status}")
        
        return api_status
    
    def _check_api_enabled(self, api_name: str) -> bool:
        """API 활성화 상태 확인"""
        return self._enabled_apis.get(api_name, True)  # 기본값은 True (이전 버전 호환)





    # ===== Git 관련 헬퍼 메서드들 =====
def initialize_repl():
    """REPL 환경 초기화"""
    global repl_globals, wisdom, hooks
    
    print("🚀 JSON REPL Session v5.0 초기화 중...")
    
    # 1. helpers 객체 생성
    helpers = AIHelpers()
    repl_globals['helpers'] = helpers
    repl_globals['h'] = helpers  # 짧은 별칭
    
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
    
    # 4. context 연결
    context = helpers.get_context()
    if context:
        repl_globals['context'] = context
    
    # 5. 프로젝트 자동 초기화 (현재 디렉토리)
    try:
        project_path = os.getcwd()
        project_name = os.path.basename(project_path)
        if hasattr(helpers, 'initialize_context'):
            context = helpers.initialize_context(project_path)
            repl_globals['context'] = context
            print(f"✅ 프로젝트 '{project_name}' 자동 초기화")
    except Exception as e:
        print(f"⚠️ 프로젝트 자동 초기화 건너뜀: {e}")
    
    # 6. Git Version Manager 초기화
    try:
        from git_version_manager import GitVersionManager
        git_manager = GitVersionManager()
        repl_globals['git_manager'] = git_manager
        print("✅ Git Version Manager 초기화 완료")
        
        # Git 상태 확인
        status = git_manager.git_status()
        print(f"  - 브랜치: {status.get('branch', 'unknown')}")
        print(f"  - 수정된 파일: {len(status.get('modified', []))}개")
    except Exception as e:
        print(f"⚠️ Git Manager 초기화 실패: {e}")
        git_manager = None
    
    print("✅ REPL 초기화 완료!")
    print("💡 사용법: helpers.create_file('test.py') 또는 h.read_file('test.py')")
    print("📋 함수 목록: helpers.list_functions()")

# ============================================================================
# 💻 코드 실행
# ============================================================================

def execute_code(code: str) -> Dict[str, Any]:
    """Python 코드 실행"""
    global execution_count
    
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    start_time = time.time()
    
    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            # 코드 실행
            exec(code, repl_globals)
            
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
        sys.stdout.write(response_json)
        sys.stdout.write('\x04')  # EOT
        sys.stdout.flush()
    except Exception as e:
        error_response = {
            "success": False,
            "error": f"Response encoding error: {str(e)}",
            "error_type": "ResponseError"
        }
        sys.stdout.write(json.dumps(error_response))
        sys.stdout.write('\x04')
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
# 🎯 실행
# ============================================================================

if __name__ == "__main__":
    # 이미지 생성 관련
    try:
        from api.image_generator import ImageGenerator, generate_ai_image, list_ai_images, search_ai_images
        print("✅ 이미지 생성 모듈 로드 성공")
    except ImportError as e:
        print(f"⚠️ 이미지 생성 모듈 로드 실패: {e}")
        ImageGenerator = None
        generate_ai_image = None
    
    main()
