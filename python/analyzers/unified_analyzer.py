"""
통합 파일 분석기 - AST 기반 구조 분석과 코드 품질 분석을 통합
Pydantic v2 모델을 사용하여 타입 안정성 강화

ast_parser_helpers.py의 기능을 최대한 활용하여
Python과 TypeScript 모두를 AST 기반으로 분석합니다.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

# Pydantic 모델 import
from python.models.analysis_models import (
    FileAnalysisResult, FunctionInfo, ClassInfo, MethodInfo,
    ImportInfo, CodeSmell, StyleIssue, QualityMetrics,
    DependencyInfo, ParsingMetadata, WisdomInsights,
    LanguageType, ComplexityLevel, CodeSmellType
)

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
            분석 결과 딕셔너리 (FileAnalysisResult의 dict 형태)
        """
        try:
            result = self._analyze_with_pydantic(file_path, force_reparse)
            # 기존 시스템과의 호환성을 위해 딕셔너리로 반환
            return result.to_legacy_dict()
        except Exception as e:
            # 오류 발생 시 기본 결과 반환
            return self._create_error_result(str(e))
            
    def analyze_to_model(self, file_path: str, force_reparse: bool = False) -> FileAnalysisResult:
        """
        파일을 분석하여 Pydantic 모델로 반환
        
        Args:
            file_path: 분석할 파일 경로
            force_reparse: 캐시를 무시하고 강제로 재분석
            
        Returns:
            FileAnalysisResult Pydantic 모델
        """
        return self._analyze_with_pydantic(file_path, force_reparse)
    
    def _analyze_with_pydantic(self, file_path: str, force_reparse: bool = False) -> FileAnalysisResult:
        """Pydantic 모델을 사용한 실제 분석 로직"""
        # 파일 존재 확인
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # 1. ast_parser_helpers로 구조 분석 (캐싱 활용)
        try:
            if self.helpers and hasattr(self.helpers, 'parse_with_snippets'):
                parse_result = self.helpers.parse_with_snippets(file_path)
            else:
                # 직접 호출
                parse_result = parse_with_snippets(file_path)
        except Exception as e:
            raise RuntimeError(f"Parsing failed: {str(e)}")
            
        if not parse_result.get('parsing_success'):
            raise RuntimeError(parse_result.get('error', 'Unknown parsing error'))
            
        # 2. 파일 메타데이터
        file_stat = os.stat(file_path)
        
        # 3. 언어 타입 변환
        language_str = parse_result.get('language', 'unknown').lower()
        language = LanguageType.UNKNOWN
        if language_str == 'python':
            language = LanguageType.PYTHON
        elif language_str == 'typescript':
            language = LanguageType.TYPESCRIPT
        elif language_str == 'javascript':
            language = LanguageType.JAVASCRIPT
            
        # 4. Import 정보 추출
        imports = self._extract_imports_to_model(parse_result)
        
        # 5. 클래스 정보 변환
        classes = self._transform_classes_to_models(parse_result.get('classes', []))
        
        # 6. 함수 정보 변환
        functions = self._transform_functions_to_models(parse_result.get('functions', []))
        
        # 7. 품질 메트릭 분석
        quality_metrics = self._analyze_code_quality_to_model(
            file_path, functions, classes, imports, language
        )
        
        # 8. 의존성 정보
        dependencies = DependencyInfo(
            internal_count=len(imports.internal),
            external_count=len(imports.external),
            depth=self._calculate_import_depth(imports.internal),
            circular_risk=imports.has_circular_risk
        )
        
        # 9. 파싱 메타데이터
        parsing_metadata = ParsingMetadata(
            line_count=self._count_lines(file_path),
            has_syntax_errors=False,
            parsed_at=datetime.now()
        )
        
        # 10. Wisdom insights 생성
        wisdom_insights = WisdomInsights.from_quality_metrics(quality_metrics)
        
        # 11. FileAnalysisResult 생성
        result = FileAnalysisResult(
            path=file_path,
            file_path=file_path,  # 호환성을 위해 명시적으로 설정
            last_modified=datetime.fromtimestamp(file_stat.st_mtime),
            size=file_stat.st_size,
            language=language,
            summary=self._generate_summary(file_path, functions, classes, quality_metrics),
            imports=imports,
            classes=classes,
            functions=functions,
            quality_metrics=quality_metrics,
            dependencies=dependencies,
            parsing_metadata=parsing_metadata,
            wisdom_insights=wisdom_insights
        )
        
        # 12. Symbol Index 업데이트
        self._update_symbol_index(file_path, result)
        
        # 13. Wisdom Manager 연동
        if self.wisdom_manager:
            for smell in quality_metrics.code_smells:
                self.wisdom_manager.track_mistake(smell.type, smell.name or file_path)
            for issue in quality_metrics.style_issues:
                self.wisdom_manager.track_mistake(issue.type, issue.message)
        
        return result
        
    def _extract_imports_to_model(self, parse_result: Dict) -> ImportInfo:
        """Import 정보를 Pydantic 모델로 변환"""
        imports = ImportInfo()
        imports_data = parse_result.get('imports', [])
        
        # 프로젝트 루트 패키지명 추정
        project_packages = self._get_project_packages()
        
        for imp in imports_data:
            if isinstance(imp, str):
                module_name = imp
            elif isinstance(imp, dict):
                module_name = imp.get('module', imp.get('name', ''))
            else:
                continue
                
            # 내부/외부 분류
            is_internal = self._is_internal_import(module_name, project_packages)
            imports.add_import(module_name, is_internal)
                
        return imports
        
    def _transform_classes_to_models(self, classes: List[Dict]) -> List[ClassInfo]:
        """클래스 정보를 Pydantic 모델로 변환"""
        result = []
        
        for cls in classes:
            # 메서드 변환
            methods = []
            for method in cls.get('methods', []):
                method_info = MethodInfo(
                    name=method.get('name', ''),
                    line=method.get('line_start', 0),
                    line_end=method.get('line_end'),
                    params=method.get('args', []),
                    summary=method.get('docstring', '') or '',
                    is_async=method.get('is_async', False),
                    decorators=method.get('decorators', []),
                    complexity=ComplexityLevel.LOW  # 간단히 LOW로 설정
                )
                methods.append(method_info)
            
            # 클래스 생성
            class_info = ClassInfo(
                name=cls.get('name', ''),
                line=cls.get('line_start', 0),
                line_end=cls.get('line_end'),
                methods=methods,
                summary=cls.get('docstring', '') or '',
                complexity=len(methods),
                inheritance=cls.get('bases', [])
            )
            result.append(class_info)
            
        return result
        
    def _transform_functions_to_models(self, functions: List[Dict]) -> List[FunctionInfo]:
        """함수 정보를 Pydantic 모델로 변환"""
        result = []
        
        for func in functions:
            # 복잡도 계산
            line_count = (func.get('line_end', 0) - func.get('line_start', 0)) if func.get('line_end') else 0
            param_count = len(func.get('args', []))
            
            if line_count > 50:
                complexity = ComplexityLevel.HIGH
            elif line_count > 20 or param_count > 5:
                complexity = ComplexityLevel.MEDIUM
            else:
                complexity = ComplexityLevel.LOW
            
            func_info = FunctionInfo(
                name=func.get('name', ''),
                line=func.get('line_start', 0),
                line_end=func.get('line_end'),
                params=func.get('args', []),
                summary=func.get('docstring', '') or '',
                is_async=func.get('is_async', False),
                decorators=func.get('decorators', []),
                complexity=complexity
            )
            result.append(func_info)
            
        return result
        
    def _analyze_code_quality_to_model(self, file_path: str, functions: List[FunctionInfo], 
                                     classes: List[ClassInfo], imports: ImportInfo,
                                     language: LanguageType) -> QualityMetrics:
        """코드 품질을 분석하여 Pydantic 모델로 반환"""
        code_smells = []
        style_issues = []
        
        # 언어별 분석
        if language == LanguageType.PYTHON:
            code_smells, style_issues = self._analyze_python_quality(
                file_path, functions, classes, imports
            )
        elif language in [LanguageType.TYPESCRIPT, LanguageType.JAVASCRIPT]:
            code_smells, style_issues = self._analyze_typescript_quality(
                file_path, functions, classes
            )
            
        # 복잡도 점수 계산
        total_functions = len(functions)
        if total_functions > 0:
            avg_complexity = sum(f.complexity for f in functions) / total_functions
            complexity_score = round(avg_complexity, 2)
        else:
            complexity_score = 0.0
            
        # QualityMetrics 생성 (maintainability_index는 자동 계산됨)
        return QualityMetrics(
            code_smells=code_smells,
            style_issues=style_issues,
            complexity_score=complexity_score,
            test_coverage_hint=self._get_test_coverage_hint(file_path, functions)
        )
        
    def _analyze_python_quality(self, file_path: str, functions: List[FunctionInfo],
                               classes: List[ClassInfo], imports: ImportInfo) -> tuple:
        """Python 코드 품질 분석"""
        code_smells = []
        style_issues = []
        
        # 긴 함수 감지
        for func in functions:
            if func.length > 50:
                code_smells.append(CodeSmell(
                    type=CodeSmellType.LONG_FUNCTION,
                    name=func.name,
                    line=func.line,
                    message=f"함수 '{func.name}'이(가) {func.length}줄로 너무 깁니다",
                    severity="warning"
                ))
                
        # 큰 클래스 감지
        for cls in classes:
            if cls.is_large:
                code_smells.append(CodeSmell(
                    type=CodeSmellType.LARGE_CLASS,
                    name=cls.name,
                    line=cls.line,
                    message=f"클래스 '{cls.name}'에 {len(cls.methods)}개의 메서드가 있습니다",
                    severity="warning"
                ))
                
        # 많은 매개변수 감지
        for func in functions:
            if len(func.params) > 5:
                code_smells.append(CodeSmell(
                    type=CodeSmellType.TOO_MANY_PARAMETERS,
                    name=func.name,
                    line=func.line,
                    message=f"함수 '{func.name}'의 매개변수가 {len(func.params)}개로 너무 많습니다",
                    severity="warning"
                ))
                
        # 많은 import 감지
        if imports.total_count > 20:
            style_issues.append(StyleIssue(
                type="too_many_imports",
                message=f"import가 {imports.total_count}개로 많습니다. 모듈 분리를 고려하세요",
                count=imports.total_count
            ))
            
        return code_smells, style_issues
        
    def _analyze_typescript_quality(self, file_path: str, functions: List[FunctionInfo],
                                  classes: List[ClassInfo]) -> tuple:
        """TypeScript/JavaScript 코드 품질 분석"""
        code_smells = []
        style_issues = []
        
        # 긴 함수 감지
        for func in functions:
            if func.length > 50:
                code_smells.append(CodeSmell(
                    type=CodeSmellType.LONG_FUNCTION,
                    name=func.name,
                    line=func.line,
                    message=f"함수 '{func.name}'이(가) {func.length}줄로 너무 깁니다",
                    severity="warning"
                ))
                
        # console 사용 감지
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                console_matches = re.findall(r'console\.(log|error|warn|info)', content)
                if console_matches:
                    style_issues.append(StyleIssue(
                        type="console_usage",
                        message=f"console 사용이 {len(console_matches)}회 발견되었습니다. logger 사용 권장",
                        count=len(console_matches)
                    ))
        except:
            pass
            
        return code_smells, style_issues
        
    def _get_test_coverage_hint(self, file_path: str, functions: List[FunctionInfo]) -> str:
        """테스트 커버리지 힌트 생성"""
        filename = Path(file_path).name.lower()
        
        if 'test' in filename:
            return "test_file"
        elif any(f.name.startswith('test_') for f in functions):
            return "has_tests"
        else:
            return "unknown"
            
    def _generate_summary(self, file_path: str, functions: List[FunctionInfo],
                         classes: List[ClassInfo], metrics: QualityMetrics) -> str:
        """파일 요약 생성"""
        filename = Path(file_path).name
        
        # 파일 이름과 구조에서 역할 추론
        if 'test' in filename.lower():
            return f"테스트 파일 - {len(functions)}개의 테스트 함수 포함"
        
        # 품질 정보 포함
        quality_info = ""
        if metrics.total_issues > 0:
            quality_info = f", {metrics.total_issues}개의 코드 품질 이슈 발견"
        
        if len(classes) > 0 and len(functions) > 0:
            main_class = classes[0].name if classes else ""
            return f"{filename}: {len(classes)}개의 클래스와 {len(functions)}개의 함수, 주요 클래스: {main_class}{quality_info}"
        elif len(classes) > 0:
            main_class = classes[0].name if classes else ""
            return f"{filename}: {len(classes)}개의 클래스, 주요 클래스: {main_class}{quality_info}"
        elif len(functions) > 0:
            return f"{filename}: {len(functions)}개의 함수{quality_info}"
        else:
            return f"{filename}: 구조 분석 필요{quality_info}"
            
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
        
    def _count_lines(self, file_path: str) -> int:
        """파일의 라인 수 계산"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return len(f.readlines())
        except:
            return 0
            
    def _update_symbol_index(self, file_path: str, result: FileAnalysisResult):
        """Symbol Index 업데이트"""
        # 파일별 심볼 정보 저장
        symbols = {
            'classes': [(c.name, c.line) for c in result.classes],
            'functions': [(f.name, f.line) for f in result.functions],
            'language': result.language
        }
        
        self.symbol_index[file_path] = symbols
        
        # 전역 심볼 인덱스 업데이트 (helpers가 있으면)
        if self.helpers and hasattr(self.helpers, 'update_symbol_index'):
            try:
                # FileAnalysisResult를 딕셔너리로 변환하여 전달
                self.helpers.update_symbol_index(file_path, result.to_legacy_dict())
            except:
                pass  # 실패해도 계속 진행
                
    def _create_error_result(self, error_msg: str) -> Dict[str, Any]:
        """에러 결과 생성 (딕셔너리 형태)"""
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
                'error': error_msg,
                'parsed_at': datetime.now().isoformat()
            },
            'quality_metrics': {
                'code_smells': [],
                'style_issues': [],
                'complexity_score': 0,
                'maintainability_index': 0,
                'test_coverage_hint': 'unknown'
            },
            'dependencies': {
                'internal_count': 0,
                'external_count': 0,
                'depth': 0,
                'circular_risk': False
            },
            'wisdom_insights': {
                'potential_issues': [error_msg],
                'improvement_suggestions': []
            }
        }
        
    def get_symbol_index(self) -> Dict[str, Dict]:
        """현재 심볼 인덱스 반환"""
        return self.symbol_index
