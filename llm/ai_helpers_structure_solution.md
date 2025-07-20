# AI Helpers 구조 기반 해결책

아래 내용을 요약하면 다음과 같습니다.

1) project.py 는 그대로 둔다.  
2) __init__.py 에서 “export” 단계에서만 세 함수를 래핑한다.  
3) 래핑 버전은 라이브러리 표준(ok/err 패턴)을 따르고,  
   원본(raw) 함수도 동시에 노출해 100 % 하위호환을 보장한다.  
4) 이렇게 하면 수정 지점이 한 곳이라 유지보수가 가장 쉽다.

────────────────────────
Q1. project.py 를 직접 고칠까?  
→ “안 고치는” 편이 안전하다.  
   • 프로젝트 외부에서 이미 쓰고 있을 수 있는 원본 반환 타입(list/dict)을 건드리지 않음  
   • git blame/이력 보존, side-effect 위험 ↓

Q2. __init__.py 에서 처리할 수 있나?  
→ 가능하다. 모듈 import 직후 원하는 함수에 래퍼를 씌우면 된다.  
   Python 의 모듈 시스템은 심볼을 다시 바인딩해도 문제가 없다.

Q3. 가장 깔끔하고 유지보수성이 높은 방법?  
→ “__init__.py 에서 래핑 + raw 함수 동시 노출” 방식  
   • 기존 코드 : ai_helpers.project.scan_directory( … )  → 그대로 작동  
     (raw 함수를 직접 임포트하거나 기존 경로를 유지하면 list/dict 그대로 받음)  
   • 새 코드 : ai_helpers.scan_directory( … )            → ok() 패턴을 받음  
   • 모든 변경이 한 파일(__init__.py)에 모여 있어 관리 용이

Q4. 구체적 코드
(아래 코드는 __init__.py 의 하단부에 추가/수정하면 된다)

```python
# 기존 import 라인을 그대로 두고 별칭으로 raw 버전을 확보
from .project import (
    scan_directory        as _scan_directory_raw,
    scan_directory_dict   as _scan_directory_dict_raw,
    get_current_project   as _get_current_project_raw,
    create_project_structure                      # ← 기존 그대로
)

# ----------------------------------------
# 내부 helper: ok() 래퍼
# ----------------------------------------
from functools import wraps
from .util import ok, is_ok

def _wrap_ok(fn):
    """원본 함수를 ok() 패턴으로 감싸서 반환"""
    @wraps(fn)
    def _inner(*args, **kwargs):
        result = fn(*args, **kwargs)
        # 이미 ok/err 패턴이면 그대로
        if isinstance(result, dict) and ('ok' in result):
            return result
        return ok(result)
    # 원본 함수에 접근할 수 있게 속성으로 보관
    _inner.__raw__ = fn
    return _inner


# ----------------------------------------
# 래핑 & export
# ----------------------------------------
# 표준-패턴 버전
scan_directory       = _wrap_ok(_scan_directory_raw)
scan_directory_dict  = _wrap_ok(_scan_directory_dict_raw)
get_current_project  = _wrap_ok(_get_current_project_raw)

# 100 % 호환용 raw 별칭
scan_directory_raw       = _scan_directory_raw
scan_directory_dict_raw  = _scan_directory_dict_raw
get_current_project_raw  = _get_current_project_raw

# __all__ 갱신
__all__.extend([
    # 래핑 버전은 이미 __all__ 에 포함돼 있으므로 raw 버전만 추가
    'scan_directory_raw', 'scan_directory_dict_raw', 'get_current_project_raw'
])
```

사용 예

```python
# 신규 권장 방식
from ai_helpers import scan_directory
res = scan_directory('.')        # -> {'ok': True, 'data': [...], ...}

# 레거시 코드 그대로
from ai_helpers.project import scan_directory
lst = scan_directory('.')        # -> ['file1.py', 'file2.py', ...] (변경 없음)

# 혹은 raw 버전을 명시적으로
from ai_helpers import scan_directory_raw
lst2 = scan_directory_raw('.')
```

장점
• 세 함수의 반환값을 새·구 방식 모두 제공 → 100 % 호환  
• 다른 50 개 함수와 동일한 패턴을 완전히 충족(래핑 버전)  
• 수정 위치가 __init__.py 하나라 유지보수 쉽고, project.py 는 untouched  
• 새로운 사용자에게는 일관된 ok/err 패턴만 노출돼 학습 비용 ↓

결론  
“project.py 를 건드리지 않고 __init__.py 에서 import 시점에 래핑” 하는 것이
가장 안전하고, 일관되며, 유지보수성이 높은 해결책이다.