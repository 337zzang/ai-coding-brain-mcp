
# 🔄 safe_replace → replace 마이그레이션 계획

## 📌 목표
safe_replace의 모든 기능을 replace로 통합하여 API 단순화

## 📅 타임라인

### Week 1: 기능 통합
```python
# python/ai_helpers_new/code.py
def replace(file_path: str, old_code: str, new_code: str,
           text_mode: bool = False, validate: bool = False) -> Dict[str, Any]:
    """통합된 코드 교체 함수 (safe_replace 기능 포함)

    Args:
        file_path: 대상 파일
        old_code: 교체할 코드
        new_code: 새 코드
        text_mode: True시 단순 텍스트 교체 (기본값: False = AST 사용)
        validate: True시 수정 후 구문 검증 (기본값: False)

    Returns:
        성공: {'ok': True, 'data': {...}}
        실패: {'ok': False, 'error': str, ...}
    """
    # 1. validate 옵션 처리
    if validate:
        # 먼저 시뮬레이션
        content = read(file_path)['data']
        if text_mode:
            test_content = content.replace(old_code, new_code)
        else:
            # AST 기반 교체 시뮬레이션
            test_content = _simulate_ast_replace(content, old_code, new_code)

        try:
            import ast
            ast.parse(test_content)
        except SyntaxError as e:
            return {
                'ok': False,
                'error': f'구문 오류 예상: {e}',
                'line': e.lineno
            }

    # 2. 실제 교체 (기존 로직)
    if text_mode:
        # 단순 텍스트 교체
        return _text_replace(file_path, old_code, new_code)
    else:
        # AST 기반 교체 (libcst)
        return _ast_replace(file_path, old_code, new_code)
```

### Week 2-4: Deprecation 단계
```python
# python/ai_helpers_new/utils/safe_wrappers.py
import warnings

def safe_replace(file_path: str, old_code: str, new_code: str,
                text_mode: bool = False, validate: bool = False) -> Dict[str, Any]:
    """[DEPRECATED] replace() 함수를 사용하세요.

    이 함수는 v3.0에서 제거될 예정입니다.
    """
    warnings.warn(
        "safe_replace는 deprecated되었습니다. "
        "대신 replace(file_path, old_code, new_code, validate=True)를 사용하세요.\n"
        "마이그레이션 가이드: https://docs.../migration",
        DeprecationWarning,
        stacklevel=2
    )

    # replace로 단순 위임
    from ..code import replace
    return replace(file_path, old_code, new_code, 
                  text_mode=text_mode, validate=validate)
```

### Month 2: 완전 제거
- safe_replace 함수 제거
- import 정리
- 문서 업데이트

## 🛠️ 마이그레이션 도구

### 1. 자동 탐지 스크립트
```python
# scripts/find_safe_replace_usage.py
import ast
import os
from pathlib import Path

def find_safe_replace_usage(directory):
    """safe_replace 사용 찾기"""
    usages = []

    for py_file in Path(directory).rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                # 함수 호출 찾기
                if isinstance(node, ast.Call):
                    # safe_replace 호출 확인
                    if (isinstance(node.func, ast.Attribute) and 
                        node.func.attr == 'safe_replace'):
                        usages.append({
                            'file': str(py_file),
                            'line': node.lineno,
                            'code': ast.get_source_segment(content, node)
                        })
                    elif (isinstance(node.func, ast.Name) and 
                          node.func.id == 'safe_replace'):
                        usages.append({
                            'file': str(py_file),
                            'line': node.lineno,
                            'code': ast.get_source_segment(content, node)
                        })
        except:
            continue

    return usages

# 사용법
if __name__ == "__main__":
    usages = find_safe_replace_usage(".")
    print(f"Found {len(usages)} safe_replace usages:")
    for usage in usages:
        print(f"  {usage['file']}:{usage['line']}")
```

### 2. 자동 변환 스크립트
```python
# scripts/migrate_safe_replace.py
def migrate_safe_replace(file_path):
    """safe_replace를 replace로 자동 변환"""
    with open(file_path, 'r') as f:
        content = f.read()

    # 패턴 1: h.safe_replace → h.replace
    content = content.replace('h.safe_replace', 'h.replace')

    # 패턴 2: from ... import safe_replace
    content = content.replace(
        'from ai_helpers_new.utils.safe_wrappers import safe_replace',
        'from ai_helpers_new.code import replace'
    )
    content = content.replace('safe_replace(', 'replace(')

    # 백업 생성
    backup_path = file_path + '.backup'
    with open(backup_path, 'w') as f:
        f.write(content)

    # 원본 파일 업데이트
    with open(file_path, 'w') as f:
        f.write(content)

    print(f"✅ Migrated {file_path}")
    print(f"   Backup: {backup_path}")
```

## 📊 마이그레이션 체크리스트

### Pre-migration
- [ ] replace 함수에 validate 기능 추가
- [ ] replace 함수 테스트 작성
- [ ] 성능 벤치마크

### During migration
- [ ] Deprecation warning 추가
- [ ] 마이그레이션 가이드 작성
- [ ] 자동 변환 도구 제공
- [ ] 사용자 공지

### Post-migration
- [ ] safe_replace 제거
- [ ] import 정리
- [ ] 문서 업데이트
- [ ] 릴리스 노트 작성

## 📈 예상 효과

### Before (현재)
```python
from ai_helpers_new import replace, safe_replace

# 혼란: 어떤 함수를 써야 할까?
replace("file.py", "old", "new")  # 기본?
safe_replace("file.py", "old", "new", validate=True)  # 안전?
```

### After (마이그레이션 후)
```python
from ai_helpers_new import replace

# 명확: 하나의 함수, 필요한 옵션 선택
replace("file.py", "old", "new")  # 기본
replace("file.py", "old", "new", validate=True)  # 안전
replace("file.py", "old", "new", text_mode=True)  # 빠름
```

## ⚠️ 주의사항

1. **호환성 보장**
   - 최소 1개월 deprecation 기간
   - 명확한 마이그레이션 경로
   - 자동 변환 도구 제공

2. **성능 영향 최소화**
   - validate=False가 기본값
   - 기존 동작 변경 없음

3. **문서화**
   - 변경 이유 설명
   - 구체적인 예시 제공
   - FAQ 준비

## 🎯 최종 목표
- **API 단순화**: 2개 → 1개 함수
- **일관성**: 하나의 명확한 인터페이스
- **확장성**: 향후 기능 추가 용이
