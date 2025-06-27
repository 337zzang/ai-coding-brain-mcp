"""
Wisdom System Core
"""

from .wisdom_factory import WisdomFactory
from .wisdom_plugin_base import WisdomPlugin, PluginManager, Detection, WisdomPattern
from .wisdom_auto_fixer import WisdomAutoFixer
# Removed wisdom_integration to avoid circular import

__all__ = [
    'WisdomFactory',
    'WisdomPlugin', 
    'PluginManager',
    'Detection',
    'WisdomPattern',
    'WisdomAutoFixer'
]
