# execute_code 함수 O3 개선안

생성일: 2025-08-04

## O3 제안 코드

```python
import ast
from typing import Any, Dict

SAFE_BUILTINS = {
    'abs': abs,
    'max': max,
    'min': min,
    'sum': sum,
    'range': range,
    'len': len,
    'print': print,
}

class UnsafeCodeError(Exception):
    pass


# --- 1. AST 검사 ----------------------------------------------------------- #
def _parse_and_validate(src: str) -> ast.AST:
    """코드를 AST 로 파싱 후 금지 노드가 있으면 예외 발생"""
    tree = ast.parse(src, mode='exec')
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal)):
            raise UnsafeCodeError(f'금지된 구문: {type(node).__name__}')
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == '__import__':
                raise UnsafeCodeError('__import__ 사용 금지')
    return tree


# --- 2. 안전한 실행 환경 ---------------------------------------------------- #
def _build_env() -> Dict[str, Any]:
    """제한된 built-ins 만 노출"""
    return {'__builtins__': SAFE_BUILTINS.copy()}


# --- 3. 실행 및 결과 수집 --------------------------------------------------- #
def _exec_tree(tree: ast.AST, env: Dict[str, Any]) -> Any:
    """컴파일 후 실행, 마지막 표현식 결과는 '_' 로 노출"""
    compiled = compile(tree, '<user>', 'exec')
    exec(compiled, env)
    return env.get('_')   # 사용자가 '_' 변수에 결과를 넣었다면 반환


# --- 4. 외부 API ----------------------------------------------------------- #
def execute_code(code: str) -> Dict[str, Any]:
    """
    사용자 코드 실행.
    반환 형식: {'ok': bool, 'data': Any, 'error': str}
    """
    try:
        tree = _parse_and_validate(code)
        env = _build_env()
        data = _exec_tree(tree, env)
        return {'ok': True, 'data': data, 'error': ''}
    except Exception as exc:
        return {'ok': False, 'data': None, 'error': str(exc)}


# --- 사용 예시 ------------------------------------------------------------- #
if __name__ == '__main__':
    print(execute_code("x = 2 ** 5\n_ = x"))
    print(execute_code("import os"))  # 금지된 코드 예시
```