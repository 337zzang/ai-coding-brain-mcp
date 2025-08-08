# 📋 Search 헬퍼 함수 개선안
생성일: 2025-08-07 14:15

## 🔴 긴급 수정 필요 (Critical Bugs)

### 1. find_in_file 함수 - NameError
**문제**: 함수 내부에서 'h.search_code' 호출 시 'h' 미정의
**원인**: 모듈 내부에서 외부 네임스페이스 참조
**해결책**:
```python
# 현재 (오류)
result = h.search_code(pattern, ...)

# 수정 후
result = search_code(pattern, ...)  # 직접 함수 호출
```

### 2. AST 기반 함수들 - 경로 문제
**문제**: find_function/find_class의 strict 모드가 항상 빈 결과 반환
**원인**: search_files가 상대 경로 반환, AST 함수는 이를 직접 사용
**해결책**:
```python
# 현재 (오류)
for file_path in py_files:
    with open(file_path, 'r') as f:  # 파일을 찾을 수 없음

# 수정 후
for file_name in py_files:
    file_path = os.path.join(path, file_name)
    with open(file_path, 'r') as f:
```

## 🟡 성능 개선 필요 (Performance Issues)

### 3. search_files - 느린 재귀 탐색
**현재**: 전체 프로젝트 검색 시 5초 이상
**개선안**:
- os.walk() 대신 pathlib.Path.rglob() 사용
- 제외 패턴 추가 (node_modules, .git, __pycache__ 등)
- 병렬 처리 고려 (큰 프로젝트)

### 4. search_code - 비효율적인 파일 읽기
**현재**: 각 파일을 완전히 읽어 메모리에 로드
**개선안**:
- 대용량 파일은 스트리밍 방식으로 읽기
- 바이너리 파일 자동 스킵
- 캐싱 메커니즘 도입

## 🟢 기능 개선 제안 (Feature Enhancements)

### 5. 통합 검색 인터페이스
**제안**: 모든 검색 함수를 통합하는 단일 인터페이스
```python
def search(
    query: str,
    search_type: Literal['files', 'code', 'function', 'class', 'text'] = 'code',
    path: str = '.',
    **kwargs
) -> Dict[str, Any]
```

### 6. 검색 결과 하이라이팅
**제안**: 터미널에서 매칭 부분 색상 표시
- colorama 라이브러리 활용
- 매칭 부분을 색상으로 강조

### 7. 검색 히스토리 및 캐싱
**제안**: 자주 사용하는 검색 결과 캐싱
- .ai-brain/cache/ 디렉토리 활용
- LRU 캐시 구현
- 파일 변경 감지하여 캐시 무효화

## ⚪ 코드 품질 개선 (Code Quality)

### 8. 에러 처리 일관성
**현재**: 일부 함수만 try-except 사용
**개선**: 모든 함수에 일관된 에러 처리 패턴 적용

### 9. 타입 힌트 강화
**현재**: 기본적인 타입 힌트만 존재
**개선**: TypedDict로 반환 타입 명확히 정의

### 10. 단위 테스트 추가
**현재**: 테스트 코드 부재
**개선**: pytest 기반 테스트 케이스 작성

## 📊 우선순위 매트릭스

| 우선순위 | 항목 | 난이도 | 영향도 | 예상 시간 |
|---------|------|--------|--------|-----------|
| 🔴 P0 | find_in_file 수정 | 낮음 | 높음 | 10분 |
| 🔴 P0 | AST 경로 문제 | 낮음 | 높음 | 20분 |
| 🟡 P1 | search_files 성능 | 중간 | 중간 | 1시간 |
| 🟡 P1 | search_code 성능 | 중간 | 중간 | 1시간 |
| 🟢 P2 | 통합 인터페이스 | 높음 | 중간 | 2시간 |
| ⚪ P3 | 테스트 코드 | 중간 | 낮음 | 2시간 |

## 🚀 즉시 적용 가능한 Quick Fix

```python
# 1. find_in_file 수정 (search.py 481번 라인)
- result = h.search_code(pattern, os.path.dirname(file_path) or '.', 
+ result = search_code(pattern, os.path.dirname(file_path) or '.',

# 2. _find_function_ast 수정 (search.py 221번 라인 근처)
- for file_path in py_files:
+ for file_name in py_files:
+     file_path = os.path.join(path, file_name)

# 3. _find_class_ast 수정 (search.py 333번 라인 근처)  
- for file_path in py_files:
+ for file_name in py_files:
+     file_path = os.path.join(path, file_name)
```

## 📈 예상 효과
- 버그 수정: 3개 함수 정상 작동
- 성능 향상: 50-70% 속도 개선 예상
- 사용성: 통합 인터페이스로 편의성 증대
- 유지보수: 테스트 코드로 안정성 확보
