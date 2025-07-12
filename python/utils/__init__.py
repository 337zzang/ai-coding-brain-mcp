"""Utility modules for AI Coding Brain MCP"""

from .io_helpers import open_text
from .path_utils import (
    get_project_root, 
    verify_git_root, 
    find_git_root,
    ensure_dir,
    safe_relative_path,
    write_gitignore,
    is_git_available
)

__all__ = [
    'open_text',
    'get_project_root', 'verify_git_root', 'find_git_root',
    'ensure_dir', 'safe_relative_path', 'write_gitignore', 'is_git_available'
]