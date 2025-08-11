# AI Helpers 문제 해결 보고서

## 발생일시
2025-08-11

## 발견된 문제

### 1. list_directory() 반환 구조 문제
- **위치**: `python/ai_helpers_new/file.py`
- **문제**: 반환값의 키 이름이 문서화되지 않아 혼란 발생
- **실제 구조**:
  ```python
  {
      'ok': True,
      'data': {
          'path': str,
          'items': [...],  # 'entries'가 아님!
          'count': int
      }
  }
  ```
- **올바른 사용법**:
  ```python
  dirs = h.file.list_directory(".")
  if dirs['ok']:
      items = dirs['data']['items']  # ✅ 올바른 접근
  ```

### 2. git_status_normalized() 표준 형식 미준수
- **위치**: `python/ai_helpers_new/git.py:697`
- **문제**: 표준 응답 형식 `{'ok': True, 'data': ...}` 미준수
- **원인**: `return normalized` (표준 래퍼 미사용)
- **수정**: `return ok(normalized)`
- **영향**: `status['ok']` 접근 시 KeyError 발생

## 해결 방법

### git_status_normalized() 수정
```python
# Before (line 697)
return normalized

# After (line 697)
return ok(normalized)
```

## 테스트 결과
- ✅ git_status_normalized() 정상 작동 확인
- ✅ 표준 응답 형식 준수 확인
- ✅ 모든 헬퍼 함수 정상 작동

## 권장사항

1. **표준 응답 형식 준수**
   - 모든 public 함수는 `ok()` 또는 `err()` 래퍼 사용
   - 일관된 응답 구조 유지

2. **문서화 개선**
   - 각 함수의 반환 구조 명확히 문서화
   - 특히 중첩된 딕셔너리 키 이름 명시

3. **테스트 추가**
   - 표준 응답 형식 검증 테스트
   - 반환값 구조 검증 테스트

## 커밋 정보
- 커밋 메시지: `fix: git_status_normalized() 표준 응답 형식 준수`
- 수정 파일: `python/ai_helpers_new/git.py`
