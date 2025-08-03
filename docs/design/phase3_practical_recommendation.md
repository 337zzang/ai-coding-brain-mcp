
# 🎯 Phase 3 실용적 수정 권고안

## 📋 즉시 실행 가능한 개선 (1-2일)

### 1. 선택적 AST 모드 추가
```python
# search.py 수정 - 기존 API 유지하면서 옵션 추가
def find_function(name: str, path: str = ".", strict: bool = False) -> Dict[str, Any]:
    if strict and _ast_available:
        try:
            return _find_function_ast(name, path)
        except Exception as e:
            # AST 실패 시 자동으로 정규식 폴백
            logger.warning(f"AST parsing failed, falling back to regex: {e}")

    # 기존 정규식 로직 (기본값)
    return _find_function_regex(name, path)
```

### 2. 안전한 코드 수정 검증
```python
# code.py - 수정 전 AST 검증 추가
def safe_replace(file_path: str, old_code: str, new_code: str, 
                validate: bool = True) -> Dict[str, Any]:
    if validate:
        # 수정 후 코드가 유효한지 AST로 검증
        try:
            test_content = current_content.replace(old_code, new_code)
            ast.parse(test_content)
        except SyntaxError as e:
            return {
                'ok': False,
                'error': f'수정 후 구문 오류 발생: {e}',
                'line': e.lineno
            }

    # 기존 로직 계속...
```

### 3. 경량 캐싱 시스템
```python
# Simple LRU cache for AST results
from functools import lru_cache
import os

@lru_cache(maxsize=20)  # 작은 캐시로 시작
def _cached_ast_parse(file_path: str, mtime: float):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return ast.parse(content)

def parse_with_cache(file_path: str):
    mtime = os.path.getmtime(file_path)
    return _cached_ast_parse(file_path, mtime)
```

## 📊 중기 개선 계획 (1-2주)

### 1. 하이브리드 검색 시스템
- 정규식으로 빠른 후보 찾기
- AST로 정확성 검증
- 두 방식의 장점 결합

### 2. 점진적 마이그레이션 인프라
- Feature toggle 시스템 구축
- 사용 통계 수집
- A/B 테스트 가능

### 3. 성능 모니터링
- 각 방식의 실행 시간 측정
- 캐시 히트율 추적
- 메모리 사용량 모니터링

## ⚠️ 하지 말아야 할 것들

1. **전면적 API 변경** ❌
   - 기존 사용자 코드 파손
   - 마이그레이션 비용 과다

2. **text_mode 즉시 제거** ❌
   - 유용한 escape hatch
   - 긴급 상황 대응 필요

3. **대용량 AST 캐싱** ❌
   - 메모리 부담
   - GC 압박

## ✅ 성공 지표

1. **단기 (1개월)**
   - 치명적 버그 0건
   - strict 모드 사용률 10%
   - 성능 저하 없음

2. **중기 (3개월)**
   - 코드 수정 정확도 향상
   - strict 모드 사용률 30%
   - 버그 리포트 감소

3. **장기 (6개월)**
   - AST 기반 신기능 출시
   - 사용자 만족도 향상
   - 유지보수 비용 감소
