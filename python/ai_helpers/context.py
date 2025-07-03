"""
AI Helpers의 컨텍스트 관련 함수들
새로운 ContextManager와 통합됩니다.
"""
import builtins
import os
from typing import Optional, Dict, Any


def _ensure_context_manager():
    """ContextManager가 없으면 자동으로 초기화"""
    # 이미 있으면 그대로 반환
    if hasattr(builtins, 'repl_session') and hasattr(builtins.repl_session, 'context_manager'):
        return builtins.repl_session.context_manager
    
    # helpers에서 가져오기 시도
    if hasattr(builtins, 'helpers') and hasattr(builtins.helpers, '_context_manager') and builtins.helpers._context_manager:
        # repl_session이 없으면 생성
        if not hasattr(builtins, 'repl_session'):
            class DummyReplSession:
                pass
            builtins.repl_session = DummyReplSession()
        
        # context_manager 설정
        builtins.repl_session.context_manager = builtins.helpers._context_manager
        print("✅ ContextManager 자동 연결 완료")
        return builtins.repl_session.context_manager
    
    # 둘 다 없으면 새로 생성 시도
    try:
        from core.context_manager import get_context_manager
        cm = get_context_manager()
        
        # 현재 프로젝트 이름 추측
        project_name = os.path.basename(os.getcwd())
        cm.initialize(project_name)
        
        # repl_session 설정
        if not hasattr(builtins, 'repl_session'):
            class DummyReplSession:
                pass
            builtins.repl_session = DummyReplSession()
        
        builtins.repl_session.context_manager = cm
        print(f"✅ ContextManager 자동 초기화 완료 (프로젝트: {project_name})")
        return cm
    except Exception as e:
        print(f"⚠️ ContextManager 자동 초기화 실패: {e}")
        print("   → JSON REPL 세션에서 실행하거나 flow_project 명령을 사용하세요.")
        return None


def get_context() -> Optional[Dict[str, Any]]:
    """현재 프로젝트 컨텍스트 반환

    Returns:
        dict: 현재 컨텍스트 또는 None
    """
    try:
        cm = _ensure_context_manager()
        if cm:
            return cm.get_context()
        else:
            return None
    except Exception as e:
        print(f'❌ 컨텍스트 가져오기 실패: {e}')
        return None


def get_value(key: str, default: Any=None) -> Any:
    """캐시에서 값 가져오기
    
    Args:
        key: 가져올 키
        default: 기본값
        
    Returns:
        캐시된 값 또는 기본값
    """
    try:
        cm = _ensure_context_manager()
        if cm:
            return cm.get_value(key, default)
        else:
            return default
    except Exception as e:
        print(f'❌ 값 가져오기 실패: {e}')
        return default


def initialize_context(project_path: Optional[str]=None) -> Optional[Dict[str, Any]]:
    """프로젝트 컨텍스트 초기화
    
    Args:
        project_path: 프로젝트 경로 (미사용, 호환성을 위해 유지)
        
    Returns:
        dict: 초기화된 컨텍스트
    """
    cm = _ensure_context_manager()
    if cm:
        return cm.get_context()
    else:
        return None


def update_cache(*args, **kwargs) -> Optional[Any]:
    """캐시 업데이트
    
    Args:
        *args: 위치 인자 (key, value 순서)
        **kwargs: 키워드 인자
        
    Returns:
        업데이트 성공 여부
    """
    try:
        cm = _ensure_context_manager()
        if cm:
            cm.update_context(*args, **kwargs)
            return True
        else:
            return False
    except Exception as e:
        print(f'❌ 캐시 업데이트 실패: {e}')
        return False


def save_context() -> bool:
    """현재 컨텍스트를 파일에 저장
    
    Returns:
        저장 성공 여부
    """
    try:
        cm = _ensure_context_manager()
        if cm:
            cm.save_all()
            return True
        else:
            return False
    except Exception as e:
        print(f'❌ 컨텍스트 저장 실패: {e}')
        return False


def get_project_context():
    """ProjectContext 인스턴스를 직접 가져오기 (레거시 호환성)
    
    Returns:
        현재 컨텍스트 딕셔너리
    """
    return get_context()


# 별칭들 (호환성)
update_context = update_cache
get_cache_value = get_value
