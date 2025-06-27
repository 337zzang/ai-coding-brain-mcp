"""
Wisdom Migration Helper
기존 코드를 새로운 WisdomFactory 구조로 마이그레이션
"""

# 기존 get_wisdom_manager 함수를 WisdomFactory로 리다이렉트
from python.core.wisdom_factory import get_wisdom_manager as new_get_wisdom_manager

# 하위 호환성을 위한 wrapper
def get_wisdom_manager(project_id=None):
    """기존 API와의 하위 호환성 유지"""
    return new_get_wisdom_manager(project_id)

# 플러그인 매니저 초기화
from python.core.wisdom_plugin_base import PluginManager
from python.wisdom_plugins import (
    PythonIndentationPlugin,
    ConsoleUsagePlugin,
    HardcodedPathPlugin
)

def init_default_plugins():
    """기본 플러그인 초기화"""
    manager = PluginManager()
    
    # 기본 플러그인 등록
    manager.register(PythonIndentationPlugin())
    manager.register(ConsoleUsagePlugin())
    manager.register(HardcodedPathPlugin())
    
    return manager

# 전역 플러그인 매니저 인스턴스
default_plugin_manager = init_default_plugins()
