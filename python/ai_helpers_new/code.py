"""
AI Helpers Code Module
코드 분석과 수정을 위한 단순하고 실용적인 함수들
"""
import ast
from pathlib import Path
from typing import Dict, Any, List, Optional
from .util import ok, err


def parse(path: str) -> Dict[str, Any]:
    """Python 파일을 파싱하여 함수와 클래스 정보 추출

    Returns:
        성공: {
            'ok': True,
            'data': {
                'functions': [{'name': 'func1', 'line': 10, 'args': ['a', 'b'], ...}, ...],
                'classes': [{'name': 'Class1', 'line': 20, 'methods': ['method1'], ...}, ...],
                'imports': ['os', 'sys', ...],
                'globals': [{'name': 'VAR', 'line': 5, 'is_constant': True, ...}, ...]
            },
            'total_lines': 100
        }
        실패: {'ok': False, 'error': 에러메시지}
    """
    # 헬퍼 함수: 타입 표현 추출
    def get_type_repr(node) -> Optional[str]:
        if node is None:
            return None

        # Python 3.9+ ast.unparse 지원
        if hasattr(ast, 'unparse'):
            try:
                return ast.unparse(node)
            except:
                pass

        # Fallback for older versions
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Attribute):
            value = get_type_repr(node.value)
            return f"{value}.{node.attr}" if value else node.attr
        else:
            return None

    # AST 수집기 클래스
    class ASTCollector(ast.NodeVisitor):
        def __init__(self):
            self.functions = []
            self.classes = []
            self.imports = []
            self.globals = []
            self._current_class = None

        def visit_FunctionDef(self, node):
            self._collect_function(node, is_async=False)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            self._collect_function(node, is_async=True)
            self.generic_visit(node)

        def _collect_function(self, node, is_async):
            func_info = {
                'name': node.name,
                'line': node.lineno,
                'args': [arg.arg for arg in node.args.args],
                'is_async': is_async,
                'decorators': [get_type_repr(d) for d in node.decorator_list],
                'returns': get_type_repr(node.returns),
                'docstring': ast.get_docstring(node)
            }

            if hasattr(node, 'end_lineno'):
                func_info['end_line'] = node.end_lineno

            if self._current_class is not None:
                self._current_class['methods'].append(func_info)
            else:
                self.functions.append(func_info)

        def visit_ClassDef(self, node):
            class_info = {
                'name': node.name,
                'line': node.lineno,
                'methods': [],
                'bases': [get_type_repr(base) for base in node.bases],
                'decorators': [get_type_repr(d) for d in node.decorator_list],
                'docstring': ast.get_docstring(node)
            }

            if hasattr(node, 'end_lineno'):
                class_info['end_line'] = node.end_lineno

            self.classes.append(class_info)

            old_class = self._current_class
            self._current_class = class_info
            self.generic_visit(node)
            self._current_class = old_class

        def visit_Import(self, node):
            for alias in node.names:
                self.imports.append(alias.name)

        def visit_ImportFrom(self, node):
            if node.module:
                self.imports.append(node.module)

        def visit_Assign(self, node):
            if self._current_class is None:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.globals.append({
                            'name': target.id,
                            'line': node.lineno,
                            'is_constant': target.id.isupper()
                        })

    # 파일 읽기
    try:
        content = Path(path).read_text(encoding='utf-8')
    except FileNotFoundError:
        return err(f'File not found: {path}')
    except PermissionError:
        return err(f'Permission denied: {path}')
    except UnicodeDecodeError as e:
        return err(f'Encoding error: {e}')
    except Exception as e:
        return err(f'Failed to read file: {e}')

    # AST 파싱
    try:
        tree = ast.parse(content, filename=path)
    except SyntaxError as e:
        return err(f'Syntax error at line {e.lineno}: {e.msg}')
    except Exception as e:
        return err(f'Parse error: {e}')

    # 정보 수집
    collector = ASTCollector()
    collector.visit(tree)

    # 중복 제거
    collector.imports = list(dict.fromkeys(collector.imports))

    return ok({
        'functions': collector.functions,
        'classes': collector.classes,
        'imports': collector.imports,
        'globals': collector.globals
    }, total_lines=content.count('\n') + 1, path=path)
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


def safe_replace(path: str, old: str, new: str, preview: bool = False) -> Dict[str, Any]:
    """지능형 코드 교체 - 자동으로 최적의 방법 선택
    
    Args:
        path: 파일 경로
        old: 찾을 패턴
        new: 교체할 패턴
        preview: True면 미리보기만, False면 실제 수정
    
    Returns:
        성공: {'ok': True, 'data': {'replacements': N, 'mode': 'ast'/'text', 'backup': path}, 'preview': diff}
        실패: {'ok': False, 'error': 메시지}
    
    Examples:
        # 함수 호출 변경 (AST 모드 자동 감지)
        safe_replace("app.py", "print", "logger.info")
        
        # 미리보기
        result = safe_replace("test.py", "old_var", "new_var", preview=True)
        print(result['preview'])
    """
    try:
        from pathlib import Path
        import shutil
        import difflib
        
        p = Path(path)
        if not p.exists():
            return err(f"File not found: {path}")
            
        # 파일 읽기
        content = p.read_text(encoding='utf-8')
        
        # 모드 자동 감지
        mode = "text"  # 기본값
        
        # Python 파일이고 유효한 식별자면 AST 모드 고려
        if path.endswith('.py') and old.isidentifier() and new.isidentifier():
            try:
                # libcst 사용 가능한지 확인
                import libcst as cst
                
                # 간단한 AST 파싱 테스트
                tree = cst.parse_module(content)
                mode = "ast"
            except:
                mode = "text"
        
        # 교체 수행
        if mode == "text":
            # 단순 텍스트 교체
            occurrences = content.count(old)
            if occurrences == 0:
                return ok({'replacements': 0, 'mode': mode}, message="No matches found")
                
            new_content = content.replace(old, new)
            replacements = occurrences
            
        else:  # mode == "ast"
            try:
                import libcst as cst
                
                # AST 기반 교체를 위한 Transformer
                class NameReplacer(cst.CSTTransformer):
                    def __init__(self, old_name: str, new_name: str):
                        self.old_name = old_name
                        self.new_name = new_name
                        self.replacements = 0
                        
                    def visit_Name(self, node: cst.Name) -> None:
                        # 변수명/함수명 방문
                        pass
                        
                    def leave_Name(self, original_node: cst.Name, updated_node: cst.Name) -> cst.Name:
                        # 이름 교체
                        if updated_node.value == self.old_name:
                            self.replacements += 1
                            return updated_node.with_changes(value=self.new_name)
                        return updated_node
                    
                    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
                        # 함수 호출 처리
                        if isinstance(updated_node.func, cst.Name) and updated_node.func.value == self.old_name:
                            # 이미 leave_Name에서 처리됨
                            pass
                        return updated_node
                
                # 파싱 및 변환
                tree = cst.parse_module(content)
                replacer = NameReplacer(old, new)
                modified_tree = tree.visit(replacer)
                new_content = modified_tree.code
                replacements = replacer.replacements
                
                if replacements == 0:
                    return ok({'replacements': 0, 'mode': mode}, message="No matches found")
                    
                # 문법 검증
                compile(new_content, path, 'exec')
                
            except SyntaxError as e:
                # AST 모드 실패 시 텍스트 모드로 폴백
                mode = "text"
                occurrences = content.count(old)
                if occurrences == 0:
                    return ok({'replacements': 0, 'mode': mode}, message="No matches found")
                new_content = content.replace(old, new)
                replacements = occurrences
            except Exception as e:
                # libcst 관련 오류
                return err(f"AST parsing failed: {e}")
        
        # 미리보기 모드
        if preview:
            diff = difflib.unified_diff(
                content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"{path} (original)",
                tofile=f"{path} (modified)",
                n=3
            )
            diff_text = ''.join(diff)
            
            return ok({
                'replacements': replacements,
                'mode': mode,
                'preview': diff_text
            })
        
        # 실제 수정
        # 백업 생성
        backup_path = f"{path}.backup"
        shutil.copy2(path, backup_path)
        
        # 파일 쓰기
        p.write_text(new_content, encoding='utf-8')
        
        return ok({
            'replacements': replacements,
            'mode': mode,
            'backup': backup_path
        })
        
    except Exception as e:
        return err(f"Replace failed: {e}")


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
            lines.h.insert(insert_line + i, code_line)

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
