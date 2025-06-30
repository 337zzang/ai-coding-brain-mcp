"""컨텍스트 관리 함수들"""

import os
import json
from typing import Dict, Any, Optional
from .decorators import track_operation, lazy_import


@track_operation('context', 'get')
def get_context() -> Optional[Dict[str, Any]]:
    """현재 프로젝트 컨텍스트 반환
    
    Returns:
        dict: 현재 컨텍스트 또는 None
    """
    # 1. context manager를 통해 가져오기 (우선순위)
    try:
        from core.context_manager import get_context_manager
        manager = get_context_manager()
        if manager and manager.context:
            # Pydantic 모델을 dict로 변환
            return manager.context.dict()
    except ImportError:
        pass
    
    # 2. api.public을 통해 가져오기
    try:
        from api.public import get_current_context
        context = get_current_context()
        if context:
            return context
    except ImportError:
        pass
    
    # 3. 전역 context 확인 (폴백)
    import sys
    frame = sys._getframe()
    for _ in range(10):
        if not frame:
            break
        if 'context' in frame.f_globals:
            ctx = frame.f_globals['context']
            # 모듈이 아닌 실제 context 인스턴스인지 확인
            if not hasattr(ctx, '__file__'):  # 모듈이 아님
                if isinstance(ctx, dict):
                    return ctx
                # Pydantic 모델인 경우 dict로 변환
                elif hasattr(ctx, 'dict'):
                    return ctx.dict()
        frame = frame.f_back
    
    return None


@track_operation('context', 'get_value')
def get_value(key: str, default: Any = None) -> Any:
    """캐시에서 값 가져오기 (MCP 워크플로우 지원)
    
    Args:
        key: 가져올 키
        default: 기본값
    
    Returns:
        Any: 캐시된 값 또는 기본값
    """
    try:
        # context에서 먼저 찾기
        context = get_context()
        if context and key in context:
            return context[key]
        
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


@track_operation('context', 'initialize')
def initialize_context(project_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """프로젝트 컨텍스트 초기화
    
    Args:
        project_path: 프로젝트 경로
    
    Returns:
        dict: 초기화된 컨텍스트 또는 None
    """
    try:
        from api.public import initialize_context as init_ctx
        return init_ctx(project_path)
    except Exception as e:
        print(f"⚠️ initialize_context 오류: {e}")
        return None


@track_operation('context', 'update')
def update_cache(*args, **kwargs) -> Optional[Any]:
    """캐시 업데이트
    
    Args:
        *args: 위치 인자 (key, value 순서)
        **kwargs: 키워드 인자
    
    Returns:
        Any: 업데이트 결과
    """
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


# 지연 로딩을 위한 함수들
save_context = lazy_import('claude_code_ai_brain', 'save_context')


def get_project_context():
    """ProjectContext 인스턴스를 직접 가져오기"""
    try:
        from core.context_manager import get_context_manager
        manager = get_context_manager()
        if manager and manager.context:
            return manager.context
    except:
        pass
    return None

"""
자동 추적 래퍼 - v6.2
- execute_code 환경 개선
- task별 작업 추적 기능 추가
- 캐시 구조 개선
- Git 자동 커밋 통합 (v6.2)
"""
import sys
import os
import json
import functools
from datetime import datetime
from typing import Any, Dict, Optional, Callable

# Git Version Manager 통합
try:
    from git_version_manager import get_git_manager
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    
try:
    from api.public import get_current_context
    from core.context_manager import UnifiedContextManager
except ImportError:
    pass


# 캐시 저장 조건 제어를 위한 전역 변수
_operation_counter = 0
_cache_save_interval = 10  # 10회마다 저장
_excluded_operations = {'read_file', 'search_files_advanced', 'search_code_content', 'scan_directory_dict'}

# ============================================================================
# 통합 추적 데코레이터
# ============================================================================

