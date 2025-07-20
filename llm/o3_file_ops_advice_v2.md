
# o3 파일 작업 헬퍼 리팩토링 조언 v2
날짜: 2025-07-19 08:37:21

## 기존 구현 분석
- FileResult 클래스: 2곳에 존재
- Generic[T] 기반 투명 래퍼 패턴
- 다른 Result 클래스들 존재

## 질문

[🎯 핵심 질문]
AI Coding Brain MCP의 파일 작업 헬퍼 리팩토링에 대한 조언이 필요합니다.

[📊 현재 상황]
1. 기존 구현 발견:
   - FileResult 클래스가 이미 2곳에 존재 (file_ops.py, helper_result.py)
   - Generic[T] 기반 투명 래퍼 패턴으로 구현됨
   - 다른 Result 클래스들: HelperResult, ParseResult, SearchResult

2. 현재 파일 작업 함수들:
   ['_read_bytes_cached', '_get_cached_bytes', 'read_file', 'write_file', 'create_file', 'append_to_file', 'file_exists', 'read_json', 'write_json', 'read_file_safe']

3. FileResult 현재 구현:
   ```python
   class FileResult(Generic[T]):
       path: Path
       content: T
       mtime: float
       size: int
       # 투명 래핑 - content처럼 동작
       def __getattr__(self, attr):
           return getattr(self.content, attr)
   ```

[🔍 요구사항]
1. 기존 FileResult와 호환되는 개선 방안
2. safe/unsafe 모드 통합 전략
3. 에러 처리 표준화 (현재 구현에는 success/error 필드 없음)
4. edit_block 기능 설계 (기존 구조 활용)

[💡 구체적 질문]
1. 현재 Generic[T] 기반 투명 래퍼 vs Result 패턴 중 어느 것이 나은가?
2. 기존 FileResult를 확장할지, 새로운 SafeFileResult를 만들지?
3. 에러 처리를 위해 Union[FileResult, ErrorResult] 패턴이 적절한가?
4. edit_block은 별도 모듈로 분리하는 것이 좋은가?

[⚡ 긴급도]
☑ 오늘 중 (리팩토링 진행 필요)


## o3의 답변
🧭 1 분 요약
‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
• FileResult 하나만 살리고 dataclass + error 필드를 넣어 Safe/Unsafe, Ok/Err 를 모두 커버  
• 다른 *Result 들은 BaseResult<T> 를 상속 → 표준화  
• “unsafe” API = Ok 값만 리턴(실패 시 raise); “safe” API = FileResult 리턴(실패 시 error 채움). unwrap(), expect() 로 두 모드 연결  
• edit_block 은 “파일 내용 변형” 계층이므로 file_ops.py 와 분리 (ex. file_edit.py)  
• Union[FileResult, ErrorResult] 대신 단일 FileResult(error=…) 가 Python-ic & 실용적  

─────────────────────────────────────────────────────────────────────────────
1. Generic[T] 투명 래퍼 vs Result 패턴
─────────────────────────────────────────────────────────────────────────────
장점 결합형이 현실적  
• 래퍼 → str/bytes 처럼 바로 쓰기 편함  
• Result → 오류·메타데이터 보존  

⇒ 투명 래퍼(FileResult) 를 그대로 두되 error 슬롯을 추가해 Result 기능까지 흡수  

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generic, TypeVar, Optional, Any

T = TypeVar("T")

@dataclass(slots=True)
class FileResult(Generic[T]):
    path:      Path
    content:   Optional[T] = None     # 실패 시 None
    mtime:     Optional[float] = None
    size:      Optional[int] = None
    error:     Optional[Exception] = None

    # -------- Result helpers --------
    @property
    def ok(self) -> bool:          # FileResult.ok => bool
        return self.error is None

    def unwrap(self) -> T:         # unsafe 모드 진입점
        if self.error:
            raise self.error
        return self.content        # type: ignore[return-value]

    def expect(self, msg: str) -> T:
        if self.error:
            raise RuntimeError(f"{msg}: {self.error}")
        return self.content        # type: ignore[return-value]

    # -------- Transparent wrapper --------
    def __getattr__(self, attr: str) -> Any:
        if self.content is None:
            raise AttributeError(attr)
        return getattr(self.content, attr)
```

• HelperResult, ParseResult, SearchResult 모두 `class …(BaseResult[T]): pass` 형태로 통일 가능.  

```python
@dataclass(slots=True)
class BaseResult(Generic[T]):
    value: Optional[T] = None
    error: Optional[Exception] = None

    def ok(self) -> bool: ...
    def unwrap(self) -> T: ...
```

FileResult 는 BaseResult 를 직접 상속하지 않아도 되지만, 일관성을 원하면
`class FileResult(BaseResult[T])` 로 바꾼 뒤 path/mtime/size 필드를 추가하면 된다.


─────────────────────────────────────────────────────────────────────────────
2. Safe / Unsafe API 통합
─────────────────────────────────────────────────────────────────────────────
패턴: “한 함수, 두 층”  

```python
def read_file(path: Path, *, encoding="utf-8", safe: bool = False) -> str | FileResult[str]:
    try:
        raw = path.read_text(encoding=encoding)
        if safe:
            stat = path.stat()
            return FileResult[str](path, raw, stat.st_mtime, stat.st_size)
        return raw                       # unsafe: 바로 문자열
    except Exception as exc:
        if safe:
            return FileResult[str](path, error=exc)
        raise
```

• 내부 로직을 한 번만 구현하고, safe=True 일 때만 FileResult 로 래핑  
• 기존 호출부 깨지지 않음 (safe=False 디폴트면 옛 API 동일)  
• 새 코드에서는 `safe=True` 를 주거나 `read_file_safe = partial(read_file, safe=True)` 헌터 함수를 노출

─────────────────────────────────────────────────────────────────────────────
3. 에러 처리 표준화
─────────────────────────────────────────────────────────────────────────────
• 단일 FileResult 안에 error 넣는 것이 Python-ic  
• Ok/Err 분할 클래스를 만들 필요가 없음 → 소비자는 `if fr.ok:` 또는 `fr.unwrap()` 사용  
• decorator 로 단순화 가능  

```python
def as_fileresult(func):
    @wraps(func)
    def _wrapper(*a, **kw):
        try:
            data = func(*a, **kw)
            return FileResult(path=kw.get("path") or a[0], content=data)
        except Exception as exc:
            return FileResult(path=kw.get("path") or a[0], error=exc)
    return _wrapper

@as_fileresult
def read_json(path: Path) -> Any: ...
```

─────────────────────────────────────────────────────────────────────────────
4. edit_block 설계
─────────────────────────────────────────────────────────────────────────────
역할이 “문자열 ↔ 문자열 변형” 이므로 I/O 와 분리하는 편이 보수·테스트 양쪽에 이롭다.

• `file_edit.py` (또는 helpers/edit_block.py)  
• 순수 함수 `edit_block(text: str, tag: str, new_content: str) -> str`  
• 파일과 결합이 필요하면 `edit_block_in_file(path: Path, …, safe=False)` 가
  내부에서 read_file / write_file 를 호출

```python
def edit_block_in_file(path: Path, tag: str, new_content: str,
                       *, safe: bool = False) -> FileResult[str] | None:
    result = read_file(path, safe=True)          # 항상 safe
    if not result.ok:
        return result if safe else result.unwrap()   # propagate

    edited = edit_block(result.content, tag, new_content)
    write_file(path, edited, safe=True)
    return FileResult[str](path, edited, result.mtime, len(edited))
```

─────────────────────────────────────────────────────────────────────────────
구체 질문 ☑ 답변
─────────────────────────────────────────────────────────────────────────────
1. 투명 래퍼 vs Result?  
   → 둘 다 필요. 현 래퍼를 dataclass + error 로 확장해 두 기능 융합.

2. FileResult 확장 vs SafeFileResult?  
   → FileResult 하나로 충분. SafeFileResult 만들면 API가 분열된다.

3. Union[FileResult, ErrorResult]?  
   → 불필요. FileResult 안에 error 필드 두어 `.ok / .unwrap()` 패턴 사용.

4. edit_block 모듈 분리?  
   → 예. I/O 레이어와 문자열 변형 레이어를 나누면 테스트·재사용성이 좋아진다.

─────────────────────────────────────────────────────────────────────────────
추가 체크리스트
─────────────────────────────────────────────────────────────────────────────
☐ file_ops.py / helper_result.py 중 하나로 FileResult 정의를 이동하고 나머지에서 import  
☐ 모든 기존 호출부에서 .content 접근 대신 직접 값 사용 여부 점검  
☐ 타입 힌트: `from __future__ import annotations` + Python ≥3.11 의 Self 타입 고려  
☐ mypy ‑-strict 로 확인 (slots + Optional 처리 주의)  
☐ 단위테스트: safe/unsafe, ok/err, unwrap(), edit_block 경계조건  

오늘 안에 리팩토링이 필요하다면  
1) FileResult 확장 → 2) read/write 계층 래핑 → 3) 안전 테스트 → 4) edit_block 분리  
순으로 진행하면 단계별 실패 확산을 최소화할 수 있습니다. 화이팅!

## 적용 계획
- [ ] 1단계: 기존 FileResult 분석
- [ ] 2단계: 개선 방안 설계
- [ ] 3단계: 점진적 마이그레이션
