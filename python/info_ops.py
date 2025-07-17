"""
프로젝트 정보 작업을 위한 헬퍼 함수들
타입 힌트와 안전한 래퍼 제공
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json

@dataclass
class ProjectInfo:
    """프로젝트 정보 데이터클래스"""
    name: str
    path: str
    memory_files: int
    memory_size_kb: float
    has_workflow: bool
    has_active_workflow: bool
    has_history: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectInfo':
        """딕셔너리에서 ProjectInfo 객체 생성"""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """ProjectInfo 객체를 딕셔너리로 변환"""
        return {
            'name': self.name,
            'path': self.path,
            'memory_files': self.memory_files,
            'memory_size_kb': self.memory_size_kb,
            'has_workflow': self.has_workflow,
            'has_active_workflow': self.has_active_workflow,
            'has_history': self.has_history
        }

def get_project_info() -> ProjectInfo:
    """
    현재 프로젝트 정보를 안전하게 가져오기

    Returns:
        ProjectInfo: 프로젝트 정보 객체

    Raises:
        TypeError: pi()가 dict를 반환하지 않는 경우
    """
    # globals()에서 pi 함수 직접 가져오기
    import sys
    main_module = sys.modules.get('__main__')

    if main_module and hasattr(main_module, 'pi'):
        pi_func = getattr(main_module, 'pi')
    else:
        # REPL globals에서 찾기
        pi_func = globals().get('pi')

    if not pi_func:
        raise RuntimeError("pi function not found")

    data = pi_func()
    if not isinstance(data, dict):
        raise TypeError(f"pi() must return dict, got {type(data)}")

    return ProjectInfo.from_dict(data)

def list_projects_safe() -> List[str]:
    """
    프로젝트 목록을 안전하게 가져오기

    Returns:
        List[str]: 프로젝트 이름 목록
    """
    import sys
    main_module = sys.modules.get('__main__')

    if main_module and hasattr(main_module, 'lp'):
        lp_func = getattr(main_module, 'lp')
    else:
        lp_func = globals().get('lp')

    if not lp_func:
        raise RuntimeError("lp function not found")

    result = lp_func()
    if isinstance(result, list):
        return result
    elif isinstance(result, dict):
        return list(result.keys())
    else:
        return []

def get_recent_history(count: int = 10) -> None:
    """
    최근 히스토리를 출력

    Args:
        count: 가져올 히스토리 개수
    """
    import sys
    main_module = sys.modules.get('__main__')

    if main_module and hasattr(main_module, 'show_history'):
        show_history_func = getattr(main_module, 'show_history')
    else:
        show_history_func = globals().get('show_history')

    if not show_history_func:
        raise RuntimeError("show_history function not found")

    show_history_func(count)

# 편의를 위한 별칭
project_info = get_project_info
list_projects = list_projects_safe
recent_history = get_recent_history

__all__ = ["ProjectInfo", "get_project_info", "list_projects_safe", 
           "get_recent_history", "project_info", "list_projects", "recent_history"]
