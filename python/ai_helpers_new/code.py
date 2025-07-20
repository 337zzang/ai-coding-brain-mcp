"""
AI Helpers Code Module
코드 분석과 수정을 위한 단순하고 실용적인 함수들
"""
import ast
from pathlib import Path
from typing import Dict, Any, List
from .util import ok, err


def parse(path: str) -> Dict[str, Any]:
    """Python 파일을 파싱하여 함수와 클래스 정보 추출

    Returns:
        성공: {
            'ok': True,
            'data': {
                'functions': [{'name': 'func1', 'line': 10, 'args': ['a', 'b']}, ...],
                'classes': [{'name': 'Class1', 'line': 20, 'methods': ['method1']}, ...],
                'imports': ['os', 'sys', ...]
            },
            'total_lines': 100
        }
        실패: {'ok': False, 'error': 에러메시지}
    """
    try:
        content = Path(path).read_text(encoding='utf-8')
        tree = ast.parse(content)

        functions = []
        classes = []
        imports = []

        # 최상위 노드만 확인
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'line': node.lineno,
                    'args': [arg.arg for arg in node.args.args]
                })

            elif isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(item.name)

                classes.append({
                    'name': node.name,
                    'line': node.lineno,
                    'methods': methods
                })

            elif isinstance(node, ast.Import):
                imports.extend([alias.name for alias in node.names])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return ok({
            'functions': functions,
            'classes': classes,
            'imports': list(set(imports))  # 중복 제거
        }, total_lines=content.count('\n') + 1, path=path)

    except Exception as e:
        return err(f"Parse error: {e}", path=path)


def view(path: str, name: str) -> Dict[str, Any]:
    """특정 함수나 클래스의 코드 보기

    Returns:
        성공: {'ok': True, 'data': '코드 내용', 'line_start': 10, 'line_end': 20}
        실패: {'ok': False, 'error': 에러메시지}
    """
    try:
        lines = Path(path).read_text(encoding='utf-8').splitlines()

        # AST로 위치 찾기
        tree = ast.parse('\n'.join(lines))

        for node in tree.body:
            node_name = None

            if isinstance(node, ast.FunctionDef) and node.name == name:
                node_name = node.name
            elif isinstance(node, ast.ClassDef) and node.name == name:
                node_name = node.name
            else:
                # 클래스 내부 메서드도 확인
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name == name:
                            node = item
                            node_name = f"{node.name}.{item.name}"
                            break

            if node_name:
                start = node.lineno - 1
                end = getattr(node, 'end_lineno', start + 1)

                code_lines = lines[start:end]
                return ok(
                    '\n'.join(code_lines),
                    line_start=start + 1,
                    line_end=end,
                    type='function' if isinstance(node, ast.FunctionDef) else 'class'
                )

        return err(f"'{name}' not found in {path}")

    except Exception as e:
        return err(f"View error: {e}", path=path)


def replace(path: str, old: str, new: str, count: int = 1) -> Dict[str, Any]:
    """파일에서 텍스트 교체

    Args:
        path: 파일 경로
        old: 찾을 텍스트
        new: 교체할 텍스트
        count: 교체 횟수 (기본값: 1, -1이면 모두 교체)

    Returns:
        성공: {'ok': True, 'data': 교체된 횟수, 'backup': 백업 경로}
        실패: {'ok': False, 'error': 에러메시지}
    """
    try:
        import shutil
        p = Path(path)

        if not p.exists():
            return err(f"File not found: {path}")

        content = p.read_text(encoding='utf-8')

        # 교체할 내용이 있는지 확인
        occurrences = content.count(old)
        if occurrences == 0:
            return ok(0, message="No matches found")

        # 백업 생성
        backup_path = f"{path}.backup"
        shutil.copy2(path, backup_path)

        # 교체
        if count == -1:
            new_content = content.replace(old, new)
            replaced = occurrences
        else:
            new_content = content.replace(old, new, count)
            replaced = min(count, occurrences)

        # 새 파일 쓰기
        p.write_text(new_content, encoding='utf-8')

        return ok(replaced, backup=backup_path, path=path)

    except Exception as e:
        return err(f"Replace error: {e}", path=path)


def insert(path: str, marker: str, code: str, after: bool = True) -> Dict[str, Any]:
    """마커 위치에 코드 삽입

    Args:
        path: 파일 경로
        marker: 삽입 위치를 표시하는 텍스트
        code: 삽입할 코드
        after: True면 마커 뒤에, False면 마커 앞에 삽입

    Returns:
        성공: {'ok': True, 'data': '삽입됨', 'line': 삽입된 줄 번호}
        실패: {'ok': False, 'error': 에러메시지}
    """
    try:
        lines = Path(path).read_text(encoding='utf-8').splitlines()

        # 마커 찾기
        insert_line = None
        for i, line in enumerate(lines):
            if marker in line:
                insert_line = i + 1 if after else i
                break

        if insert_line is None:
            return err(f"Marker '{marker}' not found", path=path)

        # 코드 삽입
        code_lines = code.splitlines()

        # 들여쓰기 맞추기 (마커 줄의 들여쓰기 사용)
        if 0 <= insert_line - 1 < len(lines):
            marker_line = lines[insert_line - 1]
            indent = len(marker_line) - len(marker_line.lstrip())
            code_lines = [' ' * indent + line if line.strip() else line for line in code_lines]

        # 삽입
        for i, code_line in enumerate(code_lines):
            lines.insert(insert_line + i, code_line)

        # 파일 쓰기
        Path(path).write_text('\n'.join(lines), encoding='utf-8')

        return ok('삽입됨', line=insert_line + 1, path=path)

    except Exception as e:
        return err(f"Insert error: {e}", path=path)


def functions(path: str) -> Dict[str, Any]:
    """파일의 모든 함수 목록만 빠르게 추출

    Returns:
        성공: {'ok': True, 'data': ['func1', 'func2', ...]}
        실패: {'ok': False, 'error': 에러메시지}
    """
    result = parse(path)
    if not result['ok']:
        return result

    func_names = [f['name'] for f in result['data']['functions']]
    return ok(func_names, count=len(func_names))


def classes(path: str) -> Dict[str, Any]:
    """파일의 모든 클래스 목록만 빠르게 추출

    Returns:
        성공: {'ok': True, 'data': ['Class1', 'Class2', ...]}
        실패: {'ok': False, 'error': 에러메시지}
    """
    result = parse(path)
    if not result['ok']:
        return result

    class_names = [c['name'] for c in result['data']['classes']]
    return ok(class_names, count=len(class_names))
