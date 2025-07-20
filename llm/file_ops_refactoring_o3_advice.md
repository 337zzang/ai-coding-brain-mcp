
# 파일 작업 리팩토링 - o3 설계 자문

## 질문

[🎯 핵심 질문]
파일 작업 헬퍼 함수 리팩토링 - 실용적이고 효율적인 설계 방안

[📊 현재 상황]
- 프로젝트: ai-coding-brain-mcp의 파일 작업 헬퍼 함수들
- 환경: Python REPL 세션에서 인터랙티브하게 사용
- 현재 구조: FileResult 객체 반환 → .content 접근 필요 (번거로움)

[🔍 현재 구현의 문제점]
1. 사용성: helpers.read_json("file.json").content 처럼 매번 .content 접근 필요
2. 일관성: 일부는 FileResult, 일부는 직접 값 반환
3. 캐싱: read_json은 캐싱되는데 read_file은 안됨
4. 대용량 파일: 전체를 메모리에 로드

[💻 현재 코드 예시]
```python
# 현재 불편한 사용법
data = helpers.read_json("config.json").content  # FileResult → dict
text = helpers.read_file("readme.md").content   # FileResult → str

# 원하는 간편한 사용법
data = helpers.read_json("config.json")  # 바로 dict 반환
text = helpers.read_file("readme.md")    # 바로 str 반환
```

[📋 개선 요구사항]
1. REPL에서 즉시 사용 가능한 간편한 인터페이스
2. 메타데이터가 필요한 경우만 선택적으로 FileResult 반환
3. 스마트 캐싱 (파일 수정 시간 체크)
4. 대용량 파일 스트리밍 지원
5. 오버엔지니어링 방지 - 실용성 우선

[🎯 요청사항]
1. FileResult vs 직접 반환 중 어떤 방식이 REPL 사용에 적합한가?
2. 캐싱 전략: 모든 읽기에 적용? 선택적 적용?
3. 대용량 파일: 자동 스트리밍 전환 임계값?
4. 에러 처리: 예외 vs Result 타입 중 REPL에 적합한 방식?
5. 하위 호환성 유지하면서 개선하는 방법?

[⚡ 우선순위]
실용성 > 완벽한 설계
즉시 사용 가능 > 미래 확장성
간단함 > 기능 풍부


## o3 응답
⎈ 핵심 제안 요약
1) “평상시엔 바로 값, 필요할 때만 메타데이터”라는 기본 방침을 잡는다.  
2) read_* 계열 함수에는 3가지 공통 선택 인자만 둔다.  
   • meta=False → 바로 값 반환(디폴트)  
   • cache=True  → mtime-기반 캐싱(디폴트)  
   • stream=False→ 임계값(예: 10 MB)을 넘으면 자동으로 True  
3) 에러는 예외로 그대로 올려 REPL 디버깅을 쉽게 하고, 안전모드가 필요하면 read_*_safe 를 따로 둔다.  
4) 지금 존재하는 FileResult 는 없애지 않고 “투명 래퍼”로 바꿔 하위 호환성을 지킨다.

────────────────────────────────────────────
1. FileResult vs 직접 반환
────────────────────────────────────────────
• REPL · 스크립트에서 가장 자주 쓰는 형태는 “일단 내용만 빠르게 보고 싶다.”  
  → 기본 반환은 raw content(dict, str 등)가 가장 편하다.

• 가끔 파일 크기, mtime 등을 같이 써야 하는 경우  
  → meta=True 를 주면 FileResult 반환.  
  → 또는 read_json_meta, read_file_meta 처럼 접미사를 두어 명시적으로 호출.

• 하위 호환: 현재 코드가 FileResult 를 기대하고 있으므로
  – FileResult 를 투명 컨테이너로 리팩터링한다.
    ( __getattr__, __iter__, __getitem__ 등을 content 로 위임 )
  – 따라서 예전 코드 data = helpers.read_json("x").content 도 동작,
    새 코드 data = helpers.read_json("x") 도 동작.

예시:
```python
result = helpers.read_json("cfg.json", meta=True)
print(result.size, result.mtime)   # 메타데이터
print(result["key"])               # dict처럼 바로 사용
```

────────────────────────────────────────────
2. 캐싱 전략
────────────────────────────────────────────
목표: “빠르고 똑똑하지만 복잡하진 않게”.

• 모든 읽기 함수에 동일한 캐시 로직을 적용한다.  
• 키: (absolute_path, os.path.getmtime(path))  
• 저장소: functools.lru_cache(maxsize=N) 또는 전역 dict.  
• cache 인자(False 면 강제 리로드)만 두고 TTL 따위는 넣지 않는다.

장점
– 구현 15줄 내외.  
– 파일 바뀌면 mtime 이 변해 즉시 캐시 무효화.  
– 함수별로 일관적.

────────────────────────────────────────────
3. 대용량 파일 스트리밍
────────────────────────────────────────────
• 기본값 stream=False.  
• 파일 크기가 streaming_threshold (예: 10 MB) 이상이면 자동 전환.  
  – 내부적으로 if not stream and size > threshold: stream = True  
• stream=True 시 반환값
  – read_file → file-like object(generator/iterator).  
  – read_json 은 크기가 커도 보통 파싱해야 하므로 강제 스트리밍 X; 대신
    read_json_lines 같은 별도 함수 제공(1줄 1JSON).  

임계값은 settings.py 또는 환경변수로 조정 가능하도록 해두면 충분.

────────────────────────────────────────────
4. 에러 처리
────────────────────────────────────────────
• 기본: 파이썬 예외 그대로 raise.  
  – REPL 에선 traceback 이 곧바로 보이는 것이 가장 친절.  
• 안전모드가 필요하면 함수 뒤에 _safe 를 붙여 None 또는 Result 를 반환.  
  – read_json_safe(path, default=None) 처럼.  
  – core 코드는 예외, UI·서비스 레이어에선 safe 버전을 사용.

────────────────────────────────────────────
5. 하위 호환성 유지 로드맵
────────────────────────────────────────────
step 0) FileResult 를 아래처럼 수정하여 ‘내용 → dict/str 처럼 동작’하도록 만든다.

```python
@dataclass
class FileResult(Generic[T]):
    path: Path
    content: T
    mtime: float
    size: int

    # 투명 래핑
    def __getattr__(self, item):
        return getattr(self.content, item)
    def __iter__(self): return iter(self.content)
    def __getitem__(self, k): return self.content[k]
    def __repr__(self): return f"<FileResult {self.path} ({self.size}B)>"
```

step 1) 기존 helpers.read_* 내부에서
```
def read_json(path, *, meta=False, cache=True, **kw):
    if not meta:
        return _read_json_impl(path, cache=cache, **kw)
    return _read_json_impl(path, cache=cache, **kw, return_result=True)
```

step 2) 문서·도움말에 “이제 .content 없이 바로 쓰세요; meta=True 때만 FileResult” 라고 안내.

step 3) 1~2 릴리스 뒤 DeprecationWarning: “.content 는 앞으로 없어질 예정” (원하면 유지).

────────────────────────────────────────────
실제 코드 스케치
────────────────────────────────────────────
```python
import json, os
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")
STREAM_THRESHOLD = 10 * 1024 * 1024  # 10 MB

@dataclass
class FileResult(Generic[T]):
    path: Path
    content: T
    mtime: float
    size: int
    def __getattr__(self, attr):  # transparent
        return getattr(self.content, attr)
    def __iter__(self): return iter(self.content)
    def __getitem__(self, k): return self.content[k]

# internal cache
@lru_cache(maxsize=128)
def _read_bytes_cached(path: str, mtime: float) -> bytes:
    with open(path, "rb") as fp:
        return fp.read()

def _get_cached_bytes(path: Path, cache: bool) -> bytes:
    mtime = path.stat().st_mtime
    if cache:
        return _read_bytes_cached(str(path), mtime)
    # bypass cache
    with open(path, "rb") as fp:
        return fp.read()

# public helpers
def read_file(path, *, meta=False, cache=True, stream=False, encoding="utf-8"):
    path = Path(path)
    if not stream and path.stat().st_size > STREAM_THRESHOLD:
        stream = True
    if stream:
        fp = open(path, "r", encoding=encoding)
        return fp if not meta else FileResult(path, fp, path.stat().st_mtime, path.stat().st_size)
    data = _get_cached_bytes(path, cache).decode(encoding)
    if meta:
        return FileResult(path, data, path.stat().st_mtime, len(data))
    return data

def read_json(path, *, meta=False, cache=True, encoding="utf-8", **json_kw):
    path = Path(path)
    raw = _get_cached_bytes(path, cache).decode(encoding)
    obj = json.loads(raw, **json_kw)
    if meta:
        st = path.stat()
        return FileResult(path, obj, st.st_mtime, st.st_size)
    return obj
```

────────────────────────────────────────────
정리
────────────────────────────────────────────
• 사용자 관점: `helpers.read_json("cfg.json")` 한 줄이면 끝.  
• 필요 시 `meta=True`로 모든 메타데이터 확보.  
• 모든 read_*가 캐싱·스트리밍·에러 처리 규칙을 공유하므로 학습 부담 0.  
• 기존 FileResult 를 투명 래퍼로 바꿔 코드가 바로 깨질 일 없음.  
➜ “실용성 > 완벽” 요구조건을 가장 단순한 형태로 충족한다.

생성일시: 2025-07-19 07:32:21
