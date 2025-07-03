"""
⚠️ DEPRECATED: 이 모듈은 utils.path_utils로 이동되었습니다.
향후 제거될 예정이므로 새 코드에서는 사용하지 마세요.
"""
import warnings
from utils.path_utils import *
from pathlib import Path

warnings.warn(
    "core.path_utils 모듈이 utils.path_utils로 이동되었습니다. "
    "이 import는 향후 제거될 예정입니다.",
    DeprecationWarning,
    stacklevel=2
)

# 기존 core에만 있던 함수들 (임시 호환성 유지)
def get_desktop_path() -> Path:
    """DEPRECATED: Desktop 경로는 프로젝트와 무관합니다."""
    warnings.warn("get_desktop_path()는 제거될 예정입니다.", DeprecationWarning)
    import os
    return Path(os.path.expanduser("~/Desktop"))

def get_workflow_path() -> Path:
    """DEPRECATED: get_memory_path('workflow.json')을 사용하세요."""
    warnings.warn("get_workflow_path() 대신 get_memory_path('workflow.json')을 사용하세요.", DeprecationWarning)
    return get_memory_path('workflow.json')
