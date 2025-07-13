# helpers.read_file() 사용 가이드

## 🚨 일반적인 오류

```python
# ❌ 잘못된 사용 - AttributeError 발생
content = helpers.read_file("file.py").get_data("")
lines = content.split('\n')  # 'dict' object has no attribute 'split'
```

## ✅ 올바른 사용법

### 1. 기본 사용법
```python
# 파일 읽기
result = helpers.read_file("file.py")
data = result.get_data({})
content = data['content']  # 실제 파일 내용 (문자열)
```

### 2. 안전한 사용법
```python
# None 체크 포함
content = helpers.read_file("file.py").get_data({}).get('content', '')
if content:
    lines = content.split('\n')
```

### 3. 한 줄 사용법
```python
# 간단하게 한 줄로
content = helpers.read_file("file.py").get_data({}).get('content', '')
```

## 📊 반환값 구조

```python
{
    'content': '파일 내용 문자열',
    'path': '파일 전체 경로',
    'size': 파일크기,
    'modified': 수정시간,
    'format': 'text'
}
```

## 💡 편의 함수

```python
def read_file_content(path):
    """파일 내용을 직접 문자열로 반환"""
    return helpers.read_file(path).get_data({}).get('content', '')

# 사용
content = read_file_content("python/api/file.py")
lines = content.split('\n')
```

## 🔍 다른 helpers 메서드들도 같은 패턴

- `helpers.scan_directory()` → `.get_data({})` → `['files']`, `['directories']`
- `helpers.search_files()` → `.get_data({})` → `['results']`
- `helpers.git_status()` → 직접 딕셔너리 반환 (HelperResult 아님)

## ⚠️ 주의사항

1. 모든 helpers 메서드가 HelperResult를 반환하는 것은 아님
2. git 관련 메서드들은 대부분 직접 딕셔너리 반환
3. 파일 관련 메서드들은 대부분 HelperResult 반환
