# 🔧 개선된 Replace 함수 통합 가이드

## 📊 개선 내용

### 기존 문제점
- 들여쓰기 하나라도 틀리면 매칭 실패
- 오류 시 디버깅 어려움
- 멀티라인 코드 교체 어려움

### 해결책: replace_v2
- **Fuzzy Matching**: 들여쓰기 차이 무시
- **Smart Indentation**: 자동 들여쓰기 조정
- **Better Errors**: 유사 텍스트 제안 + diff
- **Preview Mode**: 실제 수정 전 확인

## 🚀 사용법

### 1. 기본 사용 (들여쓰기 자동 조정)
```python
# 들여쓰기가 틀려도 OK
h.replace_v2(
    "file.py",
    "def func():",      # 스페이스 2개
    "def func(x):",     # 실제 파일은 4개여도 OK
    fuzzy=True          # 기본값
)
```

### 2. 미리보기
```python
result = h.replace_v2(
    "file.py",
    old_code,
    new_code,
    preview=True
)
print(result['diff'])  # 변경사항 확인
```

### 3. 엄격한 매칭
```python
h.replace_v2(
    "file.py",
    exact_pattern,
    new_code,
    fuzzy=False  # 정확한 매칭만
)
```

### 4. 스마트 모드
```python
h.replace_smart(
    "file.py",
    old,
    new,
    mode='auto'  # 자동으로 최적 방법 선택
)
```

## 📋 비교표

| 기능 | 기존 replace | replace_v2 | Desktop Commander |
|------|-------------|------------|-------------------|
| 정확한 매칭 | ✅ | ✅ | ✅ |
| Fuzzy 매칭 | ❌ | ✅ | ✅ |
| 들여쓰기 조정 | ❌ | ✅ | ✅ |
| 미리보기 | ❌ | ✅ | ✅ |
| 오류 제안 | ❌ | ✅ | ✅ |
| 속도 | 빠름 | 보통 | 보통 |
| 의존성 | 없음 | difflib (내장) | Desktop Commander |

## 🔄 마이그레이션

### 하위 호환성 유지
```python
# 기존 코드는 그대로 작동
h.replace(file, old, new)  # 정확한 매칭

# 새 기능 사용
h.replace_v2(file, old, new)  # Fuzzy 매칭
h.replace_smart(file, old, new)  # 자동 선택
```

### 점진적 전환
1. 새 코드는 `replace_v2` 사용
2. 문제가 있는 기존 코드만 수정
3. 복잡한 경우 `replace_smart` 사용

## 💡 Best Practices

### DO ✅
- 멀티라인 코드는 `replace_v2` 사용
- 미리보기로 확인 후 적용
- threshold 조절로 매칭 정확도 제어

### DON'T ❌
- 단순 문자열 교체에 fuzzy 사용 (성능 낭비)
- threshold 너무 낮게 설정 (잘못된 매칭)
- 검증 없이 대량 교체

## 🎯 결론

`replace_v2`는 Desktop Commander의 `edit_block`과 동등한 수준의 기능을 제공하면서도:
- 추가 의존성 없음 (Python 내장 라이브러리만 사용)
- 기존 코드와 호환
- 더 나은 오류 처리

**권장사항**: 
1. 멀티라인/블록 교체 → `replace_v2`
2. 단순 문자열 교체 → 기존 `replace`
3. 자동 선택 → `replace_smart`
