# HelperResult 반환값 구조 정리

## 🎯 HelperResult 기본 구조

```python
class HelperResult:
    ok: bool          # 성공 여부
    data: Any         # 실제 데이터 (dict, list, str 등)
    error: str | None # 에러 메시지

    def get_data(self, default=None):
        """안전한 데이터 접근 메서드"""
        return self.data if self.ok else default
```

## 📊 주요 함수별 반환값 구조

### 1. 파일 관련 함수

#### 📄 `read_file(path, offset=0, length=1000)`
```python
# 반환 타입: dict
{
    'content': str,      # 파일 내용 (핵심!)
    'path': str,         # 파일 경로
    'size': int,         # 파일 크기 (bytes)
    'modified': float,   # 수정 시간 (timestamp)
    'format': str        # 파일 형식 (예: 'text')
}

# 사용 예시
result = helpers.read_file("file.py")
if result.ok:
    content = result.data['content']  # 또는
    content = result.get_data({}).get('content', '')
```

#### 📝 `write_file(path, content, mode='rewrite')`
```python
# 반환 타입: dict
{
    'path': str,         # 파일 경로
    'size': int,         # 작성된 크기
    'mode': str,         # 'rewrite' 또는 'append'
    'lines_written': int # 작성된 줄 수
}
```

#### 📋 `read_json(path)`
```python
# 반환 타입: Any (JSON 파일의 내용)
# JSON 파일의 실제 내용을 그대로 반환
# 예: dict, list, str, int 등
```

### 2. 디렉토리 관련 함수

#### 📁 `scan_directory_dict(path)`
```python
# 반환 타입: dict
{
    'files': [           # 파일 목록
        {
            'name': str,     # 파일명
            'path': str,     # 전체 경로
            'size': int      # 파일 크기
        },
        ...
    ],
    'directories': [     # 디렉토리 목록
        {
            'name': str,     # 디렉토리명
            'path': str      # 전체 경로
        },
        ...
    ],
    'total_files': int,      # 총 파일 수
    'total_directories': int # 총 디렉토리 수
}
```

### 3. 검색 관련 함수

#### 🔍 `search_files_advanced(path, pattern)`
```python
# 반환 타입: dict
{
    'results': [str, ...]  # 매칭된 파일 경로 목록
}
```

#### 💻 `search_code_content(path, pattern, file_pattern)`
```python
# 반환 타입: dict
{
    'results': [
        {
            'file_path': str,    # 파일 경로
            'matches': [         # 매칭 목록
                {
                    'line': int,     # 라인 번호
                    'content': str,  # 라인 내용
                    'match': str     # 매칭된 부분
                },
                ...
            ]
        },
        ...
    ]
}
```

### 4. Git 관련 함수

#### 🌿 `git_status()`
```python
# 반환 타입: dict
{
    'branch': str,           # 현재 브랜치
    'modified': [str, ...],  # 수정된 파일 목록
    'added': [str, ...],     # 추가된 파일 목록
    'untracked': [str, ...], # 추적되지 않은 파일 목록
    'untracked_count': int,  # 추적되지 않은 파일 수
    'clean': bool           # 깨끗한 상태 여부
}
```

#### 📜 `git_log(limit=10)`
```python
# 반환 타입: list[dict]
[
    {
        'hash': str,         # 커밋 해시
        'author': str,       # 작성자
        'date': str,         # 날짜
        'message': str       # 커밋 메시지
    },
    ...
]
```

### 5. 워크플로우 관련 함수

#### 📋 `workflow(command)`
```python
# 반환 타입: dict (명령어에 따라 다름)

# "/status" 명령어의 경우:
{
    'success': bool,
    'status': str,              # 'active', 'no_plan' 등
    'plan_id': str,
    'plan_name': str,
    'plan_description': str,
    'total_tasks': int,
    'completed_tasks': int,
    'progress_percent': int,
    'current_task': {
        'id': str,
        'title': str,
        'status': str,          # 'todo', 'in_progress', 'done'
        'description': str
    },
    'tasks_summary': {...},
    'recent_activity': [...]
}

# "/next" 명령어의 경우:
{
    'success': bool,
    'message': str,
    'completed_task': {...},
    'next_task': {...} | None,
    'progress': {...}
}
```

### 6. 유틸리티 함수

#### 📚 `list_functions()`
```python
# 반환 타입: dict
{
    'total_count': int,         # 총 함수 수
    'functions': {              # 모듈별 함수 목록
        'file': ['read_file', 'write_file', ...],
        'git': ['git_status', 'git_commit', ...],
        ...
    },
    'suggestions': {            # 잘못된 이름 → 올바른 이름
        'list_directory': 'scan_directory_dict',
        'search_files': 'search_files_advanced',
        ...
    },
    'usage': str               # 사용법 설명
}
```

## 💡 사용 팁

### 1. 안전한 데이터 접근
```python
# ❌ 위험한 방법
data = result.data['key']  # KeyError 가능

# ✅ 안전한 방법 1: get() 사용
data = result.data.get('key', default_value)

# ✅ 안전한 방법 2: get_data() 사용
data = result.get_data({}).get('key', default_value)
```

### 2. 에러 처리
```python
result = helpers.some_function()
if not result.ok:
    print(f"에러 발생: {result.error}")
    return None

# 성공한 경우에만 데이터 사용
data = result.get_data()
```

### 3. 타입별 처리
```python
# dict 반환하는 함수
result = helpers.git_status()
if result.ok:
    status = result.get_data({})
    branch = status.get('branch', 'unknown')

# list 반환하는 함수
result = helpers.git_log()
if result.ok:
    commits = result.get_data([])
    for commit in commits:
        print(commit['message'])

# 특수한 경우 (read_file)
result = helpers.read_file("file.txt")
if result.ok:
    # content는 dict 안에 있음
    content = result.data['content']
```

## 🔍 디버깅 방법

```python
# 반환값 구조 확인
result = helpers.some_function()
if result.ok:
    print(f"데이터 타입: {type(result.data)}")
    if isinstance(result.data, dict):
        print(f"키 목록: {list(result.data.keys())}")
    elif isinstance(result.data, list):
        print(f"리스트 크기: {len(result.data)}")
        if result.data:
            print(f"첫 번째 항목: {result.data[0]}")
```
