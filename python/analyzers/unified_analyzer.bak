"""
통합 파일 분석기 - AST 기반 구조 분석과 코드 품질 분석을 통합

ast_parser_helpers.py의 기능을 최대한 활용하여
Python과 TypeScript 모두를 AST 기반으로 분석합니다.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

# ast_parser_helpers의 parse_with_snippets 활용
try:
    from python.ast_parser_helpers import parse_with_snippets, update_symbol_index
except ImportError:
    # JSON REPL 환경에서는 직접 import
    import sys
    if hasattr(sys.modules.get('__main__', None), 'helpers'):
        helpers = sys.modules['__main__'].helpers
        parse_with_snippets = helpers.parse_with_snippets
        update_symbol_index = helpers.update_symbol_index if hasattr(helpers, 'update_symbol_index') else None


class UnifiedAnalyzer:
    """통합 파일 분석기 - AST 기반 구조 분석과 코드 품질 분석을 통합"""
    
    def __init__(self, wisdom_manager=None):
        """UnifiedAnalyzer 초기화
        
        Args:
            wisdom_manager: ProjectWisdomManager 인스턴스 (선택사항)
        """
        self.symbol_index = {}
        self.wisdom_manager = wisdom_manager
        self._init_helpers()
        
    def _init_helpers(self):
        """helpers 객체를 찾아서 초기화합니다."""
        import sys
        
        # helpers 객체 찾기
        if 'global_helpers' in globals():
            self.helpers = globals()['global_helpers']
        elif hasattr(sys.modules.get('__main__', None), 'helpers'):
            self.helpers = sys.modules['__main__'].helpers
        elif 'helpers' in globals():
            self.helpers = globals()['helpers']
        else:
            self.helpers = None
            
    def analyze(self, file_path: str, force_reparse: bool = False) -> Dict[str, Any]:
        """
        파일을 분석하여 구조와 품질 정보를 통합 반환
        
        Args:
            file_path: 분석할 파일 경로
            force_reparse: 캐시를 무시하고 강제로 재분석
            
        Returns:
            분석 결과 딕셔너리
        """
        # 파일 존재 확인
        if not os.path.exists(file_path):
            return self._create_error_result(f"File not found: {file_path}")
            
        # 1. ast_parser_helpers로 구조 분석 (캐싱 활용)
        try:
            if self.helpers and hasattr(self.helpers, 'parse_with_snippets'):
                parse_result = self.helpers.parse_with_snippets(file_path)
            else:
                # 직접 호출
                parse_result = parse_with_snippets(file_path)
        except Exception as e:
            return self._create_error_result(f"Parsing failed: {str(e)}")
            
        if not parse_result.get('parsing_success'):
            return self._create_error_result(parse_result.get('error', 'Unknown parsing error'))
            
        # 2. 파일 메타데이터
        file_stat = os.stat(file_path)
        
        # 3. 기본 구조 정보 변환
        result = {
            'path': file_path,
            'file_path': file_path,  # ProjectAnalyzer 호환성
            'last_modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            'size': file_stat.st_size,
            'language': parse_result.get('language', 'unknown'),
            'summary': '',  # 나중에 생성
            'imports': self._extract_imports(parse_result),
            'classes': self._transform_classes(parse_result.get('classes', [])),
            'functions': self._transform_functions(parse_result.get('functions', [])),
            'parsing_metadata': {
                'line_count': self._count_lines(file_path),
                'has_syntax_errors': False,
                'parsed_at': datetime.now().isoformat()
            }
        }
        
        # 4. 요약 생성 (구조 정보 기반)
        result['summary'] = self._generate_summary(file_path, result)
        
        # 5. 코드 품질 분석 추가
        quality_metrics = self._analyze_code_quality(file_path, result, parse_result)
        result['quality_metrics'] = quality_metrics
        
        # 6. 의존성 그래프 정보 추가
        result['dependencies'] = self._analyze_dependencies(result['imports'], file_path)
        
        # 7. Symbol Index 업데이트
        self._update_symbol_index(file_path, result)
        
        # 8. Wisdom insights 생성 (기존 호환성)
        result['wisdom_insights'] = self._generate_wisdom_insights(quality_metrics)
        
        return result
        
    def _create_error_result(self, error_msg: str) -> Dict[str, Any]:
        """에러 결과 생성"""
        return {
            'path': '',
            'file_path': '',
            'last_modified': datetime.now().isoformat(),
            'size': 0,
            'language': 'unknown',
            'summary': f'Analysis failed: {error_msg}',
            'imports': {'internal': [], 'external': []},
            'classes': [],
            'functions': [],
            'parsing_metadata': {
                'has_syntax_errors': True,
                'error': error_msg
            },
            'quality_metrics': {},
            'wisdom_insights': {'potential_issues': [error_msg], 'improvement_suggestions': []}
        }
        
    def _count_lines(self, file_path: str) -> int:
        """파일의 라인 수 계산"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        except:
            return 0
            
    def _generate_summary(self, file_path: str, result: Dict) -> str:
        """파일 요약 생성"""
        filename = Path(file_path).name
        language = result.get('language', 'unknown')
        
        # 언어별 요약 생성
        classes = result.get('classes', [])
        functions = result.get('functions', [])
        
        # 파일 이름과 구조에서 역할 추론
        if 'test' in filename.lower():
            return f"테스트 파일 ({language}) - {len(functions)}개의 테스트 함수 포함"
        
        if 'handler' in filename.lower():
            return f"핸들러 모듈 ({language}) - {len(functions)}개의 핸들러 함수 정의"
        
        if 'analyzer' in filename.lower():
            return f"분석 모듈 ({language}) - {len(classes)}개의 분석 클래스 포함"
        
        if 'manager' in filename.lower():
            return f"관리 모듈 ({language}) - {len(classes)}개의 관리 클래스 정의"
        
        # 일반적인 요약
        class_count = len(classes)
        func_count = len(functions)
        
        # 품질 정보 포함
        quality_info = ""
        if 'quality_metrics' in result:
            issues = len(result['quality_metrics'].get('code_smells', []))
            if issues > 0:
                quality_info = f", {issues}개의 코드 품질 이슈 발견"
        
        if class_count > 0 and func_count > 0:
            main_class = classes[0]['name'] if classes else ""
            return f"{filename}: {class_count}개의 클래스와 {func_count}개의 함수, 주요 클래스: {main_class}{quality_info}"
        elif class_count > 0:
            main_class = classes[0]['name'] if classes else ""
            return f"{filename}: {class_count}개의 클래스, 주요 클래스: {main_class}{quality_info}"
        elif func_count > 0:
            return f"{filename}: {func_count}개의 함수{quality_info}"
        else:
            return f"{filename}: {language} 파일{quality_info}"
            
    def _extract_imports(self, parse_result: Dict) -> Dict[str, List[str]]:
        """import 정보 추출 및 내부/외부 분류"""
        imports_data = parse_result.get('imports', [])
        imports = {'internal': [], 'external': []}
        
        # 프로젝트 루트 패키지명 추정 (pyproject.toml 또는 package.json에서)
        project_packages = self._get_project_packages()
        
        for imp in imports_data:
            if isinstance(imp, str):
                module_name = imp
            elif isinstance(imp, dict):
                module_name = imp.get('module', imp.get('name', ''))
            else:
                continue
                
            # 내부/외부 분류 개선
            if self._is_internal_import(module_name, project_packages):
                imports['internal'].append(module_name)
            else:
                imports['external'].append(module_name)
                
        # 중복 제거
        imports['internal'] = list(set(imports['internal']))
        imports['external'] = list(set(imports['external']))
        
        return imports
        
    def _is_internal_import(self, module_name: str, project_packages: Set[str]) -> bool:
        """내부 import인지 판단"""
        if not module_name:
            return True
            
        # 상대 import
        if module_name.startswith('.'):
            return True
            
        # 프로젝트 패키지
        for package in project_packages:
            if module_name == package or module_name.startswith(f"{package}."):
                return True
                
        # 로컬 파일 경로 형태 (TypeScript)
        if module_name.startswith('./') or module_name.startswith('../'):
            return True
            
        return False
        
    def _get_project_packages(self) -> Set[str]:
        """프로젝트의 패키지명 추정"""
        packages = set()
        
        # 현재 프로젝트 이름 추가
        cwd = os.path.basename(os.getcwd())
        packages.add(cwd)
        packages.add(cwd.replace('-', '_'))  # 하이픈을 언더스코어로
        
        # pyproject.toml에서 패키지명 찾기
        if os.path.exists('pyproject.toml'):
            try:
                with open('pyproject.toml', 'r') as f:
                    content = f.read()
                    # 간단한 정규식으로 name 추출
                    match = re.search(r'name\s*=\s*["\']([^"\']]+)["\']', content)
                    if match:
                        packages.add(match.group(1))
                        packages.add(match.group(1).replace('-', '_'))
            except:
                pass
                
        # src 디렉토리의 하위 폴더들도 패키지로 간주
        for src_dir in ['src', 'python']:
            if os.path.exists(src_dir):
                for item in os.listdir(src_dir):
                    if os.path.isdir(os.path.join(src_dir, item)) and not item.startswith('.'):
                        packages.add(item)
                        
        return packages
        
    def _transform_classes(self, classes: List[Dict]) -> List[Dict[str, Any]]:
        """parse_with_snippets의 클래스 정보를 표준 형식으로 변환"""
        result = []
        
        for cls in classes:
            class_info = {
                'name': cls.get('name', ''),
                'line': cls.get('line_start', 0),
                'line_end': cls.get('line_end', 0),
                'methods': [],
                'summary': cls.get('docstring', '') or '',
                'complexity': len(cls.get('methods', [])),  # 메서드 수로 복잡도 추정
                'inheritance': cls.get('bases', [])  # 상속 정보
            }
            
            # 메서드 정보 변환
            for method in cls.get('methods', []):
                method_info = {
                    'name': method.get('name', ''),
                    'line': method.get('line_start', 0),
                    'line_end': method.get('line_end', 0),
                    'is_async': method.get('is_async', False),
                    'decorators': method.get('decorators', [])
                }
                class_info['methods'].append(method_info)
                
            result.append(class_info)
            
        return result
        
    def _transform_functions(self, functions: List[Dict]) -> List[Dict[str, Any]]:
        """parse_with_snippets의 함수 정보를 표준 형식으로 변환"""
        result = []
        
        for func in functions:
            func_info = {
                'name': func.get('name', ''),
                'line': func.get('line_start', 0),
                'line_end': func.get('line_end', 0),
                'params': func.get('args', []),
                'summary': func.get('docstring', '') or '',
                'is_async': func.get('is_async', False),
                'decorators': func.get('decorators', []),
                'complexity': self._calculate_function_complexity(func)
            }
            result.append(func_info)
            
        return result
        
    def _calculate_function_complexity(self, func: Dict) -> int:
        """함수의 복잡도 계산 (간단한 추정)"""
        # 라인 수 기반 복잡도
        line_count = func.get('line_end', 0) - func.get('line_start', 0)
        
        # 매개변수 수도 고려
        param_count = len(func.get('args', []))
        
        # 간단한 복잡도 점수
        if line_count > 50:
            return 3  # High
        elif line_count > 20 or param_count > 5:
            return 2  # Medium
        else:
            return 1  # Low
            
    def _analyze_code_quality(self, file_path: str, result: Dict, parse_result: Dict) -> Dict[str, Any]:
        """코드 품질 분석"""
        metrics = {
            'code_smells': [],
            'style_issues': [],
            'complexity_score': 0,
            'maintainability_index': 100,  # 시작점 100
            'test_coverage_hint': 'unknown'
        }
        
        # 언어별 분석
        if result['language'] == 'python':
            metrics = self._analyze_python_quality(file_path, result, parse_result, metrics)
        elif result['language'] in ['typescript', 'javascript']:
            metrics = self._analyze_typescript_quality(file_path, result, parse_result, metrics)
            
        # 전체 복잡도 점수 계산
        total_functions = len(result['functions'])
        total_classes = len(result['classes'])
        
        if total_functions + total_classes > 0:
            avg_complexity = sum(f.get('complexity', 1) for f in result['functions']) / max(total_functions, 1)
            metrics['complexity_score'] = round(avg_complexity, 2)
            
        # 유지보수성 지수 계산 (간단한 버전)
        metrics['maintainability_index'] = max(0, 100 - len(metrics['code_smells']) * 10 - len(metrics['style_issues']) * 5)
        
        return metrics
        
    def _analyze_python_quality(self, file_path: str, result: Dict, parse_result: Dict, metrics: Dict) -> Dict:
        """Python 코드 품질 분석"""
        # 긴 함수 감지
        for func in result['functions']:
            line_count = func.get('line_end', 0) - func.get('line', 0)
            if line_count > 50:
                metrics['code_smells'].append({
                    'type': 'long_function',
                    'name': func['name'],
                    'line': func['line'],
                    'message': f"함수 '{func['name']}'이(가) {line_count}줄로 너무 깁니다"
                })
                
        # 큰 클래스 감지
        for cls in result['classes']:
            method_count = len(cls.get('methods', []))
            if method_count > 20:
                metrics['code_smells'].append({
                    'type': 'large_class',
                    'name': cls['name'],
                    'line': cls['line'],
                    'message': f"클래스 '{cls['name']}'에 {method_count}개의 메서드가 있습니다"
                })
                
        # 많은 매개변수 감지
        for func in result['functions']:
            param_count = len(func.get('params', []))
            if param_count > 5:
                metrics['code_smells'].append({
                    'type': 'too_many_parameters',
                    'name': func['name'],
                    'line': func['line'],
                    'message': f"함수 '{func['name']}'의 매개변수가 {param_count}개로 너무 많습니다"
                })
                
        # 순환 import 가능성
        internal_imports = result['imports']['internal']
        if len(internal_imports) > 10:
            metrics['style_issues'].append({
                'type': 'too_many_imports',
                'message': f"내부 import가 {len(internal_imports)}개로 많습니다. 모듈 구조 재검토 필요"
            })
            
        # 테스트 파일 여부 확인
        if 'test' in Path(file_path).name.lower():
            metrics['test_coverage_hint'] = 'test_file'
        elif any(f['name'].startswith('test_') for f in result['functions']):
            metrics['test_coverage_hint'] = 'has_tests'
            
        return metrics
        
    def _analyze_typescript_quality(self, file_path: str, result: Dict, parse_result: Dict, metrics: Dict) -> Dict:
        """TypeScript/JavaScript 코드 품질 분석"""
        # 긴 함수 감지 (TypeScript도 동일 기준)
        for func in result['functions']:
            line_count = func.get('line_end', 0) - func.get('line', 0)
            if line_count > 50:
                metrics['code_smells'].append({
                    'type': 'long_function',
                    'name': func['name'],
                    'line': func['line'],
                    'message': f"함수 '{func['name']}'이(가) {line_count}줄로 너무 깁니다"
                })
                
        # console 사용 감지 (TypeScript 특화)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                console_matches = re.findall(r'console\.(log|error|warn|info)', content)
                if console_matches:
                    metrics['style_issues'].append({
                        'type': 'console_usage',
                        'count': len(console_matches),
                        'message': f"console 사용이 {len(console_matches)}회 발견되었습니다. logger 사용 권장"
                    })
        except:
            pass
            
        return metrics
        
    def _analyze_dependencies(self, imports: Dict[str, List[str]], file_path: str) -> Dict[str, Any]:
        """의존성 분석"""
        return {
            'internal_count': len(imports['internal']),
            'external_count': len(imports['external']),
            'depth': self._calculate_import_depth(imports['internal']),
            'circular_risk': len(imports['internal']) > 5  # 간단한 위험도 평가
        }
        
    def _calculate_import_depth(self, internal_imports: List[str]) -> int:
        """import 깊이 계산"""
        if not internal_imports:
            return 0
            
        max_depth = 0
        for imp in internal_imports:
            # 상대 경로의 깊이 계산
            if imp.startswith('.'):
                depth = imp.count('.')
                max_depth = max(max_depth, depth)
            else:
                # 절대 경로의 깊이
                depth = imp.count('.')
                max_depth = max(max_depth, depth)
                
        return max_depth
        
    def _update_symbol_index(self, file_path: str, result: Dict):
        """Symbol Index 업데이트"""
        # 파일별 심볼 정보 저장
        symbols = {
            'classes': [(c['name'], c['line']) for c in result['classes']],
            'functions': [(f['name'], f['line']) for f in result['functions']],
            'language': result['language']
        }
        
        self.symbol_index[file_path] = symbols
        
        # 전역 심볼 인덱스 업데이트 (helpers가 있으면)
        if self.helpers and hasattr(self.helpers, 'update_symbol_index'):
            try:
                self.helpers.update_symbol_index(file_path, result)
            except:
                pass  # 실패해도 계속 진행
                
    def _generate_wisdom_insights(self, quality_metrics: Dict) -> Dict[str, Any]:
        """기존 시스템과의 호환성을 위한 wisdom_insights 생성"""
        insights = {
            'potential_issues': [],
            'improvement_suggestions': []
        }
        
        # code_smells를 potential_issues로 변환
        for smell in quality_metrics.get('code_smells', []):
            insights['potential_issues'].append(smell['message'])
            
        # style_issues를 improvement_suggestions으로 변환
        for issue in quality_metrics.get('style_issues', []):
            insights['improvement_suggestions'].append(issue['message'])
            
        # 복잡도 기반 제안
        if quality_metrics.get('complexity_score', 0) > 2:
            insights['improvement_suggestions'].append(
                "전반적인 코드 복잡도가 높습니다. 리팩토링을 고려해보세요."
            )
            
        # Wisdom Manager에 기록
        if self.wisdom_manager:
            for smell in quality_metrics.get('code_smells', []):
                self.wisdom_manager.track_mistake(smell['type'], smell.get('name', ''))
            for issue in quality_metrics.get('style_issues', []):
                self.wisdom_manager.track_mistake(issue['type'], issue.get('message', ''))
                
        return insights
        
    def get_symbol_index(self) -> Dict[str, Dict]:
        """현재 심볼 인덱스 반환"""
        return self.symbol_index
