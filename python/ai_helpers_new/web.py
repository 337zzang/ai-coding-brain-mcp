"""
Web module wrapper - imports from web_new
Refactored on 2025-08-22
"""

from .web_new import *

# Ensure all exports are available
__all__ = [
    'WebNamespace',
    'WebRecorder', 
    'web_start',
    'web_goto',
    'web_click',
    'web_type',
    'web_wait',
    'web_screenshot',
    'web_extract',
    'web_close',
    'web_status',
    'web_execute',
    'web_wait_for',
    'web_scroll',
    'web_select',
    'web_hover',
    'web_cookies',
    'web_headers',
    'web_navigate',
    'web_find',
    'web_find_all',
    'web_exists'
]
