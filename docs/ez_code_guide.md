# Ez Code - 초간단 코드 수정 도구

REPL 환경에서 쉽게 사용할 수 있는 최소한의 코드 수정 도구입니다.

## 🚀 특징

- **초간단**: 단 3개 함수로 모든 작업
- **자동 백업**: 수정 시 자동으로 백업 생성
- **REPL 친화적**: 복잡한 객체 없이 간단한 dict 반환
- **빠른 실행**: 최소한의 코드로 빠르게 동작

## 📋 사용법

### 1. 파싱 - ez_parse()
```python
# 파일의 모든 함수/클래스 위치 확인
items = ez_parse("example.py")
# {'function_name': (10, 20), 'Class.method': (30, 45), ...}
```

### 2. 교체 - ez_replace()
```python
# 함수 교체
result = ez_replace("example.py", "old_function", """
def old_function():
    # 새로운 구현
    return "updated"
""")
# ✅ Replaced old_function (5 → 4 lines)
#    Backup: example.py.backup_20250716_213519
```

### 3. 보기 - ez_view()
```python
# 특정 함수/클래스 코드 보기
print(ez_view("example.py", "MyClass.method"))

# 전체 목록 보기
print(ez_view("example.py"))
```

## 💡 실전 예시

### 함수 수정
```python
# 1. 현재 코드 확인
print(ez_view("app.py", "process_data"))

# 2. 수정
new_code = """
def process_data(data):
    # 개선된 로직
    result = data * 2
    return result
"""
ez_replace("app.py", "process_data", new_code)
```

### 클래스 메서드 수정
```python
# 클래스.메서드 형식으로 지정
ez_replace("models.py", "User.save", """
def save(self):
    self.updated_at = datetime.now()
    super().save()
""")
```

## ⚡ vs 기존 code_ops.py

| 기능 | ez_code | code_ops |
|------|---------|----------|
| 코드 크기 | 75줄 | 662줄 |
| 사용 난이도 | 초간단 | 복잡 |
| 백업 | 자동 | 수동 |
| 정밀도 | 기본 | 높음 |
| REPL 사용 | 최적화 | 어려움 |

## 🎯 권장 사용 시나리오

✅ Ez Code 사용:
- REPL에서 빠른 수정
- 간단한 함수/메서드 교체
- 프로토타이핑
- 자동 백업이 필요한 경우

❌ code_ops.py 사용:
- 정밀한 좌표 기반 수정
- LSP 통합
- 대규모 리팩토링
- 복잡한 코드 변환
