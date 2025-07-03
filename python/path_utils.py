"""
⚠️ DEPRECATED: 이 모듈은 utils.path_utils로 이동되었습니다.
향후 제거될 예정이므로 새 코드에서는 사용하지 마세요.
"""
import warnings
from utils.path_utils import *

warnings.warn(
    "path_utils 모듈이 utils.path_utils로 이동되었습니다. "
    "이 import는 향후 제거될 예정입니다.", 
    DeprecationWarning, 
    stacklevel=2
)

# 하위 호환성을 위한 모든 함수 재export
__all__ = [
    'get_project_root', 'ensure_dir', 'get_memory_dir',
    'get_memory_path', 'get_context_path', 'get_cache_dir',
    'get_file_directory_cache_path', 'safe_relative_path',
    'find_git_root', 'verify_git_root'
]
