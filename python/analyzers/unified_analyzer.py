"""
UnifiedAnalyzer: FileAnalyzer와 ASTWisdomAnalyzer의 통합 분석기
한 번의 AST 파싱으로 구조 정보와 코드 품질을 동시에 분석합니다.
"""

import ast
import os
import re
from typing import Dict, List, Any, Optional, Tuple, Set
from pathlib import Path
from collections import defaultdict
import textwrap

class UnifiedAnalyzer:
    """통합 파일 분석기 - 구조 정보와 코드 품질을 동시에 분석"""
    
    def __init__(self, wisdom_manager=None):
        """
        Args:
            wisdom_manager: ProjectWisdomManager 인스턴스 (선택사항)
        """
        self.wisdom_manager = wisdom_manager
        self.helpers = None
        self._init_helpers()
        
        # 코드 품질 기준값
        self.LONG_FUNCTION_LINES = 50
        self.LARGE_CLASS_METHODS = 20
        self.HIGH_COMPLEXITY = 10
        self.MAX_FUNCTION_PARAMS = 5
        
    def _init_helpers(self):
        """JSON REPL 환경의 helpers 초기화"""
        try:
            import sys
            if 'helpers' in sys.modules['__main__'].__dict__:
                self.helpers = sys.modules['__main__'].helpers
        except:
            pass
            
    def analyze(self, file_path: str) -> Dict[str, Any]:
        """
        파일을 분석하여 구조 정보와 품질 분석 결과를 반환
        
        Returns:
            {
                'path': str,
                'language': str,
                'summary': str,
                'structure': {
                    'imports': {'internal': [], 'external': []},
                    'classes': [...],
                    'functions': [...]
                },
                'quality': {
                    'issues': [...],
                    'stats': {...},
                    'suggestions': [...]
                },
                'wisdom_insights': {...}
            }
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
            
        # 언어 감지
        ext = Path(file_path).suffix.lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript', 
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript'
        }
        language = language_map.get(ext, 'unknown')
        
        # 파일 내용 읽기
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {
                'path': file_path,
                'language': language,
                'error': f"파일 읽기 실패: {str(e)}"
            }
            
        # 언어별 분석 수행
        if language == 'python':
            result = self._analyze_python(file_path, content)
        elif language in ['javascript', 'typescript']:
            result = self._analyze_typescript(file_path, content)
        else:
            result = {
                'path': file_path,
                'language': language,
                'summary': f"지원하지 않는 파일 형식: {ext}"
            }
            
        # 공통 정보 추가
        result['path'] = file_path
        result['language'] = language
        
        return result
        
    def _analyze_python(self, file_path: str, content: str) -> Dict[str, Any]:
        """Python 파일을 AST로 파싱하여 종합 분석"""
        try:
            # AST 파싱
            tree = ast.parse(content)
            
            # 구조 정보 추출
            structure_info = self._extract_structure_info(tree, content)
            
            # 코드 품질 분석
            quality_info = self._analyze_code_quality(tree, content, structure_info)
            
            # 파일 요약 생성
            summary = self._generate_summary(file_path, {
                'structure': structure_info,
                'quality': quality_info
            })
            
            # Wisdom insights 생성
            wisdom_insights = self._generate_wisdom_insights(structure_info, quality_info)
            
            # Wisdom 시스템에 기록
            if self.wisdom_manager and quality_info.get('issues'):
                self._record_to_wisdom(quality_info, file_path)
                
            return {
                'summary': summary,
                'structure': structure_info,
                'quality': quality_info,
                'wisdom_insights': wisdom_insights
            }
            
        except SyntaxError as e:
            return {
                'summary': f"구문 오류: {str(e)}",
                'structure': {'imports': {'internal': [], 'external': []}, 'classes': [], 'functions': []},
                'quality': {'issues': [{'type': 'error', 'message': str(e), 'line': e.lineno or 0, 'severity': 'error'}]},
                'error': str(e)
            }
            
    def _extract_structure_info(self, tree: ast.AST, content: str) -> Dict[str, Any]:
        """AST에서 구조 정보 추출"""
        imports = {'internal': [], 'external': []}
        classes = []
        functions = []
        
        for node in ast.walk(tree):
            # Import 분석
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports['external'].append(alias.name)
                    
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                level = node.level
                
                # 상대 import는 내부로 분류
                if level > 0 or module.startswith('.'):
                    imports['internal'].append(module)
                else:
                    # TODO: 프로젝트 패키지명 기반 판별 개선 필요
                    imports['external'].append(module)
                    
            # 클래스 정보 추출
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'end_line': node.end_lineno if hasattr(node, 'end_lineno') else None,
                    'methods': [],
                    'docstring': ast.get_docstring(node) or '',
                    'bases': [self._get_node_name(base) for base in node.bases],
                    'decorators': [self._get_node_name(dec) for dec in node.decorator_list]
                }
                
                # 메서드 추출
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        class_info['methods'].append({
                            'name': item.name,
                            'line': item.lineno,
                            'params': [arg.arg for arg in item.args.args if arg.arg != 'self']
                        })
                        
                classes.append(class_info)
                
            # 함수 정보 추출 (최상위 레벨만)
            elif isinstance(node, ast.FunctionDef) and not self._is_nested_function(node, tree):
                function_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'end_line': node.end_lineno if hasattr(node, 'end_lineno') else None,
                    'params': [arg.arg for arg in node.args.args],
                    'docstring': ast.get_docstring(node) or '',
                    'decorators': [self._get_node_name(dec) for dec in node.decorator_list],
                    'is_async': isinstance(node, ast.AsyncFunctionDef)
                }
                functions.append(function_info)
                
        return {
            'imports': imports,
            'classes': classes,
            'functions': functions
        }
        
    def _analyze_code_quality(self, tree: ast.AST, content: str, structure_info: Dict) -> Dict[str, Any]:
        """코드 품질 분석"""
        issues = []
        stats = {
            'total_lines': len(content.splitlines()),
            'code_lines': 0,
            'complexity': 0,
            'unused_imports': [],
            'unused_variables': [],
            'long_functions': [],
            'large_classes': []
        }
        
        # 코드 라인 수 계산 (빈 줄과 주석 제외)
        for line in content.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                stats['code_lines'] += 1
                
        # 사용된 이름 수집
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
                
        # Import 사용 여부 확인
        all_imports = structure_info['imports']['internal'] + structure_info['imports']['external']
        for imp in all_imports:
            imp_name = imp.split('.')[0]
            if imp_name and imp_name not in used_names:
                stats['unused_imports'].append(imp)
                issues.append({
                    'type': 'code_smell',
                    'message': f"미사용 import: {imp}",
                    'line': 0,  # TODO: import 라인 번호 추출
                    'severity': 'warning'
                })
                
        # 함수 분석
        for func in structure_info['functions']:
            # 함수 길이 체크
            if func.get('end_line') and func.get('line'):
                func_length = func['end_line'] - func['line']
                if func_length > self.LONG_FUNCTION_LINES:
                    stats['long_functions'].append(func['name'])
                    issues.append({
                        'type': 'code_smell',
                        'message': f"긴 함수: {func['name']} ({func_length}줄)",
                        'line': func['line'],
                        'severity': 'warning'
                    })
                    
            # 매개변수 개수 체크
            if len(func.get('params', [])) > self.MAX_FUNCTION_PARAMS:
                issues.append({
                    'type': 'code_smell',
                    'message': f"매개변수가 너무 많음: {func['name']} ({len(func['params'])}개)",
                    'line': func['line'],
                    'severity': 'info'
                })
                
        # 클래스 분석
        for cls in structure_info['classes']:
            if len(cls.get('methods', [])) > self.LARGE_CLASS_METHODS:
                stats['large_classes'].append(cls['name'])
                issues.append({
                    'type': 'code_smell',
                    'message': f"큰 클래스: {cls['name']} (메서드 {len(cls['methods'])}개)",
                    'line': cls['line'],
                    'severity': 'warning'
                })
                
        # 복잡도 계산 (간단한 버전)
        complexity_visitor = ComplexityVisitor()
        complexity_visitor.visit(tree)
        stats['complexity'] = complexity_visitor.complexity
        
        if stats['complexity'] > self.HIGH_COMPLEXITY:
            issues.append({
                'type': 'code_smell',
                'message': f"높은 복잡도: {stats['complexity']}",
                'line': 0,
                'severity': 'warning'
            })
            
        return {
            'issues': issues,
            'stats': stats,
            'suggestions': self._generate_suggestions(issues, stats)
        }
        
    def _analyze_typescript(self, file_path: str, content: str) -> Dict[str, Any]:
        """TypeScript/JavaScript 파일 분석 (정규표현식 기반, 향후 개선 예정)"""
        # 기존 FileAnalyzer의 TypeScript 분석 로직 활용
        imports = {'internal': [], 'external': []}
        classes = []
        functions = []
        
        # Import 추출 - 간단한 패턴 사용
        import_lines = [line for line in content.splitlines() if line.strip().startswith('import')]
        for line in import_lines:
            if ' from ' in line:
                parts = line.split(' from ')
                if len(parts) >= 2:
                    module = parts[1].strip().strip(';').strip('"').strip("'")
                    if module.startswith('.'):
                        imports['internal'].append(module)
                    else:
                        imports['external'].append(module)
                
        # 클래스 추출
        class_pattern = r"(?:export\s+)?class\s+(\w+)"
        for match in re.finditer(class_pattern, content):
            classes.append({
                'name': match.group(1),
                'line': content[:match.start()].count('\n') + 1,
                'methods': [],
                'docstring': ''
            })
            
        # 함수 추출
        func_patterns = [
            r"(?:export\s+)?(?:async\s+)?function\s+(\w+)",
            r"(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\(.*?\)\s*=>",
            r"(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?function"
        ]
        
        for pattern in func_patterns:
            for match in re.finditer(pattern, content):
                functions.append({
                    'name': match.group(1),
                    'line': content[:match.start()].count('\n') + 1,
                    'params': [],
                    'docstring': ''
                })
                
        # 기본적인 품질 분석
        issues = []
        stats = {
            'total_lines': len(content.splitlines()),
            'code_lines': sum(1 for line in content.splitlines() if line.strip() and not line.strip().startswith('//')),
            'complexity': 0,
            'unused_imports': [],
            'unused_variables': [],
            'long_functions': [],
            'large_classes': []
        }
        
        # console 사용 감지
        console_lines = []
        for i, line in enumerate(content.splitlines(), 1):
            if 'console.' in line and any(method in line for method in ['log', 'error', 'warn', 'info']):
                console_lines.append((i, line.strip()))
                
        for line_num, line_content in console_lines:
            issues.append({
                'type': 'code_smell',
                'message': f"console 사용 감지: {line_content[:50]}...",
                'line': line_num,
                'severity': 'warning'
            })
                
        return {
            'summary': f"TypeScript 파일: {len(classes)}개 클래스, {len(functions)}개 함수",
            'structure': {
                'imports': imports,
                'classes': classes,
                'functions': functions
            },
            'quality': {
                'issues': issues,
                'stats': stats,
                'suggestions': []
            },
            'wisdom_insights': {
                'note': 'TypeScript 분석은 현재 기본적인 수준입니다. Phase 3에서 tree-sitter로 개선 예정입니다.'
            }
        }
        

    def _generate_summary(self, file_path: str, analysis: Dict) -> str:
        """분석 결과를 바탕으로 파일 요약 생성"""
        structure = analysis.get('structure', {})
        quality = analysis.get('quality', {})
        
        num_classes = len(structure.get('classes', []))
        num_functions = len(structure.get('functions', []))
        num_issues = len(quality.get('issues', []))
        
        summary_parts = []
        
        # 기본 정보
        if num_classes > 0:
            summary_parts.append(f"{num_classes}개의 클래스")
        if num_functions > 0:
            summary_parts.append(f"{num_functions}개의 함수")
            
        # 주요 클래스/함수 언급
        if structure.get('classes'):
            main_classes = [c['name'] for c in structure['classes'][:3]]
            summary_parts.append(f"주요 클래스: {', '.join(main_classes)}")
            
        # 품질 이슈
        if num_issues > 0:
            summary_parts.append(f"{num_issues}개의 코드 품질 이슈 발견")
            
        if summary_parts:
            return f"{Path(file_path).name}: " + ", ".join(summary_parts)
        else:
            return f"{Path(file_path).name}: 빈 파일 또는 분석 불가"
            
    def _generate_wisdom_insights(self, structure: Dict, quality: Dict) -> Dict[str, List[str]]:
        """Wisdom insights 생성"""
        insights = {
            'potential_issues': [],
            'improvement_suggestions': []
        }
        
        # 구조적 이슈
        if len(structure.get('imports', {}).get('internal', [])) > 10:
            insights['potential_issues'].append("많은 내부 의존성 - 모듈 분리 고려")
            
        # 품질 기반 제안
        stats = quality.get('stats', {})
        if stats.get('long_functions'):
            insights['improvement_suggestions'].append(
                f"긴 함수 리팩토링: {', '.join(stats['long_functions'])}"
            )
            
        if stats.get('unused_imports'):
            insights['improvement_suggestions'].append(
                f"미사용 import 제거: {', '.join(stats['unused_imports'][:3])}"
            )
            
        return insights
        
    def _generate_suggestions(self, issues: List[Dict], stats: Dict) -> List[str]:
        """개선 제안 생성"""
        suggestions = []
        
        # 이슈 유형별 집계
        issue_types = defaultdict(int)
        for issue in issues:
            issue_types[issue['type']] += 1
            
        if issue_types['code_smell'] > 5:
            suggestions.append("코드 스멜이 많습니다. 리팩토링을 고려하세요.")
            
        if stats.get('complexity', 0) > self.HIGH_COMPLEXITY:
            suggestions.append("복잡도가 높습니다. 함수를 더 작은 단위로 분리하세요.")
            
        if stats.get('long_functions'):
            suggestions.append("긴 함수를 더 작은 함수로 분리하여 가독성을 높이세요.")
            
        return suggestions
        
    def _record_to_wisdom(self, quality_result: Dict, file_path: str) -> None:
        """Wisdom 시스템에 발견된 문제점 기록"""
        if not self.wisdom_manager:
            return
            
        # 주요 이슈 기록
        for issue in quality_result.get('issues', []):
            if issue['severity'] in ['error', 'warning']:
                if 'console' in issue['message']:
                    self.wisdom_manager.track_mistake('console_usage', file_path)
                elif '긴 함수' in issue['message']:
                    self.wisdom_manager.track_mistake('long_function', file_path)
                elif '큰 클래스' in issue['message']:
                    self.wisdom_manager.track_mistake('large_class', file_path)
                    
    def _is_nested_function(self, node: ast.FunctionDef, tree: ast.AST) -> bool:
        """함수가 다른 함수나 클래스 내부에 정의되었는지 확인"""
        for parent in ast.walk(tree):
            if isinstance(parent, (ast.FunctionDef, ast.ClassDef)):
                for child in ast.walk(parent):
                    if child is node and child is not parent:
                        return True
        return False
        
    def _get_node_name(self, node: ast.AST) -> str:
        """AST 노드의 이름 추출"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_node_name(node.value)}.{node.attr}"
        elif hasattr(node, 'id'):
            return node.id
        return str(node)
        

class ComplexityVisitor(ast.NodeVisitor):
    """McCabe 복잡도 계산을 위한 Visitor"""
    
    def __init__(self):
        self.complexity = 1  # 기본 복잡도
        
    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_With(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_Assert(self, node):
        self.complexity += 1
        self.generic_visit(node)
        
    def visit_BoolOp(self, node):
        # and/or 연산자도 분기로 계산
        self.complexity += len(node.values) - 1
        self.generic_visit(node)
