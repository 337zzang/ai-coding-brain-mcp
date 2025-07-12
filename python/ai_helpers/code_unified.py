"""
통합 코드 작업 모듈 - AST 기반 코드 분석 및 수정
중복 제거 및 성능 최적화
"""
import ast
import os
import re
import difflib
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Union, Tuple, Literal
from pathlib import Path
from .helper_result import HelperResult

# 코드 요소 타입 정의
ElementType = Literal['function', 'class', 'method', 'variable', 'import']
PositionType = Literal['before', 'after', 'replace']


class UnifiedCodeOperations:
    """통합 코드 작업 클래스 - AST 기반"""
    
    def __init__(self):
        self.encoding = 'utf-8'
        self._cache = {}
        self._verbose = False
    
    def set_verbose(self, enabled: bool):
        """상세 출력 모드 설정"""
        self._verbose = enabled
    
    def parse_code(self, file_path: str, include_snippets: bool = True) -> HelperResult:
        """
        코드 파일 파싱 및 구조 분석
        
        Args:
            file_path: 파일 경로
            include_snippets: 코드 스니펫 포함 여부
            
        Returns:
            HelperResult with parsed structure
        """
        try:
            path = Path(file_path).resolve()
            if not path.exists():
                return HelperResult(False, error=f"File not found: {file_path}")
            
            with open(path, 'r', encoding=self.encoding) as f:
                content = f.read()
            
            # AST 파싱
            tree = ast.parse(content, filename=str(path))
            
            # 구조 추출
            structure = {
                'file_path': str(path),
                'language': 'python',
                'imports': self._extract_imports(tree, content, include_snippets),
                'classes': self._extract_classes(tree, content, include_snippets),
                'functions': self._extract_functions(tree, content, include_snippets),
                'variables': self._extract_variables(tree, content, include_snippets),
                'line_count': len(content.splitlines()),
                'has_main': self._has_main_block(tree)
            }
            
            return HelperResult(True, data=structure)
            
        except SyntaxError as e:
            return HelperResult(False, error=f"Syntax error: {e}")
        except Exception as e:
            return HelperResult(False, error=f"Parse failed: {str(e)}")
    
    def modify_code(self,
                   file_path: str,
                   target: str,
                   element_type: ElementType,
                   operation: PositionType,
                   new_code: str,
                   class_name: Optional[str] = None,
                   preserve_format: bool = True,
                   backup: bool = True) -> HelperResult:
        """
        통합 코드 수정 함수
        
        Args:
            file_path: 파일 경로
            target: 대상 요소 이름
            element_type: 요소 타입 ('function', 'class', 'method', 'variable', 'import')
            operation: 작업 타입 ('before', 'after', 'replace')
            new_code: 새로운 코드
            class_name: 메서드의 경우 클래스 이름
            preserve_format: 포맷 유지 여부
            backup: 백업 생성 여부
            
        Returns:
            HelperResult with modification result
        """
        try:
            path = Path(file_path).resolve()
            if not path.exists():
                return HelperResult(False, error=f"File not found: {file_path}")
            
            # 백업 생성
            if backup:
                backup_path = self._create_backup(path)
            
            # 코드 읽기
            with open(path, 'r', encoding=self.encoding) as f:
                original_content = f.read()
            
            # AST 파싱
            tree = ast.parse(original_content)
            
            # 요소 타입별 처리
            if element_type == 'function':
                modifier = FunctionModifier(target, operation, new_code, preserve_format)
            elif element_type == 'class':
                modifier = ClassModifier(target, operation, new_code, preserve_format)
            elif element_type == 'method':
                if not class_name:
                    return HelperResult(False, error="class_name required for method modification")
                modifier = MethodModifier(class_name, target, operation, new_code, preserve_format)
            else:
                return HelperResult(False, error=f"Unsupported element type: {element_type}")
            
            # AST 변환
            modified_tree = modifier.visit(tree)
            
            # 코드 생성
            modified_content = ast.unparse(modified_tree)
            
            # 포맷 보존
            if preserve_format:
                modified_content = self._preserve_format(original_content, modified_content)
            
            # 파일 쓰기
            with open(path, 'w', encoding=self.encoding) as f:
                f.write(modified_content)
            
            return HelperResult(True, data={
                'file_path': str(path),
                'operation': operation,
                'target': target,
                'element_type': element_type,
                'backup_path': str(backup_path) if backup else None
            })
            
        except Exception as e:
            return HelperResult(False, error=f"Code modification failed: {str(e)}")
    
    def find_element(self, file_path: str, element_name: str,
                    element_type: Optional[ElementType] = None) -> HelperResult:
        """코드 요소 찾기"""
        try:
            parse_result = self.parse_code(file_path, include_snippets=True)
            if not parse_result.ok:
                return parse_result
            
            data = parse_result.data
            results = []
            
            # 타입별 검색
            if not element_type or element_type == 'function':
                for func in data.get('functions', []):
                    if element_name in func['name']:
                        results.append({
                            'type': 'function',
                            'name': func['name'],
                            'line': func['line'],
                            'snippet': func.get('snippet', '')
                        })
            
            if not element_type or element_type == 'class':
                for cls in data.get('classes', []):
                    if element_name in cls['name']:
                        results.append({
                            'type': 'class',
                            'name': cls['name'],
                            'line': cls['line'],
                            'snippet': cls.get('snippet', '')
                        })
            
            return HelperResult(True, data={
                'results': results,
                'count': len(results),
                'file_path': file_path
            })
            
        except Exception as e:
            return HelperResult(False, error=f"Find element failed: {str(e)}")
    
    def get_snippet(self, file_path: str, element_name: str,
                   element_type: ElementType,
                   context_lines: int = 3) -> HelperResult:
        """코드 스니펫 가져오기"""
        try:
            # 요소 찾기
            find_result = self.find_element(file_path, element_name, element_type)
            if not find_result.ok:
                return find_result
            
            if not find_result.data['results']:
                return HelperResult(False, error=f"{element_type} '{element_name}' not found")
            
            # 첫 번째 결과 사용
            element = find_result.data['results'][0]
            
            # 파일 읽기
            with open(file_path, 'r', encoding=self.encoding) as f:
                lines = f.readlines()
            
            # 컨텍스트 포함 스니펫 생성
            line_num = element['line'] - 1  # 0-based
            start = max(0, line_num - context_lines)
            end = min(len(lines), line_num + context_lines + 20)  # 함수/클래스 전체 포함
            
            snippet_lines = []
            for i in range(start, end):
                prefix = ">>>" if i == line_num else "   "
                snippet_lines.append(f"{prefix} {i+1:4d} | {lines[i].rstrip()}")
            
            return HelperResult(True, data={
                'element': element,
                'snippet': '\n'.join(snippet_lines),
                'file_path': file_path
            })
            
        except Exception as e:
            return HelperResult(False, error=f"Get snippet failed: {str(e)}")
    
    # Private helper methods
    def _extract_imports(self, tree: ast.AST, content: str, include_snippets: bool) -> List[Dict]:
        """Import 문 추출"""
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'type': 'import',
                        'name': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno,
                        'snippet': ast.get_source_segment(content, node) if include_snippets else None
                    })
            elif isinstance(node, ast.ImportFrom):
                imports.append({
                    'type': 'import_from',
                    'module': node.module,
                    'names': [(n.name, n.asname) for n in node.names],
                    'line': node.lineno,
                    'snippet': ast.get_source_segment(content, node) if include_snippets else None
                })
        return imports
    
    def _extract_classes(self, tree: ast.AST, content: str, include_snippets: bool) -> List[Dict]:
        """클래스 추출"""
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append({
                            'name': item.name,
                            'line': item.lineno,
                            'async': isinstance(item, ast.AsyncFunctionDef),
                            'args': [arg.arg for arg in item.args.args]
                        })
                
                classes.append({
                    'name': node.name,
                    'line': node.lineno,
                    'methods': methods,
                    'bases': [ast.unparse(base) for base in node.bases],
                    'docstring': ast.get_docstring(node),
                    'snippet': ast.get_source_segment(content, node)[:200] + '...' if include_snippets else None
                })
        return classes
    
    def _extract_functions(self, tree: ast.AST, content: str, include_snippets: bool) -> List[Dict]:
        """함수 추출 (최상위 레벨만)"""
        functions = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append({
                    'name': node.name,
                    'line': node.lineno,
                    'async': isinstance(node, ast.AsyncFunctionDef),
                    'args': [arg.arg for arg in node.args.args],
                    'returns': ast.unparse(node.returns) if node.returns else None,
                    'docstring': ast.get_docstring(node),
                    'snippet': ast.get_source_segment(content, node)[:200] + '...' if include_snippets else None
                })
        return functions
    
    def _extract_variables(self, tree: ast.AST, content: str, include_snippets: bool) -> List[Dict]:
        """전역 변수 추출"""
        variables = []
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.append({
                            'name': target.id,
                            'line': node.lineno,
                            'value': ast.unparse(node.value)[:50],
                            'snippet': ast.get_source_segment(content, node) if include_snippets else None
                        })
        return variables
    
    def _has_main_block(self, tree: ast.AST) -> bool:
        """__main__ 블록 존재 여부"""
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                if (isinstance(node.test, ast.Compare) and
                    isinstance(node.test.left, ast.Name) and
                    node.test.left.id == '__name__'):
                    return True
        return False
    
    def _create_backup(self, path: Path) -> Path:
        """백업 생성"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.with_suffix(f'.{timestamp}.bak')
        shutil.copy2(path, backup_path)
        return backup_path
    
    def _preserve_format(self, original: str, modified: str) -> str:
        """원본 포맷 유지 (간단한 구현)"""
        # TODO: 더 정교한 포맷 보존 로직 구현
        return modified


# AST 변환 클래스들
class FunctionModifier(ast.NodeTransformer):
    """함수 수정 클래스"""
    
    def __init__(self, target: str, operation: PositionType, new_code: str, preserve_format: bool):
        self.target = target
        self.operation = operation
        self.new_code = new_code
        self.preserve_format = preserve_format
        self.modified = False
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        if node.name == self.target and not self.modified:
            self.modified = True
            
            if self.operation == 'replace':
                # 새 코드 파싱
                new_node = ast.parse(self.new_code).body[0]
                return new_node
            elif self.operation == 'before':
                # 새 노드를 현재 노드 앞에 추가
                new_node = ast.parse(self.new_code).body[0]
                return [new_node, node]
            elif self.operation == 'after':
                # 새 노드를 현재 노드 뒤에 추가
                new_node = ast.parse(self.new_code).body[0]
                return [node, new_node]
        
        return self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        # 동일한 로직 적용
        return self.visit_FunctionDef(node)


class ClassModifier(ast.NodeTransformer):
    """클래스 수정 클래스"""
    
    def __init__(self, target: str, operation: PositionType, new_code: str, preserve_format: bool):
        self.target = target
        self.operation = operation
        self.new_code = new_code
        self.preserve_format = preserve_format
        self.modified = False
    
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        if node.name == self.target and not self.modified:
            self.modified = True
            
            if self.operation == 'replace':
                new_node = ast.parse(self.new_code).body[0]
                return new_node
            elif self.operation == 'before':
                new_node = ast.parse(self.new_code).body[0]
                return [new_node, node]
            elif self.operation == 'after':
                new_node = ast.parse(self.new_code).body[0]
                return [node, new_node]
        
        return self.generic_visit(node)


class MethodModifier(ast.NodeTransformer):
    """메서드 수정 클래스"""
    
    def __init__(self, class_name: str, method_name: str, operation: PositionType,
                 new_code: str, preserve_format: bool):
        self.class_name = class_name
        self.method_name = method_name
        self.operation = operation
        self.new_code = new_code
        self.preserve_format = preserve_format
        self.in_target_class = False
        self.modified = False
    
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        if node.name == self.class_name:
            self.in_target_class = True
            result = self.generic_visit(node)
            self.in_target_class = False
            return result
        return self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        if self.in_target_class and node.name == self.method_name and not self.modified:
            self.modified = True
            
            if self.operation == 'replace':
                # 인덴트 조정
                new_node = ast.parse(self.new_code).body[0]
                return new_node
            # before/after는 클래스 내에서 처리 필요
        
        return self.generic_visit(node)


# 전역 인스턴스
_code_ops = UnifiedCodeOperations()


# 공개 API 함수들
def parse_code(file_path: str, **kwargs) -> HelperResult:
    """코드 파싱"""
    return _code_ops.parse_code(file_path, **kwargs)


def replace_function(file_path: str, function_name: str, new_code: str, **kwargs) -> HelperResult:
    """함수 교체"""
    return _code_ops.modify_code(file_path, function_name, 'function', 'replace', new_code, **kwargs)


def replace_class(file_path: str, class_name: str, new_code: str, **kwargs) -> HelperResult:
    """클래스 교체"""
    return _code_ops.modify_code(file_path, class_name, 'class', 'replace', new_code, **kwargs)


def replace_method(file_path: str, class_name: str, method_name: str, new_code: str, **kwargs) -> HelperResult:
    """메서드 교체"""
    return _code_ops.modify_code(file_path, method_name, 'method', 'replace', new_code,
                                class_name=class_name, **kwargs)


def add_function(file_path: str, target: str, new_code: str, position: Literal['before', 'after'] = 'after', **kwargs) -> HelperResult:
    """함수 추가"""
    return _code_ops.modify_code(file_path, target, 'function', position, new_code, **kwargs)


def add_method_to_class(file_path: str, class_name: str, new_method: str, **kwargs) -> HelperResult:
    """클래스에 메서드 추가"""
    # TODO: 클래스 내부에 메서드 추가하는 로직 구현
    return HelperResult(False, error="Not implemented yet")


def get_code_snippet(file_path: str, element_name: str, element_type: ElementType = 'function', **kwargs) -> HelperResult:
    """코드 스니펫 가져오기"""
    return _code_ops.get_snippet(file_path, element_name, element_type, **kwargs)


def find_code_element(file_path: str, element_name: str, element_type: Optional[ElementType] = None) -> HelperResult:
    """코드 요소 찾기"""
    return _code_ops.find_element(file_path, element_name, element_type)


# 설정 함수
def set_verbose(enabled: bool):
    """상세 출력 모드 설정"""
    _code_ops.set_verbose(enabled)