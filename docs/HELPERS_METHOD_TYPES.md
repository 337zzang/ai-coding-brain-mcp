# helpers 메서드 사용법 (AI 필독)

## 핵심 규칙
1. **helpers.read_file()은 HelperResult 객체를 반환합니다**
2. **실제 내용은 .get_data({}).get('content', '')로 추출합니다**
3. **v48부터 read_file_safe()와 read_file_lines() 사용 가능**

## 메서드별 반환 타입

### HelperResult 반환 (get_data 필요)
- read_file() → .get_data({})['content']
- scan_directory() → .get_data({})['files'], ['directories']  
- search_files() → .get_data({})['results']
- list_functions() → .get_data({})

### 직접 dict/list 반환 (get_data 불필요)
- git_status() → dict
- git_add() → dict
- git_commit() → dict
- workflow() → dict
- list_apis() → dict

## 실전 예제

```python
# 1. 파일 읽고 특정 함수 찾기
content = helpers.read_file_safe('file.py')  # 새 메서드!
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'def my_function' in line:
        print(f"Found at line {i+1}: {line}")

# 2. 여러 파일 검색
py_files = helpers.search_files('.', '*.py').get_data({}).get('results', [])
for file in py_files:
    content = helpers.read_file_safe(file)
    if 'import pandas' in content:
        print(f"{file} uses pandas")

# 3. Git 작업
status = helpers.git_status()  # 직접 dict
if status['modified']:
    helpers.git_add('.')
    helpers.git_commit("Update files")
```
