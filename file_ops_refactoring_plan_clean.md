
# 파일 작업 헬퍼 리팩토링 실행 계획 (Revised)

## 🎯 변경된 방향
- **하위 호환성 제거** - 기존 함수 모두 삭제
- **깔끔한 새 구현** - 중복 없이 최소한의 인터페이스
- **완전 교체** - 테스트 완료 후 기존 코드 제거

## 📁 리팩토링 단계별 계획

### Phase 1: 새로운 Result 시스템 구현 (1시간)

1. **helper_result.py 완전 재작성**
```python
# 기존 내용 모두 삭제 후 새로 작성
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generic, TypeVar, Optional, Union, List

T = TypeVar("T")

@dataclass
class BaseResult(ABC, Generic[T]):
    """모든 Result 클래스의 기본"""
    content: Optional[T] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and self.content is not None

    def unwrap(self) -> T:
        if self.success:
            return self.content
        raise ValueError(f"Result error: {self.error}")

    def unwrap_or(self, default: T) -> T:
        return self.content if self.success else default

@dataclass
class FileResult(BaseResult[T]):
    """파일 작업 결과"""
    path: Path
    size: Optional[int] = None
    mtime: Optional[float] = None
    encoding: str = "utf-8"

    # 투명 래퍼 - content처럼 동작
    def __getattr__(self, name):
        if self.success and hasattr(self.content, name):
            return getattr(self.content, name)
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

@dataclass
class SearchResult(BaseResult[List[dict]]):
    """검색 결과"""
    pattern: str
    path: Path
    count: int = 0

@dataclass
class ParseResult(BaseResult[dict]):
    """파싱 결과"""
    path: Path
    language: str = "python"
```

### Phase 2: 새로운 파일 작업 함수 (2시간)

2. **file_ops.py 완전 재작성**
```python
# 기존 함수 모두 제거, 다음 4개만 구현
from pathlib import Path
from typing import Union, Optional
import json

def read_file(
    path: Union[Path, str],
    encoding: str = 'utf-8',
    safe: bool = True
) -> Union[str, FileResult[str]]:
    """파일 읽기 - safe 모드에 따라 반환 타입 결정"""

def write_file(
    path: Union[Path, str],
    content: str,
    mode: str = 'w',  # 'w', 'a', 'x'
    encoding: str = 'utf-8',
    safe: bool = True,
    backup: bool = False
) -> Union[bool, FileResult[str]]:
    """파일 쓰기 - create/append 통합"""

def read_json(
    path: Union[Path, str],
    safe: bool = True
) -> Union[dict, FileResult[dict]]:
    """JSON 읽기"""

def write_json(
    path: Union[Path, str],
    data: dict,
    indent: int = 2,
    safe: bool = True,
    backup: bool = False
) -> Union[bool, FileResult[dict]]:
    """JSON 쓰기"""
```

### Phase 3: edit_block 구현 (2시간)

3. **file_edit.py 새로 생성**
```python
from dataclasses import dataclass
from typing import Union, List, Literal, Optional, Tuple
from pathlib import Path

@dataclass
class EditOperation:
    """편집 작업 정의"""
    type: Literal['replace', 'insert', 'delete']
    target: Union[int, str, Tuple[int, int]]  # 라인, 패턴, 범위
    content: Optional[str] = None
    position: Literal['before', 'after', 'at'] = 'at'

@dataclass
class EditResult(BaseResult[str]):
    """편집 결과"""
    path: Path
    operations: List[EditOperation]
    changes: List[dict] = field(default_factory=list)
    backup_path: Optional[Path] = None
    preview: Optional[str] = None

def edit_block(
    path: Union[Path, str],
    operations: Union[EditOperation, List[EditOperation]],
    safe: bool = True,
    backup: bool = True,
    preview: bool = False,
    encoding: str = 'utf-8'
) -> Union[str, EditResult]:
    """파일 편집 - 정밀한 부분 수정"""
```

### Phase 4: 테스트 및 교체 (2시간)

4. **완전 교체 프로세스**

   a. 테스트 파일 작성 (test_new_file_ops.py)
   b. 모든 기능 테스트
   c. 성능 벤치마크

   d. **기존 코드 제거** (테스트 통과 후)
      - 삭제할 함수들:
        * read_file_safe()
        * read_json_safe()
        * create_file()
        * append_to_file()
        * 기타 중복 함수들

   e. import 경로 업데이트
   f. 최종 검증

## 📊 최종 결과

### Before (기존)
- 파일 함수: 12개+ (중복 많음)
- 일관성 없는 인터페이스
- safe/unsafe 버전 분리

### After (새로운)
- 파일 함수: 4개 (통합)
- 일관된 safe 파라미터
- edit_block 추가
- 깔끔한 코드베이스

## ⚠️ 주의사항
- 기존 함수 사용처 모두 확인
- 테스트 100% 통과 후 삭제
- 백업은 Git으로 관리
