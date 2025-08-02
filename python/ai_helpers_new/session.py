"""
Session management for AI Coding Brain MCP
Provides centralized state management with optional explicit injection
"""
from typing import Optional, Dict, Any
from contextvars import ContextVar
from pathlib import Path
from datetime import datetime
import uuid


# Thread-safe current session storage
_current_session: ContextVar[Optional['Session']] = ContextVar('current_session', default=None)


class Session:
    """Central session object managing all state for REPL session"""

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.now()
        self.project_context: Optional['ProjectContext'] = None
        self.flow_manager: Optional['ContextualFlowManager'] = None
        self.metadata: Dict[str, Any] = {}

    def set_project(self, project_name: str, base_path: Optional[Path] = None) -> 'ProjectContext':
        """Set current project (without os.chdir)"""
        from .flow_context import ProjectContext
        from .contextual_flow_manager import ContextualFlowManager

        # Create/load ProjectContext
        self.project_context = ProjectContext(name=project_name, base_path=base_path)

        # Initialize FlowManager for this project
        flow_path = self.project_context.resolve_path(".ai-brain/flow")
        self.flow_manager = ContextualFlowManager(str(flow_path))

        return self.project_context

    @property
    def flow_context(self) -> Optional['FlowContext']:
        """Get current flow context (project-dependent)"""
        if not self.flow_manager:
            return None
        return self.flow_manager.get_context()

    def clear(self):
        """Clear session state"""
        self.project_context = None
        self.flow_manager = None
        self.metadata.clear()


def get_current_session() -> Session:
    """Get current session (create if none)"""
    session = _current_session.get()
    if session is None:
        session = Session()
        _current_session.set(session)
    return session


def set_current_session(session: Session) -> None:
    """Set current session (for testing/isolation)"""
    _current_session.set(session)


def clear_current_session() -> None:
    """Clear current session"""
    _current_session.set(None)


class isolated_session:
    """Context manager for isolated session (useful for testing)"""

    def __init__(self, session: Optional[Session] = None):
        self.session = session or Session()
        self.previous_session = None

    def __enter__(self) -> Session:
        self.previous_session = _current_session.get()
        _current_session.set(self.session)
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        _current_session.set(self.previous_session)
