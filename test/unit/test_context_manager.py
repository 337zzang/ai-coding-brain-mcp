"""
Context Manager 단위 테스트
"""
import pytest
from core.context_manager import UnifiedContextManager, get_context_manager

def test_context_manager_singleton():
    """컨텍스트 매니저가 싱글톤인지 확인"""
    manager1 = get_context_manager()
    manager2 = get_context_manager()
    assert manager1 is manager2

def test_initialize_context(temp_project_dir):
    """컨텍스트 초기화 테스트"""
    manager = UnifiedContextManager()
    context = manager.initialize_context(str(temp_project_dir))
    
    assert context['project_name'] == 'test_project'
    assert context['project_root'] == str(temp_project_dir)
    assert 'cache_dir' in context
    assert 'analyzed_files' in context

def test_update_cache(mock_context):
    """캐시 업데이트 테스트"""
    manager = UnifiedContextManager()
    manager.context = mock_context
    
    # 새로운 값 추가
    manager.update_cache('test_key', 'test_value')
    assert manager.get_value('test_key') == 'test_value'
    
    # 기존 값 업데이트
    manager.update_cache('test_key', 'new_value')
    assert manager.get_value('test_key') == 'new_value'
