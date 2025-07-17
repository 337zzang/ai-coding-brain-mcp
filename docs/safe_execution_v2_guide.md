# Enhanced Safe Execution v2 통합 가이드

## 📋 개요

Enhanced Safe Execution v2는 f-string과 정규식의 런타임 오류를 실행 전에 차단하는 고급 검사 시스템입니다.

## 🚀 주요 기능

### 1. f-string 안전성 검사
- AST 기반 미정의 변수 감지
- 포맷 오류 사전 검출
- 실행 전 경고 제공

### 2. 정규식 안전성 검사
- 컴파일 오류 즉시 감지
- ReDoS (Catastrophic Backtracking) 패턴 탐지
- 성능 위험 경고

### 3. 통합 분석
- 코드 실행 전 정적 분석
- 경고와 함께 실행 가능
- 심각한 오류 시 실행 차단

## 🔧 MCP 통합 방법

### 1. json_repl_session.py 수정

```python
# 기존 import에 추가
try:
    from safe_execution_v2 import safe_exec
    SAFE_EXEC_V2_AVAILABLE = True
except ImportError:
    SAFE_EXEC_V2_AVAILABLE = False

# execute 함수 수정
def execute(code, mode='exec'):
    """코드 실행"""
    # 옵션 1: safe_execution_v2 우선 사용
    if SAFE_EXEC_V2_AVAILABLE and CONFIG.get('use_safe_exec_v2', True):
        success, output = safe_exec(code, repl_globals)
        if not success:
            return {'success': False, 'error': output}
        return {'success': True, 'stdout': output}

    # 옵션 2: 기존 방식 폴백
    # ... 기존 코드 ...
```

### 2. 설정 옵션 추가

```python
CONFIG = {
    'use_safe_exec_v2': True,  # Enhanced Safe Execution 사용
    'fstring_check': True,     # f-string 검사 활성화
    'regex_check': True,       # 정규식 검사 활성화
    'redos_protection': True,  # ReDoS 보호 활성화
}
```

### 3. UI 통합 (tool-definitions.ts)

```typescript
{
    name: 'execute_code',
    description: `...

🛡️ **안전성 검사 기능**
- f-string 미정의 변수 감지
- 정규식 컴파일 오류 사전 차단
- ReDoS 패턴 경고
- 실행 전 정적 분석

⚠️ 경고가 있어도 실행은 계속되지만, 
   오류가 있으면 실행이 차단됩니다.
    `
}
```

## 📊 사용 예시

### 기본 사용

```python
from safe_execution_v2 import safe_exec

# 안전한 실행
success, output = safe_exec("""
name = "Alice"
age = 30
print(f"Hello {name}, you are {age} years old")
""")
```

### 정규식 검사

```python
from safe_execution_v2 import check_regex

# 패턴 검사
result = check_regex(r"(a+)+")
# {'valid': True, 'warnings': ['Nested quantifiers (ReDoS risk)']}
```

### 성능 벤치마크

```python
from safe_execution_v2 import benchmark_regex_safety

# ReDoS 위험 테스트
result = benchmark_regex_safety(r"(x+)*y")
if result.get('timeout_risk'):
    print("⛔ 이 패턴은 위험합니다!")
```

## ⚡ 성능 고려사항

- AST 파싱 오버헤드: ~1-2ms
- 정규식 분석: ~0.5ms per pattern
- 전체 오버헤드: 일반적으로 3ms 미만

## 🔍 디버깅

문제 발생 시 다음을 확인하세요:

1. `safe_execution_v2.py`가 python 디렉토리에 있는지
2. AST 모듈이 정상 작동하는지
3. 로그에서 상세 오류 메시지 확인

## 📝 라이선스

MIT License - AI Coding Brain MCP 프로젝트의 일부
