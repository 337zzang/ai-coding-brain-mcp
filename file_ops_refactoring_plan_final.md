
# 파일 작업 헬퍼 리팩토링 실행 계획

## 🎯 o3 조언 핵심 요약

1. **FileResult 통합**
   - 기존 FileResult에 error 필드 추가
   - safe/unsafe 모드를 하나의 클래스로 통합
   - 투명 래퍼 기능은 유지

2. **Result 패턴 표준화**
   - BaseResult 추상 클래스 생성
   - 모든 Result 클래스가 상속
   - 공통 인터페이스: success, error, unwrap(), expect()

3. **API 설계**
   - unsafe: 실패시 예외 발생, 성공시 값 직접 반환
   - safe: 항상 FileResult 반환 (성공/실패 모두)
   - 변환 메서드: unwrap(), expect()로 연결

4. **모듈 구조**
   - file_ops.py: 기본 파일 작업
   - file_edit.py: edit_block 등 고급 편집 기능
   - helper_result.py: Result 클래스들

## 📁 리팩토링 단계별 계획

### Phase 1: BaseResult 및 FileResult 개선 (1시간)

1. **BaseResult 추상 클래스 생성**
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar, Optional

T = TypeVar("T")

@dataclass
class BaseResult(ABC, Generic[T]):
    content: Optional[T] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and self.content is not None

    @property
    def failed(self) -> bool:
        return not self.success

    def unwrap(self) -> T:
        """성공시 값 반환, 실패시 예외 발생"""
        if self.success:
            return self.content
        raise ValueError(f"Result error: {self.error}")

    def expect(self, msg: str) -> T:
        """사용자 정의 에러 메시지로 unwrap"""
        if self.success:
            return self.content
        raise ValueError(f"{msg}: {self.error}")

    def unwrap_or(self, default: T) -> T:
        """실패시 기본값 반환"""
        return self.content if self.success else default
```

2. **FileResult 개선**
```python
@dataclass(slots=True)
class FileResult(BaseResult[T]):
    path: Path
    mtime: Optional[float] = None
    size: Optional[int] = None
    lines: Optional[List[str]] = None
    encoding: str = "utf-8"

    # 투명 래퍼 기능 유지
    def __getattr__(self, attr):
        if self.success and self.content is not None:
            return getattr(self.content, attr)
        raise AttributeError(f"FileResult has no attribute '{attr}'")
```

### Phase 2: 파일 작업 함수 통합 (2시간)

1. **읽기 함수 통합**
```python
def read_file(path: Path | str, 
              encoding: str = 'utf-8',
              safe: bool = True) -> Union[str, FileResult[str]]:
    """
    safe=True: FileResult 반환 (에러 포함)
    safe=False: 내용 직접 반환 (에러시 예외)
    """
    path = Path(path)
    try:
        content = path.read_text(encoding=encoding)
        stat = path.stat()

        result = FileResult(
            path=path,
            content=content,
            mtime=stat.st_mtime,
            size=stat.st_size,
            encoding=encoding
        )

        return result if safe else content

    except Exception as e:
        if safe:
            return FileResult(path=path, error=str(e))
        raise
```

2. **쓰기 함수 통합**
```python
def write_file(path: Path | str,
               content: str,
               mode: Literal['w', 'a', 'x'] = 'w',
               encoding: str = 'utf-8',
               safe: bool = True,
               backup: bool = False) -> Union[bool, FileResult[str]]:
    # 구현...
```

### Phase 3: edit_block 구현 (file_edit.py) (2시간)

```python
from dataclasses import dataclass
from typing import List, Union, Literal
from pathlib import Path

@dataclass
class EditOperation:
    type: Literal['replace', 'insert', 'delete']
    target: Union[int, str, tuple]  # 라인번호, 패턴, 범위
    content: Optional[str] = None

@dataclass
class EditResult(BaseResult[str]):
    path: Path
    operations: List[EditOperation]
    changes: List[dict] = field(default_factory=list)
    backup_path: Optional[Path] = None

def edit_block(path: Path | str,
               operations: Union[EditOperation, List[EditOperation]],
               safe: bool = True,
               backup: bool = True,
               preview: bool = False) -> Union[str, EditResult]:
    # 구현...
```

### Phase 4: 하위 호환성 및 마이그레이션 (1시간)

1. **Deprecation warnings 추가**
2. **기존 함수 래퍼 생성**
3. **마이그레이션 가이드 작성**

## 📊 예상 영향 및 이점

- **코드 중복 감소**: 12개 → 4개 핵심 함수
- **일관된 에러 처리**: BaseResult 패턴
- **타입 안전성**: Generic + Union 타입
- **점진적 마이그레이션**: 하위 호환성 유지

## ⚠️ 주의사항

1. 기존 코드와의 호환성 유지
2. 단계별 테스트 필수
3. 성능 벤치마크 (캐싱 기능 유지)
