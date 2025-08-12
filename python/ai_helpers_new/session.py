"""
간단한 Session 모듈 - 프로젝트 전환 지원
"""
import os
from typing import Dict, Any, Optional

# 전역 프로젝트 상태
_current_project = {
    "name": None,
    "path": None,
    "type": None,
    "has_git": False
}

class SimpleSession:
    """간단한 세션 관리자"""

    def __init__(self):
        self.is_initialized = _current_project["name"] is not None
        self.project_context = _current_project.copy()

    def set_project(self, name: str, path: str):
        """프로젝트 설정"""
        _current_project["name"] = name
        _current_project["path"] = path
        _current_project["type"] = "python"
        _current_project["has_git"] = os.path.exists(os.path.join(path, ".git"))

        # 디렉토리 변경
        if os.path.exists(path):
            os.chdir(path)

        self.is_initialized = True
        self.project_context = _current_project.copy()

    def get_project_name(self) -> Optional[str]:
        """현재 프로젝트 이름 반환"""
        return _current_project.get("name")
    
    def get_project_path(self) -> Optional[str]:
        """현재 프로젝트 경로 반환"""
        return _current_project.get("path")

def get_current_session() -> SimpleSession:
    """현재 세션 반환"""
    return SimpleSession()

def set_current_project(name: str, path: str) -> Dict[str, Any]:
    """프로젝트 설정 (project.py에서 사용)"""
    session = get_current_session()
    session.set_project(name, path)
    return {"ok": True, "data": _current_project.copy()}

def get_current_project_info() -> Dict[str, Any]:
    """현재 프로젝트 정보 반환"""
    if _current_project["name"]:
        return {"ok": True, "data": _current_project.copy()}
    else:
        # 현재 디렉토리 기반으로 초기화
        cwd = os.getcwd()
        name = os.path.basename(cwd)
        set_current_project(name, cwd)
        return {"ok": True, "data": _current_project.copy()}
