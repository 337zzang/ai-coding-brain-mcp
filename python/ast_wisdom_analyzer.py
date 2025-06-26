"""
AST 기반 코드 분석기
프로젝트별로 코드 패턴과 오류를 더 정확하게 감지
"""

import ast
import os
from typing import List, Dict, Any, Tuple
from pathlib import Path

class ASTWisdomAnalyzer:
    """AST를 사용한 고급 코드 분석기"""
    
    def __init__(self, wisdom_manager):
        self.wisdom = wisdom_manager
        self.issues = []
    
    def analyze_code(self, code: str, filename: str = "unknown.py") -> Dict[str, Any]:
        """코드를 AST로 분석하여 문제점 감지"""
        self.issues = []
        result = {
            'syntax_errors': [],
            'indentation_errors': [],
            'style_issues': [],
            'code_smells': [],
            'metrics': {}
        }
        
        # 1. 구문 분석 시도
        try:
            tree = ast.parse(code)
            
            # 2. AST 기반 분석
            self._analyze_imports(tree, result)
            self._analyze_functions(tree, result)
            self._analyze_classes(tree, result)
            self._analyze_variables(tree, result)
            self._check_code_complexity(tree, result)
            
        except SyntaxError as e:
            result['syntax_errors'].append({
                'line': e.lineno,
                'column': e.offset,
                'message': e.msg,
                'text': e.text
            })
            
        except IndentationError as e:
            result['indentation_errors'].append({
                'line': e.lineno,
                'message': str(e)
            })
            
        # 3. 줄 단위 분석 (AST로 잡지 못하는 것들)
        self._analyze_lines(code, result)
        
        # 4. Wisdom에 기록
        self._record_to_wisdom(result, filename)
        
        return result
    
    def _analyze_imports(self, tree: ast.AST, result: Dict[str, Any]):
        """import 분석"""
        imports = []
        import_lines = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
                    import_lines.add(node.lineno)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
                    import_lines.add(node.lineno)
        
        # 중복 import 감지
        duplicates = [imp for imp in imports if imports.count(imp) > 1]
        if duplicates:
            result['code_smells'].append({
                'type': 'duplicate_imports',
                'imports': list(set(duplicates))
            })
        
        result['metrics']['import_count'] = len(set(imports))
        result['metrics']['import_lines'] = list(import_lines)
    
    def _analyze_functions(self, tree: ast.AST, result: Dict[str, Any]):
        """함수 분석"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'args': len(node.args.args),
                    'decorators': len(node.decorator_list),
                    'body_length': len(node.body)
                }
                
                # 함수 복잡도 체크
                if func_info['body_length'] > 50:
                    result['code_smells'].append({
                        'type': 'long_function',
                        'name': node.name,
                        'line': node.lineno,
                        'length': func_info['body_length']
                    })
                
                # 너무 많은 인자
                if func_info['args'] > 5:
                    result['style_issues'].append({
                        'type': 'too_many_arguments',
                        'name': node.name,
                        'line': node.lineno,
                        'args': func_info['args']
                    })
                
                functions.append(func_info)
        
        result['metrics']['function_count'] = len(functions)
        result['metrics']['functions'] = functions
    
    def _analyze_classes(self, tree: ast.AST, result: Dict[str, Any]):
        """클래스 분석"""
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                class_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'methods': len(methods),
                    'base_classes': len(node.bases)
                }
                
                # 너무 많은 메서드
                if class_info['methods'] > 20:
                    result['code_smells'].append({
                        'type': 'large_class',
                        'name': node.name,
                        'line': node.lineno,
                        'methods': class_info['methods']
                    })
                
                classes.append(class_info)
        
        result['metrics']['class_count'] = len(classes)
        result['metrics']['classes'] = classes
    
    def _analyze_variables(self, tree: ast.AST, result: Dict[str, Any]):
        """변수 사용 분석"""
        # 정의된 변수와 사용된 변수 추적
        defined_vars = set()
        used_vars = set()
        
        class VarVisitor(ast.NodeVisitor):
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Store):
                    defined_vars.add(node.id)
                elif isinstance(node.ctx, ast.Load):
                    used_vars.add(node.id)
                self.generic_visit(node)
        
        VarVisitor().visit(tree)
        
        # 미사용 변수 감지
        unused = defined_vars - used_vars - {'self', '_', '__'}
        if unused:
            result['style_issues'].append({
                'type': 'unused_variables',
                'variables': list(unused)
            })
    
    def _check_code_complexity(self, tree: ast.AST, result: Dict[str, Any]):
        """코드 복잡도 측정"""
        # McCabe complexity 간단 버전
        complexity = 0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        result['metrics']['complexity'] = complexity
        
        if complexity > 10:
            result['code_smells'].append({
                'type': 'high_complexity',
                'complexity': complexity
            })
    
    def _analyze_lines(self, code: str, result: Dict[str, Any]):
        """줄 단위 분석"""
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 줄 끝 공백
            if line.endswith((' ', '\t')):
                result['style_issues'].append({
                    'type': 'trailing_whitespace',
                    'line': i
                })
            
            # 너무 긴 줄
            if len(line) > 100:
                result['style_issues'].append({
                    'type': 'line_too_long',
                    'line': i,
                    'length': len(line)
                })
            
            # TODO/FIXME 주석
            if 'TODO' in line or 'FIXME' in line:
                result['code_smells'].append({
                    'type': 'todo_comment',
                    'line': i,
                    'comment': line.strip()
                })
    
    def _record_to_wisdom(self, result: Dict[str, Any], filename: str):
        """분석 결과를 Wisdom에 기록"""
        # 주요 문제들만 기록
        if result['syntax_errors']:
            self.wisdom.track_error('SyntaxError', f"{filename}: {result['syntax_errors'][0]['message']}")
        
        if result['indentation_errors']:
            self.wisdom.track_mistake('indentation_error', filename)
        
        for smell in result['code_smells']:
            if smell['type'] == 'high_complexity':
                self.wisdom.track_mistake('complex_code', filename)
            elif smell['type'] == 'large_class':
                self.wisdom.track_mistake('large_class', filename)
