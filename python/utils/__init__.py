"""Utility modules for AI Coding Brain MCP"""

from utils.io_helpers import open_text, read_text, write_text, append_text
from utils.path_utils import (
    get_project_root, 
    verify_git_root, 
    find_git_root,
    ensure_dir,
    safe_relative_path
)

__all__ = [
    'open_text', 'read_text', 'write_text', 'append_text',
    'get_project_root', 'verify_git_root', 'find_git_root',
    'ensure_dir', 'safe_relative_path'
]