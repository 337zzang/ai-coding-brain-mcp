# Code.py - Parse/View 함수 상세 분석 보고서

**분석일**: 2025-08-09 21:41
**분석자**: Claude + O3 협업
**대상 파일**: `python/ai_helpers_new/code.py`

## 📋 요약

Parse/View 함수에서 **구조적 문제**와 **실제 버그**를 발견했습니다.

## 🔴 발견된 버그 (즉시 수정 필요)

### 1. View 함수 - Parse 실패 처리 버그

**위치**: View 함수 L13-16
```python
parsed = parse(filepath)
if isinstance(parsed, dict) and 'data' in parsed:
    parsed = parsed['data']

# 이후 parsed.get('functions', []) 접근
```

**문제점**:
- parse()가 실패하면 `{'ok': False, 'data': None}` 반환
- parsed['data']는 None이 됨
- None.get('functions', []) 시도 → **AttributeError 발생**

**테스트 결과**:
- 구문 오류 파일에서 실제 에러 확인
- `'NoneType' object has no attribute 'get'` 발생

**수정안**:
```python
parsed = parse(filepath)
if not parsed.get('ok'):
    return {'ok': False, 'error': f"Parse failed: {parsed.get('error')}"}
parsed = parsed['data']
```

### 2. get_type_repr 불필요한 복잡성

**위치**: Parse 함수 내부 (40+ 줄)

**문제점**:
- AST 노드를 수동으로 문자열 변환
- Python 3.9+ ast.unparse() 있는데도 수동 구현
- 모든 노드 타입을 다루지 못함

**수정안**:
```python
def get_type_repr(node):
    if node is None:
        return None
    try:
        return ast.unparse(node)  # Python 3.9+ 우선
    except (ImportError, AttributeError):
        # 3.8 이하 fallback
        return str(node)  # 또는 astor 사용
```

### 3. context_lines 하드코딩

**위치**: View 함수 L54
```python
context_lines = 10  # 고정값
```

**문제점**:
- 사용자가 컨텍스트 크기 조절 불가
- 재사용성 저하

**수정안**:
```python
def view(filepath, target=None, context_lines=10):
    # 파라미터로 받기
```

## 🟡 구조적 개선사항

### 1. 반환 타입 일관성
- Parse: `{'ok': bool, 'data': dict}` 
- View: `{'ok': bool, 'data': str}`
- 에러 처리 통일 필요

### 2. 데이터 구조화
```python
@dataclass
class FunctionInfo:
    name: str
    line: int
    returns: Optional[str]

@dataclass  
class ModuleInfo:
    path: str
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
```

### 3. 예외 처리
- 커스텀 예외 클래스 도입
- ParseError, ViewError 구분

## 📊 테스트 결과

| 테스트 케이스 | 결과 | 비고 |
|-------------|------|------|
| 정상 파일 parse | ✅ | 작동 |
| 정상 파일 view | ✅ | 작동 |
| 존재하지 않는 파일 | ✅ | 에러 처리 |
| **구문 오류 파일 parse** | ✅ | 에러 처리 |
| **구문 오류 파일 view** | ❌ | **AttributeError 발생** |

## 💡 O3 분석 핵심 제안

1. **ast.unparse() 전면 활용**
   - get_type_repr 90% 단순화 가능
   - Python 3.9+ 표준 기능 활용

2. **dataclass/TypedDict 도입**
   - 타입 안정성 향상
   - IDE 자동완성 지원

3. **표준 응답 형식**
   ```json
   {
     "status": "ok",
     "data": {...}
   }
   ```

4. **파라미터화**
   - context_lines → 파라미터
   - 유연한 사용 가능

## 🎯 권장 조치 순서

1. **긴급**: View 함수 parse 실패 처리 수정
2. **중요**: get_type_repr ast.unparse() 활용
3. **개선**: context_lines 파라미터화
4. **장기**: dataclass 구조 도입

## 📁 관련 파일

- 원본: `python/ai_helpers_new/code.py`
- 백업: `backups/code_py_backup_20250809_212546.py`
- O3 분석: 4,000+ 문자 상세 분석 완료

---
*이 보고서는 실제 테스트와 O3 AI 분석을 기반으로 작성되었습니다.*
