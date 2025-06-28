"""
정규표현식 패턴 모음
execute_code 환경에서 다중 파싱 문제를 피하기 위해 별도 파일로 관리합니다.
"""
import re

# 기본 패턴들
NAME_PATTERN = r'name\s*=\s*["'"]([^"'"]+)["'"]'
EMAIL_PATTERN = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
URL_PATTERN = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b'
PHONE_PATTERN = r'\+?1?\d{9,15}'

# Python 코드 분석 패턴
IMPORT_PATTERN = r'^\s*(?:from\s+([\w.]+)\s+)?import\s+(.+)$'
FUNCTION_PATTERN = r'^\s*def\s+(\w+)\s*\([^)]*\)\s*:'
CLASS_PATTERN = r'^\s*class\s+(\w+)\s*(?:\([^)]*\))?\s*:'
DECORATOR_PATTERN = r'^\s*@(\w+(?:\.\w+)*)(?:\([^)]*\))?\s*$'

# TypeScript/JavaScript 패턴
TS_IMPORT_PATTERN = r'^\s*import\s+(?:{[^}]+}|\*\s+as\s+\w+|\w+)\s+from\s+["']([^"']+)["']'
TS_EXPORT_PATTERN = r'^\s*export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)'
CONSOLE_PATTERN = r'\bconsole\.(log|error|warn|info|debug)\s*\('

# 파일 경로 패턴
WINDOWS_PATH_PATTERN = r'[A-Za-z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*'
UNIX_PATH_PATTERN = r'/(?:[^/\0]+/)*[^/\0]*'
RELATIVE_PATH_PATTERN = r'\.{1,2}/(?:[^/\0]+/)*[^/\0]*'

# Git 패턴
GIT_BRANCH_PATTERN = r'^(?:feature|bugfix|hotfix|release)/[\w-]+$'
GIT_COMMIT_PATTERN = r'^(?:feat|fix|docs|style|refactor|test|chore)(?:\([\w-]+\))?:\s+.+'

# 컴파일된 정규식 객체들 (성능 향상)
COMPILED_PATTERNS = {
    'name': re.compile(NAME_PATTERN),
    'email': re.compile(EMAIL_PATTERN),
    'url': re.compile(URL_PATTERN),
    'import': re.compile(IMPORT_PATTERN, re.MULTILINE),
    'function': re.compile(FUNCTION_PATTERN, re.MULTILINE),
    'class': re.compile(CLASS_PATTERN, re.MULTILINE),
    'console': re.compile(CONSOLE_PATTERN),
}

def test_pattern(pattern_name: str, text: str) -> list:
    """패턴 테스트 헬퍼 함수"""
    if pattern_name in COMPILED_PATTERNS:
        return COMPILED_PATTERNS[pattern_name].findall(text)
    else:
        raise ValueError(f"Unknown pattern: {pattern_name}")

def validate_pattern(pattern: str) -> dict:
    """정규식 패턴 검증"""
    try:
        compiled = re.compile(pattern)
        return {
            'valid': True,
            'pattern': pattern,
            'groups': compiled.groups,
            'flags': compiled.flags
        }
    except re.error as e:
        return {
            'valid': False,
            'error': str(e),
            'pattern': pattern
        }

# 패턴 검증 예시
if __name__ == "__main__":
    # 각 패턴의 백슬래시 개수 확인
    print("Pattern validation:")
    for name, pattern in globals().items():
        if name.endswith('_PATTERN') and isinstance(pattern, str):
            print(f"{name}: {pattern.count('\\\\')//2} backslashes")
