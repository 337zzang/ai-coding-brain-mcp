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

# Wisdom 시스템 통합
try:
    from project_wisdom import get_wisdom_manager
    from wisdom_hooks import get_wisdom_hooks
    from core.wisdom_integration import wisdom_integration
    WISDOM_AVAILABLE = True
except ImportError:
    WISDOM_AVAILABLE = False
    import sys
    if sys.stdout.encoding.lower() != 'utf-8':
        print("Warning: Wisdom system is not available.")
    else:
        print("⚠️ Wisdom 시스템을 사용할 수 없습니다.")

# ============================================================================
# 🌟 전역 변수 초기화
# ============================================================================
repl_globals = {}  # REPL 전역 네임스페이스
execution_count = 0  # 실행 카운터
wisdom = None  # Wisdom 매니저
hooks = None   # Wisdom Hooks

# ============================================================================
# 🛡️ AIHelpers - 네임스페이스 보호된 헬퍼 함수 모음
# ============================================================================

class AIHelpers:
    """AI Coding Brain 헬퍼 함수 네임스페이스"""
    
    def __init__(self):
        self._load_helpers()
        self._enabled_apis = {}  # API 활성화 상태 관리
    def _load_helpers(self):
        """헬퍼 함수들을 로드"""
        # cmd_flow 초기화
        self.cmd_flow = None
        
        # 지연 로딩을 위한 헬퍼 함수들
        def lazy_cmd_flow(*args, **kwargs):
            if not self.cmd_flow:
                from claude_code_ai_brain import cmd_flow
                self.cmd_flow = cmd_flow
            return self.cmd_flow(*args, **kwargs)
        
        def lazy_initialize_context(*args, **kwargs):
            from claude_code_ai_brain import initialize_context
            return initialize_context(*args, **kwargs)
        
        def lazy_save_context(*args, **kwargs):
            from claude_code_ai_brain import save_context
            return save_context(*args, **kwargs)
        
        def lazy_update_cache(*args, **kwargs):
            from claude_code_ai_brain import update_cache
            return update_cache(*args, **kwargs)
        
        def lazy_get_value(*args, **kwargs):
            from claude_code_ai_brain import get_value
            return get_value(*args, **kwargs)
        
        def lazy_track_file_access(*args, **kwargs):
            from claude_code_ai_brain import track_file_access
            return track_file_access(*args, **kwargs)
        
        def lazy_track_function_edit(*args, **kwargs):
            from claude_code_ai_brain import track_function_edit
            return track_function_edit(*args, **kwargs)
        
        def lazy_get_work_tracking_summary(*args, **kwargs):
            from claude_code_ai_brain import get_work_tracking_summary
            return get_work_tracking_summary(*args, **kwargs)
        
        def lazy_cmd_plan(*args, **kwargs):
            from claude_code_ai_brain import cmd_plan
            return cmd_plan(*args, **kwargs)
        
        def lazy_cmd_task(*args, **kwargs):
            from claude_code_ai_brain import cmd_task
            return cmd_task(*args, **kwargs)
        
        def lazy_cmd_next(*args, **kwargs):
            from claude_code_ai_brain import cmd_next
            return cmd_next(*args, **kwargs)
        
        # 지연 로딩 함수들 할당
        self.cmd_flow = lazy_cmd_flow
        self.initialize_context = lazy_initialize_context
        self.save_context = lazy_save_context
        self.update_cache = lazy_update_cache
        self.get_value = lazy_get_value
        self.track_file_access = lazy_track_file_access
        self.track_function_edit = lazy_track_function_edit
        self.get_work_tracking_summary = lazy_get_work_tracking_summary
        self.cmd_plan = lazy_cmd_plan
        self.cmd_task = lazy_cmd_task
        self.cmd_next = lazy_cmd_next
        
        # context manager는 나중에 필요할 때 로드
        self._context_manager = None
        
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
            # 파일 작업 및 코드 분석 (auto_tracking_wrapper에서)
            from auto_tracking_wrapper import (
                create_file, read_file, backup_file, restore_backup,
                replace_block, insert_block,
                parse_with_snippets, get_snippet_preview,
                scan_directory_dict, search_files_advanced, search_code_content
            )
            
            # 파일 작업
            self.create_file = create_file
            self.read_file = read_file
            self.backup_file = backup_file
            self.restore_backup = restore_backup
            
            # 코드 수정
            self.replace_block = replace_block
            self.insert_block = insert_block
            
            # 코드 분석
            self.parse_with_snippets = parse_with_snippets
            self.get_snippet_preview = get_snippet_preview
            
            # 검색
            self.scan_directory_dict = scan_directory_dict
            self.search_files_advanced = search_files_advanced
            self.search_code_content = search_code_content
            
            # 폴더 구조 캐싱 (새로 추가)
            try:
                from auto_tracking_wrapper import (
                    cache_project_structure, get_project_structure,
                    search_in_structure, get_directory_tree, get_structure_stats
                )
                
                self.cache_project_structure = cache_project_structure
                self.get_project_structure = get_project_structure
                self.search_in_structure = search_in_structure
                self.get_directory_tree = get_directory_tree
                self.get_structure_stats = get_structure_stats
                
                print("✅ 폴더 구조 캐싱 함수 로드 성공")
            except ImportError as e:
                print(f"⚠️ 폴더 구조 캐싱 함수 로드 실패: {e}")
        
        except ImportError as e:
            print(f"⚠️ auto_tracking_wrapper 로드 실패: {e}")
    
    def get_context(self):
        """현재 프로젝트 컨텍스트 반환"""
        if self._context_manager and self._context_manager.context:
            return self._context_manager.context
        return None
    
    def get_value(self, key, default=None):
        """캐시에서 값 가져오기 (MCP 워크플로우 지원)"""
        try:
            # context에서 먼저 찾기
            if self._context_manager and self._context_manager.context:
                if key in self._context_manager.context:
                    return self._context_manager.context[key]
            
            # 캐시 파일에서 찾기
            cache_file = os.path.join('memory', '.cache', 'cache_core.json')
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    if key in cache:
                        return cache[key]
            
            return default
        except Exception as e:
            print(f"⚠️ get_value 오류: {e}")
            return default
    
    def initialize_context(self, project_path=None):
        """프로젝트 컨텍스트 초기화"""
        try:
            from api.public import initialize_context as init_ctx
            return init_ctx(project_path)
        except Exception as e:
            print(f"⚠️ initialize_context 오류: {e}")
            return None
    
    def update_cache(self, *args, **kwargs):
        """캐시 업데이트"""
        try:
            from api.public import update_cache as update
            # 인자가 2개일 경우 key와 value로 처리
            if len(args) == 2:
                return update(key=args[0], value=args[1])
            # 인자가 1개이고 딕셔너리인 경우
            elif len(args) == 1 and isinstance(args[0], dict):
                # 딕셔너리의 key, value를 사용
                return update(key=args[0].get('key'), value=args[0].get('value'))
            # 키워드 인자로 호출된 경우
            elif kwargs:
                return update(**kwargs)
            # 인자가 없는 경우 
            else:
                print("⚠️ update_cache: 인자가 필요합니다 (key, value)")
                return None
        except Exception as e:
            print(f"⚠️ update_cache 오류: {e}")
            return None
    
    def cmd_plan(self, *args, **kwargs):
        """plan 명령 래퍼"""
        try:
            from commands.plan import cmd_plan
            return cmd_plan(*args, **kwargs)
        except Exception as e:
            print(f"⚠️ cmd_plan 오류: {e}")
            return None
    
    def cmd_task(self, *args, **kwargs):
        """task 명령 래퍼"""
        try:
            from commands.task import cmd_task
            return cmd_task(*args, **kwargs)
        except Exception as e:
            print(f"⚠️ cmd_task 오류: {e}")
            return None
    
    def cmd_next(self, *args, **kwargs):
        """next 명령 래퍼"""
        try:
            from commands.next import cmd_next
            return cmd_next(*args, **kwargs)
        except Exception as e:
            print(f"⚠️ cmd_next 오류: {e}")
            return None
    
    def list_functions(self):
        """사용 가능한 함수 목록 표시"""
        funcs = [attr for attr in dir(self) 
                if not attr.startswith('_') and callable(getattr(self, attr))]
        print(f"🔧 사용 가능한 헬퍼 함수 ({len(funcs)}개):")
        for func in sorted(funcs):
            print(f"  • helpers.{func}()")
        return funcs
    
    def get_wisdom_stats(self):
        """Wisdom 시스템 통계 조회"""
        if not WISDOM_AVAILABLE or not wisdom:
            return {"error": "Wisdom 시스템을 사용할 수 없습니다."}
        
        return {
            "common_mistakes": len(wisdom.wisdom_data.get('common_mistakes', {})),
            "error_patterns": len(wisdom.wisdom_data.get('error_patterns', {})),
            "best_practices": len(wisdom.wisdom_data.get('best_practices', {})),
            "top_mistakes": list(wisdom.wisdom_data.get('common_mistakes', {}).items())[:3]
        }
    
    def check_code_patterns(self, code, filename="unknown"):
        """코드 패턴 검사"""
        if not WISDOM_AVAILABLE or not hooks:
            return {}
        
        return hooks.check_code_patterns(code, filename)
    
    def track_mistake(self, mistake_type, context=""):
        """실수 추적"""
        if not WISDOM_AVAILABLE or not wisdom:
            return False
        
        wisdom.track_mistake(mistake_type, context)
        return True
    
    def add_best_practice(self, practice, category="general"):
        """베스트 프랙티스 추가"""
        if not WISDOM_AVAILABLE or not wisdom:
            return False
        
        wisdom.add_best_practice(practice, category)
        return True
    
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
    
    # 6. Wisdom 시스템 초기화
    if WISDOM_AVAILABLE:
        try:
            # 프로젝트별 Wisdom Manager 초기화
            project_path = os.getcwd()
            if 'Desktop' in project_path and 'ai-coding-brain-mcp' in project_path:
                # ai-coding-brain-mcp 프로젝트인 경우
                project_root = project_path.split('ai-coding-brain-mcp')[0] + 'ai-coding-brain-mcp'
            else:
                project_root = project_path
            
            from project_wisdom import ProjectWisdomManager
            wisdom = ProjectWisdomManager(project_root)
            print(f"✅ Wisdom 시스템 초기화: {project_root}")
            
            # get_wisdom_manager와 get_wisdom_hooks 호출
            wisdom = get_wisdom_manager()
            hooks = get_wisdom_hooks()
            print("✅ Wisdom 시스템 초기화 완료")
            print(f"  - 추적된 실수: {len(wisdom.wisdom_data.get('common_mistakes', {}))}개")
            print(f"  - 오류 패턴: {len(wisdom.wisdom_data.get('error_patterns', {}))}개")
            
            # 전역 변수로 설정
            repl_globals['wisdom'] = wisdom
            repl_globals['hooks'] = hooks
        except Exception as e:
            print(f"⚠️ Wisdom 초기화 실패: {e}")
            wisdom = None
            hooks = None
    
    # 7. Git Version Manager 초기화
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
    global execution_count, WISDOM_AVAILABLE, hooks
    
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    start_time = time.time()
    
    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            # Wisdom Integration 실행 (코드 실행 전 분석 및 자동 수정)
            if WISDOM_AVAILABLE and hasattr(wisdom_integration, 'pre_execute_check'):
                try:
                    should_proceed, modified_code, analysis = wisdom_integration.pre_execute_check(
                        code, 
                        language="python"
                    )
                    
                    # 코드가 수정된 경우
                    if modified_code and modified_code != code:
                        print("\n✅ Wisdom System이 코드를 자동 수정했습니다.")
                        code = modified_code
                        
                    # 심각한 문제로 실행 중단이 필요한 경우
                    if not should_proceed:
                        print("\n❌ Wisdom System이 심각한 문제를 감지하여 실행을 중단합니다.")
                        return {
                            "success": False,
                            "output": "",
                            "error": "Code execution blocked by Wisdom System",
                            "execution_time": time.time() - start_time,
                            "variable_count": len(repl_globals),
                            "execution_count": execution_count,
                            "wisdom_analysis": analysis
                        }
                except Exception as e:
                    print(f"⚠️ Wisdom Integration 오류: {e}")
            
            # Wisdom Hooks 실행 (코드 실행 전)
            if WISDOM_AVAILABLE and hooks:
                try:
                    # 코드 패턴 검사
                    detected = hooks.check_code_patterns(code, "execute_code")
                    if detected:
                        print("\n⚠️ Wisdom Hooks 감지:")
                        # detected는 패턴 이름의 list
                        for pattern_name in detected:
                            print(f"  - {pattern_name} 패턴 감지됨")
                        print()
                except Exception as e:
                    print(f"⚠️ Hooks 실행 중 오류: {e}")
            
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
