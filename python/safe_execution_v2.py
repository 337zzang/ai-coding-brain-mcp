"""
Enhanced Safe Execution v2 - Final Version
f-string과 정규식의 런타임 오류를 사전에 차단하는 고급 검사 시스템
"""

import ast
import re
import time
from typing import Tuple, List, Set, Dict, Any
from textwrap import dedent

class SafeExecutionAnalyzer(ast.NodeVisitor):
    """코드 안전성 분석기"""

    def __init__(self, globals_dict: dict):
        self.globals_dict = globals_dict
        self.defined_names = set(globals_dict.keys())
        self.fstring_issues = []
        self.regex_issues = []
        self.imports = set()

        # 변수와 패턴 저장
        self.variables = {}  # 변수명 -> 값
        self.regex_patterns = []  # 발견된 정규식 패턴들

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname or alias.name
            self.imports.add(alias.name)
            self.defined_names.add(name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            name = alias.asname or alias.name
            self.defined_names.add(name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.defined_names.add(node.name)
        # 함수 파라미터 추가
        for arg in node.args.args:
            self.defined_names.add(arg.arg)
        self.generic_visit(node)

    def visit_Assign(self, node):
        # 변수 할당 추적
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.defined_names.add(target.id)

                # 정규식 패턴 문자열 저장
                if isinstance(node.value, (ast.Constant, ast.Str)):
                    value = node.value.value if isinstance(node.value, ast.Constant) else node.value.s
                    if isinstance(value, str) and target.id.endswith('pattern'):
                        self.variables[target.id] = value

        self.generic_visit(node)

    def visit_For(self, node):
        if isinstance(node.target, ast.Name):
            self.defined_names.add(node.target.id)
        self.generic_visit(node)

    def visit_JoinedStr(self, node):
        """f-string 검사"""
        for value in node.values:
            if isinstance(value, ast.FormattedValue):
                self._check_fstring_value(value, node.lineno, node.col_offset)
        self.generic_visit(node)

    def _check_fstring_value(self, node, line, col):
        """f-string 내부 값 검사"""
        # 사용된 이름 추출
        names = set()

        class NameCollector(ast.NodeVisitor):
            def visit_Name(self, n):
                names.add(n.id)

        collector = NameCollector()
        collector.visit(node.value)

        # 미정의 변수 체크
        for name in names:
            if (name not in self.defined_names and
                name not in dir(__builtins__)):
                self.fstring_issues.append({
                    'name': name,
                    'line': line,
                    'col': col
                })

    def visit_Call(self, node):
        """함수 호출 분석"""
        # re.compile() 등의 호출 감지
        if isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name) and
                node.func.value.id == 're' and
                node.func.attr in ['compile', 'search', 'match', 'findall', 'sub']):

                # 첫 번째 인자 확인
                if node.args:
                    pattern = None
                    line = node.lineno

                    # 직접 문자열
                    if isinstance(node.args[0], (ast.Constant, ast.Str)):
                        pattern = node.args[0].value if isinstance(node.args[0], ast.Constant) else node.args[0].s
                    # 변수 참조
                    elif isinstance(node.args[0], ast.Name):
                        var_name = node.args[0].id
                        if var_name in self.variables:
                            pattern = self.variables[var_name]

                    if pattern:
                        self.regex_patterns.append({
                            'pattern': pattern,
                            'function': node.func.attr,
                            'line': line
                        })

                        # 즉시 분석
                        analysis = analyze_regex_pattern(pattern)
                        if not analysis['valid']:
                            self.regex_issues.append({
                                'type': 'error',
                                'message': analysis['errors'][0],
                                'line': line
                            })
                        elif analysis['warnings']:
                            for warning in analysis['warnings']:
                                self.regex_issues.append({
                                    'type': 'warning',
                                    'message': warning,
                                    'line': line
                                })

        self.generic_visit(node)

def analyze_regex_pattern(pattern: str) -> dict:
    """정규식 패턴 분석"""
    result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }

    # 컴파일 테스트
    try:
        re.compile(pattern)
    except re.error as e:
        result['valid'] = False
        result['errors'].append(f"Invalid regex: {e.msg}")
        return result

    # ReDoS 패턴 검사
    dangerous_patterns = [
        (r'\([^)]*[*+]\)[*+]', 'Nested quantifiers (ReDoS risk)'),
        (r'\([^)]*\|[^)]*\)[*+]', 'Alternation with quantifier (ReDoS risk)'),
        (r'(\\w|\\d|\\s|\.)\+\*', 'Overlapping quantifiers'),
        (r'(.*)\+', 'Greedy capture with quantifier'),
    ]

    for regex, desc in dangerous_patterns:
        if re.search(regex, pattern):
            result['warnings'].append(desc)

    # 복잡도 체크
    if pattern.count('(') > 5:
        result['warnings'].append(f"High complexity: {pattern.count('(')} groups")

    return result

def enhanced_safe_exec_v2(code: str, globals_dict: dict) -> Tuple[bool, str]:
    """
    향상된 안전한 실행 시스템 v2

    Returns:
        (성공 여부, 메시지/출력)
    """
    # 1. 코드 정리
    code = dedent(code).strip()

    # 2. 구문 분석
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        error_msg = f"❌ Syntax Error: {e.msg} (line {e.lineno}, col {e.offset or 0})"
        if e.text:
            error_msg += f"\n    {e.text.rstrip()}"
            if e.offset:
                error_msg += f"\n    {' ' * (e.offset - 1)}^"
        return False, error_msg

    # 3. 안전성 분석
    analyzer = SafeExecutionAnalyzer(globals_dict)
    analyzer.visit(tree)

    # 4. 발견된 문제 정리
    all_issues = []

    # f-string 이슈
    for issue in analyzer.fstring_issues:
        # 내장 함수는 경고에서 제외
        if issue['name'] not in dir(__builtins__):
            all_issues.append(
                f"⚠️ f-string: Undefined '{issue['name']}' (line {issue['line']})"
            )

    # 정규식 이슈
    for issue in analyzer.regex_issues:
        icon = "❌" if issue['type'] == 'error' else "⚠️"
        all_issues.append(
            f"{icon} Regex: {issue['message']} (line {issue['line']})"
        )

    # 5. 심각한 오류가 있으면 실행 중단
    has_errors = any(issue['type'] == 'error' for issue in analyzer.regex_issues)
    if has_errors:
        return False, "\n".join(all_issues)

    # 6. 코드 실행
    import io, sys

    old_stdout = sys.stdout
    sys.stdout = io.StringIO()

    try:
        # 컴파일
        mode = 'eval' if len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr) else 'exec'
        code_obj = compile(tree, '<safe_exec>', mode)

        # 실행
        if mode == 'eval':
            result = eval(code_obj, globals_dict)
            if result is not None:
                print(result)
        else:
            exec(code_obj, globals_dict)

        output = sys.stdout.getvalue()

        # 경고와 출력 조합
        final_message = ""
        if all_issues:
            final_message = "⚠️ Analysis Results:\n" + "\n".join(all_issues)
        if output:
            if final_message:
                final_message += "\n\n📤 Output:\n" + output
            else:
                final_message = output

        return True, final_message

    except Exception as e:
        error_msg = f"❌ Runtime Error: {type(e).__name__}: {str(e)}"
        if all_issues:
            error_msg = "\n".join(all_issues) + "\n\n" + error_msg
        return False, error_msg

    finally:
        sys.stdout = old_stdout

# 간편 사용 함수
def safe_exec(code: str, globals_dict: dict = None) -> Tuple[bool, str]:
    """간편한 안전 실행 래퍼"""
    if globals_dict is None:
        globals_dict = {}
    return enhanced_safe_exec_v2(code, globals_dict)

def check_regex(pattern: str) -> dict:
    """정규식 패턴 검사"""
    return analyze_regex_pattern(pattern)

def check_fstring(template: str, **variables) -> Tuple[bool, str]:
    """f-string 템플릿 검사"""
    code = f'result = {template}'
    success, msg = safe_exec(code, variables)
    return success, msg

# 성능 벤치마크
def benchmark_regex_safety(pattern: str, test_inputs: list = None) -> dict:
    """정규식 성능 및 안전성 벤치마크"""
    if test_inputs is None:
        # ReDoS 테스트용 기본 입력
        test_inputs = [
            "a" * 10,
            "a" * 20,
            "a" * 30,
            "a" * 40 + "b",
            "x" * 50 + "y"
        ]

    analysis = analyze_regex_pattern(pattern)
    if not analysis['valid']:
        return {'error': analysis['errors'][0]}

    results = {
        'pattern': pattern,
        'warnings': analysis['warnings'],
        'performance': []
    }

    try:
        compiled = re.compile(pattern)

        for test_input in test_inputs:
            start = time.time()
            try:
                match = compiled.search(test_input)
                elapsed = time.time() - start

                results['performance'].append({
                    'input_length': len(test_input),
                    'time_ms': elapsed * 1000,
                    'matched': bool(match)
                })

                # 시간 초과 감지
                if elapsed > 0.1:  # 100ms
                    results['timeout_risk'] = True
                    break

            except Exception as e:
                results['performance'].append({
                    'input_length': len(test_input),
                    'error': str(e)
                })

    except Exception as e:
        results['error'] = str(e)

    return results

if __name__ == "__main__":
    print("Enhanced Safe Execution v2 - Final Version Ready")
