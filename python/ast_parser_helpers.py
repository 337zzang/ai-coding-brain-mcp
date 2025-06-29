"""
AST Parser Helper - Refactored Version
Python: ast.parse() 기반 파싱
JavaScript/TypeScript: Tree-sitter 지연 로딩 파싱  
"""
import ast
import os
import time
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, cast
import textwrap
import re
TREE_SITTER_AVAILABLE = False
_tree_sitter_modules = {}
_advanced_parser = None
_parser_lock = threading.Lock()
VERBOSE = False

def set_verbose(flag: bool) -> None:
    """전역 verbose 모드 설정"""
    global VERBOSE
    VERBOSE = flag

def get_verbose() -> bool:
    """현재 verbose 모드 상태 반환"""
    return VERBOSE

def _log(msg: str, level: str='INFO') -> None:
    """조건부 로깅"""
    if VERBOSE:
        print(f'[{level}] {msg}')

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

class TreeSitterManager:
    """Tree-sitter 파서 관리"""
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
            self._parsers = {}
            self.initialized = True

    def get_parser(self, language: str):
        """언어별 파서 반환"""
        if not _lazy_import_tree_sitter():
            return None
        if language not in self._parsers:
            self._parsers[language] = self._create_parser(language)
        return self._parsers[language]

    def _create_parser(self, language: str):
        """파서 생성"""
        tree_sitter = _tree_sitter_modules.get('tree_sitter')
        if not tree_sitter:
            return None
        parser = tree_sitter.Parser()
        lang_map = {'python': 'python', 'javascript': 'javascript', 'typescript': 'javascript'}
        lang_key = lang_map.get(language)
        if not lang_key:
            return None
        lang_module = _tree_sitter_modules.get(lang_key)
        if lang_module:
            parser.language = tree_sitter.Language(lang_module.language())
            return parser
        return None

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
        self.replaced = False
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
        self.inserted = False
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
        self.inserted = True
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
        """Python docstring 추출"""
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            return None
        if not hasattr(node, 'body') or not node.body:
            return None
        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, (ast.Str, ast.Constant)):
            if isinstance(first.value, ast.Str):
                return textwrap.dedent(first.value.s).strip()
            elif isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
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

def _get_parser() -> ASTParser:
    """싱글톤 파서 인스턴스 반환"""
    global _advanced_parser, _parser_lock
    if _advanced_parser is None:
        with _parser_lock:
            if _advanced_parser is None:
                _advanced_parser = ASTParser()
    return _advanced_parser

def parse_with_snippets(file_path: str, language: str='auto', include_snippets: bool=True) -> Dict[str, Any]:
    """파일 파싱 (공개 API)"""
    parser = _get_parser()
    detected_language = parser._detect_language(file_path, language)
    if detected_language == 'python':
        return parser.parse_python(file_path, include_snippets)
    elif detected_language in ['javascript', 'typescript']:
        return parser.parse_javascript(file_path, detected_language, include_snippets)
    else:
        return {'parsing_success': False, 'language': detected_language, 'error': f'Unsupported language: {detected_language}'}

def get_snippet_preview(file_path: str, element_name: str, element_type: str='function', max_lines: int=10, start_line: int=-1, end_line: int=-1) -> str:
    """코드 스니펫 미리보기 (공개 API)"""
    parser = _get_parser()
    
    # start_line과 end_line이 제공된 경우 직접 사용
    if start_line > 0 and end_line > 0:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            # 0-based index로 변환
            return parser._get_snippet(lines, start_line - 1, end_line - 1, max_lines)
        except Exception as e:
            return f"Error reading file: {str(e)}"
    
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
        return f"Error: {str(e)}"

def update_symbol_index(file_path: str, parse_result: dict) -> None:
    """
    파싱 결과를 기반으로 심볼 인덱스 업데이트
    """
    try:
        import claude_code_ai_brain
        context = claude_code_ai_brain.get_current_context()
        if not context:
            return
        symbol_index = context.get('symbol_index', {})
        for func in parse_result.get('functions', []):
            symbol_index[func['name']] = {'type': 'function', 'file_path': file_path, 'line_start': func.get('line_start'), 'line_end': func.get('line_end'), 'class_name': None}
        for cls in parse_result.get('classes', []):
            symbol_index[cls['name']] = {'type': 'class', 'file_path': file_path, 'line_start': cls.get('line_start'), 'line_end': cls.get('line_end'), 'class_name': None}
            for method in cls.get('methods', []):
                method_key = f"{cls['name']}.{method['name']}"
                symbol_index[method_key] = {'type': 'method', 'file_path': file_path, 'line_start': method.get('line_start'), 'line_end': method.get('line_end'), 'class_name': cls['name']}
        claude_code_ai_brain.update_cache('symbol_index', symbol_index)
    except Exception as e:
        _log(f'Failed to update symbol index: {e}', 'ERROR')