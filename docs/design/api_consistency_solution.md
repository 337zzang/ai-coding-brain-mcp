
# 🔧 API 일관성 문제 해결 최종 설계

## 📋 개요
O3와 Claude의 병렬 분석을 통해 API 일관성 문제의 근본 원인과 해결책을 도출했습니다.

## 🔍 핵심 문제 요약

### 1. 확인된 문제점
| 문제 | 원인 | 영향도 |
|------|------|---------|
| UltraSimpleFlowManager.get_current_plan() 없음 | FlowAPI에만 구현, Manager 리팩토링 시 제거 | 높음 |
| TaskLogger.task_info() dependencies 미지원 | v2 업그레이드 시 제거, 문서 미갱신 | 중간 |
| view() 타입 불안정 (오해) | 실제로는 정상, 사용법 문서 부족 | 낮음 |
| FlowAPI ok 키 없음 | 설계상 의도, 일관성 부족 | 중간 |

### 2. 근본 원인
- 빠른 기능 추가 후 문서화 지연
- 모듈별 독립 개발로 인한 API 일관성 부족
- 통합 테스트 및 타입 검증 부재
- Breaking change 관리 프로세스 부재

## 📐 해결 방안

### Phase 1: 즉시 수정 (2시간)

#### 1.1 Manager에 get_current_plan() 추가
```python
# ultra_simple_flow_manager.py
def get_current_plan(self) -> Optional[Plan]:
    """현재 선택된 Plan 반환 (FlowAPI 위임 또는 최근 Plan)"""
    try:
        from .flow_api import get_flow_api
        flow_api = get_flow_api()
        current = flow_api.get_current_plan()
        if current:
            return self.get_plan(current['id'])
    except Exception:
        pass

    # Fallback: 가장 최근 수정된 Plan
    plans = self.list_plans()
    if plans:
        return max(plans, key=lambda p: p.updated_at or '')
    return None
```

#### 1.2 TaskLogger 유연성 개선
```python
# task_logger.py
def task_info(self, title: str, priority: str = "medium",
              estimate: Optional[str] = None, 
              description: str = "", **extras) -> Response:
    """Task 정보 기록 (extras로 확장 가능)"""
    return self._log(
        "TASK_INFO",
        title=title,
        priority=priority,
        estimate=estimate,
        description=description,
        **extras  # dependencies 등 추가 필드 지원
    )
```

#### 1.3 타입 정의 통일
```python
# wrappers.py
from typing import TypedDict, Any, Optional

class Response(TypedDict, total=False):
    ok: bool
    data: Any
    error: Optional[str]

def ensure_response(data: Any, error: Optional[str] = None) -> Response:
    """모든 반환값을 표준 Response 형식으로 변환"""
    if isinstance(data, dict) and 'ok' in data:
        return data

    if error:
        return {'ok': False, 'error': error}

    return {'ok': True, 'data': data}
```

### Phase 2: API 일관성 확보 (3시간)

#### 2.1 안전한 API 래퍼 제공
```python
# safe_api.py
def safe_call(func, *args, **kwargs) -> Response:
    """모든 API 호출을 안전하게 래핑"""
    try:
        result = func(*args, **kwargs)
        return ensure_response(result)
    except Exception as e:
        return {'ok': False, 'error': str(e)}

# FlowAPI 전용 래퍼
class SafeFlowAPI:
    def __init__(self):
        self._api = get_flow_api()

    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            return safe_call(getattr(self._api, name), *args, **kwargs)
        return wrapper
```

#### 2.2 타입 힌트 추가
- 모든 public API에 `-> Response` 타입 힌트 추가
- mypy 설정 파일 추가 및 CI 통합

#### 2.3 통합 테스트 작성
```python
# test_api_consistency.py
def test_all_apis_return_response():
    """모든 API가 표준 Response 형식을 반환하는지 검증"""
    apis = [
        (h.read, ["test.txt"]),
        (h.view, ["file.py", "func"]),
        (h.parse, ["file.py"]),
        # ... 모든 API
    ]

    for api, args in apis:
        result = api(*args)
        assert isinstance(result, dict), f"{api.__name__} must return dict"
        assert 'ok' in result, f"{api.__name__} must have 'ok' key"
```

### Phase 3: 문서 및 프로세스 개선 (2시간)

#### 3.1 문서 자동 검증
- doctest 또는 pytest-docs로 문서의 코드 예제 검증
- 오래된 예제 자동 탐지 스크립트

#### 3.2 Breaking Change 관리
```python
# version.py
__version__ = "2.1.0"  # Semantic Versioning 도입

# deprecation.py
def deprecated(reason, version):
    """Deprecation 데코레이터"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is deprecated since {version}. {reason}",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

#### 3.3 마이그레이션 가이드
- MIGRATION.md 작성
- 각 breaking change별 대응 방법 명시

## 📊 구현 우선순위

### 긴급 (오늘)
1. Manager.get_current_plan() 추가 - 가장 많은 오류 해결
2. TaskLogger **extras 지원 - 호환성 문제 해결
3. 안전한 사용 가이드 배포

### 중요 (이번 주)
1. Response 타입 통일
2. 타입 힌트 추가
3. 통합 테스트 작성

### 개선 (다음 주)
1. 문서 자동 검증
2. CI/CD 파이프라인 구축
3. Semantic Versioning 도입

## ✅ 예상 효과
1. **즉시**: 기존 코드 오류 해결
2. **단기**: API 사용 시 예측 가능성 향상
3. **장기**: 유지보수성 및 확장성 개선

## 🚀 Task 구성
1. **긴급 수정** (2시간)
   - Manager.get_current_plan() 구현
   - TaskLogger 유연성 개선
   - 기본 테스트 작성

2. **API 일관성 확보** (3시간)
   - Response 타입 통일
   - 안전한 래퍼 구현
   - 통합 테스트 스위트

3. **문서 및 프로세스** (2시간)
   - 문서 업데이트
   - 마이그레이션 가이드
   - CI/CD 설정

**총 예상 시간**: 7시간
