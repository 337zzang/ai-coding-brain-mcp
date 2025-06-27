"""
Wisdom System Plugins
"""

from .python_indentation_plugin import PythonIndentationPlugin
from .console_usage_plugin import ConsoleUsagePlugin
from .hardcoded_path_plugin import HardcodedPathPlugin

__all__ = [
    'PythonIndentationPlugin',
    'ConsoleUsagePlugin', 
    'HardcodedPathPlugin'
]
