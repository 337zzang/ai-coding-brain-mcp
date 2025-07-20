
# 파일 작업 헬퍼 리팩토링 및 edit_block 설계안

## 1. FileResult 클래스 설계

```python
from dataclasses import dataclass
from typing import Any, Optional, List
from enum import Enum

class FileOperation(Enum):
    READ = "read"
    WRITE = "write"
    APPEND = "append"
    CREATE = "create"
    DELETE = "delete"
    EDIT = "edit"

@dataclass
class FileResult:
    """파일 작업 결과를 담는 표준 클래스"""
    success: bool
    operation: FileOperation
    path: str
    content: Optional[Any] = None
    error: Optional[str] = None
    encoding: str = "utf-8"
    size: Optional[int] = None
    lines: Optional[int] = None
    backup_path: Optional[str] = None

    @property
    def failed(self) -> bool:
        return not self.success

    def __bool__(self) -> bool:
        """if result: 형태로 성공 여부 확인 가능"""
        return self.success
```

## 2. 통합된 파일 작업 헬퍼

### 2.1 읽기 작업 통합

```python
def read_file(
    path: str,
    encoding: str = 'utf-8',
    safe: bool = True,
    offset: int = 0,
    length: Optional[int] = None
) -> Union[str, FileResult]:
    """
    파일 읽기 통합 함수

    Args:
        path: 파일 경로
        encoding: 인코딩 (기본: utf-8)
        safe: True면 FileResult 반환, False면 내용 직접 반환
        offset: 시작 라인 (0부터 시작)
        length: 읽을 라인 수 (None이면 전체)

    Returns:
        safe=True: FileResult 객체
        safe=False: 파일 내용 문자열
    """
    try:
        with open(path, 'r', encoding=encoding) as f:
            if offset or length:
                lines = f.readlines()
                start = offset
                end = offset + length if length else None
                content = ''.join(lines[start:end])
            else:
                content = f.read()

        if safe:
            return FileResult(
                success=True,
                operation=FileOperation.READ,
                path=path,
                content=content,
                encoding=encoding,
                size=os.path.getsize(path),
                lines=content.count('\n') + 1
            )
        else:
            return content

    except Exception as e:
        if safe:
            return FileResult(
                success=False,
                operation=FileOperation.READ,
                path=path,
                error=str(e)
            )
        else:
            raise
```

### 2.2 쓰기 작업 통합

```python
def write_file(
    path: str,
    content: str,
    mode: Literal['w', 'a', 'x'] = 'w',
    encoding: str = 'utf-8',
    safe: bool = True,
    backup: bool = False
) -> Union[bool, FileResult]:
    """
    파일 쓰기 통합 함수

    Args:
        path: 파일 경로
        content: 쓸 내용
        mode: 'w'(덮어쓰기), 'a'(추가), 'x'(새 파일만)
        encoding: 인코딩
        safe: True면 FileResult 반환
        backup: True면 백업 생성
    """
    backup_path = None

    try:
        # 백업 생성
        if backup and os.path.exists(path):
            backup_path = f"{path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(path, backup_path)

        # 파일 쓰기
        with open(path, mode, encoding=encoding) as f:
            f.write(content)

        if safe:
            return FileResult(
                success=True,
                operation=FileOperation.WRITE if mode == 'w' else FileOperation.APPEND,
                path=path,
                content=content,
                encoding=encoding,
                size=len(content.encode(encoding)),
                lines=content.count('\n') + 1,
                backup_path=backup_path
            )
        else:
            return True

    except Exception as e:
        if safe:
            return FileResult(
                success=False,
                operation=FileOperation.WRITE,
                path=path,
                error=str(e),
                backup_path=backup_path
            )
        else:
            raise
```

## 3. edit_block 기능 설계

```python
@dataclass
class EditOperation:
    """단일 편집 작업"""
    type: Literal['replace', 'insert', 'delete']
    target: Union[int, str, tuple]  # 라인 번호, 패턴, (start, end)
    content: Optional[str] = None
    position: Literal['before', 'after', 'replace'] = 'replace'

@dataclass
class EditResult(FileResult):
    """편집 결과"""
    changes: List[dict] = None
    preview: Optional[str] = None

def edit_block(
    path: str,
    operations: Union[EditOperation, List[EditOperation]],
    safe: bool = True,
    backup: bool = True,
    preview: bool = False,
    encoding: str = 'utf-8'
) -> EditResult:
    """
    파일의 특정 부분을 정밀하게 수정

    Args:
        path: 파일 경로
        operations: 편집 작업(들)
        safe: 안전 모드
        backup: 백업 생성 여부
        preview: 미리보기만 할지 여부
        encoding: 파일 인코딩

    Examples:
        # 라인 번호로 수정
        edit_block('file.py', EditOperation('replace', 10, 'new line'))

        # 패턴으로 수정
        edit_block('file.py', EditOperation('replace', 'old_func', 'new_func'))

        # 범위로 삭제
        edit_block('file.py', EditOperation('delete', (10, 15)))

        # 다중 수정
        edit_block('file.py', [
            EditOperation('replace', 10, 'line 10'),
            EditOperation('insert', 20, 'new line', 'before'),
            EditOperation('delete', (30, 35))
        ])
    """
    if not isinstance(operations, list):
        operations = [operations]

    try:
        # 파일 읽기
        with open(path, 'r', encoding=encoding) as f:
            lines = f.readlines()

        original_content = ''.join(lines)
        changes = []

        # 작업을 라인 번호 기준으로 정렬 (역순으로 처리)
        sorted_ops = sorted(operations, 
                          key=lambda op: _get_line_number(op, lines), 
                          reverse=True)

        # 각 작업 수행
        for op in sorted_ops:
            change = _apply_operation(lines, op)
            changes.append(change)

        new_content = ''.join(lines)

        # 미리보기 모드
        if preview:
            return EditResult(
                success=True,
                operation=FileOperation.EDIT,
                path=path,
                preview=_generate_diff(original_content, new_content),
                changes=changes
            )

        # 백업 생성
        backup_path = None
        if backup:
            backup_path = f"{path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            with open(backup_path, 'w', encoding=encoding) as f:
                f.write(original_content)

        # 실제 쓰기
        with open(path, 'w', encoding=encoding) as f:
            f.write(new_content)

        return EditResult(
            success=True,
            operation=FileOperation.EDIT,
            path=path,
            content=new_content,
            changes=changes,
            backup_path=backup_path,
            encoding=encoding,
            size=len(new_content.encode(encoding)),
            lines=len(lines)
        )

    except Exception as e:
        return EditResult(
            success=False,
            operation=FileOperation.EDIT,
            path=path,
            error=str(e)
        )
```

## 4. 하위 호환성 유지

```python
# 기존 함수들을 래퍼로 유지
def read_file_safe(path: str) -> FileResult:
    """Deprecated: use read_file(path, safe=True) instead"""
    warnings.warn("read_file_safe is deprecated, use read_file(path, safe=True)", 
                  DeprecationWarning)
    return read_file(path, safe=True)

def create_file(path: str, content: str = '') -> FileResult:
    """Deprecated: use write_file(path, content, mode='x') instead"""
    warnings.warn("create_file is deprecated, use write_file(path, content, mode='x')", 
                  DeprecationWarning)
    return write_file(path, content, mode='x', safe=True)

def append_to_file(path: str, content: str) -> FileResult:
    """Deprecated: use write_file(path, content, mode='a') instead"""
    warnings.warn("append_to_file is deprecated, use write_file(path, content, mode='a')", 
                  DeprecationWarning)
    return write_file(path, content, mode='a', safe=True)
```

## 5. 구현 우선순위

1. **Phase 1** (즉시): FileResult 클래스 구현
2. **Phase 2** (1시간): read_file, write_file 통합
3. **Phase 3** (2시간): edit_block 구현
4. **Phase 4** (30분): 하위 호환성 래퍼
5. **Phase 5** (1시간): 테스트 및 문서화

## 6. 주요 개선사항

- **통합된 인터페이스**: safe 파라미터로 반환 타입 제어
- **일관된 에러 처리**: FileResult로 표준화
- **백업 자동화**: backup 옵션 제공
- **정밀한 편집**: edit_block으로 라인/패턴 기반 수정
- **미리보기 기능**: preview 옵션으로 변경사항 확인
- **하위 호환성**: Deprecation 경고와 함께 기존 함수 유지
