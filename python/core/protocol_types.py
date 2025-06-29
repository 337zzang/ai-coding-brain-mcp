"""
JSON Protocol Types for TypeScript-Python communication
"""
from typing import Dict, Any, Optional, Literal, Union
from dataclasses import dataclass
import json


@dataclass
class Request:
    """Base request structure"""
    command: str
    action: str
    payload: Dict[str, Any]
    
    @classmethod
    def from_json(cls, data: Union[str, dict]) -> 'Request':
        """Create Request from JSON string or dict"""
        if isinstance(data, str):
            data = json.loads(data)
        return cls(**data)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "command": self.command,
            "action": self.action,
            "payload": self.payload
        }


@dataclass 
class Response:
    """Base response structure"""
    status: Literal["success", "error"]
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        result = {"status": self.status}
        if self.data is not None:
            result["data"] = self.data
        if self.error is not None:
            result["error"] = self.error
        return json.dumps(result)
    
    @classmethod
    def success(cls, data: Dict[str, Any]) -> 'Response':
        """Create success response"""
        return cls(status="success", data=data)
    
    @classmethod
    def error(cls, code: str, message: str, details: Optional[dict] = None) -> 'Response':
        """Create error response"""
        return cls(
            status="error",
            error={
                "code": code,
                "message": message,
                "details": details or {}
            }
        )
