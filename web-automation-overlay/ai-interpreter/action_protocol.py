"""
action_protocol.py - Web Automation Action Protocol
Defines structured action format for token-efficient AI communication
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

class ActionType(Enum):
    """Supported action types"""
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    WAIT = "wait"
    SCROLL = "scroll"
    HOVER = "hover"
    SCREENSHOT = "screenshot"

class OverlayColor(Enum):
    """Overlay highlight colors"""
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    YELLOW = "yellow"
    PURPLE = "purple"

@dataclass
class Target:
    """Target element specification"""
    selector: Optional[str] = None
    text: Optional[str] = None
    position: Optional[Dict[str, float]] = None

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class Overlay:
    """Visual overlay configuration"""
    color: str
    label: str
    duration: int = 2000  # milliseconds

    def to_dict(self):
        return asdict(self)

@dataclass
class ActionOptions:
    """Action execution options"""
    delay: Optional[int] = None
    wait_for: Optional[str] = None
    retry_max_attempts: Optional[int] = None
    retry_interval: Optional[int] = None
    continue_on_error: bool = False

    def to_dict(self):
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class Action:
    """Single automation action"""
    type: ActionType
    target: Target
    value: Optional[str] = None
    overlay: Optional[Overlay] = None
    options: Optional[ActionOptions] = None

    def to_dict(self):
        result = {
            "type": self.type.value,
            "target": self.target.to_dict()
        }
        if self.value:
            result["value"] = self.value
        if self.overlay:
            result["overlay"] = self.overlay.to_dict()
        if self.options:
            result["options"] = self.options.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """Create Action from dictionary"""
        return cls(
            type=ActionType(data["type"]),
            target=Target(**data["target"]),
            value=data.get("value"),
            overlay=Overlay(**data["overlay"]) if "overlay" in data else None,
            options=ActionOptions(**data["options"]) if "options" in data else None
        )

class ActionSequence:
    """Complete action sequence for automation"""

    def __init__(self, session_id: Optional[str] = None):
        self.version = "1.0.0"
        self.session_id = session_id or self._generate_session_id()
        self.actions: List[Action] = []
        self.metadata = {}

    def _generate_session_id(self):
        """Generate unique session ID"""
        import time
        import random
        return f"session_{int(time.time())}_{random.randint(1000, 9999)}"

    def add_action(self, action: Action):
        """Add action to sequence"""
        self.actions.append(action)
        return self

    def click(self, selector: str, label: str = None, color: str = "blue"):
        """Add click action with optional overlay"""
        action = Action(
            type=ActionType.CLICK,
            target=Target(selector=selector),
            overlay=Overlay(color=color, label=label or f"Click {selector}") if label else None
        )
        return self.add_action(action)

    def type_text(self, selector: str, text: str, label: str = None):
        """Add type action"""
        action = Action(
            type=ActionType.TYPE,
            target=Target(selector=selector),
            value=text,
            overlay=Overlay(color="green", label=label or f"Type: {text[:20]}...") if label else None
        )
        return self.add_action(action)

    def wait(self, selector: str = None, delay: int = 1000):
        """Add wait action"""
        action = Action(
            type=ActionType.WAIT,
            target=Target(selector=selector) if selector else Target(selector="body"),
            options=ActionOptions(delay=delay)
        )
        return self.add_action(action)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps({
            "version": self.version,
            "session_id": self.session_id,
            "actions": [action.to_dict() for action in self.actions],
            "metadata": self.metadata
        }, indent=2)

    @classmethod
    def from_json(cls, json_str: str):
        """Create from JSON string"""
        data = json.loads(json_str)
        sequence = cls(session_id=data.get("session_id"))
        sequence.version = data.get("version", "1.0.0")
        sequence.metadata = data.get("metadata", {})

        for action_data in data.get("actions", []):
            sequence.actions.append(Action.from_dict(action_data))

        return sequence

    def optimize_for_tokens(self) -> str:
        """Generate token-optimized representation"""
        # Compact representation for AI processing
        compact = []
        for i, action in enumerate(self.actions, 1):
            if action.type == ActionType.CLICK:
                compact.append(f"{i}. Click: {action.target.selector}")
            elif action.type == ActionType.TYPE:
                compact.append(f"{i}. Type '{action.value}' in {action.target.selector}")
            elif action.type == ActionType.WAIT:
                compact.append(f"{i}. Wait {action.options.delay}ms")
        return "\n".join(compact)

# Example usage
def create_login_sequence(username: str, password: str) -> ActionSequence:
    """Create a login action sequence"""
    seq = ActionSequence()
    seq.click("#username", "Step 1: Enter username", "blue")
    seq.type_text("#username", username, "Type username")
    seq.click("#password", "Step 2: Enter password", "green")
    seq.type_text("#password", password, "Type password")
    seq.click("button[type='submit']", "Step 3: Submit", "red")
    seq.wait(delay=2000)
    return seq
