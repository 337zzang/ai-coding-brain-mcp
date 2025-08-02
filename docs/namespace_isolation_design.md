# JSON REPL 네임스페이스 격리 상세 설계

## 🎯 목표
1. 전역 네임스페이스 오염 제거
2. 하위 호환성 100% 유지
3. 점진적 마이그레이션 지원
4. 성능 영향 최소화

## 🏗️ 아키텍처 설계

### Phase 0: 즉시 적용 (5-10줄 수정)

#### 1. LazyHelperProxy 클래스 추가
```python
import importlib
import warnings
import types
from functools import wraps

class LazyHelperProxy(types.ModuleType):
    """지연 로딩과 캐싱을 지원하는 헬퍼 프록시"""

    def __init__(self, name='helpers'):
        super().__init__(name)
        self._module = None
        self._warned = set()  # 경고 출력 추적

    def _load(self):
        if self._module is None:
            self._module = importlib.import_module('ai_helpers_new')

    def __getattr__(self, item):
        self._load()
        attr = getattr(self._module, item)
        setattr(self, item, attr)  # 캐싱
        return attr

    def __setattr__(self, name, value):
        # _로 시작하는 내부 속성만 설정 허용
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            raise AttributeError(f"Cannot override helper function '{name}'")
```

#### 2. load_helpers() 수정
```python
def load_helpers():
    """AI Helpers v2.0과 워크플로우 시스템 로드"""
    global helpers, HELPERS_AVAILABLE
    if HELPERS_AVAILABLE:
        return True

    try:
        # 프록시 객체 생성
        h = LazyHelperProxy('helpers')

        # 전역에는 h 객체만 등록
        globals()['h'] = h
        globals()['helpers'] = h

        # 레거시 호환성을 위한 스텁 함수들
        legacy_functions = [
            'read', 'write', 'append', 'exists', 'parse', 
            'search_files', 'git_status', 'git_commit'
        ]

        for func_name in legacy_functions:
            globals()[func_name] = create_legacy_stub(h, func_name)

        HELPERS_AVAILABLE = True
        return True
    except Exception as e:
        print(f"헬퍼 로드 실패: {e}")
        return False

def create_legacy_stub(h, func_name):
    """레거시 호환성을 위한 스텁 생성"""
    @wraps(getattr(h, func_name, None))
    def legacy_stub(*args, **kwargs):
        # 첫 호출 시에만 경고
        if func_name not in _legacy_warnings:
            _legacy_warnings.add(func_name)
            warnings.warn(
                f"Direct use of '{func_name}()' is deprecated. "
                f"Use 'h.{func_name}()' instead.",
                DeprecationWarning,
                stacklevel=2
            )
        return getattr(h, func_name)(*args, **kwargs)
    return legacy_stub

_legacy_warnings = set()  # 경고 추적
```

### Phase 1: 코드베이스 수정 (1-2주)

#### 마이그레이션 스크립트
```python
# migration_helper.py
import re
import os

def migrate_file(filepath):
    """파일 내 레거시 함수 호출을 h.* 형태로 변경"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 함수 호출 패턴 변경
    patterns = [
        (r'\b(read|write|append)\s*\(', r'h.\1('),
        (r'\b(parse|view|replace)\s*\(', r'h.\1('),
        (r'\b(search_files|search_code)\s*\(', r'h.\1('),
        (r'\b(git_status|git_commit|git_push)\s*\(', r'h.\1('),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    # 백업 후 저장
    backup_path = filepath + '.bak'
    os.rename(filepath, backup_path)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
```

### Phase 2: 완전 격리 (메이저 버전)

#### 최종 load_helpers()
```python
def load_helpers():
    """AI Helpers v2.0 로드 (격리된 버전)"""
    global HELPERS_AVAILABLE
    if HELPERS_AVAILABLE:
        return True

    try:
        # 오직 h 객체만 전역에 추가
        h = LazyHelperProxy('helpers')
        globals()['h'] = h

        HELPERS_AVAILABLE = True
        return True
    except Exception as e:
        print(f"헬퍼 로드 실패: {e}")
        return False
```

## 📊 영향 분석

### 성능
- LazyHelperProxy: 첫 호출 시 약간의 오버헤드 (< 1ms)
- 캐싱으로 이후 호출은 직접 호출과 동일
- 메모리 사용량 감소 (필요한 함수만 로드)

### 호환성
- Phase 0: 100% 하위 호환
- Phase 1: 경고 메시지 외 동작 동일
- Phase 2: 레거시 코드 수정 필요

### 보안
- 함수 덮어쓰기 방지 (__setattr__ 보호)
- 네임스페이스 충돌 제거
- 예측 가능한 동작 보장

## 🚀 실행 계획

### 즉시 (오늘)
1. LazyHelperProxy 클래스 구현
2. load_helpers() 수정
3. 기본 테스트 실행

### 1주차
1. 마이그레이션 스크립트 개발
2. 전체 코드베이스 스캔
3. 점진적 변환 시작

### 2주차
1. 테스트 커버리지 확인
2. 성능 벤치마크
3. 문서 업데이트

### 1개월 후
1. Phase 1 완료
2. 레거시 스텁 제거 준비
3. 사용자 공지

## ⚠️ 위험 관리

### 잠재적 문제
1. 동적 함수 호출 코드 (`eval`, `exec` 사용)
2. 외부 스크립트 의존성
3. 타입 힌트 호환성

### 대응 방안
1. 정적 분석 도구로 사용 패턴 파악
2. 단계적 배포와 롤백 계획
3. 상세한 마이그레이션 가이드 제공
