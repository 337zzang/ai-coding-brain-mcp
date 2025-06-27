"""
Wisdom 플러그인 패키지
기본 제공 플러그인들을 포함합니다.
"""

from .python_indentation_plugin import PythonIndentationPlugin
from .console_usage_plugin import ConsoleUsagePlugin
from .hardcoded_path_plugin import HardcodedPathPlugin

__all__ = [
    'PythonIndentationPlugin',
    'ConsoleUsagePlugin', 
    'HardcodedPathPlugin'
]
