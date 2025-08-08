"""프로젝트 경로 관리를 위한 Context 클래스"""

import os
from pathlib import Path
from typing import Optional, Dict, Any


class ProjectContext:
    """프로젝트 경로를 관리하는 Context 클래스

    os.chdir을 사용하지 않고 프로젝트별 경로를 관리합니다.
    """

    def __init__(self):
        self._current_project: Optional[str] = None
        self._project_path: Optional[Path] = None
        self._base_path: Optional[Path] = None
        self._initialize_base_path()

    def _initialize_base_path(self):
        """기본 프로젝트 경로 초기화"""
        # 환경변수 우선
        env_path = os.environ.get("PROJECT_BASE_PATH")
        if env_path:
            self._base_path = Path(env_path).expanduser().resolve()
        else:
            # 기본값: 홈/Desktop
            self._base_path = (Path.home() / "Desktop").resolve()

    def set_project(self, project_name: str) -> None:
        """현재 프로젝트 설정"""
        self._current_project = project_name
        self._project_path = (self._base_path / project_name).resolve()

    def get_project_name(self) -> Optional[str]:
        """현재 프로젝트 이름 반환"""
        return self._current_project

    def get_project_path(self) -> Optional[Path]:
        """현재 프로젝트 경로 반환"""
        return self._project_path

    def resolve_path(self, relative_path: str) -> Path:
        """상대 경로를 프로젝트 기준 절대 경로로 변환"""
        if self._project_path:
            return self._project_path / relative_path
        else:
            # 프로젝트가 설정되지 않은 경우 현재 디렉토리 기준
            return Path.cwd() / relative_path

    def get_base_path(self) -> Path:
        """기본 프로젝트 경로 반환"""
        return self._base_path

    def set_base_path(self, path: str) -> None:
        """기본 프로젝트 경로 설정"""
        self._base_path = Path(path)


# 전역 ProjectContext 인스턴스
_project_context = ProjectContext()


def get_project_context() -> ProjectContext:
    """ProjectContext 싱글톤 인스턴스 반환"""
    return _project_context


def resolve_project_path(relative_path: str) -> str:
    """편의 함수: 상대 경로를 프로젝트 기준 절대 경로로 변환"""
    return str(get_project_context().resolve_path(relative_path))
