
# 🛠️ Phase 3 실용적 구현 계획

## 📌 구현 전략
기존 API를 100% 유지하면서 opt-in 방식으로 AST 기반 정확성 추가

## 📁 변경 파일 (최소화)
1. `python/ai_helpers_new/search.py` - find_function/find_class에 strict 모드
2. `python/ai_helpers_new/utils/safe_wrappers.py` - safe_replace에 validate 추가

## 🚀 구체적 구현 코드

### 1. search.py 수정 (find_function)
```python
def find_function(name: str, path: str = ".", strict: bool = False) -> Dict[str, Any]:
    """Python 파일에서 함수 정의 찾기

    Args:
        name: 함수명
        path: 검색 경로
        strict: True시 AST 기반 정확한 검색 (느리지만 정확)
    """
    if strict:
        try:
            # AST 기반 검색
            return _find_function_ast(name, path)
        except Exception as e:
            logger.warning(f"AST search failed, falling back to regex: {e}")
            # 자동 폴백

    # 기존 정규식 로직 (변경 없음)
    return _find_function_regex(name, path)

def _find_function_ast(name: str, path: str) -> Dict[str, Any]:
    """AST 기반 함수 검색 (새로 추가)"""
    import ast
    results = []

    # 모든 .py 파일 검색
    py_files = search_files("*.py", path)['data']

    for file_path in py_files[:100]:  # 성능을 위해 제한
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content)

            # AST에서 함수 찾기
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == name:
                    results.append({
                        'file': file_path,
                        'line': node.lineno,
                        'definition': ast.get_source_segment(content, node)
                    })
        except:
            continue

    return {
        'ok': True,
        'data': results,
        'count': len(results),
        'function_name': name
    }
```

### 2. safe_wrappers.py 수정 (safe_replace)
```python
def safe_replace(file_path: str, old_code: str, new_code: str, 
                text_mode: bool = False, validate: bool = False) -> Dict[str, Any]:
    """안전한 코드 교체 with 선택적 AST 검증

    Args:
        validate: True시 수정 후 AST 파싱으로 구문 검증
    """
    try:
        # 파일 읽기
        content = read_file(file_path)

        # 교체 수행
        if text_mode:
            # 기존 텍스트 모드
            new_content = content.replace(old_code, new_code)
        else:
            # 기존 AST 모드 (libcst)
            new_content = _ast_replace(content, old_code, new_code)

        # 새로운 기능: 수정 후 검증
        if validate:
            try:
                import ast
                ast.parse(new_content)
            except SyntaxError as e:
                return {
                    'ok': False,
                    'error': f'수정 후 구문 오류: {e}',
                    'line': e.lineno,
                    'text': e.text
                }

        # 파일 쓰기
        write_file(file_path, new_content)

        return {
            'ok': True,
            'data': {
                'lines_changed': old_code.count('\n'),
                'validated': validate
            }
        }
    except Exception as e:
        return {
            'ok': False,
            'error': str(e)
        }
```

## ⏱️ 구현 일정

### Day 1: 기본 구현 (2시간)
- [ ] find_function에 strict 모드 추가
- [ ] _find_function_ast 헬퍼 구현
- [ ] safe_replace에 validate 추가
- [ ] 기본 테스트

### Day 2: 완성 및 테스트 (2시간)
- [ ] find_class에도 strict 모드 추가
- [ ] 엣지 케이스 처리
- [ ] 성능 측정
- [ ] 문서 업데이트

## 📊 사용 예시

### 1. 정확한 함수 찾기
```python
# 주석이나 문자열 내부의 함수명은 무시
results = h.find_function("process_data", strict=True)
```

### 2. 안전한 코드 수정
```python
# 수정 후 구문 오류 방지
result = h.safe_replace(
    "module.py",
    "def old():\n    pass",
    "def new():\n    return None",
    validate=True
)
```

## 🎯 성공 지표

1. **호환성**: 기존 코드 변경 없이 작동 ✅
2. **성능**: strict=False시 기존과 동일 ✅
3. **정확성**: strict=True시 주석/문자열 무시 ✅
4. **안전성**: validate=True시 구문 오류 방지 ✅

## 🔄 향후 계획: safe_replace → replace 통합

### Phase 1: 기능 통합 (1주차)
```python
# code.py의 replace 함수 확장
def replace(file_path, old_code, new_code, 
           text_mode=False, validate=False):
    # safe_replace의 모든 기능 포함
```

### Phase 2: Deprecation (2-4주차)
```python
# safe_wrappers.py
def safe_replace(...):
    warnings.warn(
        "safe_replace is deprecated. Use replace() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return replace(...)
```

### Phase 3: 제거 (2개월 후)
- safe_replace 완전 제거
- 마이그레이션 도구 제공

## 💡 장점

1. **즉시 사용 가능**: 기존 코드 수정 불필요
2. **점진적 도입**: 필요한 곳에만 적용
3. **자동 폴백**: 실패해도 정규식으로 동작
4. **명확한 로드맵**: 장기적 API 개선 방향

이것이 가장 실용적이고 안전한 Phase 3 구현 방법입니다!
