# 📊 파일 수정 헬퍼 함수 종합 개선안

## 🎯 요약
파일 수정 헬퍼 함수들의 들여쓰기 및 문법 오류 문제를 해결하기 위한 종합 개선안입니다.

## 🔍 현재 상태 분석

### 1. 기존 함수들의 테스트 결과
- **h.replace()**: 단순 텍스트 교체, 들여쓰기 포함 시 정확한 매칭 필요
- **h.safe_replace()**: AST/텍스트 모드 자동 선택, libcst 의존
- **h.insert()**: 라인 단위 삽입
- **Desktop Commander edit_block**: 가장 안정적, diff 기반

### 2. 테스트 결과
✅ **성공 케이스**:
- 간단한 문자열 교체
- 정확한 들여쓰기가 포함된 블록 교체
- Desktop Commander의 edit_block

❌ **문제 케이스**:
- 들여쓰기가 일치하지 않을 때
- 탭/스페이스 혼용
- 부분적인 블록 수정

## 🚀 개선 방안

### 1. 계층적 API 설계
```python
# 제안하는 3계층 구조
class FileEditManager:
    def __init__(self):
        self.text_engine = TextEngine()     # 단순 텍스트
        self.cst_engine = CSTEngine()       # libcst 기반
        self.patch_engine = PatchEngine()   # diff/patch 기반
```

### 2. 들여쓰기 보존 전략

#### A. 정규식 기반 (TextEngine)
```python
def replace_with_indent(content, pattern, replacement):
    # 들여쓰기 캡처 그룹 사용
    import re
    indent_pattern = r'^([ \t]*)'

    # 각 라인의 들여쓰기 보존
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if pattern in line:
            indent = re.match(indent_pattern, line).group(1)
            lines[i] = indent + replacement
    return '\n'.join(lines)
```

#### B. CST 기반 (CSTEngine) 
```python
def safe_cst_replace(file_path, selector, transformer):
    import libcst as cst

    # 파일의 기존 포맷 설정 감지
    with open(file_path) as f:
        content = f.read()

    # 들여쓰기 스타일 감지
    config = detect_indent_config(content)

    # CST 파싱 및 변환
    module = cst.parse_module(content, config=config)
    modified = module.visit(transformer)

    return modified.code
```

#### C. Diff/Patch 기반 (PatchEngine) - 가장 안전
```python
def edit_block_improved(file_path, old_block, new_block):
    # Desktop Commander 스타일
    # 1. 정확한 매칭 찾기
    # 2. diff 생성
    # 3. patch 적용
    # 들여쓰기는 자동 보존됨
```

### 3. 실용적 구현 제안

#### A. 즉시 적용 가능한 개선
```python
def smart_replace(file_path, old, new, mode='auto'):
    """
    개선된 replace 함수
    - mode: 'text', 'ast', 'patch', 'auto'
    """
    if mode == 'auto':
        # 파일 타입과 패턴 분석으로 모드 자동 선택
        if file_path.endswith('.py'):
            if '\n' in old:  # 멀티라인
                mode = 'patch'
            elif old.isidentifier():  # 식별자
                mode = 'ast'
            else:
                mode = 'text'

    if mode == 'patch':
        # edit_block 스타일 사용
        return edit_block(file_path, old, new)
    elif mode == 'ast':
        # libcst 사용
        return safe_cst_replace(file_path, old, new)
    else:
        # 기본 텍스트 교체
        return simple_replace(file_path, old, new)
```

#### B. 들여쓰기 감지 유틸리티
```python
def detect_indent_style(content):
    """파일의 들여쓰기 스타일 감지"""
    import re

    # 탭 vs 스페이스 카운트
    tabs = len(re.findall(r'^\t+', content, re.MULTILINE))
    spaces = len(re.findall(r'^ +', content, re.MULTILINE))

    # 스페이스 너비 감지 (2, 4, 8)
    space_widths = re.findall(r'^( +)', content, re.MULTILINE)
    if space_widths:
        width_counts = {}
        for spaces in space_widths:
            width = len(spaces)
            if width in [2, 4, 8]:
                width_counts[width] = width_counts.get(width, 0) + 1

        if width_counts:
            dominant_width = max(width_counts, key=width_counts.get)
        else:
            dominant_width = 4
    else:
        dominant_width = 4

    return {
        'use_tabs': tabs > spaces,
        'tab_width': dominant_width,
        'dominant': '\t' if tabs > spaces else ' ' * dominant_width
    }
```

### 4. 특수 케이스 처리

#### A. 클래스 메서드 전체 교체
```python
def replace_method(file_path, class_name, method_name, new_method_code):
    """CST 기반 메서드 교체"""
    import libcst as cst

    class MethodReplacer(cst.CSTTransformer):
        def leave_FunctionDef(self, original, updated):
            if updated.name.value == method_name:
                # 새 메서드로 교체
                return cst.parse_statement(new_method_code)
            return updated

    # 적용...
```

#### B. 블록 내부 코드 수정
```python
def modify_block_content(file_path, block_type, block_name, modifier_fn):
    """
    if/for/while/try 블록 내부 수정
    """
    # CST로 블록 찾기
    # modifier_fn으로 내용 수정
    # 들여쓰기 자동 보존
```

### 5. 최종 권장사항

1. **Desktop Commander의 edit_block을 주력으로 사용**
   - 가장 안정적
   - 들여쓰기 문제 없음
   - diff 기반으로 직관적

2. **h.replace는 단순 케이스에만 사용**
   - 한 줄 교체
   - 정확한 매칭이 가능한 경우

3. **복잡한 리팩토링은 CST 활용**
   - libcst 기반 safe_replace 개선
   - 메서드/클래스 단위 교체

4. **들여쓰기 감지 로직 추가**
   - 파일별 스타일 자동 감지
   - 교체 시 스타일 보존

## 📋 구현 우선순위

1. **즉시**: Desktop Commander edit_block 적극 활용
2. **단기**: detect_indent_style() 유틸리티 추가
3. **중기**: smart_replace() 통합 함수 구현
4. **장기**: 완전한 CST 기반 리팩토링 도구

## 🔧 실전 팁

1. **교체 전 항상 백업**
```python
shutil.copy2(file_path, f"{file_path}.backup")
```

2. **교체 후 항상 검증**
```python
# AST 파싱으로 구문 검증
ast.parse(new_content)
compile(new_content, file_path, 'exec')
```

3. **diff 미리보기 제공**
```python
diff = difflib.unified_diff(old_lines, new_lines)
print(''.join(diff))
```

4. **정확한 패턴 매칭**
- 멀티라인 패턴은 들여쓰기까지 정확히 포함
- 가능하면 unique한 패턴 사용
- 컨텍스트 라인 포함하여 매칭

## 💡 결론

현재 가장 실용적인 접근:
1. **Desktop Commander의 edit_block 사용** (즉시 사용 가능)
2. **정확한 패턴 매칭**으로 h.replace 사용
3. 복잡한 케이스는 **수동 편집** 후 검증

향후 개선 방향:
- smart_replace() 구현으로 모든 케이스 커버
- CST 기반 도구 강화
- 들여쓰기 자동 감지 및 보존
