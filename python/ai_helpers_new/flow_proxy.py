"""
Flow Proxy - 프로젝트별 독립적인 FlowManagerUnified 관리
"""
import os
from pathlib import Path
from typing import Dict, Optional

from .flow_manager_unified import FlowManagerUnified


def _detect_project_root(start: Optional[str] = None) -> str:
    """
    프로젝트 루트 디렉토리 자동 탐색
    .git, pyproject.toml, requirements.txt 등을 마커로 사용
    """
    cur = Path(start or os.getcwd()).resolve()
    markers = {'.git', 'pyproject.toml', 'requirements.txt', '.ai-brain-root'}

    # 현재 디렉토리부터 상위로 올라가며 마커 찾기
    for parent in [cur, *cur.parents]:
        if any((parent / m).exists() for m in markers):
            return str(parent)

    # 마커를 찾지 못하면 현재 디렉토리를 프로젝트 루트로 간주
    return str(cur)


class _WorkflowProxy:
    """
    싱글톤 Proxy 클래스
    실제 작업은 프로젝트별 FlowManagerUnified 인스턴스가 담당
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._registry: Dict[str, FlowManagerUnified] = {}
            cls._instance._current: Optional[FlowManagerUnified] = None
        return cls._instance

    def switch(self, project_root: Optional[str] = None) -> FlowManagerUnified:
        """
        프로젝트 전환 - 해당 프로젝트의 FlowManagerUnified로 전환
        """
        # 프로젝트 루트 결정
        if project_root:
            root = os.path.abspath(project_root)
        else:
            root = _detect_project_root()

        # 레지스트리에 없으면 새로 생성
        if root not in self._registry:
            print(f"📁 새 프로젝트 Flow 초기화: {os.path.basename(root)}")
            self._registry[root] = FlowManagerUnified(project_root=root)

        # 현재 매니저 전환
        self._current = self._registry[root]
        return self._current

    def current(self) -> FlowManagerUnified:
        """
        현재 활성화된 FlowManagerUnified 반환
        없으면 현재 디렉토리 기준으로 생성
        """
        if self._current is None:
            self.switch()  # 현재 디렉토리 기준으로 초기화
        return self._current

    def get_project_root(self) -> str:
        """현재 프로젝트 루트 경로 반환"""
        return self.current().project_root

    # Python magic method - 모든 속성/메서드를 current로 위임
    def __getattr__(self, item):
        """모든 속성 접근을 현재 FlowManagerUnified로 전달"""
        return getattr(self.current(), item)

    def __repr__(self):
        if self._current:
            return f"<WorkflowProxy: {self._current.project_root}>"
        return "<WorkflowProxy: No active project>"


# 싱글톤 프록시 인스턴스
_workflow_proxy = _WorkflowProxy()


# 외부 노출 함수
def get_workflow_proxy() -> _WorkflowProxy:
    """워크플로우 프록시 반환"""
    return _workflow_proxy
