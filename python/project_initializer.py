"""프로젝트 초기화 전용 모듈

새 프로젝트 생성 시 필요한 모든 초기화 작업을 담당합니다.
단일 책임 원칙에 따라 프로젝트 스켈레톤 생성만을 처리합니다.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import subprocess

from python.ai_helpers.helper_result import HelperResult

logger = logging.getLogger(__name__)


def is_git_available() -> bool:
    """Git 사용 가능 여부 확인"""
    try:
        result = subprocess.run(['git', '--version'], capture_output=True)
        return result.returncode == 0
    except:
        return False


class ProjectInitializer:
    """프로젝트 초기화를 담당하는 클래스"""
    
    # 기본 디렉터리 구조
    DEFAULT_DIRS = ['src', 'test', 'docs', 'memory']
    
    def __init__(self):
        self.created_items = {
            'directories': [],
            'files': [],
            'git_initialized': False
        }
    
    def create_project(self, project_name: str, base_path: Optional[Path] = None, 
                      init_git: bool = True) -> HelperResult:
        """새 프로젝트 생성
        
        Args:
            project_name: 프로젝트 이름
            base_path: 프로젝트를 생성할 기본 경로 (기본값: 현재 디렉터리)
            init_git: Git 초기화 여부
            
        Returns:
            HelperResult: 생성 결과
        """
        try:
            # 기본 경로 설정
            if base_path is None:
                base_path = Path.home() / 'Desktop'
            
            project_path = base_path / project_name
            
            # 이미 존재하는지 확인
            if project_path.exists():
                return HelperResult.fail(
                    f"프로젝트 '{project_name}'이(가) 이미 존재합니다. (경로: {str(project_path)})"
                )
            
            logger.info(f"새 프로젝트 생성 시작: {project_name}")
            
            # 프로젝트 루트 생성
            project_path.mkdir(parents=True)
            self.created_items['directories'].append(str(project_path))
            
            # 디렉터리 구조 생성
            self._create_directory_structure(project_path)
            
            # 기본 파일 생성
            self._create_basic_files(project_path, project_name)
            
            # 컨텍스트 초기화
            self._initialize_context(project_path, project_name)
            
            # Git 초기화
            if init_git and is_git_available():
                self._initialize_git(project_path, project_name)
            
            logger.info(f"프로젝트 생성 완료: {project_name}")
            
            return HelperResult.success({
                'project_name': project_name,
                'project_path': str(project_path),
                'created': self.created_items,
                'message': f"✅ 프로젝트 '{project_name}' 생성 완료"
            })
            
        except Exception as e:
            logger.error(f"프로젝트 생성 실패: {e}")
            return HelperResult.fail(
                f"프로젝트 생성 중 오류 발생: {str(e)} ({type(e).__name__})"
            )
    
    def _create_directory_structure(self, project_path: Path):
        """표준 디렉터리 구조 생성"""
        for dir_name in self.DEFAULT_DIRS:
            dir_path = project_path / dir_name
            dir_path.mkdir(exist_ok=True)
            self.created_items['directories'].append(str(dir_path))
            logger.debug(f"디렉터리 생성: {dir_path}")
    
    def _create_basic_files(self, project_path: Path, project_name: str):
        """기본 파일들 생성"""
        # README.md
        self._create_readme(project_path, project_name)
        
        # docs/overview.md
        self._create_docs_overview(project_path, project_name)
        
        # test 파일들
        self._create_test_files(project_path)
        
        # src/__init__.py
        self._create_src_init(project_path)
    
    def _create_readme(self, project_path: Path, project_name: str):
        """README.md 생성"""
        content = f"""# {project_name}

## 🚀 프로젝트 개요
{project_name} 프로젝트입니다.

## 📁 디렉터리 구조
```
{project_name}/
├── README.md          # 프로젝트 문서
├── src/              # 소스 코드
├── test/             # 테스트 코드  
├── docs/             # 문서
└── memory/           # 프로젝트 메모리/컨텍스트
```

## 🛠️ 시작하기
프로젝트가 초기화되었습니다. 이제 개발을 시작하세요!

### 다음 단계
1. 프로젝트로 전환: `/flow {project_name}`
2. 워크플로우 생성: `/plan "초기 개발 계획"`
3. 개발 시작!

생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        file_path = project_path / "README.md"
        file_path.write_text(content, encoding="utf-8")
        self.created_items['files'].append(str(file_path))
        logger.debug(f"파일 생성: {file_path}")
    
    def _create_docs_overview(self, project_path: Path, project_name: str):
        """docs/overview.md 생성"""
        content = f"""# {project_name} 프로젝트 문서

## 프로젝트 설명
이 문서는 {project_name} 프로젝트의 기술 문서입니다.

## 주요 기능
- [ ] 기능 1
- [ ] 기능 2
- [ ] 기능 3

## 아키텍처
프로젝트 아키텍처 설명을 여기에 작성하세요.

## API 문서
API 상세 설명을 여기에 작성하세요.

## 개발 가이드
개발 시 참고할 가이드라인을 여기에 작성하세요.
"""
        file_path = project_path / "docs" / "overview.md"
        file_path.write_text(content, encoding="utf-8")
        self.created_items['files'].append(str(file_path))
        logger.debug(f"파일 생성: {file_path}")
    
    def _create_test_files(self, project_path: Path):
        """테스트 파일들 생성"""
        # test/__init__.py
        init_path = project_path / "test" / "__init__.py"
        init_path.touch()
        self.created_items['files'].append(str(init_path))
        
        # test/test_smoke.py
        test_content = '''"""Smoke test for project initialization"""

import os
import sys
from pathlib import Path

def test_smoke():
    """프로젝트가 정상적으로 초기화되었는지 확인"""
    assert True, "Basic smoke test passed"

def test_project_structure():
    """프로젝트 구조가 올바른지 확인"""
    project_root = Path(__file__).parent.parent
    
    # 필수 디렉터리 확인
    required_dirs = ['src', 'test', 'docs', 'memory']
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        assert dir_path.exists(), f"{dir_name} 디렉터리가 없습니다"
        assert dir_path.is_dir(), f"{dir_name}은 디렉터리가 아닙니다"
    
    # 필수 파일 확인
    assert (project_root / "README.md").exists(), "README.md가 없습니다"
    assert (project_root / "docs" / "overview.md").exists(), "docs/overview.md가 없습니다"
    
    print("✅ 프로젝트 구조 테스트 통과")

if __name__ == "__main__":
    test_smoke()
    test_project_structure()
'''
        test_path = project_path / "test" / "test_smoke.py"
        test_path.write_text(test_content, encoding="utf-8")
        self.created_items['files'].append(str(test_path))
        logger.debug(f"파일 생성: {test_path}")
    
    def _create_src_init(self, project_path: Path):
        """src/__init__.py 생성"""
        init_content = f'''"""
{project_path.name} 프로젝트 소스 코드
"""

__version__ = "0.1.0"
__author__ = "AI Coding Brain MCP"
'''
        file_path = project_path / "src" / "__init__.py"
        file_path.write_text(init_content, encoding="utf-8")
        self.created_items['files'].append(str(file_path))
        logger.debug(f"파일 생성: {file_path}")
    
    def _initialize_context(self, project_path: Path, project_name: str):
        """프로젝트 컨텍스트 초기화"""
        context_data = {
            "project_name": project_name,
            "created_at": datetime.now().isoformat(),
            "description": f"{project_name} 프로젝트",
            "version": "0.1.0",
            "project_path": str(project_path),
            "last_updated": datetime.now().isoformat(),
            "tags": ["new", "initialized"],
            "metadata": {
                "created_by": "project_initializer",
                "template": "default"
            }
        }
        
        context_path = project_path / "memory" / "context.json"
        context_path.write_text(
            json.dumps(context_data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        self.created_items['files'].append(str(context_path))
        logger.debug(f"컨텍스트 초기화: {context_path}")
    
    def _initialize_git(self, project_path: Path, project_name: str):
        """Git 저장소 초기화"""
        try:
            # Git 초기화
            result = subprocess.run(
                ['git', 'init'],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.warning(f"Git 초기화 실패: {result.stderr}")
                return
            
            # .gitignore 생성
            gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project specific
*.log
.DS_Store
Thumbs.db
memory/context.json.backup*
memory/workflow.json.backup*
"""
            gitignore_path = project_path / ".gitignore"
            gitignore_path.write_text(gitignore_content, encoding="utf-8")
            self.created_items['files'].append(str(gitignore_path))
            
            # 첫 커밋
            subprocess.run(['git', 'add', '.'], cwd=project_path)
            subprocess.run(
                ['git', 'commit', '-m', f'feat: {project_name} 프로젝트 초기화'],
                cwd=project_path
            )
            
            self.created_items['git_initialized'] = True
            logger.info(f"Git 저장소 초기화 완료: {project_path}")
            
        except Exception as e:
            logger.warning(f"Git 초기화 중 오류 (계속 진행): {e}")


# 싱글톤 인스턴스
_initializer = ProjectInitializer()


def create_new_project(project_name: str, base_path: Optional[Path] = None, 
                      init_git: bool = True) -> HelperResult:
    """새 프로젝트 생성 (외부 인터페이스)
    
    Args:
        project_name: 프로젝트 이름
        base_path: 프로젝트를 생성할 기본 경로
        init_git: Git 초기화 여부
        
    Returns:
        HelperResult: 생성 결과
    """
    return _initializer.create_project(project_name, base_path, init_git)
