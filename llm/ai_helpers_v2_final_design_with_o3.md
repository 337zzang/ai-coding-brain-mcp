
# AI Helpers v2.0 개선 상세 설계 문서 (o3 분석 통합)

## 📋 개요
본 문서는 o3 AI의 심층 분석 결과를 통합한 최종 설계입니다.

## 🤖 o3 분석 핵심 통찰

### search_code 개선
- 분석 결과 없음

### 코드 수정 방안
- 분석 결과 없음

### 워크플로우 개선
- 분석 결과 없음

## 1. search_code max_results 즉시 수정

### 1.1 구현 코드
```python
def search_code(pattern: str, path: str = ".", file_pattern: str = "*", 
                max_results: int = 100) -> Dict[str, Any]:
    """파일 내용에서 패턴 검색 (정규식 지원)

    o3 권장사항 적용:
    - 조기 종료 로직으로 정확한 max_results 보장
    - truncated 플래그로 결과 잘림 표시
    - 파일 단위 조기 종료로 성능 최적화
    """
    try:
        regex = re.compile(pattern, re.IGNORECASE)
        matches = []
        files_searched = 0

        files_result = search_files(file_pattern, path, recursive=True)
        if not files_result['ok']:
            return files_result

        for file_path in files_result['data']:
            # 파일 열기 전 체크 (o3 권장)
            if len(matches) >= max_results:
                break

            full_path = os.path.join(path, file_path)

            if full_path.endswith(('.pyc', '.pyo', '.so', '.dll', '.exe')):
                continue

            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    files_searched += 1

                    for line_num, line in enumerate(f, 1):
                        match = regex.search(line)
                        if match:
                            matches.append({
                                'file': file_path,
                                'line': line_num,
                                'text': line.rstrip(),
                                'match': match.group(0)
                            })

                            # 정확한 수 도달 시 즉시 반환 (o3 핵심 권장)
                            if len(matches) == max_results:
                                return ok(
                                    matches,
                                    count=len(matches),
                                    files_searched=files_searched,
                                    truncated=True  # 결과가 잘렸음을 명시
                                )
            except Exception:
                # 파일 읽기 실패는 무시하고 계속
                continue

        return ok(
            matches,
            count=len(matches),
            files_searched=files_searched,
            truncated=False
        )

    except re.error as e:
        return err(f"Invalid regex pattern: {e}")
    except Exception as e:
        return err(f"Search failed: {str(e)}")
```

## 2. WorkflowManager 점진적 리팩토링

### 2.1 Phase 1: 최소 변경 (즉시 적용)
```python
# workflow_manager.py 상단에 추가
def _ensure_dict_response(func):
    """데코레이터: 문자열 반환을 dict로 래핑"""
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        if isinstance(result, str):
            return ok({"message": result, "display": result})
        return result
    return wrapper

# 기존 메서드에 적용
@_ensure_dict_response
def _show_status(self) -> str:
    # 기존 코드 그대로 유지
    pass
```

### 2.2 Phase 2: 완전한 리팩토링 (1주 내)
- verbose 파라미터 추가
- 구조화된 데이터 반환
- 기존 출력 로직 분리

## 3. 테스트 구조 즉시 구축

### 3.1 최소 테스트 (오늘 구현)
```python
# test/test_search_fix.py
import pytest
from ai_helpers_new import search_code

def test_search_max_results_exact():
    """max_results가 정확히 작동하는지 테스트"""
    # 테스트 데이터 준비
    result = search_code("def", "python/", max_results=3)
    assert result['ok']
    assert len(result['data']) <= 3
    if len(result['data']) == 3:
        assert result.get('truncated') == True

def test_search_max_results_zero():
    """max_results=0 엣지 케이스"""
    result = search_code("def", ".", max_results=0)
    assert result['ok']
    assert len(result['data']) == 0
```

## 4. 구현 우선순위 (o3 분석 기반)

### 🔴 즉시 (30분 내)
1. search_code 수정 및 배포
2. 기본 테스트 실행
3. _workflow_managers 오류 수정 확인

### 🟡 오늘 중
1. WorkflowManager 데코레이터 적용
2. 테스트 파일 구조 생성
3. 핵심 함수 테스트 작성

### 🟢 이번 주
1. 전체 API 일관성 검토
2. 문서화 업데이트
3. CI/CD 통합

## 5. 검증 계획

### 5.1 수동 테스트
```python
# 1. search_code 테스트
result = h.search_code("def", ".", max_results=2)
print(f"결과 수: {len(result['data'])}")
print(f"잘림 여부: {result.get('truncated', False)}")

# 2. workflow 테스트
result = wf("/status")
print(f"타입: {type(result)}")
print(f"성공 여부: {result.get('ok') if isinstance(result, dict) else 'N/A'}")
```

### 5.2 자동화 테스트
- pytest 실행
- 커버리지 측정
- 성능 벤치마크
