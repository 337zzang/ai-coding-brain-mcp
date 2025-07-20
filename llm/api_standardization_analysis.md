# API 표준화 분석

✅ 결론부터  
‣ 기존 로직을 건드리지 않고 “표준 응답 {ok, data, error}”를 제공하려면 **어댑터(Adapter) 패턴**이 가장 적합합니다.  
‣ 3개의 기존 함수는 그대로 두고, 동일한 인수-시그니처를 지닌 “_std” 버전을 별도로 만들어 새 표준을 충족시킵니다.  
‣ 과거 호출 코드는 계속 구동되고, 신규/점진적 마이그레이션 코드는 어댑터를 호출하면 됩니다.

────────────────────────────────────────
1. 왜 ‘어댑터’인가? (Wrapper vs Adapter)

Wrapper(래퍼)는 단순히 감싸서 동일한 인터페이스를 되풀이할 때 주로 쓰입니다.  
Adapter는 “인터페이스 변환(translation)”이 핵심이며, 반환 형식을 새 규격에 맞게 바꿔 줍니다.  
지금 문제는 “반환 형식 변환”이므로 Adapter가 정확히 들어맞습니다.

2. 하위 호환성 전략

(a) 레거시 함수 그대로 유지  
(b) “_std”(혹은 v2) 접미사를 갖는 새 함수 추가  
(c) 신규 함수 내부에서 레거시 함수를 호출한 뒤 결과를 변환  
(d) deprecate 경고만 넣어서 개발자에게 점진적 전환 유도

기존 코드는 아무 수정 없이 계속 동작하고, 새로운 코드만 _std 버전으로 갈아타면 됩니다.

3. 구현 코드

# ─── standard_api.py ───────────────────────────────────────────
from typing import Any, Callable, Dict
import functools, warnings

def ok(data: Any = None, **meta) -> Dict[str, Any]:
    """표준 성공 응답"""
    return {"ok": True, "data": data, **meta}

def err(msg: str, **meta) -> Dict[str, Any]:
    """표준 실패 응답"""
    return {"ok": False, "data": None, "error": msg, **meta}

def adapter(func: Callable[..., Any]) -> Callable[..., Dict[str, Any]]:
    """
    기존 함수 → {ok, data, error} 로 감싸는 어댑터
    ▸ 시그니처를 바꾸지 않기 위해 *args/**kwargs 로 그대로 전달
    """
    @functools.wraps(func)
    def _wrapped(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            # 기존 결과 자체를 data 필드로 넘김
            return ok(result)
        except Exception as e:                # 모든 예외를 err 로 변환
            return err(str(e))
    return _wrapped

# ──── 레거시 함수 import ───
from filesystem import (
    scan_directory as _scan_directory,
    scan_directory_dict as _scan_directory_dict,
    get_current_project as _get_current_project
)

# ──── 어댑터 적용: “_std” 접미사로 노출 ───
scan_directory_std       = adapter(_scan_directory)
scan_directory_dict_std  = adapter(_scan_directory_dict)
get_current_project_std  = adapter(_get_current_project)

__all__ = [
    "scan_directory_std",
    "scan_directory_dict_std",
    "get_current_project_std",
    "ok",
    "err",
]

4. 사용 예시

# 구(舊) 방식 – 그대로 동작
files: list[str] = scan_directory(".", max_depth=3)

# 새(新) 방식 – 표준 응답
resp = scan_directory_std(".", max_depth=3)
if resp["ok"]:
    print("files:", resp["data"])
else:
    print("fail:", resp["error"])

5. 점진적 마이그레이션 로드맵

① standard_api.py(또는 같은 패키지 내부) 추가  
② 신규 기능/모듈은 무조건 *_std 함수 사용  
③ 레거시 코드베이스에 `warnings.warn("scan_directory() is deprecated…")` 같은 경고를 삽입(선택)  
④ CI 통계로 `_std` 사용률을 모니터링 후 일정 시점에 옛 함수를 제거하거나 `_std` 이름을 기본으로 승격

6. 장점 요약

• 기존 함수 시그니처/동작 불변  
• 예외 → error 필드로 직렬화되므로 API 일관성 확보  
• 한 줄짜리 adapter로 재사용성·테스트 용이성 향상  
• 적용/롤백 난이도 ↓

이렇게 하면 “패턴 위반” 문제를 고치면서도 코드베이스를 안전하게 진화시킬 수 있습니다.