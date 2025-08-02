"""
Context-aware Flow Manager
Extends UltraSimpleFlowManager with context management
"""
from typing import Optional, Dict, Any
from .ultra_simple_flow_manager import UltraSimpleFlowManager
from .flow_context import FlowContext


class ContextualFlowManager(UltraSimpleFlowManager):
    """Flow manager with context support"""

    def __init__(self, base_path: str):
        super().__init__(base_path)
        self._context = FlowContext()

    def get_context(self) -> FlowContext:
        """Get current flow context"""
        return self._context

    def create_plan(self, name: str, **kwargs) -> Any:
        """Create plan and update context"""
        plan = super().create_plan(name, **kwargs)
        self._context.select_plan(plan.id)
        return plan

    def select_plan(self, plan_id: str) -> bool:
        """Select plan and update context"""
        # Verify plan exists
        try:
            plan = self.get_plan(plan_id)
            self._context.select_plan(plan_id)
            return True
        except Exception:
            return False

    def get_current_plan(self) -> Optional[Any]:
        """Get currently selected plan"""
        if self._context.current_plan_id:
            try:
                return self.get_plan(self._context.current_plan_id)
            except Exception:
                self._context.current_plan_id = None
        return None

    def add_task_to_current_plan(self, title: str, **kwargs) -> Any:
        """Add task to current plan"""
        if not self._context.current_plan_id:
            raise ValueError("No plan selected")
        return self.add_task(self._context.current_plan_id, title, **kwargs)
