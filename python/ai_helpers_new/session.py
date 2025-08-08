"""
Session management for AI Coding Brain MCP

Thread-safe session management using contextvars to handle
project context, flow state, and other session-specific data.
"""

from typing import Optional, Dict, Any, TYPE_CHECKING
from contextvars import ContextVar
from pathlib import Path
import threading

if TYPE_CHECKING:
    from .flow_context import ProjectContext, FlowContext
    from .contextual_flow_manager import ContextualFlowManager

# Thread-safe current session storage
_current_session: ContextVar[Optional['Session']] = ContextVar('current_session', default=None)

# Lock for session creation
_session_lock = threading.Lock()


class Session:
    """
    Central session object managing all state for a REPL session.

    This class encapsulates:
    - Project context (current project, paths)
    - Flow manager and context
    - Session metadata

    The session is thread-safe and can be accessed globally via
    get_current_session() or passed explicitly for testing.
    """

    def __init__(self):
        """Initialize a new session."""
        self.project_context: Optional['ProjectContext'] = None
        self.flow_manager: Optional['ContextualFlowManager'] = None
        self.metadata: Dict[str, Any] = {}
        self._initialized = False

    def set_project(self, project_name: str, project_path: Optional[str] = None) -> 'ProjectContext':
        """
        Set the current project for this session.

        Args:
            project_name: Name of the project
            project_path: Optional explicit path (defaults to cwd/project_name)

        Returns:
            The ProjectContext for the project
        """
        # Import here to avoid circular imports
        from .flow_context import ProjectContext
        from .contextual_flow_manager import ContextualFlowManager

        # Create or update project context
        self.project_context = ProjectContext(
            name=project_name,
            base_path=Path(project_path) if project_path else None
        )

        # Create flow manager for this project
        flow_path = self.project_context.resolve_path(".ai-brain/flow")
        self.flow_manager = ContextualFlowManager(flow_path, self.project_context)

        # Mark as initialized
        self._initialized = True

        return self.project_context

    @property
    def flow_context(self) -> Optional['FlowContext']:
        """Get the current flow context (if project is set)."""
        if not self.flow_manager:
            return None
        return self.flow_manager.get_context()

    @property
    def is_initialized(self) -> bool:
        """Check if session has been initialized with a project."""
        return self._initialized

    def get_project_path(self) -> Optional[Path]:
        """Get the current project path."""
        if not self.project_context:
            return None
        return self.project_context.base_path

    def get_project_name(self) -> Optional[str]:
        """Get the current project name."""
        if not self.project_context:
            return None
        return self.project_context.name

    def clear(self):
        """Clear all session state."""
        self.project_context = None
        self.flow_manager = None
        self.metadata.clear()
        self._initialized = False


def get_current_session() -> Session:
    """
    Get the current session, creating one if necessary.

    This function is thread-safe and returns a session object
    that is local to the current context (thread/async task).

    Returns:
        The current Session instance
    """
    session = _current_session.get()

    if session is None:
        # Use lock to ensure only one session is created
        with _session_lock:
            # Double-check after acquiring lock
            session = _current_session.get()
            if session is None:
                session = Session()
                _current_session.set(session)

    return session


def set_session(session: Optional[Session]) -> Optional[Session]:
    """
    Set the current session (mainly for testing).

    Args:
        session: Session to set, or None to clear

    Returns:
        The previous session
    """
    previous = _current_session.get()
    _current_session.set(session)
    return previous


def clear_session():
    """Clear the current session."""
    session = _current_session.get()
    if session:
        session.clear()
    _current_session.set(None)


class SessionScope:
    """
    Context manager for temporary session changes.

    Usage:
        with SessionScope() as session:
            # Use isolated session
            session.set_project("test")
            # ... do work ...
        # Original session restored
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize scope with optional session.

        Args:
            session: Session to use, or None to create new
        """
        self.session = session or Session()
        self.previous_session: Optional[Session] = None

    def __enter__(self) -> Session:
        """Enter the scope."""
        self.previous_session = set_session(self.session)
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the scope and restore previous session."""
        set_session(self.previous_session)
        return False


# Convenience function for isolated testing
def isolated_session() -> SessionScope:
    """
    Create an isolated session scope for testing.

    Usage:
        with isolated_session() as session:
            # Test with isolated session
            api = get_flow_api(session)
            # ...
    """
    return SessionScope()
