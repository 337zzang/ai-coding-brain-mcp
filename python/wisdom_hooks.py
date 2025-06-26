"""
Wisdom Hooks - AST 기반 실시간 코드 패턴 감지
v3.0 - AST 분석 통합, 프로젝트별 관리
"""

import re
import ast
from typing import List, Dict, Any
from datetime import datetime
import os
from pathlib import Path

class ProjectWisdomHooks:
    """실시간으로 코드 패턴을 감지하고 경고하는 시스템"""
    
    def __init__(self, wisdom_manager):
        self.wisdom = wisdom_manager
        self.recent_backups = {}
        
        # 간단한 정규표현식 패턴 (빠른 체크용)
        self.quick_patterns = {
            'console_usage': {
                'pattern': re.compile(r'console\.(log|error|warn|info)'),
                'description': 'console 사용 감지',
                'severity': 'medium'
            },
            'direct_flow': {
                'pattern': re.compile(r'flow_project\s*\('),
                'description': 'flow_project 직접 호출',
                'severity': 'high'
            },
            'hardcoded_path': {
                'pattern': re.compile(r'["\']C:\\\\|["\'][A-Za-z]:\\\\'),
                'description': '하드코딩된 경로 감지',
                'severity': 'medium'
            },
            'api_assumption': {
                'pattern': re.compile(r'(helpers\.(get_project_structure|search_files_advanced|parse_with_snippets|scan_directory_dict)\s*\([^)]*\)\s*\[[\'"]?\w+[\'"]?\])'),
                'description': 'API 반환값 형식 확인 없이 직접 접근',
                'severity': 'high'
            }
        }
        
        # AST 분석기
        try:
            from ast_wisdom_analyzer import ASTWisdomAnalyzer
            self.ast_analyzer = ASTWisdomAnalyzer(wisdom_manager)
        except:
            self.ast_analyzer = None
    
    def check_code_patterns(self, code: str, filename: str = "") -> List[str]:
        """코드에서 실수 패턴 감지 (정규표현식 + AST)"""
        detected = []
        
        # 1. 빠른 정규표현식 체크
        for pattern_name, pattern_info in self.quick_patterns.items():
            pattern = pattern_info['pattern']
            if pattern.search(code):
                detected.append(pattern_name)
                self.wisdom.track_mistake(pattern_name, f"in {filename}")
        
        # 2. Python 파일인 경우 AST 분석
        if filename.endswith('.py') and self.ast_analyzer:
            try:
                result = self.ast_analyzer.analyze_code(code, filename)
                
                # AST 분석 결과를 detected에 추가
                if result['syntax_errors']:
                    detected.append('syntax_error')
                if result['indentation_errors']:
                    detected.append('indentation_error')
                
                # 코드 품질 문제
                for issue in result.get('style_issues', []):
                    if issue['type'] == 'unused_variables':
                        detected.append('unused_variables')
                    elif issue['type'] == 'line_too_long':
                        detected.append('long_lines')
                
                for smell in result.get('code_smells', []):
                    if smell['type'] == 'high_complexity':
                        detected.append('complex_code')
                    elif smell['type'] == 'duplicate_imports':
                        detected.append('duplicate_imports')
                        
            except Exception as e:
                # AST 분석 실패시 정규표현식만 사용
                pass
        
        # API 사용 패턴 추가 체크
        api_calls = [
            'helpers.get_project_structure()',
            'helpers.search_files_advanced(',
            'helpers.parse_with_snippets(',
            'helpers.scan_directory_dict('
        ]
        
        for api_call in api_calls:
            if api_call in code:
                # 반환값 형식 확인 패턴 검사
                checks = ['type(', '.keys()', 'inspect_result', 'if isinstance(']
                has_check = any(check in code for check in checks)
                
                if not has_check:
                    detected.append('api_assumption')
                    # 한 번만 감지하면 충분
                    break
        
        return list(set(detected))  # 중복 제거
    
    def analyze_file(self, filepath: str) -> Dict[str, Any]:
        """파일 전체를 분석하여 상세 리포트 생성"""
        if not os.path.exists(filepath):
            return {'error': 'File not found'}
        
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 빠른 패턴 체크
        quick_issues = self.check_code_patterns(code, filepath)
        
        # AST 상세 분석
        if filepath.endswith('.py') and self.ast_analyzer:
            ast_result = self.ast_analyzer.analyze_code(code, os.path.basename(filepath))
            return {
                'quick_patterns': quick_issues,
                'ast_analysis': ast_result,
                'file': filepath
            }
        
        return {
            'quick_patterns': quick_issues,
            'file': filepath
        }
    
    def get_project_wisdom_path(self) -> Path:
        """프로젝트별 wisdom 데이터 경로 반환"""
        return self.wisdom.wisdom_data_file if hasattr(self.wisdom, 'wisdom_data_file') else None


def get_wisdom_hooks(wisdom_manager=None):
    """Wisdom Hooks 인스턴스 생성"""
    if wisdom_manager is None:
        from project_wisdom import ProjectWisdomManager
        wisdom_manager = ProjectWisdomManager(os.getcwd())
    
    return ProjectWisdomHooks(wisdom_manager)
