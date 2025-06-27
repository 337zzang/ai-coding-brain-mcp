from functools import wraps
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')

def autosave(func: Callable[..., T]) -> Callable[..., T]:
    """
    컨텍스트를 자동으로 저장하는 데코레이터
    
    상태를 변경하는 메서드에 적용하여 변경 후 자동으로 save()를 호출합니다.
    에러 발생 시에도 안전하게 처리됩니다.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> T:
        result = None
        try:
            # 원본 메서드 실행
            result = func(self, *args, **kwargs)
            
            # 성공 시 자동 저장
            if hasattr(self, 'save'):
                try:
                    self.save()
                    logger.debug(f"Auto-saved after {func.__name__}")
                except Exception as save_error:
                    logger.error(f"Auto-save failed after {func.__name__}: {save_error}")
                    # 저장 실패해도 원본 작업은 성공으로 처리
            
            return result
            
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    
    return wrapper


def autosave_async(func: Callable[..., T]) -> Callable[..., T]:
    """
    비동기 자동 저장을 위한 데코레이터 (향후 확장용)
    """
    @wraps(func)
    async def wrapper(self, *args, **kwargs) -> T:
        result = await func(self, *args, **kwargs)
        
        if hasattr(self, 'save'):
            try:
                if hasattr(self.save, '__await__'):
                    await self.save()
                else:
                    self.save()
                logger.debug(f"Auto-saved after {func.__name__}")
            except Exception as save_error:
                logger.error(f"Auto-save failed after {func.__name__}: {save_error}")
        
        return result
    
    return wrapper
