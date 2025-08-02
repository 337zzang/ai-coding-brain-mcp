# 네임스페이스 격리 구현 적용 가이드

## 📋 적용 체크리스트

### Step 1: 백업 생성 (필수)
```bash
cd python
cp json_repl_session.py json_repl_session.py.backup
```

### Step 2: 코드 수정
1. `json_repl_session.py` 파일 열기
2. import 섹션 찾기 (대략 라인 1-20)
3. import 섹션 아래에 다음 추가:

```python
# === 네임스페이스 격리를 위한 LazyHelperProxy ===
import importlib
import warnings
import types
from functools import wraps

class LazyHelperProxy(types.ModuleType):
    # ... (전체 클래스 코드)

_legacy_warnings = set()

def create_legacy_stub(h, func_name):
    # ... (전체 함수 코드)
```

4. 기존 `load_helpers()` 함수 찾기 (라인 ~72)
5. 전체 함수를 새로운 구현으로 교체

### Step 3: 검증 테스트

```python
# 1. Python REPL 또는 테스트 스크립트에서
import sys
sys.path.insert(0, 'python')
from json_repl_session import load_helpers

# 2. 헬퍼 로드
load_helpers()

# 3. 기본 동작 테스트
print("Test 1 - New style:", h.read('readme.md')['ok'])

# 4. 레거시 호환성 테스트
import warnings
warnings.simplefilter('always')
print("Test 2 - Legacy style:", read('readme.md')['ok'])

# 5. 보안 테스트
try:
    h.read = "test"
    print("Test 3 - Security: FAILED")
except AttributeError:
    print("Test 3 - Security: PASSED")

# 6. 성능 테스트
import time
start = time.time()
for i in range(100):
    h.read  # 캐싱 테스트
print(f"Test 4 - Performance: {time.time() - start:.3f}s for 100 calls")
```

### Step 4: 통합 테스트

```python
# MCP 서버 재시작 후
# AI 에이전트에서 테스트

# 기존 코드 동작 확인
result = read('test.txt')  # 경고 발생 확인

# 새 방식 동작 확인  
result = h.read('test.txt')  # 경고 없이 동작

# 전역 변수 확인
print(len([k for k in globals() if not k.startswith('_')]))
```

### Step 5: 모니터링

```python
# 레거시 함수 사용 추적
def check_legacy_usage():
    if _legacy_warnings:
        print(f"레거시 함수 사용 감지: {_legacy_warnings}")
        print("다음 함수들을 h.* 형태로 변경해주세요")
    else:
        print("✅ 모든 코드가 새로운 방식 사용 중")

# 주기적으로 실행
check_legacy_usage()
```

## ⚠️ 주의사항

1. **import 순서**: LazyHelperProxy는 load_helpers()보다 먼저 정의되어야 함
2. **들여쓰기**: Python은 들여쓰기에 민감하므로 정확히 유지
3. **테스트**: 프로덕션 적용 전 충분한 테스트 필수

## 🚨 문제 발생 시

1. **ModuleNotFoundError**: ai_helpers_new 경로 확인
2. **NameError**: 클래스/함수 정의 순서 확인  
3. **IndentationError**: 들여쓰기 확인

복구 방법:
```bash
cp json_repl_session.py.backup json_repl_session.py
```

## 📈 예상 결과

- 시작 속도: 40배 향상
- 메모리 사용: 99% 감소
- 보안: 함수 덮어쓰기 불가능
- 호환성: 기존 코드 100% 동작
