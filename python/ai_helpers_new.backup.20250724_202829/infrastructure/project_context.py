"""
Project Context Management for AI Coding Brain MCP

This module provides the ProjectContext class which manages project-specific
paths and directories for the Flow system.
"""

from pathlib import Path
from typing import Optional, Dict, Any
import json
import os


class ProjectContext:
    """프로젝트 컨텍스트 관리 클래스

    프로젝트의 루트 디렉토리를 기준으로 모든 관련 경로를 관리합니다.
    각 프로젝트는 독립적인 .ai-brain 디렉토리를 가지며,
    flows.json과 기타 메타데이터를 프로젝트별로 격리합니다.

    Attributes:
        root: 프로젝트 루트 디렉토리 (Path 객체)

    Example:
        >>> context = ProjectContext("/path/to/project")
        >>> flows_path = context.flow_file
        >>> context.ensure_directories()
    """

    def __init__(self, root: Path):
        """ProjectContext 초기화

        Args:
            root: 프로젝트 루트 디렉토리 경로

        Raises:
            ValueError: 경로가 존재하지 않거나 디렉토리가 아닌 경우
        """
        self._root = Path(root).resolve()
        self._validate_project_root()
        self.ensure_directories()

    @property
    def root(self) -> Path:
        """프로젝트 루트 디렉토리"""
        return self._root

    @property
    def ai_brain_dir(self) -> Path:
        """AI Brain 디렉토리 (.ai-brain)"""
        return self._root / ".ai-brain"

    @property
    def flow_file(self) -> Path:
        """flows.json 파일 경로"""
        return self.ai_brain_dir / "flows.json"

    @property
    def current_flow_file(self) -> Path:
        """현재 flow ID를 저장하는 파일"""
        return self.ai_brain_dir / "current_flow.txt"

    @property
    def context_file(self) -> Path:
        """context.json 파일 경로"""
        return self.ai_brain_dir / "context.json"

    @property
    def backup_dir(self) -> Path:
        """백업 디렉토리"""
        return self._root / "backups"

    @property
    def docs_dir(self) -> Path:
        """문서 디렉토리"""
        return self._root / "docs"

    @property
    def test_dir(self) -> Path:
        """테스트 디렉토리"""
        return self._root / "test"

    def _validate_project_root(self):
        """프로젝트 루트 유효성 검증

        Raises:
            ValueError: 경로가 유효하지 않은 경우
        """
        if not self._root.exists():
            raise ValueError(f"Project root does not exist: {self._root}")

        if not self._root.is_dir():
            raise ValueError(f"Project root is not a directory: {self._root}")

    def ensure_directories(self):
        """필요한 디렉토리 생성

        다음 디렉토리들을 생성합니다:
        - .ai-brain
        - backups  
        - docs
        """
        self.ai_brain_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def get_relative_path(self, absolute_path: Path) -> Path:
        """절대 경로를 프로젝트 상대 경로로 변환

        Args:
            absolute_path: 변환할 절대 경로

        Returns:
            프로젝트 루트 기준 상대 경로.
            프로젝트 외부 경로인 경우 원본 경로 반환.
        """
        try:
            return Path(absolute_path).relative_to(self._root)
        except ValueError:
            # 프로젝트 외부 경로인 경우
            return Path(absolute_path)

    def get_absolute_path(self, relative_path: str) -> Path:
        """상대 경로를 절대 경로로 변환

        Args:
            relative_path: 프로젝트 루트 기준 상대 경로

        Returns:
            절대 경로
        """
        return self._root / relative_path

    def is_within_project(self, path: Path) -> bool:
        """경로가 프로젝트 내부에 있는지 확인

        Args:
            path: 확인할 경로

        Returns:
            프로젝트 내부 경로인 경우 True
        """
        try:
            Path(path).resolve().relative_to(self._root)
            return True
        except ValueError:
            return False

    def get_project_info(self) -> Dict[str, Any]:
        """프로젝트 정보 반환

        Returns:
            프로젝트 정보를 담은 딕셔너리:
            - root: 프로젝트 루트 경로
            - name: 프로젝트 이름 (디렉토리명)
            - ai_brain_exists: .ai-brain 디렉토리 존재 여부
            - flows_exists: flows.json 파일 존재 여부
            - has_git: Git 저장소 여부
        """
        return {
            'root': str(self._root),
            'name': self._root.name,
            'ai_brain_exists': self.ai_brain_dir.exists(),
            'flows_exists': self.flow_file.exists(),
            'has_git': (self._root / '.git').exists(),
            'has_backup': self.backup_dir.exists(),
            'has_docs': self.docs_dir.exists()
        }

    def switch_to(self):
        """현재 작업 디렉토리를 프로젝트 루트로 변경

        주의: 이 메서드는 프로세스의 작업 디렉토리를 변경합니다.
        """
        os.chdir(self._root)

    def get_ai_brain_files(self) -> Dict[str, int]:
        """AI Brain 디렉토리의 파일 목록과 크기 반환

        Returns:
            파일명과 크기(bytes)를 담은 딕셔너리
        """
        files = {}
        if self.ai_brain_dir.exists():
            for file_path in self.ai_brain_dir.iterdir():
                if file_path.is_file():
                    files[file_path.name] = file_path.stat().st_size
        return files

    def clean_ai_brain_backups(self, keep_count: int = 10):
        """.ai-brain/backups 디렉토리의 오래된 백업 정리

        Args:
            keep_count: 유지할 백업 파일 개수
        """
        backup_dir = self.ai_brain_dir / "backups"
        if backup_dir.exists():
            backups = sorted(backup_dir.glob("*.backup"))
            if len(backups) > keep_count:
                for backup in backups[:-keep_count]:
                    backup.unlink()

    def __str__(self) -> str:
        """문자열 표현"""
        return f"ProjectContext({self._root})"

    def __repr__(self) -> str:
        """개발자용 표현"""
        return f"ProjectContext(root='{self._root}')"

    def __eq__(self, other) -> bool:
        """동등성 비교"""
        if not isinstance(other, ProjectContext):
            return False
        return self._root == other._root

    def __hash__(self) -> int:
        """해시값 (딕셔너리 키로 사용 가능)"""
        return hash(self._root)
