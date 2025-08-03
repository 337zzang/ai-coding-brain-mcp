import functools
from typing import Any

def log_task_operation(operation_type: str):
    """Task 작업을 자동으로 로깅하는 데코레이터

    Args:
        operation_type: 작업 유형 (create, update, delete 등)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # 작업 전 로깅
            plan_id = args[0] if args else kwargs.get('plan_id')

            try:
                # 실제 작업 수행
                result = func(self, *args, **kwargs)

                # 성공 로깅
                if hasattr(self, '_logger') and self._logger:
                    if operation_type == 'create_task' and result:
                        self._logger.log_task_created(plan_id, result.id, result.title)
                    elif operation_type == 'update_task' and result:
                        self._logger.log_task_updated(plan_id, result.id, result.status)

                return result

            except Exception as e:
                # 실패 로깅
                if hasattr(self, '_logger') and self._logger:
                    self._logger.log_error(f"{operation_type} failed", str(e))
                raise

        return wrapper
    return decorator
