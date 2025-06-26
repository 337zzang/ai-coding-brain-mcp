"""
FileAnalyzer - 개별 파일 분석기

AST 분석과 AI 요약을 통해 파일의 구조와 의미를 파악합니다.
"""

import ast
import os
import re
from typing import Dict, List, Any, Optional, Set
from pathlib import Path


class FileAnalyzer:
    """개별 파일을 분석하는 클래스"""
    
    def __init__(self):
        """FileAnalyzer 초기화"""
        # helpers를 동적으로 import (JSON REPL 세션에서 사용)
        self.helpers = None
        self._init_helpers()
    
    def _init_helpers(self):
        """helpers 객체를 찾아서 초기화합니다."""
        import sys
        
        # 1. global_helpers 확인
        if 'global_helpers' in globals():
            self.helpers = globals()['global_helpers']
        # 2. 메인 모듈에서 확인
        elif hasattr(sys.modules.get('__main__', None), 'helpers'):
            self.helpers = sys.modules['__main__'].helpers
        # 3. 전역 변수에서 확인
        elif 'helpers' in globals():
            self.helpers = globals()['helpers']
    
    def analyze(self, file_path: str) -> Dict[str, Any]:
        """
        파일을 분석하여 구조와 의미를 추출합니다.
        
        Args:
            file_path: 분석할 파일의 절대 경로
            
        Returns:
            분석 결과 딕셔너리
        """
        result = {
            'summary': '',
            'imports': {'internal': [], 'external': []},
            'classes': [],
            'functions': [],
            'wisdom_insights': {}
        }
        
        # 파일 확장자 확인
        ext = Path(file_path).suffix.lower()
        
        if ext == '.py':
            # Python 파일 분석
            return self._analyze_python(file_path)
        elif ext in ['.ts', '.tsx', '.js', '.jsx']:
            # TypeScript/JavaScript 파일 분석
            return self._analyze_typescript(file_path)
        else:
            result['summary'] = 'Unsupported file type'
            return result
    
    def _analyze_python(self, file_path: str) -> Dict[str, Any]:
        """Python 파일을 분석합니다."""
        result = {
            'summary': '',
            'imports': {'internal': [], 'external': []},
            'classes': [],
            'functions': [],
            'wisdom_insights': {}
        }
        
        try:
            # helpers.parse_with_snippets 사용 (있는 경우)
            if self.helpers and hasattr(self.helpers, 'parse_with_snippets'):
                ast_result = self.helpers.parse_with_snippets(file_path)
                
                if ast_result and ast_result.get('parsing_success'):
                    # AST 결과에서 정보 추출
                    result['classes'] = self._extract_class_info(ast_result.get('classes', []))
                    result['functions'] = self._extract_function_info(ast_result.get('functions', []))
                    
                    # import 정보는 직접 파싱
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    result['imports'] = self._extract_imports_from_content(content)
            else:
                # helpers가 없으면 직접 AST 파싱
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=file_path)
                result = self._analyze_ast_tree(tree, content)
            
            # AI 요약 생성 (간단한 규칙 기반)
            result['summary'] = self._generate_summary(file_path, result)
            
            # Wisdom insights 추가
            result['wisdom_insights'] = self._analyze_code_quality(file_path, result)
            
        except Exception as e:
            result['summary'] = f'Analysis failed: {str(e)}'
        
        return result
    
    def _analyze_typescript(self, file_path: str) -> Dict[str, Any]:
        """TypeScript/JavaScript 파일을 분석합니다."""
        result = {
            'summary': '',
            'imports': {'internal': [], 'external': []},
            'classes': [],
            'functions': [],
            'wisdom_insights': {}
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 정규식으로 기본 구조 추출
            # Import 추출
            import_pattern = r'import\s+(?:{[^}]+}|[\w\s,]+)\s+from\s+[\'"]([^\'"]+)[\'"]'
            imports = re.findall(import_pattern, content)
            
            for imp in imports:
                if imp.startswith('.'):
                    result['imports']['internal'].append(imp)
                else:
                    result['imports']['external'].append(imp)
            
            # 클래스 추출
            class_pattern = r'(?:export\s+)?class\s+(\w+)'
            classes = re.findall(class_pattern, content)
            result['classes'] = [{'name': cls, 'summary': ''} for cls in classes]
            
            # 함수 추출
            func_pattern = r'(?:export\s+)?(?:async\s+)?function\s+(\w+)|(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\('
            functions = re.findall(func_pattern, content)
            result['functions'] = [
                {'name': func[0] or func[1], 'summary': ''} 
                for func in functions if func[0] or func[1]
            ]
            
            # 요약 생성
            result['summary'] = self._generate_summary(file_path, result)
            
        except Exception as e:
            result['summary'] = f'Analysis failed: {str(e)}'
        
        return result
    
    def _analyze_ast_tree(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """AST 트리를 직접 분석합니다."""
        result = {
            'imports': {'internal': [], 'external': []},
            'classes': [],
            'functions': [],
        }
        
        for node in ast.walk(tree):
            # Import 분석
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result['imports']['external'].append(alias.name)
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                if module.startswith('.'):
                    result['imports']['internal'].append(module)
                else:
                    result['imports']['external'].append(module)
            
            # 클래스 분석
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'methods': [],
                    'summary': self._get_docstring(node) or ''
                }
                
                # 메서드 추출
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        class_info['methods'].append({
                            'name': item.name,
                            'line': item.lineno
                        })
                
                result['classes'].append(class_info)
            
            # 함수 분석 (클래스 밖의 함수만)
            elif isinstance(node, ast.FunctionDef) and not self._is_nested_function(node, tree):
                func_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'params': [arg.arg for arg in node.args.args],
                    'summary': self._get_docstring(node) or ''
                }
                result['functions'].append(func_info)
        
        return result
    
    def _is_nested_function(self, node: ast.FunctionDef, tree: ast.AST) -> bool:
        """함수가 클래스나 다른 함수 내부에 있는지 확인합니다."""
        for parent in ast.walk(tree):
            if isinstance(parent, (ast.ClassDef, ast.FunctionDef)):
                for child in ast.iter_child_nodes(parent):
                    if child == node and parent != node:
                        return True
        return False
    
    def _get_docstring(self, node: ast.AST) -> Optional[str]:
        """노드의 docstring을 추출합니다."""
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
            if (node.body and 
                isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, ast.Str)):
                return node.body[0].value.s.strip()
        return None
    
    def _extract_imports_from_content(self, content: str) -> Dict[str, List[str]]:
        """파일 내용에서 import 정보를 추출합니다."""
        imports = {'internal': [], 'external': []}
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports['external'].append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    if module.startswith('.') or not module:
                        # 상대 import
                        imports['internal'].append(module or '.')
                    else:
                        imports['external'].append(module)
        except:
            pass
        
        return imports
    
    def _extract_class_info(self, classes: List[Dict]) -> List[Dict[str, Any]]:
        """helpers의 클래스 정보를 변환합니다."""
        result = []
        
        for cls in classes:
            class_info = {
                'name': cls.get('name', ''),
                'line': cls.get('line_start', 0),
                'methods': [
                    {'name': m.get('name', ''), 'line': m.get('line_start', 0)}
                    for m in cls.get('methods', [])
                ],
                'summary': cls.get('docstring', '') or ''
            }
            result.append(class_info)
        
        return result
    
    def _extract_function_info(self, functions: List[Dict]) -> List[Dict[str, Any]]:
        """helpers의 함수 정보를 변환합니다."""
        result = []
        
        for func in functions:
            func_info = {
                'name': func.get('name', ''),
                'line': func.get('line_start', 0),
                'params': func.get('args', []),
                'summary': func.get('docstring', '') or ''
            }
            result.append(func_info)
        
        return result
    
    def _generate_summary(self, file_path: str, analysis: Dict[str, Any]) -> str:
        """파일의 요약을 생성합니다."""
        filename = Path(file_path).name
        
        # 파일 이름과 구조에서 역할 추론
        if 'test' in filename.lower():
            return f"테스트 파일 - {len(analysis['functions'])}개의 테스트 함수 포함"
        
        if 'handler' in filename.lower():
            return f"핸들러 모듈 - {len(analysis['functions'])}개의 핸들러 함수 정의"
        
        if 'analyzer' in filename.lower():
            return f"분석 모듈 - {len(analysis['classes'])}개의 분석 클래스 포함"
        
        if 'manager' in filename.lower():
            return f"관리 모듈 - {len(analysis['classes'])}개의 관리 클래스 정의"
        
        # 일반적인 요약
        class_count = len(analysis['classes'])
        func_count = len(analysis['functions'])
        
        if class_count > 0 and func_count > 0:
            return f"{class_count}개의 클래스와 {func_count}개의 함수를 포함하는 모듈"
        elif class_count > 0:
            return f"{class_count}개의 클래스를 정의하는 모듈"
        elif func_count > 0:
            return f"{func_count}개의 유틸리티 함수를 제공하는 모듈"
        else:
            return "구조 분석이 필요한 모듈"
    
    def _analyze_code_quality(self, file_path: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """코드 품질 관련 인사이트를 생성합니다."""
        insights = {
            'potential_issues': [],
            'improvement_suggestions': []
        }
        
        # 긴 함수 감지
        for func in analysis['functions']:
            if 'line_end' in func and 'line' in func:
                length = func.get('line_end', 0) - func.get('line', 0)
                if length > 50:
                    insights['potential_issues'].append(
                        f"함수 '{func['name']}'이(가) {length}줄로 너무 깁니다"
                    )
        
        # 순환 import 가능성
        internal_imports = analysis['imports']['internal']
        if len(internal_imports) > 5:
            insights['improvement_suggestions'].append(
                "내부 import가 많습니다. 모듈 구조 재검토 필요"
            )
        
        return insights


# 테스트 코드
if __name__ == '__main__':
    analyzer = FileAnalyzer()
    
    # 현재 파일 분석 테스트
    result = analyzer.analyze(__file__)
    print(f"분석 결과: {result}")
