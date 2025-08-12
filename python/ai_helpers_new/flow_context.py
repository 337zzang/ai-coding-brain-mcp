"""
Flow Context 모듈 - 프로젝트 컨텍스트 관리
"""
import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

class ProjectContext:
    """프로젝트 컨텍스트 관리 클래스"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.project_name = self.project_path.name
        self.context = {
            "name": self.project_name,
            "path": str(self.project_path),
            "type": self._detect_project_type(),
            "has_git": (self.project_path / ".git").exists(),
            "has_flow": (self.project_path / ".ai-brain").exists()
        }
    
    def _detect_project_type(self) -> str:
        """프로젝트 타입 감지"""
        if (self.project_path / "package.json").exists():
            return "node"
        elif (self.project_path / "requirements.txt").exists():
            return "python"
        elif (self.project_path / "Cargo.toml").exists():
            return "rust"
        else:
            return "unknown"
    
    def get_readme(self, max_lines: int = 60) -> str:
        """README 파일 읽기"""
        readme_files = ["README.md", "readme.md", "README.txt", "readme.txt"]
        for readme in readme_files:
            readme_path = self.project_path / readme
            if readme_path.exists():
                try:
                    with open(readme_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()[:max_lines]
                        return ''.join(lines)
                except Exception as e:
                    return f"Error reading README: {e}"
        return "No README found"
    
    def get_file_structure(self, max_depth: int = 3) -> Dict[str, Any]:
        """프로젝트 파일 구조 가져오기"""
        def scan_dir(path: Path, depth: int = 0) -> Dict[str, Any]:
            if depth >= max_depth:
                return {}
            
            result = {}
            try:
                for item in path.iterdir():
                    if item.name.startswith('.'):
                        continue
                    if item.is_dir():
                        if item.name not in ['node_modules', '__pycache__', 'venv', '.git']:
                            result[item.name] = scan_dir(item, depth + 1)
                    else:
                        result[item.name] = "file"
            except PermissionError:
                pass
            
            return result
        
        return scan_dir(self.project_path)
    
    def to_dict(self) -> Dict[str, Any]:
        """컨텍스트를 딕셔너리로 변환"""
        return self.context
    
    def read_file(self, filename: str) -> Optional[str]:
        """프로젝트 내 파일 읽기"""
        try:
            file_path = self.project_path / filename.lower()
            # 대소문자 구분 없이 파일 찾기
            if not file_path.exists():
                # 다른 케이스로 시도
                for f in self.project_path.iterdir():
                    if f.name.lower() == filename.lower():
                        file_path = f
                        break
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception:
            pass
        return None

def find_project_path(project_name: str) -> Optional[str]:
    """프로젝트 경로 찾기 - Desktop 전용 (단순화)"""
    
    # Desktop 폴더만 검색
    desktop = Path.home() / "Desktop"
    
    if desktop.exists():
        # 직접 경로 확인
        project_path = desktop / project_name
        if project_path.exists() and project_path.is_dir():
            return str(project_path)
    
    return None

def get_project_list() -> List[Dict[str, str]]:
    """사용 가능한 프로젝트 목록 가져오기"""
    projects = []
    
    # Desktop 디렉토리 스캔
    desktop = Path.home() / "Desktop"
    if desktop.exists():
        for path in desktop.iterdir():
            if path.is_dir() and not path.name.startswith('.'):
                # 프로젝트로 간주할 조건
                if any([
                    (path / ".git").exists(),
                    (path / "package.json").exists(),
                    (path / "requirements.txt").exists(),
                    (path / ".ai-brain").exists()
                ]):
                    projects.append({
                        "name": path.name,
                        "path": str(path),
                        "has_flow": (path / ".ai-brain").exists()
                    })
    
    return projects
