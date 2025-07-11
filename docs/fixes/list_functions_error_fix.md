# list_functions() 오류 영구적 해결 문서

## 문제 상황
`helpers.list_functions()` 호출 시 다음 오류 발생:
```
TypeError: list_functions() missing 1 required positional argument: 'helpers_instance'
```

## 원인 분석
1. `HelpersWrapper`의 `_bind_override_methods()`가 `setattr()`를 사용
2. 하지만 `__getattr__()`가 `_helpers` 객체의 같은 이름 메서드를 먼저 찾아 반환
3. 결과적으로 `ai_helpers.utils.list_functions`가 사용되어 인자 오류 발생

## 영구적 해결 방법

### 1. 코드 수정 내용
`python/helpers_wrapper.py`의 두 부분을 수정:

#### _bind_override_methods() 수정
```python
def _bind_override_methods(self):
    """클래스에 정의된 메서드들을 명시적으로 바인딩"""
    override_methods = ['list_functions', 'workflow', 'read_file']
    for method_name in override_methods:
        if hasattr(self.__class__, method_name):
            method = getattr(self.__class__, method_name)
            if callable(method):
                # self.__dict__에 직접 설정 (최우선순위)
                self.__dict__[method_name] = method.__get__(self, self.__class__)
```

#### __getattr__() 수정
```python
def __getattr__(self, name: str) -> Any:
    """동적으로 helpers 메서드를 래핑"""
    # 안전장치: override 메서드 재확인
    override_methods = ['list_functions', 'workflow', 'read_file']
    if name in override_methods and hasattr(self.__class__, name):
        method = getattr(self.__class__, name)
        bound_method = method.__get__(self, self.__class__)
        # 캐시에 저장
        self.__dict__[name] = bound_method
        return bound_method
    # ... 기존 로직 계속
```

### 2. 핵심 원리
Python의 속성 접근 우선순위 활용:
1. `self.__dict__` (최우선)
2. `__getattribute__()`
3. `__getattr__()` (마지막)

`self.__dict__`에 직접 바인딩하여 `__getattr__()`보다 우선순위를 높임

## 테스트 결과
- ✅ `helpers.list_functions()` 인자 없이 호출 가능
- ✅ 새 인스턴스 생성 시에도 정상 작동
- ✅ 반복 호출 시 안정적
- ✅ 다른 override 메서드들도 정상 작동

## 영향 범위
- `list_functions()`
- `workflow()`  
- `read_file()`

세 메서드 모두 동일한 방식으로 개선됨

## 추가 개선 사항
향후 새로운 override 메서드 추가 시:
1. `override_methods` 리스트에 추가
2. `HelpersWrapper` 클래스에 메서드 구현
3. 자동으로 올바르게 바인딩됨

---
작성일: 2025-01-09
해결자: Claude with Human
테스트: 완료
