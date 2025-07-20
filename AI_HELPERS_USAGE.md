# AI Helpers v2.0 사용 예시

## 설치
```python
import ai_helpers_new as h
```

## 파일 작업
```python
# 파일 읽기/쓰기
content = h.read('file.txt')['data']
h.write('output.txt', content)
h.append('log.txt', '\n새로운 로그')

# JSON 작업
data = h.read_json('config.json')['data']
h.write_json('output.json', {'key': 'value'})

# 파일 정보
if h.exists('file.txt'):
    info = h.info('file.txt')['data']
    print(f"크기: {info['size']} bytes")
```

## 코드 분석
```python
# 파일 파싱
result = h.parse('module.py')
if result['ok']:
    functions = result['data']['functions']
    classes = result['data']['classes']

# 특정 함수 보기
code = h.view('module.py', 'my_function')['data']

# 코드 수정
h.replace('file.py', 'old_name', 'new_name')
h.insert('file.py', '# TODO:', '\n# 새로운 할 일')

# 빠른 조회
funcs = h.functions('module.py')['data']
clses = h.classes('module.py')['data']
```

## 검색
```python
# 파일명 검색
files = h.search_files('*.py', '.')['data']

# 코드 내용 검색 (정규식)
matches = h.search_code('import.*os', '.')
for match in matches['data']:
    print(f"{match['file']}:{match['line']}")

# 함수/클래스 찾기
h.find_function('main', '.')
h.find_class('MyClass', '.')

# 간단한 텍스트 검색
results = h.grep('TODO', '.', context=2)

# 특정 파일에서만 검색
h.find_in_file('module.py', 'def.*test')
```

## 에러 처리
```python
# 일관된 에러 처리
result = h.read('missing.txt')
if not h.is_ok(result):
    print(f"에러: {h.get_error(result)}")
else:
    content = h.get_data(result)
```

## 핵심 장점
1. **일관성**: 모든 함수가 동일한 dict 형식 반환
2. **명확성**: 직관적인 함수명
3. **단순함**: 복잡한 클래스 없음
4. **실용성**: REPL에 최적화된 API
