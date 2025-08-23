"""
Pipeline for composing streaming operations.
"""

from typing import Any, Callable, List
from dataclasses import dataclass


@dataclass
class PipelineStage:
    """Single stage in a processing pipeline."""
    name: str
    func: Callable
    
    
class Pipeline:
    """Composable pipeline for streaming operations."""
    
    def __init__(self):
        self.stages: List[PipelineStage] = []
        
    def add_stage(self, name: str, func: Callable) -> 'Pipeline':
        """Add a processing stage."""
        self.stages.append(PipelineStage(name, func))
        return self
        
    def execute(self, data: Any) -> Any:
        """Execute pipeline on data."""
        result = data
        for stage in self.stages:
            result = stage.func(result)
        return result