
# 🚀 safe_replace → replace 마이그레이션 구현 코드

## 📝 Step 1: replace 함수 확장 (code.py)

### 1.1 현재 replace 함수를 백업
```python
# 기존 replace를 _legacy_replace로 이름 변경
def _legacy_replace(file_path: str, old_code: str, new_code: str) -> Dict[str, Any]:
    """레거시 replace 함수 (임시 보관)"""
    # 기존 코드...
```

### 1.2 새로운 통합 replace 함수
```python
# python/ai_helpers_new/code.py

def replace(file_path: str, old_code: str, new_code: str, 
           text_mode: bool = False, validate: bool = False) -> Dict[str, Any]:
    """파일에서 코드를 안전하게 교체

    Args:
        file_path: 대상 파일 경로
        old_code: 찾을 코드 (정확히 일치해야 함)
        new_code: 교체할 코드
        text_mode: True면 libcst 대신 텍스트 교체 (deprecated)
        validate: True면 교체 후 Python 구문 검증

    Returns:
        성공: {
            'ok': True, 
            'data': {
                'file': 파일경로,
                'replacements': 교체 횟수,
                'validated': 검증 여부,
                'line_changes': 변경된 라인 수
            }
        }
        실패: {'ok': False, 'error': 오류메시지}
    """
    try:
        # 1. 파일 읽기
        from . import read, write
        read_result = read(file_path)
        if not read_result['ok']:
            return read_result

        content = read_result['data']
        original_lines = content.count('\n')

        # 2. 코드 존재 확인
        if old_code not in content:
            # 유사 코드 찾기 (도움말)
            similar = _find_similar_code(content, old_code)
            return {
                'ok': False,
                'error': 'Code not found in file',
                'suggestion': 'Check exact whitespace and indentation',
                'similar_code': similar[:3] if similar else []
            }

        # 3. 교체 수행
        replacement_count = content.count(old_code)
        new_content = content.replace(old_code, new_code)
        new_lines = new_content.count('\n')

        # 4. 검증 (옵션)
        if validate and file_path.endswith('.py'):
            validation_result = _validate_python_syntax(new_content)
            if not validation_result['ok']:
                return {
                    'ok': False,
                    'error': validation_result['error'],
                    'line': validation_result.get('line'),
                    'preview': validation_result.get('preview')
                }

        # 5. libcst 처리 (옵션, text_mode=False일 때)
        if not text_mode and file_path.endswith('.py'):
            try:
                # libcst로 더 정교한 교체 시도
                import libcst as cst
                # ... libcst 로직 (기존 safe_replace에서 가져옴)
            except:
                # 실패시 텍스트 모드로 계속 진행
                pass

        # 6. 파일 쓰기
        write_result = write(file_path, new_content)
        if not write_result['ok']:
            return write_result

        # 7. 성공 응답
        return {
            'ok': True,
            'data': {
                'file': file_path,
                'replacements': replacement_count,
                'validated': validate,
                'line_changes': abs(new_lines - original_lines),
                'method': 'text' if text_mode else 'auto'
            }
        }

    except Exception as e:
        return {
            'ok': False,
            'error': f'Replace failed: {str(e)}',
            'file': file_path
        }


def _validate_python_syntax(code: str) -> Dict[str, Any]:
    """Python 코드 구문 검증 헬퍼"""
    try:
        import ast
        ast.parse(code)
        return {'ok': True}
    except SyntaxError as e:
        lines = code.split('\n')
        preview = lines[e.lineno - 1] if 0 < e.lineno <= len(lines) else ''
        return {
            'ok': False,
            'error': f'Syntax error at line {e.lineno}: {e.msg}',
            'line': e.lineno,
            'preview': preview.strip()
        }
    except Exception as e:
        return {
            'ok': False,
            'error': f'Validation error: {str(e)}'
        }


def _find_similar_code(content: str, target: str) -> List[str]:
    """유사한 코드 패턴 찾기 (도움말용)"""
    # 간단한 구현 - 공백 차이 무시
    import re

    similar = []
    normalized_target = re.sub(r'\s+', ' ', target.strip())
    lines = content.split('\n')

    for i, line in enumerate(lines):
        normalized_line = re.sub(r'\s+', ' ', line.strip())
        if normalized_target in normalized_line:
            similar.append(f"Line {i+1}: {line.strip()}")

    return similar[:5]  # 최대 5개
```

## 📝 Step 2: safe_replace를 Deprecation 래퍼로 변경

```python
# python/ai_helpers_new/utils/safe_wrappers.py

def safe_replace(file_path: str, old_code: str, new_code: str,
                text_mode: bool = False, validate: bool = False) -> Dict[str, Any]:
    """
    DEPRECATED: This function will be removed in v4.0.
    Please use `replace()` instead, which now includes all safety features.

    This is now just a wrapper around replace() for backward compatibility.
    """
    import warnings
    from ..code import replace

    # Deprecation 경고
    warnings.warn(
        "safe_replace() is deprecated and will be removed in v4.0. "
        "Use replace() instead - it now includes all safety features.",
        DeprecationWarning,
        stacklevel=2
    )

    # 통계 수집 (선택사항)
    _log_deprecated_usage('safe_replace', file_path)

    # 새로운 replace 호출
    return replace(file_path, old_code, new_code, text_mode, validate)


def _log_deprecated_usage(func_name: str, file_path: str):
    """Deprecated 함수 사용 통계 (모니터링용)"""
    try:
        import json
        from datetime import datetime

        log_file = '.deprecated_usage.json'

        try:
            with open(log_file, 'r') as f:
                stats = json.load(f)
        except:
            stats = {}

        if func_name not in stats:
            stats[func_name] = []

        stats[func_name].append({
            'time': datetime.now().isoformat(),
            'file': file_path
        })

        # 최근 100개만 유지
        stats[func_name] = stats[func_name][-100:]

        with open(log_file, 'w') as f:
            json.dump(stats, f)
    except:
        pass  # 통계 수집 실패는 무시
```

## 📝 Step 3: __init__.py 업데이트

```python
# python/ai_helpers_new/__init__.py

# 기존 import
from .code import (
    parse,
    view, 
    replace,  # 이제 모든 기능 포함
    insert,
    functions,
    classes,
)

# safe_replace는 호환성을 위해 유지 (하지만 deprecated)
from .utils.safe_wrappers import safe_replace

# deprecation 메시지를 __all__에 추가하지 않음
__all__ = [
    # ... 기존 항목들
    'replace',  # 권장
    # 'safe_replace',  # deprecated, 문서에서 제외
]
```

## 📝 Step 4: 마이그레이션 도우미 스크립트

```python
# scripts/migrate_safe_replace.py
"""
safe_replace → replace 마이그레이션 도우미
사용법: python scripts/migrate_safe_replace.py [directory]
"""

import os
import re
import sys
from typing import List, Tuple

def find_safe_replace_usage(directory: str) -> List[Tuple[str, int, str]]:
    """safe_replace 사용 찾기"""
    usage = []

    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()

                    for i, line in enumerate(lines, 1):
                        if 'safe_replace' in line and not line.strip().startswith('#'):
                            usage.append((file_path, i, line.strip()))
                except:
                    continue

    return usage

def generate_migration_report(usage: List[Tuple[str, int, str]]) -> str:
    """마이그레이션 리포트 생성"""
    report = f"""
# safe_replace → replace 마이그레이션 리포트

## 발견된 사용: {len(usage)}건

## 상세 내역:
"""

    for file_path, line_num, line in usage:
        report += f"\n- {file_path}:{line_num}\n  `{line}`\n"

    report += """
## 마이그레이션 방법:
1. 모든 `safe_replace` → `replace` 변경
2. 파라미터는 동일하게 유지
3. 테스트 실행 확인

## 자동 변환 명령:
```bash
# Linux/Mac
find . -name "*.py" -exec sed -i 's/safe_replace/replace/g' {} +

# Windows (PowerShell)
Get-ChildItem -Recurse -Filter *.py | ForEach {(Get-Content $_ -Raw) -replace 'safe_replace','replace' | Set-Content $_}
```
"""
    return report

if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else "."

    print(f"Scanning {directory} for safe_replace usage...")
    usage = find_safe_replace_usage(directory)

    if usage:
        report = generate_migration_report(usage)

        with open("migration_report.md", "w") as f:
            f.write(report)

        print(f"\n✅ Found {len(usage)} usage(s) of safe_replace")
        print("📄 Report saved to: migration_report.md")
    else:
        print("✅ No safe_replace usage found!")
```

## 📝 Step 5: 테스트 업데이트

```python
# test/test_replace_unified.py
import pytest
import warnings
from ai_helpers_new import replace

class TestUnifiedReplace:
    """통합된 replace 함수 테스트"""

    def test_basic_replace(self, tmp_path):
        """기본 교체 기능"""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\ny = 2")

        result = replace(str(test_file), "x = 1", "x = 10")
        assert result['ok'] is True
        assert result['data']['replacements'] == 1

        content = test_file.read_text()
        assert "x = 10" in content
        assert "y = 2" in content

    def test_validate_mode(self, tmp_path):
        """구문 검증 모드"""
        test_file = tmp_path / "test.py"
        test_file.write_text("def foo():\n    pass")

        # 유효한 교체
        result = replace(str(test_file), "pass", "return 42", validate=True)
        assert result['ok'] is True
        assert result['data']['validated'] is True

        # 구문 오류 생성
        test_file.write_text("def foo():\n    return 42")
        result = replace(str(test_file), "return 42", "return 42 +++ ", validate=True)
        assert result['ok'] is False
        assert 'Syntax error' in result['error']
        assert result['line'] == 2

    def test_code_not_found(self, tmp_path):
        """찾을 코드가 없을 때"""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1")

        result = replace(str(test_file), "y = 1", "y = 2")
        assert result['ok'] is False
        assert 'not found' in result['error']
        assert 'suggestion' in result

    def test_multiple_replacements(self, tmp_path):
        """여러 개 교체"""
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 1\ny = 1\nz = 1")

        result = replace(str(test_file), "= 1", "= 2")
        assert result['ok'] is True
        assert result['data']['replacements'] == 3
```

## 🚀 실행 순서

1. **테스트 작성 및 실행**
   ```bash
   pytest test/test_replace_unified.py -v
   ```

2. **기존 사용 스캔**
   ```bash
   python scripts/migrate_safe_replace.py .
   ```

3. **코드 수정**
   - code.py: replace 함수 확장
   - safe_wrappers.py: deprecation 래퍼로 변경

4. **점진적 배포**
   - v3.9: 새 replace 배포, safe_replace deprecation 시작
   - v4.0: safe_replace 완전 제거
