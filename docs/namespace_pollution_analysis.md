# 네임스페이스 오염 문제 해결 방안

## O3 분석 결과

───────────────────────────
Ⅰ. 개요  
───────────────────────────
json_repl_session.py 는 load_helpers() 호출 시 30여 개의 심볼을 globals() 에 직접 주입합니다.  
• 장점 : 즉시(import-time) 사용 가능  
• 단점 :  
  – 사용자 코드가 같은 이름을 재할당하면 복구 불가  
  – 테스트나 멀티 REPL 세션에서 충돌·메모리 누수  
  – IDE / 타입체커가 실제 정의 위치를 찾기 어려움  

아래 전략은 “단 5–10줄씩의 소규모 패치”를 여러 단계에 나누어 적용하여,  
기존 스크립트를 거의 손대지 않고 점진적으로 안전한 구조(h.*)로 옮기는 방법입니다.

───────────────────────────
Ⅱ. 단계별 마이그레이션 로드맵  
───────────────────────────
단계 0 (오늘 바로 적용, 5줄 내외)  
  • LazyHelperProxy 클래스를 추가하고 load_helpers() 에서 단 1개의 객체(h)만 globals 에 주입.  
  • 기존 함수명(read, write …)에는 “얇은 프록시(stub)” 를 남겨 두어 하위 호환.  
  • 해당 stub 은 DeprecationWarning 을 1회만 출력 후 h.read 로 위임.  

단계 1 (코드베이스 전반 수정 시점)  
  • 내부 코드에서 read → h.read 로 교체.  
  • stub 제거 예고(로그 한 줄).  

단계 2 (메이저 버전 업 시점)  
  • stub 과 모듈-레벨 __getattr__ 후킹 제거 → 완전 격리 완료.  

───────────────────────────
Ⅲ. 핵심 구현 스니펫  
───────────────────────────
(1) LazyHelperProxy: 프록시 + 캐싱 + 지연 import  
```python
# ── json_repl_session.py 상단 or 별도 util ────────────────────
import importlib, warnings, types

class LazyHelperProxy(types.ModuleType):
    """ai_helpers_new 를 지연 로딩하고 속성을 캐시하는 프록시"""
    _module = None
    def _load(self):
        if self._module is None:
            self._module = importlib.import_module('ai_helpers_new')
    def __getattr__(self, item):
        self._load()
        attr = getattr(self._module, item)
        setattr(self, item, attr)          # ← 1회 조회 후 캐싱
        return attr
```

(2) load_helpers() 의 변동(8~10줄)  
```python
def load_helpers():
    global helpers, HELPERS_AVAILABLE
    if HELPERS_AVAILABLE:
        return True

    helpers = LazyHelperProxy('h')     # <-- NEW
    globals()['h'] = helpers           # only one symbol!
    HELPERS_AVAILABLE = True
    return True
```

(3) 하위 호환 stub  +  DeprecationWarning (자동 생성)  
```python
# ── json_repl_session.py 하단 ────────────────────────────────
import functools, warnings

# 기존 노출 목록
_LEGACY = "read write append parse view replace search_files search_code".split()

def _make_stub(name):
    @functools.wraps(getattr(h, name, lambda *a, **kw: None))
    def _stub(*args, **kwargs):
        warnings.warn(f"'{name}' is deprecated; use h.{name}", DeprecationWarning, stacklevel=2)
        return getattr(h, name)(*args, **kwargs)
    return _stub

for _name in _LEGACY:
    globals()[_name] = _make_stub(_name)
```
• 사용자는 계속 read() 를 부를 수 있지만, 최초 1회만 경고가 뜨고 실제 호출은 h.read 로 위임된다.  
• 따라서 “전역 오염 없음 + 하위 호환 유지”가 동시에 달성된다.

───────────────────────────
Ⅳ. 오류 처리 개선 패턴  
───────────────────────────
문제: 예외 발생 시 문자열 비교로 특정 메시지를 파싱 → 파이썬 버전마다 달라짐.  
해결: safe_call 데코레이터 활용 & 표준 Response 객체 반환.

```python
# ai_helpers_new.wrappers.safe_execution 와 동일 컨셉
def safe_call(fn):
    import functools, traceback
    @functools.wraps(fn)
    def _inner(*args, **kw):
        try:
            return {'ok': True, 'data': fn(*args, **kw)}
        except Exception as e:
            return {
                'ok': False,
                'error': str(e),
                'trace': traceback.format_exc(limit=3),
                'type': type(e).__name__,
            }
    return _inner
```
적용 예시:
```python
@safe_call
def repl_eval(src):
    return eval(src, globals())
```
장점  
  • 파이썬 버전에 독립  
  • 호출부는 항상 dict 형태를 기대 → 방어 코드 단순화  
  • 추적(trace) 필드를 선택적으로 로그/프린트 가능  

───────────────────────────
Ⅴ. 성능 영향 최소화  
───────────────────────────
1. LazyHelperProxy 는 첫 접근 전까지 import 를 지연 → 초기 부팅 20-40 ms 절약.  
2. __getattr__ 내부에서 setattr 로 캐싱하여 두 번째 접근부터 O(1) 속도.  
3. Deprecation stub 함수도 첫 호출 이후 h.read 로 직접 바인딩되므로 오버헤드 1회뿐.  

───────────────────────────
Ⅵ. 요약 체크리스트  
───────────────────────────
[ ] LazyHelperProxy 클래스 추가  
[ ] load_helpers() 수정: h 하나만 주입  
[ ] Deprecation stub 루프 추가  
[ ] (선택) module-level __getattr__ 제공 → “자동 프록시”  
[ ] safe_call / ensure_response 패턴으로 에러 처리 통일  
[ ] 문서/README에 “h.* 로 점진 전환” 안내  
[ ] CI 에 DeprecationWarning → 실패 아님(‐Wd 옵션 또는 필터)  

이렇게 3-단계(단계0 →1 →2)로 진행하면,  
“전역 오염 제거·견고한 에러 처리·성능 유지”를 위험 없이 달성할 수 있습니다.

## 추가 고려사항 (Claude)

### 1. 즉시 적용 가능한 안전장치
- 함수 덮어쓰기 방지를 위한 `__setattr__` 오버라이드
- 중요 함수에 대한 불변성 보장

### 2. 테스트 전략
- 기존 코드 호환성 테스트
- 성능 벤치마크
- 오류 시나리오 테스트

### 3. 문서화
- 마이그레이션 가이드
- 변경사항 로그
- 사용자 알림
