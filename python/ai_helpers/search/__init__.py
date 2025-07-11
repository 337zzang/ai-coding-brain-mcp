"""
AI Helpers Search Sub-package
통합 검색 기능 제공
"""

# 하위 모듈에서 필요한 함수들 import
from .directory_scan import (
    scan_directory, 
    scan_directory_dict,
    cache_project_structure,
    get_project_structure,
    search_in_structure
)

from .file_search import (
    search_files_advanced,
    _search_files_advanced
)

from .code_search import (
    search_code_content,
    _search_code_content
)

from .unified import (
    list_file_paths,
    grep_code,
    scan_dir
)

# Export 정의
__all__ = [
    # 디렉토리 관련
    'scan_directory', 'scan_directory_dict', 'cache_project_structure',
    'get_project_structure', 'search_in_structure',
    
    # 파일 검색
    'search_files_advanced', '_search_files_advanced',
    
    # 코드 검색
    'search_code_content', '_search_code_content',
    
    # 표준 API
    'list_file_paths', 'grep_code', 'scan_dir'
]
