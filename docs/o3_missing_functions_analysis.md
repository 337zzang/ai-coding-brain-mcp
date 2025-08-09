# 누락된 함수 구현 방안

## O3 분석 결과

아래 내용은 “search.py”에 누락된 4 개의 함수를 어떻게 작성‧통합할 것인지에 대한 실전 가이드입니다.  
(예시는 Python-3.9 이상, 기존 util.ok / util.err, wrappers.wrap_output 의 존재를 전제로 작성했습니다)

────────────────────────────────────────
1. search_imports(module_name)
────────────────────────────────────────
목표  
• 주어진 모듈명이 import 되는 모든 위치(파일·라인번호·원문)를 AST 로 찾아낸다.  
• 결과는 [{file, lineno, code}, …] 형태로 util.ok 로 감싸서 반환  
• 동일 파라미터 호출이 자주 발생하므로 LRU 캐싱

핵심 알고리즘  
1) search_files("*.py")를 이용해 전체 Python 파일 목록 확보  
2) 각각의 파일을 ast.parse → ast.walk  
   ▸ ast.Import     : alias.name 가 module_name 또는 module_name 로 시작  
   ▸ ast.ImportFrom : node.module 이 module_name 또는 module_name 로 시작  
3) 매칭되면 (파일, line, 원본코드) 저장  
4) SyntaxError 등은 try/except 로 무시하고 계속 진행  
5) @lru_cache(maxsize=64) 로 래핑 → _CACHED_FUNCS 에 등록

예시 코드 (핵심부)  
```python
from functools import lru_cache
import ast, inspect

_CACHED_FUNCS: List[Any] = []          # cache 관리용 전역 리스트

def _register_cache(fn):
    """lru_cache 달린 함수를 레지스트리에 추가"""
    _CACHED_FUNCS.append(fn)
    return fn


@_register_cache
@lru_cache(maxsize=64)
@wrap_output                      # <- 기존 데코레이터 재사용 가능
def search_imports(module_name: str,
                   path: str = ".",
                   recursive: bool = True,
                   max_depth: Optional[int] = None):
    if not module_name:
        return err("module_name must be non-empty")

    result = []
    res_files = search_files("*.py", path, recursive, max_depth)
    if not res_files.get("ok"):
        return res_files                 # 에러 전파

    for file_path in res_files["data"]:
        try:
            source = Path(file_path).read_text(encoding="utf-8")
            tree   = ast.parse(source, filename=file_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for ali in node.names:
                        if ali.name == module_name or ali.name.startswith(f"{module_name}."):
                            result.append({"file": file_path,
                                           "lineno": node.lineno,
                                           "code": source.splitlines()[node.lineno-1].strip()})
                elif isinstance(node, ast.ImportFrom):
                    if node.module and (node.module == module_name or node.module.startswith(f"{module_name}.")):
                        result.append({"file": file_path,
                                       "lineno": node.lineno,
                                       "code": source.splitlines()[node.lineno-1].strip()})
        except (SyntaxError, UnicodeDecodeError):
            continue

    return ok(result, count=len(result))
```

────────────────────────────────────────
2. get_statistics()
────────────────────────────────────────
목표  
프로젝트 규모를 한눈에 볼 수 있는 종합 통계

수집 항목(필요에 따라 가감 가능)  
• total_files          전체 파일 개수  
• python_files         *.py 개수  
• total_lines          모든 Python 라인 수  
• code_lines           빈 줄/주석 제외 라인  
• function_count       def 개수  
• class_count          class 개수  
• todo_count           “TODO” 문자열 포함 라인 수  

알고리즘  
1) search_files("*", path, recursive=True) 로 전체 파일 수 등에 사용  
2) *.py 만 골라서  
   ─ pathlib.Path.read_text -> splitlines 로 라인 계산  
   ─ ast.parse + ast.walk 로 함수/클래스 수 계산  
3) 결과 dict → util.ok  
4) 비싼 연산이므로 @lru_cache(maxsize=1) 적용  

예시 코드  
```python
@_register_cache
@lru_cache(maxsize=1)
@wrap_output
def get_statistics(path: str = "."):
    try:
        all_files   = search_files("*", path)["data"]
        py_files    = [f for f in all_files if f.endswith(".py")]
    except Exception as e:
        return err(f"stat-scan failed: {e}")

    stats = {"total_files": len(all_files),
             "python_files": len(py_files),
             "total_lines": 0,
             "code_lines": 0,
             "function_count": 0,
             "class_count": 0,
             "todo_count": 0}

    for fp in py_files:
        try:
            src  = Path(fp).read_text(encoding="utf-8")
            lines = src.splitlines()
            stats["total_lines"] += len(lines)
            stats["code_lines"]  += sum(1 for l in lines if l.strip() and not l.lstrip().startswith("#"))
            stats["todo_count"]  += sum(1 for l in lines if "TODO" in l)

            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    stats["function_count"] += 1
                elif isinstance(node, ast.ClassDef):
                    stats["class_count"] += 1
        except Exception:
            continue

    return ok(stats)
```

────────────────────────────────────────
3. get_cache_info()
────────────────────────────────────────
목표 : lru_cache 적용 함수들의 적중/미스 현황을 확인

구현  
```python
@wrap_output
def get_cache_info():
    info = {}
    for fn in _CACHED_FUNCS:
        if hasattr(fn, "cache_info"):
            ci = fn.cache_info()        # namedtuple(hits, misses, maxsize, currsize)
            info[fn.__name__] = {"hits": ci.hits,
                                 "misses": ci.misses,
                                 "maxsize": ci.maxsize,
                                 "currsize": ci.currsize}
    return ok(info)
```

────────────────────────────────────────
4. clear_cache()
────────────────────────────────────────
목표 : 모든 @lru_cache 결과를 지운다.

구현  
```python
@wrap_output
def clear_cache():
    for fn in _CACHED_FUNCS:
        if hasattr(fn, "cache_clear"):
            fn.cache_clear()
    return ok("cache cleared")
```

────────────────────────────────────────
5. 기존 코드와의 통합 방법
────────────────────────────────────────
1) 파일 상단 import 추가  
   ```
   import ast
   from functools import lru_cache
   ```

2) 전역 리스트 _CACHED_FUNCS, 헬퍼 _register_cache 정의 → search_imports / get_statistics 선언부 위에 배치  

3) 네 함수 모두 @wrap_output(or util.ok/err 직접 사용)으로 표준 응답 포맷을 유지  

4) 다른 함수와 시그니처/옵션 통일  
   • path / recursive / max_depth 파라미터 패턴 유지  
   • 오류 시 util.err 로 통일  

5) __all__ 에 함수명 추가 (모듈 export 시 사용하는 경우)

────────────────────────────────────────
6. 효율적인 구현 패턴 제안
────────────────────────────────────────
• AST 를 한 번만 파싱 : search_imports / get_statistics 가 동시에 필요하면 내부에서 tree 를 재활용하도록 공동 헬퍼 (_parse_python_file) 작성 가능  
• 파일 수가 방대할 때는 concurrent.futures.ThreadPoolExecutor 로 병렬 파싱 (GIL-friendly I/O 작업)  
• get_statistics 는 파일 목록과 mtime 으로 해시를 만들어 변경 파일이 없으면 바로 cache hit → 불필요한 재계산 방지  
• search_imports 결과를 필요에 따라 generator 로 흘려보내고, wrap_output 데코레이터에서 list(...) 로 materialize 하여 메모리 절약  
• 테스트 코드 분리를 원한다면 search_files 호출 시 exclude 패턴 인자를 추가로 받을 수 있음  

이렇게 구현하면  
1) 누락 함수가 완전히 채워지고  
2) 기존 검색 계열 함수들과 인터페이스를 맞추며  
3) 캐시 정보 확인/초기화까지 한 번에 해결할 수 있습니다.

## 메타 정보
- Reasoning Effort: high
- Usage: {'prompt_tokens': 526, 'completion_tokens': 3496, 'total_tokens': 4022, 'reasoning_tokens': 0}
