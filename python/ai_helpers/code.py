"""코드 수정 관련 헬퍼 함수들"""

import ast
from typing import Optional, Union
from ai_helpers.decorators import track_operation
import difflib
import shutil
import warnings
from datetime import datetime
import textwrap


# HelperResult import만 수행 (safe_helper는 import하지 않음)
try:
    from .helper_result import HelperResult
except ImportError:
    try:
        from ..helper_result import HelperResult
    except ImportError:
        # Fallback 정의
        class HelperResult:
            def __init__(self, ok, data=None, error=None):
                self.ok = ok
                self.data = data
                self.error = error
import os
import time
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, cast

# 전역 변수
_cache_manager = None
_verbose_mode = False
TREE_SITTER_AVAILABLE = False
_tree_sitter_modules = {}

def set_verbose(enabled: bool) -> None:
    """상세 출력 모드 설정"""
    global _verbose_mode
    _verbose_mode = enabled

def get_verbose() -> bool:
    """상세 출력 모드 확인"""
    return _verbose_mode

def _log(message: str, level: str = 'INFO') -> None:
    """상세 로그 출력"""
    if _verbose_mode:
        print(f"[AST Parser] [{level}] {message}")



class CacheManager:
    """모든 캐시를 중앙에서 관리"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.ast_cache: Dict[str, Any] = {}
            self.file_mtime_cache: Dict[str, float] = {}
            self.language_cache: Dict[str, Any] = {}
            self.parser_cache: Dict[str, Any] = {}
            self.initialized = True

    def get_cached_ast(self, file_path: str) -> Optional[Any]:
        """캐시된 AST 반환"""
        if file_path not in self.ast_cache:
            return None
        try:
            current_mtime = os.path.getmtime(file_path)
            cached_mtime = self.file_mtime_cache.get(file_path, 0)
            if current_mtime > cached_mtime:
                del self.ast_cache[file_path]
                return None
            return self.ast_cache[file_path]
        except:
            return None

    def set_cached_ast(self, file_path: str, ast_data: Any):
        """AST 캐시 저장"""
        self.ast_cache[file_path] = ast_data
        self.file_mtime_cache[file_path] = os.path.getmtime(file_path)

    def clear_all(self):
        """모든 캐시 초기화"""
        self.ast_cache.clear()
        self.file_mtime_cache.clear()
        self.language_cache.clear()
        self.parser_cache.clear()


class FunctionReplacer(ast.NodeTransformer):
    """
    AST 트리에서 특정 이름을 가진 함수/메서드를 찾아
    새로운 코드 블록으로 교체하는 NodeTransformer입니다.
    """

    def __init__(self, target_name: str, new_code: str):
        self.target_name = target_name
        self.new_nodes = ast.parse(new_code).body

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Union[ast.FunctionDef, List[ast.AST]]:
        """일반 함수(def) 노드를 방문합니다."""
        self.generic_visit(node)
        if node.name == self.target_name:
            return self.new_nodes
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Union[ast.AsyncFunctionDef, List[ast.AST]]:
        """비동기 함수(async def) 노드를 방문합니다."""
        self.generic_visit(node)
        if node.name == self.target_name:
            return self.new_nodes
        return node

class EnhancedFunctionReplacer(ast.NodeTransformer):
    """
    클래스명.메서드명 및 중첩 클래스를 지원하는 향상된 NodeTransformer
    
    지원 형식:
    - function_name (일반 함수)
    - ClassName.method_name (클래스 메서드)
    - OuterClass.InnerClass.method_name (중첩 클래스 메서드)
    """

    def __init__(self, target_name: str, new_code: str):
        import textwrap
        self.target_name = target_name
        parts = target_name.split('.')
        if len(parts) == 1:
            self.target_path = []
            self.target_method = parts[0]
        else:
            self.target_path = parts[:-1]
            self.target_method = parts[-1]
        try:
            processed_code = textwrap.dedent(new_code).strip()
            self.new_nodes = ast.parse(processed_code).body
        except (IndentationError, SyntaxError):
            lines = new_code.strip().split('\n')
            if lines:
                min_indent = float('inf')
                for line in lines:
                    if line.strip():
                        indent = len(line) - len(line.lstrip())
                        min_indent = min(min_indent, indent)
                if min_indent < float('inf') and min_indent > 0:
                    lines = [line[min_indent:] if len(line) >= min_indent else line for line in lines]
                processed_code = '\n'.join(lines)
                self.new_nodes = ast.parse(processed_code).body
            else:
                self.new_nodes = []
        self.current_path = []
        self.found_and_replaced = False

    def visit_ClassDef(self, node: ast.ClassDef):
        """클래스 정의 방문 (중첩 클래스 지원)"""
        self.current_path.append(node.name)
        self.generic_visit(node)
        self.current_path.pop()
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """함수 정의 방문"""
        if self._is_target_function(node.name):
            self.found_and_replaced = True
            if len(self.new_nodes) == 1:
                return self.new_nodes[0]
            else:
                return self.new_nodes
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """비동기 함수 정의 방문"""
        if self._is_target_function(node.name):
            self.found_and_replaced = True
            if len(self.new_nodes) == 1:
                return self.new_nodes[0]
            else:
                return self.new_nodes
        return node

    def _is_target_function(self, func_name: str) -> bool:
        """현재 함수가 타겟인지 확인"""
        if func_name != self.target_method:
            return False
        if len(self.target_path) == 0:
            return len(self.current_path) == 0
        else:
            return self.current_path == self.target_path



class ClassReplacer(ast.NodeTransformer):
    """클래스 전체를 교체하는 NodeTransformer"""
    
    def __init__(self, target_name: str, new_code: str):
        self.target_name = target_name
        self.new_code = new_code
        self.found_and_replaced = False
        
        # 새 코드 파싱
        try:
            new_tree = ast.parse(new_code)
            if new_tree.body and isinstance(new_tree.body[0], ast.ClassDef):
                self.new_node = new_tree.body[0]
            else:
                raise ValueError("new_code must contain a class definition")
        except Exception as e:
            self.new_node = None
            self.error = str(e)
    
    def visit_ClassDef(self, node):
        if node.name == self.target_name and self.new_node:
            self.found_and_replaced = True
            return self.new_node
        return self.generic_visit(node)

class BlockInsertTransformer(ast.NodeTransformer):
    """
    코드 블록 주변이나 내부에 새 코드를 삽입하는 NodeTransformer
    
    지원 위치:
    - before: 블록 앞에 삽입
    - after: 블록 뒤에 삽입
    - start: 블록 시작 부분에 삽입 (함수/클래스 내부 첫 부분)
    - end: 블록 끝 부분에 삽입 (함수/클래스 내부 끝 부분)
    """

    def __init__(self, target_name: str, position: str, new_code: str):
        self.target_name = target_name
        self.position = position
        parts = target_name.split('.')
        if len(parts) == 1:
            self.target_path = []
            self.target_method = parts[0]
        else:
            self.target_path = parts[:-1]
            self.target_method = parts[-1]
        self.new_nodes = ast.parse(new_code).body
        self.current_path = []
        self.found_and_inserted = False

    def visit_Module(self, node: ast.Module):
        """모듈 레벨에서 before/after 처리"""
        new_body = []
        for i, child in enumerate(node.body):
            if self.position == 'before' and self._is_target_node(child):
                new_body.extend(self.new_nodes)
                self.found_and_inserted = True
            new_body.append(self.visit(child))
            if self.position == 'after' and self._is_target_node(child):
                new_body.extend(self.new_nodes)
                self.found_and_inserted = True
        node.body = new_body
        return node

    def visit_ClassDef(self, node: ast.ClassDef):
        """클래스 정의 방문"""
        self.current_path.append(node.name)
        if self._is_current_target() and self.position in ['start', 'end']:
            if self.position == 'start':
                insert_pos = 0
                if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                    insert_pos = 1
                node.body = node.body[:insert_pos] + self.new_nodes + node.body[insert_pos:]
            else:
                node.body = node.body + self.new_nodes
            self.found_and_inserted = True
        else:
            new_body = []
            for i, child in enumerate(node.body):
                if self.position == 'before' and self._is_target_node(child):
                    new_body.extend(self.new_nodes)
                    self.found_and_inserted = True
                new_body.append(self.visit(child))
                if self.position == 'after' and self._is_target_node(child):
                    new_body.extend(self.new_nodes)
                    self.found_and_inserted = True
            node.body = new_body
        self.current_path.pop()
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """함수 정의 방문"""
        if self._is_target_function(node.name) and self.position in ['start', 'end']:
            if self.position == 'start':
                insert_pos = 0
                if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                    insert_pos = 1
                node.body = node.body[:insert_pos] + self.new_nodes + node.body[insert_pos:]
            else:
                node.body = node.body + self.new_nodes
            self.found_and_inserted = True
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """비동기 함수 정의 방문"""
        if self._is_target_function(node.name) and self.position in ['start', 'end']:
            if self.position == 'start':
                insert_pos = 0
                if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                    insert_pos = 1
                node.body = node.body[:insert_pos] + self.new_nodes + node.body[insert_pos:]
            else:
                node.body = node.body + self.new_nodes
            self.found_and_inserted = True
        return node

    def _is_target_node(self, node) -> bool:
        """노드가 타겟인지 확인 (before/after용)"""
        if isinstance(node, ast.ClassDef):
            return node.name == self.target_method and len(self.target_path) == 0
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return self._is_target_function(node.name)
        return False

    def _is_target_function(self, func_name: str) -> bool:
        """현재 함수가 타겟인지 확인"""
        if func_name != self.target_method:
            return False
        if len(self.target_path) == 0:
            return len(self.current_path) == 0
        else:
            return self.current_path == self.target_path

    def _is_current_target(self) -> bool:
        """현재 경로가 타겟과 일치하는지 확인"""
        target_full_path = self.target_path + [self.target_method]
        return self.current_path == target_full_path


class TreeSitterManager:
    """Tree-sitter 파서 관리자"""
    
    def __init__(self):
        self.parsers = {}
        self.languages = {}
        
    def get_parser(self, language: str):
        """언어별 파서 반환"""
        if language in self.parsers:
            return self.parsers[language]
            
        if not _lazy_import_tree_sitter():
            return None
            
        try:
            tree_sitter = _tree_sitter_modules.get('tree_sitter')
            if not tree_sitter:
                return None
                
            # 파서 생성
            parser = tree_sitter.Parser()
            
            # 언어별 문법 로드
            if language == 'python' and 'python' in _tree_sitter_modules:
                python_module = _tree_sitter_modules['python']
                # Tree-sitter Python 바인딩에서는 Language.build_library를 사용하거나
                # 이미 빌드된 언어 객체를 사용합니다
                if hasattr(python_module, 'language'):
                    parser.set_language(python_module.language())
                elif hasattr(python_module, 'LANGUAGE'):
                    parser.set_language(python_module.LANGUAGE)
                else:
                    _log(f'Unable to get language object from tree_sitter_python')
                    return None
                self.parsers[language] = parser
                return parser
            elif language in ('javascript', 'typescript') and 'javascript' in _tree_sitter_modules:
                js_module = _tree_sitter_modules['javascript']
                if hasattr(js_module, 'language'):
                    parser.set_language(js_module.language())
                elif hasattr(js_module, 'LANGUAGE'):
                    parser.set_language(js_module.LANGUAGE)
                else:
                    _log(f'Unable to get language object from tree_sitter_javascript')
                    return None
                self.parsers[language] = parser
                return parser
            else:
                _log(f'Tree-sitter grammar not available for {language}')
                return None
                
        except Exception as e:
            _log(f'Failed to create Tree-sitter parser for {language}: {e}')
            return None


class ASTParser:
    """통합 AST 파서"""

    def __init__(self):
        self.cache_manager = CacheManager()
        self.ts_manager = TreeSitterManager()

    def _detect_language(self, file_path: str, language: str='auto') -> str:
        """파일 언어 감지"""
        if language != 'auto':
            return language
        ext = Path(file_path).suffix.lower()
        ext_map = {'.py': 'python', '.js': 'javascript', '.jsx': 'javascript', '.ts': 'typescript', '.tsx': 'typescript'}
        return ext_map.get(ext, 'unknown')

    def _extract_docstring(self, node: ast.AST) -> Optional[str]:
        """Python docstring 추출 (Python 3.8+ 지원)"""
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            return None
            
        if not hasattr(node, 'body') or not node.body:
            return None
            
        first = node.body[0]
        if isinstance(first, ast.Expr):
            if isinstance(first.value, ast.Str):
                # Python 3.7 이하
                return textwrap.dedent(first.value.s).strip()
            elif isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                # Python 3.8+
                return textwrap.dedent(first.value.value).strip()
        return None
        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Str):
            return textwrap.dedent(first.value.s).strip()
        return None

    def _extract_function_info(self, node: ast.FunctionDef, source_lines: List[str]) -> Dict:
        """함수 정보 추출"""
        info = {'type': 'function', 'name': node.name, 'line_start': node.lineno, 'line_end': node.end_lineno or node.lineno, 'col_start': node.col_offset + 1, 'col_end': getattr(node, 'end_col_offset', 0) + 1 if hasattr(node, 'end_col_offset') else None, 'args': [arg.arg for arg in node.args.args], 'docstring': self._extract_docstring(node), 'decorators': [d.id if isinstance(d, ast.Name) else str(d) for d in node.decorator_list if d], 'is_async': isinstance(node, ast.AsyncFunctionDef)}
        if source_lines and node.lineno and node.end_lineno:
            start = max(0, node.lineno - 1)
            end = min(len(source_lines), node.end_lineno)
            info['snippet'] = '\n'.join(source_lines[start:end])
        return info

    def _extract_class_info(self, node: ast.ClassDef, source_lines: List[str]) -> Dict:
        """클래스 정보 추출"""
        info = {'type': 'class', 'name': node.name, 'line_start': node.lineno, 'line_end': node.end_lineno or node.lineno, 'col_start': node.col_offset + 1, 'col_end': getattr(node, 'end_col_offset', 0) + 1 if hasattr(node, 'end_col_offset') else None, 'bases': [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases], 'docstring': self._extract_docstring(node), 'methods': []}
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._extract_function_info(item, source_lines)
                method_info['type'] = 'method'
                info['methods'].append(method_info)
        if source_lines and node.lineno and node.end_lineno:
            start = max(0, node.lineno - 1)
            end = min(len(source_lines), node.end_lineno)
            info['snippet'] = '\n'.join(source_lines[start:end])
        return info

    def parse_python(self, file_path: str, include_snippets: bool=True) -> Dict[str, Any]:
        """Python 파일 파싱"""
        try:
            cached = self.cache_manager.get_cached_ast(file_path)
            if cached and (not include_snippets):
                return cached
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content, filename=file_path)
            source_lines = content.split('\n') if include_snippets else []
            result = {'parsing_success': True, 'language': 'python', 'functions': [], 'classes': [], 'imports': []}
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    result['functions'].append(self._extract_function_info(node, source_lines))
                elif isinstance(node, ast.ClassDef):
                    result['classes'].append(self._extract_class_info(node, source_lines))
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            result['imports'].append(alias.name)
                    else:
                        result['imports'].append(node.module or '')
            if not include_snippets:
                self.cache_manager.set_cached_ast(file_path, result)
            return result
        except Exception as e:
            _log(f'Python 파싱 오류: {e}', 'ERROR')
            return {'parsing_success': False, 'language': 'python', 'error': str(e)}

    def parse_javascript(self, file_path: str, language: str='javascript', include_snippets: bool=True) -> Dict[str, Any]:
        """JavaScript/TypeScript 파일 파싱 - Tree-sitter 기반"""
        parser = self.ts_manager.get_parser(language)
        if not parser:
            return {'parsing_success': False, 'language': language, 'error': 'Tree-sitter not available'}
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            tree = parser.parse(content)
            lines = content.decode('utf-8').split('\n')
            result = {'parsing_success': True, 'language': language, 'functions': [], 'classes': [], 'imports': [], 'total_lines': len(lines), 'file_path': file_path}
            self._parse_js_basic(tree.root_node, lines, result)
            return result
        except Exception as e:
            _log(f'JavaScript 파싱 오류: {e}', 'ERROR')
            return {'parsing_success': False, 'language': language, 'error': str(e)}

    def _parse_js_basic(self, node, lines: List[str], result: Dict) -> None:
        """JavaScript 노드를 순회하며 기본 정보 추출"""
        if node.type == 'function_declaration':
            name_node = node.child_by_field_name('name')
            if name_node:
                func_info = {'name': lines[name_node.start_point[0]][name_node.start_point[1]:name_node.end_point[1]], 'type': 'function', 'line_start': node.start_point[0] + 1, 'line_end': node.end_point[0] + 1, 'snippet': self._get_snippet(lines, node.start_point[0], node.end_point[0])}
                result['functions'].append(func_info)
        elif node.type == 'class_declaration':
            name_node = node.child_by_field_name('name')
            if name_node:
                class_info = {'name': lines[name_node.start_point[0]][name_node.start_point[1]:name_node.end_point[1]], 'line_start': node.start_point[0] + 1, 'line_end': node.end_point[0] + 1, 'methods': [], 'snippet': self._get_snippet(lines, node.start_point[0], node.end_point[0])}
                result['classes'].append(class_info)
        elif node.type == 'variable_declarator':
            name_node = node.child_by_field_name('name')
            value_node = node.child_by_field_name('value')
            if name_node and value_node:
                if value_node.type in ['arrow_function', 'function_expression']:
                    func_info = {'name': lines[name_node.start_point[0]][name_node.start_point[1]:name_node.end_point[1]], 'type': 'arrow_function' if value_node.type == 'arrow_function' else 'function_expression', 'line_start': node.start_point[0] + 1, 'line_end': node.end_point[0] + 1, 'snippet': self._get_snippet(lines, node.start_point[0], node.end_point[0])}
                    result['functions'].append(func_info)
        elif node.type == 'import_statement':
            source_node = node.child_by_field_name('source')
            if source_node:
                source_text = lines[source_node.start_point[0]][source_node.start_point[1] + 1:source_node.end_point[1] - 1]
                result['imports'].append({'source': source_text, 'line': node.start_point[0] + 1})
        for child in node.children:
            self._parse_js_basic(child, lines, result)

    def _get_snippet(self, lines: List[str], start_line: int, end_line: int, max_lines: int=10) -> str:
        """코드 스니펫 생성"""
        snippet_lines = []
        for i in range(start_line, min(end_line + 1, start_line + max_lines)):
            if i < len(lines):
                snippet_lines.append(lines[i])
        return '\n'.join(snippet_lines)


def _lazy_import_tree_sitter() -> bool:
    """Tree-sitter 모듈 지연 임포트"""
    global TREE_SITTER_AVAILABLE, _tree_sitter_modules
    
    if _tree_sitter_modules:
        return True
        
    try:
        import tree_sitter
        import tree_sitter_python
        import tree_sitter_javascript
        
        _tree_sitter_modules['tree_sitter'] = tree_sitter
        _tree_sitter_modules['python'] = tree_sitter_python
        _tree_sitter_modules['javascript'] = tree_sitter_javascript
        
        TREE_SITTER_AVAILABLE = True
        _log('Tree-sitter 모듈 로드 성공')
        return True
    except ImportError as e:
        _log(f'Tree-sitter 로드 실패: {e}', 'WARNING')
        return False


# 전역 파서 인스턴스
_parser_instance = None

def _get_parser() -> 'ASTParser':
    """싱글톤 파서 인스턴스 반환"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = ASTParser()
    return _parser_instance



@track_operation('code', 'replace_block')
def replace_block(file_path: str, target_block: str, new_code: str) -> str:
    """코드 블록을 새로운 코드로 교체 - AST 기반 구현
    
    Args:
        file_path: 수정할 파일 경로
        target_block: 찾을 블록 이름 (함수명, 클래스명, ClassName.method 형식 지원)
        new_code: 교체할 새 코드
        
    Returns:
        str: 성공/실패 메시지
    """
    try:
        # 1. 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 2. AST 파싱
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            raise RuntimeError(f"파일 파싱 실패 - {e}")
        
        # 3. 새 코드 검증
        try:
            # 새 코드가 유효한지 확인
            ast.parse(new_code)
        except SyntaxError as e:
            raise ValueError(f"새 코드가 유효하지 않음 - {e}")
        
        # 4. EnhancedFunctionReplacer 사용
        replacer = EnhancedFunctionReplacer(target_block, new_code)
        modified_tree = replacer.visit(tree)
        
        # 교체가 성공했는지 확인
        if not replacer.found_and_replaced:
            # 함수/클래스를 찾지 못한 경우, BlockInsertTransformer로 시도해볼 수도 있음
            raise ValueError(f"{target_block}를 찾을 수 없습니다")
        
        # 5. 수정된 AST를 코드로 변환
        try:
            # Python 3.9+ ast.unparse 사용
            modified_code = ast.unparse(modified_tree)
        except AttributeError:
            # ast.unparse가 없는 경우 astor 시도
            try:
                import astor
                modified_code = astor.to_source(modified_tree)
            except ImportError:
                # astor도 없으면 수동으로 처리
                # 원본 코드에서 직접 교체하는 방식으로 폴백
                return _fallback_replace(file_path, target_block, new_code, content)
        
        # 6. 파일 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_code)
        
        return f"SUCCESS: {target_block} 교체 완료"
        
    except Exception as e:
        raise RuntimeError(f"{type(e).__name__} - {e}")


def _fallback_replace(file_path: str, target_block: str, new_code: str, content: str) -> str:
    """AST 기반 교체가 실패한 경우의 폴백 함수"""
    try:
        lines = content.split('\n')
        
        # 타겟 블록 찾기
        target_line = -1
        target_indent = 0
        
        for i, line in enumerate(lines):
            # 함수나 클래스 정의 찾기
            if (f'def {target_block}(' in line or 
                f'async def {target_block}(' in line or 
                f'class {target_block}' in line or
                f'class {target_block}(' in line):
                target_line = i
                target_indent = len(line) - len(line.lstrip())
                break
        
        if target_line == -1:
            # 메서드인 경우도 확인 (ClassName.method_name)
            if '.' in target_block:
                parts = target_block.split('.')
                method_name = parts[-1]
                for i, line in enumerate(lines):
                    if f'def {method_name}(' in line:
                        target_line = i
                        target_indent = len(line) - len(line.lstrip())
                        break
        
        if target_line == -1:
            raise ValueError(f"{target_block}를 찾을 수 없습니다")
        
        # 블록의 끝 찾기
        end_line = target_line + 1
        while end_line < len(lines):
            line = lines[end_line]
            # 빈 줄은 무시
            if not line.strip():
                end_line += 1
                continue
            # 같거나 더 적은 들여쓰기면 블록 끝
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= target_indent:
                break
            end_line += 1
        
        # 새 코드 처리
        new_lines = new_code.split('\n')
        
        # 원본 들여쓰기 적용
        if target_indent > 0:
            adjusted_lines = []
            for i, line in enumerate(new_lines):
                if line.strip():  # 빈 줄이 아니면
                    # 첫 줄은 이미 올바른 들여쓰기를 가질 수 있음
                    if i == 0 and not line.startswith(' '):
                        adjusted_lines.append(' ' * target_indent + line)
                    else:
                        # 기존 들여쓰기 유지하면서 target_indent 추가
                        line_indent = len(line) - len(line.lstrip())
                        if i > 0:  # 첫 줄이 아닌 경우
                            adjusted_lines.append(' ' * target_indent + line)
                        else:
                            adjusted_lines.append(line)
                else:
                    adjusted_lines.append(line)
            new_lines = adjusted_lines
        
        # 교체
        lines[target_line:end_line] = new_lines
        
        # 파일 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return f"SUCCESS: {target_block} 교체 완료 (폴백 방식)"
        
    except Exception as e:
        raise RuntimeError(f"폴백 교체 실패 - {e}")
@track_operation('code', 'insert_block')
def insert_block(file_path: str, target: str, position: str, new_code: str) -> str:
    """코드 블록을 특정 위치에 삽입 - AST 기반 구현
    
    Args:
        file_path: 수정할 파일 경로
        target: 기준이 되는 블록 이름 (함수명, 클래스명, ClassName.method 형식 지원)
        position: 삽입 위치 ('before', 'after', 'start', 'end')
        new_code: 삽입할 코드
        
    Returns:
        str: 성공/실패 메시지
    """
    try:
        # 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # AST 파싱
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            raise RuntimeError(f"파일 파싱 실패 - {e}")
        
        # 새 코드 검증
        try:
            ast.parse(new_code)
        except SyntaxError as e:
            raise ValueError(f"삽입할 코드가 유효하지 않음 - {e}")
        
        # position 유효성 검증
        valid_positions = ['before', 'after', 'start', 'end']
        if position not in valid_positions:
            raise ValueError(f"잘못된 position '{position}'. 사용 가능: {valid_positions}")
        
        # BlockInsertTransformer 사용
        try:
            inserter = BlockInsertTransformer(target, position, new_code)
            modified_tree = inserter.visit(tree)
        except Exception as e:
            raise RuntimeError(f"코드 삽입 중 오류 - {e}")
        
        # 수정된 AST를 코드로 변환
        try:
            modified_code = ast.unparse(modified_tree)
        except AttributeError:
            try:
                modified_code = astor.to_source(modified_tree)
            except ImportError:
                # 간단한 텍스트 기반 폴백
                return _simple_text_insert(file_path, target, position, new_code, content)
        
        # 파일 저장
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_code)
        
        return f"SUCCESS: {target} {position}에 코드 삽입 완료"
        
    except Exception as e:
        raise RuntimeError(f"{type(e).__name__} - {e}")


def _simple_text_insert(file_path: str, target: str, position: str, new_code: str, content: str) -> str:
    """간단한 텍스트 기반 삽입 (폴백용)"""
    lines = content.split('\n')
    
    # 타겟 찾기
    target_line = -1
    for i, line in enumerate(lines):
        if f'def {target}(' in line or f'class {target}' in line:
            target_line = i
            break
    
    if target_line == -1:
        raise ValueError(f"{target}를 찾을 수 없습니다")
    
    # 삽입
    new_lines = new_code.split('\n')
    
    if position == 'before':
        lines[target_line:target_line] = new_lines + ['']
    elif position == 'after':
        # 블록 끝 찾기 (간단한 버전)
        end_line = target_line + 1
        indent = len(lines[target_line]) - len(lines[target_line].lstrip())
        while end_line < len(lines):
            if lines[end_line].strip() and len(lines[end_line]) - len(lines[end_line].lstrip()) <= indent:
                break
            end_line += 1
        lines[end_line:end_line] = [''] + new_lines
    else:
        # start/end는 들여쓰기 추가
        indent = len(lines[target_line]) - len(lines[target_line].lstrip()) + 4
        indented_lines = [' ' * indent + line if line.strip() else line for line in new_lines]
        
        if position == 'start':
            lines[target_line + 1:target_line + 1] = indented_lines + ['']
        else:  # end
            end_line = target_line + 1
            base_indent = len(lines[target_line]) - len(lines[target_line].lstrip())
            while end_line < len(lines):
                if lines[end_line].strip() and len(lines[end_line]) - len(lines[end_line].lstrip()) <= base_indent:
                    break
                end_line += 1
            lines[end_line:end_line] = [''] + indented_lines
    
    # 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return f"SUCCESS: {target} {position}에 코드 삽입 완료 (텍스트 방식)"

@track_operation('code', 'parse')
def parse_code(file_path: str) -> dict:
    """코드 파일을 파싱하여 AST 정보 반환"""
    parser = _get_parser()
    lang = parser._detect_language(file_path)
    
    if lang == 'python':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            ast.parse(content)
            return {'parsing_success': True, 'file_path': file_path, 'language': lang}
        except Exception as e:
            return {'parsing_success': False, 'error': str(e), 'language': lang}
    elif lang in ('javascript', 'typescript'):
        # Tree-sitter를 사용한 구문 검사
        ts_parser = parser.ts_manager.get_parser(lang)
        if ts_parser:
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()
                tree = ts_parser.parse(content)
                # 파싱 성공 여부는 tree가 None이 아닌지로 판단
                return {'parsing_success': tree is not None, 'file_path': file_path, 'language': lang}
            except Exception as e:
                return {'parsing_success': False, 'error': str(e), 'language': lang}
        else:
            return {'parsing_success': False, 'error': 'Tree-sitter not available', 'language': lang}
    else:
        return {'parsing_success': False, 'error': f'Unsupported language: {lang}', 'language': lang}


@track_operation('code', 'parse_snippets')
def parse_with_snippets(file_path: str, language: str = 'auto', 
                       include_snippets: bool = True) -> dict:
    """파일을 파싱하여 구조화된 정보와 코드 스니펫 추출"""
    parser = _get_parser()
    lang = parser._detect_language(file_path, language)
    
    if lang == 'python':
        result = parser.parse_python(file_path, include_snippets=include_snippets)
    elif lang in ('javascript', 'typescript'):
        result = parser.parse_javascript(file_path, language=lang, include_snippets=include_snippets)
    else:
        result = {
            'parsing_success': False,
            'language': lang,
            'error': f"Unsupported language: {lang}",
            'file_path': file_path
        }
    
    # 결과에 file_path와 total_lines 추가 (없는 경우)
    if 'file_path' not in result:
        result['file_path'] = file_path
    
    if 'total_lines' not in result and result.get('parsing_success', False):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            result['total_lines'] = len(content.splitlines())
        except:
            pass
    
    return result


@track_operation('code', 'snippet_preview')
def get_snippet_preview(file_path: str, element_name: str, 
                       element_type: str = 'function', max_lines: int = 10,
                       start_line: int = -1, end_line: int = -1) -> str:
    """코드 스니펫 미리보기"""
    parser = _get_parser()
    
    # start_line과 end_line이 제공된 경우 직접 사용
    if start_line > 0 and end_line > 0:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            # 0-based index로 변환
            return parser._get_snippet(lines, start_line - 1, end_line - 1, max_lines)
        except Exception as e:
            raise RuntimeError(f"Error reading file: {str(e)}")
    
    # element_name으로 찾기
    try:
        # 파일 파싱
        parse_result = parse_with_snippets(file_path)
        
        # element_type에 따라 검색
        if element_type == 'function':
            elements = parse_result.get('functions', [])
        elif element_type == 'class':
            elements = parse_result.get('classes', [])
        else:
            elements = []
        
        # element_name으로 찾기
        for elem in elements:
            if elem.get('name') == element_name:
                # snippet이 이미 있으면 반환
                if 'snippet' in elem:
                    return elem['snippet']
                # 없으면 line 정보로 생성
                elif 'line_start' in elem and 'line_end' in elem:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    return parser._get_snippet(lines, elem['line_start'] - 1, elem['line_end'] - 1, max_lines)
        
        return f"Element '{element_name}' of type '{element_type}' not found"
        
    except Exception as e:
        raise RuntimeError(f"Error: {str(e)}")

def update_symbol_index(file_path: str, parse_result: dict) -> None:
    """
    파싱 결과를 기반으로 심볼 인덱스 업데이트
    """
    try:
        # context 모듈에서 현재 컨텍스트 가져오기
        from ai_helpers import context
        current_context = context.get_context()
        if not current_context:
            return
            
        symbol_index = current_context.get('symbol_index', {})
        
        # 함수 정보 업데이트
        for func in parse_result.get('functions', []):
            symbol_index[func['name']] = {
                'type': 'function',
                'file_path': file_path,
                'line_start': func.get('line_start'),
                'line_end': func.get('line_end'),
                'class_name': None
            }
        
        # 클래스 정보 업데이트
        for cls in parse_result.get('classes', []):
            symbol_index[cls['name']] = {
                'type': 'class',
                'file_path': file_path,
                'line_start': cls.get('line_start'),
                'line_end': cls.get('line_end'),
                'class_name': None
            }
            
            # 메서드 정보 업데이트
            for method in cls.get('methods', []):
                method_key = f"{cls['name']}.{method['name']}"
                symbol_index[method_key] = {
                    'type': 'method',
                    'file_path': file_path,
                    'line_start': method.get('line_start'),
                    'line_end': method.get('line_end'),
                    'class_name': cls['name']
                }
        
        # 컨텍스트 업데이트
        context.update_cache('symbol_index', symbol_index)
        
    except Exception as e:
        _log(f'Failed to update symbol index: {e}', 'ERROR')