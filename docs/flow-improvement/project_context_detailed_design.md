# ProjectContext 클래스 상세 설계

## 1. 개요
ProjectContext는 프로젝트의 루트 디렉토리와 관련 경로들을 관리하는 핵심 클래스입니다.

## 2. 클래스 구조

```python
# python/ai_helpers_new/infrastructure/project_context.py

from pathlib import Path
from typing import Optional, Dict, Any
import json
import os

class ProjectContext:
    """프로젝트 컨텍스트 관리 클래스

    프로젝트의 루트 디렉토리를 기준으로 모든 관련 경로를 관리합니다.
    """

    def __init__(self, root: Path):
        """ProjectContext 초기화

        Args:
            root: 프로젝트 루트 디렉토리
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

    def _validate_project_root(self):
        """프로젝트 루트 유효성 검증"""
        if not self._root.exists():
            raise ValueError(f"Project root does not exist: {self._root}")

        if not self._root.is_dir():
            raise ValueError(f"Project root is not a directory: {self._root}")

    def ensure_directories(self):
        """필요한 디렉토리 생성"""
        self.ai_brain_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def get_relative_path(self, absolute_path: Path) -> Path:
        """절대 경로를 프로젝트 상대 경로로 변환"""
        try:
            return Path(absolute_path).relative_to(self._root)
        except ValueError:
            return Path(absolute_path)

    def get_absolute_path(self, relative_path: str) -> Path:
        """상대 경로를 절대 경로로 변환"""
        return self._root / relative_path

    def is_within_project(self, path: Path) -> bool:
        """경로가 프로젝트 내부에 있는지 확인"""
        try:
            Path(path).resolve().relative_to(self._root)
            return True
        except ValueError:
            return False

    def get_project_info(self) -> Dict[str, Any]:
        """프로젝트 정보 반환"""
        return {
            'root': str(self._root),
            'name': self._root.name,
            'ai_brain_exists': self.ai_brain_dir.exists(),
            'flows_exists': self.flow_file.exists(),
            'has_git': (self._root / '.git').exists()
        }

    def switch_to(self):
        """현재 작업 디렉토리를 프로젝트 루트로 변경"""
        os.chdir(self._root)

    def __str__(self) -> str:
        return f"ProjectContext({self._root})"

    def __repr__(self) -> str:
        return f"ProjectContext(root='{self._root}')"
```

## 3. 사용 예시

```python
# 프로젝트 컨텍스트 생성
context = ProjectContext("/path/to/project")

# 경로 접근
flows_path = context.flow_file
print(f"Flows file: {flows_path}")

# 프로젝트 정보
info = context.get_project_info()
print(f"Project: {info['name']}")

# 작업 디렉토리 변경
context.switch_to()
```

## 4. 테스트 계획

```python
# test/test_project_context.py

import pytest
from pathlib import Path
import tempfile
import os
from ai_helpers_new.infrastructure.project_context import ProjectContext

class TestProjectContext:

    def test_init_valid_project(self, tmp_path):
        """유효한 프로젝트 디렉토리로 초기화"""
        context = ProjectContext(tmp_path)
        assert context.root == tmp_path.resolve()
        assert context.ai_brain_dir.exists()

    def test_init_invalid_project(self):
        """존재하지 않는 디렉토리로 초기화 시 에러"""
        with pytest.raises(ValueError):
            ProjectContext("/non/existent/path")

    def test_path_properties(self, tmp_path):
        """경로 속성 테스트"""
        context = ProjectContext(tmp_path)

        assert context.flow_file == tmp_path / ".ai-brain" / "flows.json"
        assert context.current_flow_file == tmp_path / ".ai-brain" / "current_flow.txt"
        assert context.backup_dir == tmp_path / "backups"

    def test_ensure_directories(self, tmp_path):
        """디렉토리 생성 테스트"""
        context = ProjectContext(tmp_path)

        assert context.ai_brain_dir.exists()
        assert context.backup_dir.exists()
        assert context.docs_dir.exists()

    def test_relative_absolute_paths(self, tmp_path):
        """상대/절대 경로 변환 테스트"""
        context = ProjectContext(tmp_path)

        # 절대 -> 상대
        abs_path = tmp_path / "subdir" / "file.txt"
        rel_path = context.get_relative_path(abs_path)
        assert rel_path == Path("subdir/file.txt")

        # 상대 -> 절대
        abs_path2 = context.get_absolute_path("subdir/file.txt")
        assert abs_path2 == abs_path

    def test_is_within_project(self, tmp_path):
        """프로젝트 내부 경로 확인 테스트"""
        context = ProjectContext(tmp_path)

        # 내부 경로
        assert context.is_within_project(tmp_path / "subdir")

        # 외부 경로
        assert not context.is_within_project(tmp_path.parent)

    def test_switch_to(self, tmp_path):
        """작업 디렉토리 변경 테스트"""
        original_cwd = os.getcwd()

        context = ProjectContext(tmp_path)
        context.switch_to()

        assert Path.cwd() == tmp_path.resolve()

        # 원래 디렉토리로 복원
        os.chdir(original_cwd)
```

## 5. 마이그레이션 전략

### 5.1 기존 코드와의 호환성
```python
# 기존 코드
storage_path = os.path.join(os.getcwd(), ".ai-brain", "flows.json")

# 새 코드 (호환성 유지)
context = ProjectContext(os.getcwd())
storage_path = str(context.flow_file)
```

### 5.2 점진적 마이그레이션
1. ProjectContext 클래스 추가 (영향 없음)
2. Repository에서 선택적 사용
3. Service 레이어 업데이트
4. FlowManager 통합
5. 레거시 코드 제거

## 6. 성능 고려사항

- Path 객체는 불변이므로 캐싱 불필요
- 디렉토리 생성은 초기화 시 한 번만
- 경로 연산은 매우 빠름 (마이크로초 단위)

## 7. 보안 고려사항

- 경로 검증으로 디렉토리 탐색 공격 방지
- 프로젝트 경계 확인으로 권한 제어
- 심볼릭 링크는 resolve()로 실제 경로 확인
