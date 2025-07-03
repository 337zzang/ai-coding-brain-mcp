"""
경로 유틸리티 - 프로젝트 경로 관리
"""
import os
from pathlib import Path
from typing import Optional

def get_project_root(project_name: Optional[str] = None) -> Path:
    """프로젝트 루트 경로 가져오기
    
    우선순위:
    1. FLOW_PROJECT_ROOT 환경변수
    2. AI_PROJECTS_DIR 환경변수  
    3. ~/Desktop (기본값)
    """
    # 환경변수 확인
    root = os.environ.get('FLOW_PROJECT_ROOT')
    if not root:
        root = os.environ.get('AI_PROJECTS_DIR')
    if not root:
        root = os.path.expanduser("~/Desktop")
        
    root_path = Path(root)
    
    if project_name:
        return root_path / project_name
    return root_path

def ensure_project_directory(project_name: str) -> Path:
    """프로젝트 디렉토리 확인 및 생성"""
    project_path = get_project_root(project_name)
    project_path.mkdir(parents=True, exist_ok=True)
    
    # 필수 서브디렉토리 생성
    subdirs = ['memory', 'test', 'docs']
    for subdir in subdirs:
        (project_path / subdir).mkdir(exist_ok=True)
        
    return project_path

def get_memory_path(filename: str, project_name: Optional[str] = None) -> Path:
    """메모리 파일 경로 가져오기"""
    if project_name:
        project_root = get_project_root(project_name)
    else:
        project_root = Path.cwd()
        
    return project_root / 'memory' / filename
