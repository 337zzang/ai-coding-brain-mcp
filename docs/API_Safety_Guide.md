# 🛡️ API 사용 실수 방지 가이드

## 발생한 실수 분석

### 1. 함수 반환 형식 가정
**문제**: API 함수의 반환 형식을 확인하지 않고 바로 사용
```python
# ❌ 잘못된 예시
files = helpers.get_project_structure()['files']  # KeyError 발생!
path = results[0]['relative_path']  # KeyError 발생!

# ✅ 올바른 예시
structure = helpers.get_project_structure()
print(f"타입: {type(structure)}")
print(f"키: {list(structure.keys())}")
# 확인 후 사용
total_files = structure.get('total_files', 0)
```

### 2. 실제 발생한 오류들
- `get_project_structure()`: 'files' 키 없음 → 'total_files', 'structure' 사용
- `search_files_advanced()`: 'relative_path' 키 없음 → 'path', 'name' 사용

## 안전한 API 사용 3단계

### 1단계: 반환 형식 검사
```python
# 디버깅 헬퍼 함수
def inspect_result(result, name="Result"):
    """결과를 안전하게 검사"""
    print(f"🔍 {name} 검사:")
    print(f"  타입: {type(result)}")
    
    if isinstance(result, dict):
        print(f"  키: {list(result.keys())}")
        if result:
            print("  첫 번째 값 타입:", type(list(result.values())[0]))
    elif isinstance(result, list):
        print(f"  길이: {len(result)}")
        if result:
            print("  첫 번째 항목:", result[0])

# 사용 예시
result = helpers.search_files_advanced(".", "*.py")
inspect_result(result, "search_files_advanced")
```

### 2단계: 안전한 접근
```python
# Option 1: 조건부 접근
if 'key' in result:
    value = result['key']

# Option 2: get() 메서드 (권장)
value = result.get('key', default_value)

# Option 3: try-except
try:
    value = result['key']
except KeyError:
    print("키가 존재하지 않습니다")
    value = None
```

### 3단계: 문서화된 API 사용
```python
# helpers 함수 반환 형식 참고
"""
get_project_structure() → {
    'root': str,
    'total_files': int,
    'total_dirs': int,
    'structure': dict,
    'last_scan': str
}

search_files_advanced() → {
    'results': [
        {
            'path': str,
            'name': str,
            'type': str,
            'size': int,
            'directory': str,
            'extension': str,
            'modified': float
        }
    ],
    'total_found': int,
    'truncated': bool
}
"""
```

## Wisdom 시스템 연동

### 자동 감지 패턴
```python
# wisdom_hooks.py에 추가된 패턴
'api_assumption': {
    'pattern': 'API 호출 후 반환값 확인 없이 접근',
    'severity': 'high'
}
```

### 실시간 경고
- API 호출 감지
- 반환값 형식 확인 코드 없으면 경고
- Wisdom 시스템에 자동 기록

## 체크리스트

- [ ] API 호출 전 문서/예제 확인
- [ ] 작은 테스트로 반환 형식 검증
- [ ] `inspect_result()` 헬퍼 사용
- [ ] 안전한 접근 패턴 사용 (get() 메서드)
- [ ] 에러 처리 추가
- [ ] 결과를 가정하지 말고 확인

## 베스트 프랙티스

1. **항상 타입과 구조 확인**
   ```python
   result = helpers.some_function()
   print(type(result), list(result.keys()) if isinstance(result, dict) else result)
   ```

2. **방어적 프로그래밍**
   ```python
   # 안전한 중첩 접근
   value = result.get('data', {}).get('items', [])
   ```

3. **명시적 에러 처리**
   ```python
   if not result or 'error' in result:
       print("오류 발생:", result.get('error', 'Unknown'))
       return
   ```

---

**작성일**: 2025-06-25  
**Wisdom 추적**: api_assumption 패턴 2회 발생