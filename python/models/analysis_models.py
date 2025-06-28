"""
파일 분석 결과를 위한 Pydantic v2 모델 정의

타입 안정성과 데이터 검증을 위해 Pydantic을 사용합니다.
"""

from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class LanguageType(str, Enum):
    """지원하는 프로그래밍 언어"""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    UNKNOWN = "unknown"


class ComplexityLevel(int, Enum):
    """코드 복잡도 레벨"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class CodeSmellType(str, Enum):
    """코드 스멜 유형"""
    LONG_FUNCTION = "long_function"
    LARGE_CLASS = "large_class"
    TOO_MANY_PARAMETERS = "too_many_parameters"
    TOO_MANY_IMPORTS = "too_many_imports"
    CONSOLE_USAGE = "console_usage"
    DUPLICATE_CODE = "duplicate_code"
    COMPLEX_CONDITION = "complex_condition"


class FunctionInfo(BaseModel):
    """함수 정보 모델"""
    model_config = ConfigDict(use_enum_values=True)
    
    name: str = Field(..., description="함수 이름")
    line: int = Field(..., ge=1, description="시작 라인 번호")
    line_end: Optional[int] = Field(None, ge=1, description="종료 라인 번호")
    params: List[str] = Field(default_factory=list, description="매개변수 목록")
    summary: str = Field("", description="함수 설명 (docstring)")
    is_async: bool = Field(False, description="비동기 함수 여부")
    decorators: List[str] = Field(default_factory=list, description="데코레이터 목록")
    complexity: ComplexityLevel = Field(ComplexityLevel.LOW, description="복잡도")
    
    @field_validator('line_end')
    def validate_line_end(cls, v, info):
        """종료 라인이 시작 라인보다 뒤에 있는지 검증"""
        if v is not None and info.data.get('line') and v < info.data['line']:
            raise ValueError('line_end must be greater than or equal to line')
        return v
    
    @property
    def length(self) -> int:
        """함수 길이 (라인 수)"""
        if self.line_end:
            return self.line_end - self.line + 1
        return 0


class MethodInfo(FunctionInfo):
    """메서드 정보 모델 (FunctionInfo 상속)"""
    is_static: bool = Field(False, description="정적 메서드 여부")
    is_class_method: bool = Field(False, description="클래스 메서드 여부")
    is_property: bool = Field(False, description="프로퍼티 여부")


class ClassInfo(BaseModel):
    """클래스 정보 모델"""
    name: str = Field(..., description="클래스 이름")
    line: int = Field(..., ge=1, description="시작 라인 번호")
    line_end: Optional[int] = Field(None, ge=1, description="종료 라인 번호")
    methods: List[MethodInfo] = Field(default_factory=list, description="메서드 목록")
    summary: str = Field("", description="클래스 설명 (docstring)")
    complexity: int = Field(0, ge=0, description="복잡도 (메서드 수)")
    inheritance: List[str] = Field(default_factory=list, description="상속 클래스 목록")
    
    @field_validator('complexity', mode='after')
    def calculate_complexity(cls, v, info):
        """메서드 수로 복잡도 자동 계산"""
        if info.data.get('methods'):
            return len(info.data['methods'])
        return v
    
    @property
    def is_large(self) -> bool:
        """큰 클래스인지 확인 (메서드 20개 초과)"""
        return len(self.methods) > 20


class ImportInfo(BaseModel):
    """Import 정보 모델"""
    internal: List[str] = Field(default_factory=list, description="내부 모듈 import")
    external: List[str] = Field(default_factory=list, description="외부 모듈 import")
    
    @property
    def total_count(self) -> int:
        """전체 import 수"""
        return len(self.internal) + len(self.external)
    
    @property
    def has_circular_risk(self) -> bool:
        """순환 의존성 위험 여부 (내부 import 5개 초과)"""
        return len(self.internal) > 5
    
    def add_import(self, module: str, is_internal: bool):
        """import 추가"""
        if is_internal:
            if module not in self.internal:
                self.internal.append(module)
        else:
            if module not in self.external:
                self.external.append(module)


class CodeSmell(BaseModel):
    """코드 스멜 정보"""
    model_config = ConfigDict(use_enum_values=True)
    
    type: CodeSmellType = Field(..., description="코드 스멜 유형")
    name: Optional[str] = Field(None, description="관련 함수/클래스 이름")
    line: Optional[int] = Field(None, ge=1, description="발생 위치")
    message: str = Field(..., description="설명 메시지")
    severity: str = Field("warning", description="심각도: info, warning, error")


class StyleIssue(BaseModel):
    """스타일 이슈 정보"""
    type: str = Field(..., description="이슈 유형")
    message: str = Field(..., description="설명 메시지")
    count: Optional[int] = Field(None, description="발생 횟수")
    locations: List[int] = Field(default_factory=list, description="발생 위치 라인 번호")


class QualityMetrics(BaseModel):
    """코드 품질 메트릭"""
    code_smells: List[CodeSmell] = Field(default_factory=list, description="코드 스멜 목록")
    style_issues: List[StyleIssue] = Field(default_factory=list, description="스타일 이슈 목록")
    complexity_score: float = Field(0.0, ge=0.0, description="전체 복잡도 점수")
    maintainability_index: int = Field(100, ge=0, le=100, description="유지보수성 지수")
    test_coverage_hint: str = Field("unknown", description="테스트 커버리지 힌트")
    
    @field_validator('maintainability_index', mode='after')
    def calculate_maintainability(cls, v, info):
        """유지보수성 지수 자동 계산"""
        code_smells = info.data.get('code_smells', [])
        style_issues = info.data.get('style_issues', [])
        
        # 기본 100점에서 감점
        score = 100
        score -= len(code_smells) * 10
        score -= len(style_issues) * 5
        
        return max(0, min(100, score))
    
    @property
    def total_issues(self) -> int:
        """전체 이슈 수"""
        return len(self.code_smells) + len(self.style_issues)
    
    @property
    def is_healthy(self) -> bool:
        """건강한 코드인지 확인 (유지보수성 70 이상)"""
        return self.maintainability_index >= 70


class DependencyInfo(BaseModel):
    """의존성 정보"""
    internal_count: int = Field(0, ge=0, description="내부 의존성 수")
    external_count: int = Field(0, ge=0, description="외부 의존성 수")
    depth: int = Field(0, ge=0, description="의존성 깊이")
    circular_risk: bool = Field(False, description="순환 의존성 위험")
    
    @property
    def total_dependencies(self) -> int:
        """전체 의존성 수"""
        return self.internal_count + self.external_count


class ParsingMetadata(BaseModel):
    """파싱 메타데이터"""
    line_count: int = Field(0, ge=0, description="전체 라인 수")
    has_syntax_errors: bool = Field(False, description="구문 오류 여부")
    parsed_at: datetime = Field(default_factory=datetime.now, description="파싱 시각")
    parser_version: str = Field("1.0.0", description="파서 버전")
    error: Optional[str] = Field(None, description="오류 메시지")


class WisdomInsights(BaseModel):
    """Wisdom 시스템 인사이트 (기존 호환성)"""
    potential_issues: List[str] = Field(default_factory=list, description="잠재적 이슈")
    improvement_suggestions: List[str] = Field(default_factory=list, description="개선 제안")
    
    @classmethod
    def from_quality_metrics(cls, metrics: 'QualityMetrics') -> 'WisdomInsights':
        """QualityMetrics에서 WisdomInsights 생성"""
        insights = cls()
        
        # code_smells를 potential_issues로 변환
        for smell in metrics.code_smells:
            insights.potential_issues.append(smell.message)
        
        # style_issues를 improvement_suggestions으로 변환
        for issue in metrics.style_issues:
            insights.improvement_suggestions.append(issue.message)
        
        # 복잡도 기반 제안
        if metrics.complexity_score > 2:
            insights.improvement_suggestions.append(
                "전반적인 코드 복잡도가 높습니다. 리팩토링을 고려해보세요."
            )
        
        return insights


class FileAnalysisResult(BaseModel):
    """파일 분석 결과 전체 모델"""
    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )
    
    # 파일 정보
    path: str = Field(..., description="파일 경로")
    file_path: str = Field("", description="파일 경로 (호환성)")  # ProjectAnalyzer 호환
    last_modified: datetime = Field(..., description="최종 수정 시각")
    size: int = Field(..., ge=0, description="파일 크기 (bytes)")
    language: LanguageType = Field(..., description="프로그래밍 언어")
    
    # 구조 정보
    summary: str = Field("", description="파일 요약")
    imports: ImportInfo = Field(default_factory=ImportInfo, description="Import 정보")
    classes: List[ClassInfo] = Field(default_factory=list, description="클래스 목록")
    functions: List[FunctionInfo] = Field(default_factory=list, description="함수 목록")
    
    # 품질 정보
    quality_metrics: QualityMetrics = Field(default_factory=QualityMetrics, description="품질 메트릭")
    dependencies: DependencyInfo = Field(default_factory=DependencyInfo, description="의존성 정보")
    
    # 메타데이터
    parsing_metadata: ParsingMetadata = Field(default_factory=ParsingMetadata, description="파싱 메타데이터")
    wisdom_insights: WisdomInsights = Field(default_factory=WisdomInsights, description="Wisdom 인사이트")
    
    @field_validator('file_path', mode='after')
    def set_file_path(cls, v, info):
        """호환성을 위해 file_path를 path와 동일하게 설정"""
        if not v and info.data.get('path'):
            return info.data['path']
        return v
    
    @property
    def total_definitions(self) -> int:
        """전체 정의 수 (클래스 + 함수)"""
        return len(self.classes) + len(self.functions)
    
    @property
    def needs_refactoring(self) -> bool:
        """리팩토링 필요 여부"""
        return (
            self.quality_metrics.maintainability_index < 50 or
            self.quality_metrics.total_issues > 10 or
            any(cls.is_large for cls in self.classes)
        )
    
    def to_legacy_dict(self) -> Dict[str, Any]:
        """기존 딕셔너리 형식으로 변환 (호환성)"""
        result = self.model_dump()
        
        # datetime 객체를 문자열로 변환
        result['last_modified'] = self.last_modified.isoformat()
        if 'parsing_metadata' in result and 'parsed_at' in result['parsing_metadata']:
            result['parsing_metadata']['parsed_at'] = self.parsing_metadata.parsed_at.isoformat()
        
        return result


# 편의 함수들
def create_file_analysis_from_dict(data: Dict[str, Any]) -> FileAnalysisResult:
    """딕셔너리에서 FileAnalysisResult 생성 (기존 코드 호환성)"""
    # datetime 변환
    if isinstance(data.get('last_modified'), str):
        data['last_modified'] = datetime.fromisoformat(data['last_modified'])
    
    # 중첩된 객체 변환
    if 'imports' in data and isinstance(data['imports'], dict):
        data['imports'] = ImportInfo(**data['imports'])
    
    if 'classes' in data:
        data['classes'] = [
            ClassInfo(
                **{
                    **cls,
                    'methods': [MethodInfo(**m) for m in cls.get('methods', [])]
                }
            )
            for cls in data['classes']
        ]
    
    if 'functions' in data:
        data['functions'] = [FunctionInfo(**func) for func in data['functions']]
    
    if 'quality_metrics' in data:
        metrics_data = data['quality_metrics']
        if 'code_smells' in metrics_data:
            metrics_data['code_smells'] = [
                CodeSmell(**smell) for smell in metrics_data['code_smells']
            ]
        if 'style_issues' in metrics_data:
            metrics_data['style_issues'] = [
                StyleIssue(**issue) for issue in metrics_data['style_issues']
            ]
        data['quality_metrics'] = QualityMetrics(**metrics_data)
    
    if 'dependencies' in data:
        data['dependencies'] = DependencyInfo(**data['dependencies'])
    
    if 'parsing_metadata' in data:
        meta = data['parsing_metadata']
        if isinstance(meta.get('parsed_at'), str):
            meta['parsed_at'] = datetime.fromisoformat(meta['parsed_at'])
        data['parsing_metadata'] = ParsingMetadata(**meta)
    
    if 'wisdom_insights' in data:
        data['wisdom_insights'] = WisdomInsights(**data['wisdom_insights'])
    
    return FileAnalysisResult(**data)


# Export all models
__all__ = [
    'LanguageType',
    'ComplexityLevel',
    'CodeSmellType',
    'FunctionInfo',
    'MethodInfo', 
    'ClassInfo',
    'ImportInfo',
    'CodeSmell',
    'StyleIssue',
    'QualityMetrics',
    'DependencyInfo',
    'ParsingMetadata',
    'WisdomInsights',
    'FileAnalysisResult',
    'create_file_analysis_from_dict'
]
