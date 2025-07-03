"""
⚠️ DEPRECATED: workflow_manager는 workflow.workflow_manager로 이동되었습니다.
"""
import warnings
warnings.warn(
    "workflow_manager 모듈이 workflow.workflow_manager로 이동되었습니다.",
    DeprecationWarning,
    stacklevel=2
)

# 하위 호환성을 위한 재export
from workflow.workflow_manager import *
