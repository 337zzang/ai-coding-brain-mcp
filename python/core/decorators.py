"""
데코레이터 정의 - 개선된 버전
"""
from functools import wraps
from typing import Callable, Any
import logging

# 로거 설정
logger = logging.getLogger(__name__)


def autosave(func: Callable) -> Callable:
    """
    메서드 실행 후 자동으로 상태를 저장하는 데코레이터
    WorkflowManager의 메서드에서 사용
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> Any:
        # 메서드 실행
        result = func(self, *args, **kwargs)
        
        # 성공적으로 실행된 경우 상태 저장
        # _save_state 메서드 확인 (WorkflowManager용)
        if hasattr(self, '_save_state') and callable(getattr(self, '_save_state')):
            try:
                self._save_state()
                logger.debug(f"✅ Auto-saved after {func.__name__}")
                print(f"💾 상태 자동 저장됨 (by {func.__name__})")
            except Exception as e:
                logger.error(f"❌ Auto-save failed after {func.__name__}: {e}")
                print(f"⚠️ 상태 저장 실패: {e}")
        # save 메서드 확인 (다른 클래스용)
        elif hasattr(self, 'save') and callable(getattr(self, 'save')):
            try:
                self.save()
                logger.debug(f"✅ Auto-saved after {func.__name__}")
            except Exception as e:
                logger.error(f"❌ Auto-save failed after {func.__name__}: {e}")
        
        return result
    
    return wrapper
