# helpers 사용 시 자주 하는 실수 (AI 참고용)

## ❌ 자주 하는 실수들

### 1. read_file 반환값 처리
```python
# ❌ 잘못됨 - get_data('')가 dict 반환
content = helpers.read_file('file').get_data('')
lines = content.split('\n')  # AttributeError!

# ✅ 올바름
content = helpers.read_file('file').get_data({}).get('content', '')
# 또는 새로운 안전한 메서드 사용
content = helpers.read_file_safe('file')
```

### 2. git 메서드 반환값
```python
# ✅ git 메서드들은 직접 dict 반환 (HelperResult 아님)
status = helpers.git_status()  # dict
modified = status.get('modified', [])
```

### 3. workflow 메서드 사용
```python
# ❌ 잘못됨 - 인자 2개만 받음
helpers.workflow("/next", "메시지")  

# ✅ 올바름
helpers.workflow("/next")
helpers.workflow("/task complete 메시지")
```

## 🎯 권장 사용법

### 파일 읽기
```python
# 새로운 안전한 메서드 사용
content = helpers.read_file_safe('파일경로')  # 문자열 반환
lines = helpers.read_file_lines('파일경로')   # 리스트 반환
```

### 디렉토리 스캔
```python
result = helpers.scan_directory('.')
data = result.get_data({})
files = data.get('files', [])
directories = data.get('directories', [])
```

### 검색
```python
result = helpers.search_files('.', '*.py')
files = result.get_data({}).get('results', [])
```
