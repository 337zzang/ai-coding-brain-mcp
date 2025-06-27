"""
UnifiedAnalyzer: FileAnalyzer와 ASTWisdomAnalyzer의 통합 분석기
"""

import ast
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

class UnifiedAnalyzer:
    """통합 파일 분석기"""
    
    def __init__(self, wisdom_manager=None):
        self.wisdom_manager = wisdom_manager
        self.helpers = None
        self._init_helpers()
        
    def _init_helpers(self):
        """JSON REPL 환경의 helpers 초기화"""
        try:
            import sys
            if 'helpers' in sys.modules['__main__'].__dict__:
                self.helpers = sys.modules['__main__'].helpers
        except:
            pass
            
    def analyze(self, file_path: str) -> Dict[str, Any]:
        """파일 분석"""
        if not os.path.exists(file_path):
            return {'error': f'File not found: {file_path}'}
            
        # 언어 감지
        ext = Path(file_path).suffix.lower()
        language = 'python' if ext == '.py' else 'typescript' if ext in ['.ts', '.tsx'] else 'unknown'
        
        # 파일 읽기
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {'error': str(e), 'path': file_path, 'language': language}
            
        # Python 파일 분석
        if language == 'python':
            return self._analyze_python_simple(file_path, content)
        else:
            return {
                'path': file_path,
                'language': language,
                'summary': f'{language} file',
                'structure': {'imports': {'internal': [], 'external': []}, 'classes': [], 'functions': []},
                'quality': {'issues': [], 'stats': {}}
            }
            
    def _analyze_python_simple(self, file_path: str, content: str) -> Dict[str, Any]:
        """Python 파일 간단 분석"""
        try:
            tree = ast.parse(content)
            
            # 기본 구조 추출
            imports = {'internal': [], 'external': []}
            classes = []
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports['external'].append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    if node.level > 0 or module.startswith('.'):
                        imports['internal'].append(module)
                    else:
                        imports['external'].append(module)
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        'name': node.name,
                        'line': node.lineno,
                        'methods': [],
                        'docstring': ast.get_docstring(node) or ''
                    })
                elif isinstance(node, ast.FunctionDef):
                    functions.append({
                        'name': node.name,
                        'line': node.lineno,
                        'params': [arg.arg for arg in node.args.args],
                        'docstring': ast.get_docstring(node) or ''
                    })
                    
            return {
                'path': file_path,
                'language': 'python',
                'summary': f'{len(classes)} classes, {len(functions)} functions',
                'structure': {
                    'imports': imports,
                    'classes': classes,
                    'functions': functions
                },
                'quality': {
                    'issues': [],
                    'stats': {
                        'total_lines': len(content.splitlines()),
                        'classes': len(classes),
                        'functions': len(functions)
                    }
                }
            }
        except SyntaxError as e:
            return {
                'path': file_path,
                'language': 'python',
                'error': str(e),
                'summary': f'Syntax error: {e}',
                'structure': {'imports': {'internal': [], 'external': []}, 'classes': [], 'functions': []},
                'quality': {'issues': [{'type': 'error', 'message': str(e), 'line': e.lineno or 0}], 'stats': {}}
            }
