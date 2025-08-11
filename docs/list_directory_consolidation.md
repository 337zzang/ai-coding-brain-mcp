# list_directory 함수 통합 보고서

## 수정 일시
2025-08-11

## 변경 내용

### Before: 두 개의 함수
- `list_directory()`: 기본 디렉토리 조회
- `debug_list_directory()`: 디버그 정보 출력

### After: 하나의 통합 함수
- `list_directory(path=".", debug=False)`: 통합된 함수
  - `debug=False` (기본값): 조용한 모드
  - `debug=True`: 디버그 정보 출력

## 사용법

```python
# 일반 사용 (조용한 모드)
dirs = h.file.list_directory(".")

# 디버그 모드
dirs = h.file.list_directory(".", debug=True)
# 콘솔에 구조 정보 출력:
# ✅ list_directory('.') 성공
#    경로: /path/to/dir
#    항목 수: 50
#    사용 가능한 키: ['path', 'items', 'entries', 'count']
#    💡 TIP: 'items' 또는 'entries' 둘 다 사용 가능
```

## 장점
1. **단순성**: 하나의 함수로 모든 기능 제공
2. **일관성**: 동일한 함수에 옵션으로 제어
3. **명확성**: debug 파라미터로 의도 명확히 표현
4. **호환성**: 기존 코드 100% 호환 (debug 기본값 False)

## 수정 파일
- `python/ai_helpers_new/file.py`: 
  - debug 파라미터 추가
  - debug_list_directory 함수 제거
- `python/ai_helpers_new/facade_safe.py`:
  - debug_list_directory export 제거

## 테스트 결과
- ✅ 일반 모드 정상 작동
- ✅ 디버그 모드 정상 작동
- ✅ 'items'와 'entries' 별칭 유지
- ✅ debug_list_directory 함수 제거 확인
