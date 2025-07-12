"""
코드 수정 헬퍼 함수 - AST 기반 고급 기능
replace_block 활용도 개선
"""
from typing import Optional, List, Dict, Any
from .helper_result import HelperResult
from .code import replace_block as _replace_block
import ast

def replace_function(file_path: str, function_name: str, new_implementation: str) -> HelperResult:
    """
    함수 전체를 새로운 구현으로 교체 (replace_block 래퍼)

    Args:
        file_path: 파일 경로
        function_name: 함수 이름
        new_implementation: 새로운 함수 구현 (def 포함)

    Returns:
        HelperResult
    """
    return _replace_block(file_path, function_name, new_implementation)


def replace_class_method(file_path: str, class_name: str, method_name: str, 
                        new_implementation: str) -> HelperResult:
    """
    클래스의 특정 메서드를 교체

    Args:
        file_path: 파일 경로
        class_name: 클래스 이름
        method_name: 메서드 이름
        new_implementation: 새로운 메서드 구현

    Returns:
        HelperResult
    """
    target = f"{class_name}.{method_name}"
    return _replace_block(file_path, target, new_implementation)


def add_method_to_class(file_path: str, class_name: str, new_method: str) -> HelperResult:
    """
    클래스에 새로운 메서드 추가

    Args:
        file_path: 파일 경로
        class_name: 클래스 이름
        new_method: 추가할 메서드 코드

    Returns:
        HelperResult
    """
    try:
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # AST 파싱
        tree = ast.parse(content)
        lines = content.splitlines()

        # 클래스 찾기
        class_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                class_node = node
                break

        if not class_node:
            return HelperResult(False, error=f"Class '{class_name}' not found")

        # 클래스의 마지막 줄 찾기
        class_end_line = class_node.end_lineno - 1

        # 클래스 내부의 들여쓰기 레벨 확인
        first_stmt = class_node.body[0] if class_node.body else None
        if first_stmt:
            indent_level = first_stmt.col_offset
        else:
            indent_level = 4  # 기본값

        # 새 메서드 들여쓰기 적용
        indent = ' ' * indent_level
        method_lines = new_method.strip().split('\n')
        indented_method = []

        for i, line in enumerate(method_lines):
            if i == 0 and line.strip().startswith('def'):
                # 첫 줄은 클래스 레벨 들여쓰기
                indented_method.append(indent + line.lstrip())
            elif line.strip():
                # 나머지 줄은 상대적 들여쓰기 유지
                indented_method.append(indent + line)
            else:
                # 빈 줄
                indented_method.append('')

        # 새 메서드 삽입
        lines.insert(class_end_line, '')  # 빈 줄 추가
        for line in reversed(indented_method):
            lines.insert(class_end_line, line)

        # 파일 쓰기
        new_content = '\n'.join(lines)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        return HelperResult(True, data={
            'class': class_name,
            'method_added': new_method.split('(')[0].strip().replace('def ', ''),
            'line': class_end_line + 1
        })

    except Exception as e:
        return HelperResult(False, error=f"Failed to add method: {str(e)}")


def update_function_signature(file_path: str, function_name: str, 
                            new_params: str, update_docstring: bool = True) -> HelperResult:
    """
    함수 시그니처 업데이트

    Args:
        file_path: 파일 경로
        function_name: 함수 이름
        new_params: 새로운 파라미터 (괄호 내용만)
        update_docstring: docstring도 업데이트할지 여부

    Returns:
        HelperResult
    """
    try:
        # 현재 함수 읽기
        from ..helpers_wrapper import extract_function_snippet

        extract_result = extract_function_snippet(file_path, function_name)
        if not extract_result.ok:
            return extract_result

        current_code = extract_result.data['snippet']
        lines = current_code.split('\n')

        # 첫 줄 (def 라인) 수정
        def_line = lines[0]
        new_def_line = f"def {function_name}({new_params}):"
        lines[0] = new_def_line

        # 새로운 함수 코드
        new_function = '\n'.join(lines)

        # replace_block으로 교체
        return _replace_block(file_path, function_name, new_function)

    except Exception as e:
        return HelperResult(False, error=f"Failed to update signature: {str(e)}")


def refactor_variable_name(file_path: str, old_name: str, new_name: str, 
                          scope: Optional[str] = None) -> HelperResult:
    """
    변수명 리팩토링

    Args:
        file_path: 파일 경로
        old_name: 기존 변수명
        new_name: 새 변수명
        scope: 특정 함수/클래스 내에서만 변경 (None이면 전체)

    Returns:
        HelperResult
    """
    try:
        import re

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 단어 경계를 사용한 정확한 매칭
        pattern = r'\b' + re.escape(old_name) + r'\b'

        if scope:
            # 특정 스코프 내에서만 변경
            # TODO: AST를 사용한 정확한 스코프 처리
            return HelperResult(False, error="Scoped refactoring not yet implemented")
        else:
            # 전체 파일에서 변경
            new_content = re.sub(pattern, new_name, content)

            if new_content == content:
                return HelperResult(False, error=f"No occurrences of '{old_name}' found")

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            # 변경 횟수 계산
            count = len(re.findall(pattern, content))

            return HelperResult(True, data={
                'old_name': old_name,
                'new_name': new_name,
                'occurrences_changed': count
            })

    except Exception as e:
        return HelperResult(False, error=f"Refactoring failed: {str(e)}")


# Export
__all__ = [
    'replace_function',
    'replace_class_method', 
    'add_method_to_class',
    'update_function_signature',
    'refactor_variable_name'
]
