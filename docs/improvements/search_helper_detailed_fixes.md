# 🔧 Search 헬퍼 함수 즉시 수정 가능한 코드

## 1. find_in_file 수정 (search.py line 481)

### 현재 코드 (버그):
```python
def find_in_file(file_path: str, pattern: str) -> Dict[str, Any]:
    if not Path(file_path).exists():
        return err(f"File not found: {file_path}")

    # 버그: h가 정의되지 않음
    result = h.search_code(pattern, os.path.dirname(file_path) or '.', 
                        os.path.basename(file_path))
```

### 수정된 코드:
```python
def find_in_file(file_path: str, pattern: str) -> Dict[str, Any]:
    if not Path(file_path).exists():
        return err(f"File not found: {file_path}")

    # 수정: 직접 search_code 호출
    result = search_code(pattern, os.path.dirname(file_path) or '.', 
                        os.path.basename(file_path))

    if result['ok']:
        for match in result['data']:
            del match['file']

    return result
```

## 2. _find_function_ast 수정 (search.py line 220-224)

### 현재 코드 (버그):
```python
for file_path in py_files:
    try:
        # 버그: 상대 경로를 그대로 사용
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
```

### 수정된 코드:
```python
for file_name in py_files:
    try:
        # 수정: 전체 경로 조합
        file_path = os.path.join(path, file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
```

## 3. _find_class_ast 수정 (search.py line 332-336)

### 현재 코드 (버그):
```python
for file_path in py_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
```

### 수정된 코드:
```python
for file_name in py_files:
    try:
        file_path = os.path.join(path, file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
```

## 4. 성능 최적화 - search_files 개선

### 현재 코드 (느림):
```python
def search_files(pattern: str, path: str = ".", recursive: bool = True, 
                 max_depth: Optional[int] = None) -> Dict[str, Any]:
    # os.walk 사용 - 느림
```

### 최적화된 코드:
```python
from pathlib import Path
import fnmatch

def search_files(pattern: str, path: str = ".", recursive: bool = True, 
                 max_depth: Optional[int] = None) -> Dict[str, Any]:
    try:
        # 자동 와일드카드 추가
        if '*' not in pattern and '?' not in pattern:
            pattern = f'*{pattern}*'

        base_path = Path(path)
        if not base_path.exists():
            return err(f"Path not found: {path}")

        results = []

        # pathlib 사용 - 더 빠름
        if recursive:
            # rglob는 훨씬 빠름
            for file_path in base_path.rglob(pattern):
                if file_path.is_file():
                    # 상대 경로로 변환
                    rel_path = file_path.relative_to(base_path)
                    results.append(str(rel_path))

                    # max_depth 체크 (옵션)
                    if max_depth and len(rel_path.parts) > max_depth:
                        continue
        else:
            # 현재 디렉토리만
            for file_path in base_path.glob(pattern):
                if file_path.is_file():
                    results.append(file_path.name)

        # 제외 패턴 적용 (성능 향상)
        exclude_patterns = ['__pycache__', '.git', 'node_modules', '.pytest_cache']
        results = [r for r in results 
                  if not any(exc in r for exc in exclude_patterns)]

        return ok(results, count=len(results))

    except Exception as e:
        return err(f"Search failed: {str(e)}")
```

## 5. 정규식 컴파일 캐싱

### 현재 코드:
```python
def search_code(pattern: str, ...):
    regex = re.compile(pattern, re.IGNORECASE)  # 매번 컴파일
```

### 최적화된 코드:
```python
# 모듈 레벨 캐시
_regex_cache = {}

def search_code(pattern: str, ...):
    # 캐시 확인
    cache_key = (pattern, re.IGNORECASE)
    if cache_key not in _regex_cache:
        _regex_cache[cache_key] = re.compile(pattern, re.IGNORECASE)

    regex = _regex_cache[cache_key]

    # 캐시 크기 제한
    if len(_regex_cache) > 100:
        _regex_cache.clear()
```

## 6. 대용량 파일 스트리밍 읽기

### 현재 코드:
```python
with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()  # 전체 파일을 메모리에 로드
    lines = content.split('\n')
```

### 최적화된 코드:
```python
with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
    # 스트리밍 방식으로 라인별 읽기
    for line_num, line in enumerate(f, 1):
        if max_results and len(results) >= max_results:
            break

        match = regex.search(line)
        if match:
            results.append({
                'file': rel_path,
                'line': line_num,
                'text': line.rstrip(),
                'match': match.group(0)
            })
```

## 7. 병렬 처리 (고급)

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def search_code_parallel(pattern: str, path: str = ".", 
                         file_pattern: str = "*", 
                         max_results: int = 1000) -> Dict[str, Any]:

    # 파일 목록 가져오기
    files_result = search_files(file_pattern, path)
    if not files_result['ok']:
        return files_result

    files = files_result['data'][:100]  # 제한
    all_results = []

    # 병렬 처리
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for file_path in files:
            future = executor.submit(_search_in_file, file_path, pattern)
            futures.append(future)

        # 결과 수집
        for future in as_completed(futures):
            try:
                file_results = future.result(timeout=1)
                all_results.extend(file_results)

                if len(all_results) >= max_results:
                    break
            except:
                continue

    return ok(all_results[:max_results], 
             count=len(all_results),
             files_searched=len(files))
```
