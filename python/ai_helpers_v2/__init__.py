"""
AI Helpers V2 - 깔끔하고 강력한 헬퍼 시스템
"""
from .file_ops import *
from .search_ops import *
from .code_ops import *
from .git_ops import *
from .project_ops import *
from .llm_ops import *
from .core import get_metrics, clear_cache, get_execution_history
from .helper_result import SearchResult, FileResult, ParseResult, HelperResult
from .ez_code import ez_replace, ez_view

__version__ = "2.0.0"

# Result 클래스들도 export
__all__ = ['SearchResult', 'FileResult', 'ParseResult', 'HelperResult']

try:
    print("🚀 AI Helpers V2 로드됨 - 프로토콜 기반 시스템")
except UnicodeEncodeError:
    print("AI Helpers V2 loaded - Protocol-based system")
