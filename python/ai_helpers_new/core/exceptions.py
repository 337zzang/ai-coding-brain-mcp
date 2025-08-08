"""
Flow 시스템 예외 정의
"""

class FlowException(Exception):
    """Flow 시스템 기본 예외"""
    pass

class PlanNotFoundError(FlowException):
    """Plan을 찾을 수 없을 때"""
    def __init__(self, plan_id: str):
        super().__init__(f"Plan not found: {plan_id}")
        self.plan_id = plan_id

class TaskNotFoundError(FlowException):
    """Task를 찾을 수 없을 때"""
    def __init__(self, task_id: str):
        super().__init__(f"Task not found: {task_id}")
        self.task_id = task_id

class InvalidOperationError(FlowException):
    """잘못된 작업 요청"""
    pass

class DuplicateError(FlowException):
    """중복된 항목"""
    def __init__(self, item_type: str, item_id: str):
        super().__init__(f"Duplicate {item_type}: {item_id}")
        self.item_type = item_type
        self.item_id = item_id
