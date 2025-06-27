"""
코드 품질 분석 통합 모듈
기존 ast_parser_helpers와 ASTWisdomAnalyzer를 활용
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import ast
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ast_parser_helpers import parse_with_snippets

# Pydantic 모델 정의
class CodeIssue(BaseModel):
    """코드 이슈 모델"""
    type: str = Field(description="이슈 타입: error, warning, info")
    severity: str = Field(description="심각도: high, medium, low")
    message: str = Field(description="이슈 설명")
    line: int = Field(description="발생 라인")
    suggestion: Optional[str] = Field(None, description="개선 제안")

class CodeQualityMetrics(BaseModel):
    """코드 품질 메트릭"""
    complexity: int = Field(default=0, description="순환 복잡도")
    total_lines: int = Field(description="전체 라인 수")
    code_lines: int = Field(description="실제 코드 라인 수")
    comment_lines: int = Field(default=0, description="주석 라인 수")
    long_functions: List[str] = Field(default_factory=list, description="긴 함수 목록")
    unused_imports: List[str] = Field(default_factory=list, description="미사용 import")
    unused_variables: List[str] = Field(default_factory=list, description="미사용 변수")

class FileAnalysisResult(BaseModel):
    """파일 분석 결과 통합 모델"""
    file_path: str
    language: str
    analyzed_at: datetime = Field(default_factory=datetime.now)
    
    # 구조 정보 (parse_with_snippets 결과)
    classes: List[Dict[str, Any]] = Field(default_factory=list)
    functions: List[Dict[str, Any]] = Field(default_factory=list)
    imports: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 품질 정보
    quality_metrics: Optional[CodeQualityMetrics] = None
    issues: List[CodeIssue] = Field(default_factory=list)
    
    # 요약
    summary: str = ""

class CodeQualityAnalyzer:
    """코드 품질 분석기 - 기존 도구 활용"""
    
    def __init__(self, wisdom_manager=None):
        self.wisdom_manager = wisdom_manager
        # 품질 기준값
        self.LONG_FUNCTION_LINES = 50
        self.HIGH_COMPLEXITY = 10
        self.MAX_PARAMS = 5
        
    def analyze_file(self, file_path: str) -> FileAnalysisResult:
        """파일 종합 분석 - 구조 + 품질"""
        # 1. 기존 parse_with_snippets로 구조 분석
        structure_result = parse_with_snippets(file_path)
        
        if not structure_result.get('parsing_success'):
            return FileAnalysisResult(
                file_path=file_path,
                language=structure_result.get('language', 'unknown'),
                summary=f"파싱 실패: {structure_result.get('error', 'Unknown error')}"
            )
        
        # 2. 결과 모델 생성
        result = FileAnalysisResult(
            file_path=file_path,
            language=structure_result.get('language', 'unknown'),
            classes=structure_result.get('classes', []),
            functions=structure_result.get('functions', []),
            imports=structure_result.get('imports', [])
        )
        
        # 3. Python 파일인 경우 품질 분석 추가
        if result.language == 'python':
            quality_metrics, issues = self._analyze_python_quality(file_path, structure_result)
            result.quality_metrics = quality_metrics
            result.issues = issues
            
        # 4. 요약 생성
        result.summary = self._generate_summary(result)
        
        return result
        
    def _analyze_python_quality(self, file_path: str, structure: dict) -> tuple[CodeQualityMetrics, List[CodeIssue]]:
        """Python 코드 품질 분석"""
        issues = []
        
        # 파일 읽기
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.splitlines()
        except:
            return CodeQualityMetrics(total_lines=0, code_lines=0), issues
            
        # 기본 메트릭
        metrics = CodeQualityMetrics(
            total_lines=len(lines),
            code_lines=sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
        )
        
        # 긴 함수 검사
        for func in structure.get('functions', []):
            if 'line_start' in func and 'line_end' in func:
                func_length = func['line_end'] - func['line_start']
                if func_length > self.LONG_FUNCTION_LINES:
                    metrics.long_functions.append(func['name'])
                    issues.append(CodeIssue(
                        type='warning',
                        severity='medium',
                        message=f"함수 '{func['name']}'가 너무 깁니다 ({func_length}줄)",
                        line=func['line_start'],
                        suggestion=f"함수를 {self.LONG_FUNCTION_LINES}줄 이하로 분리하세요"
                    ))
                    
        # 매개변수 수 검사
        for func in structure.get('functions', []):
            params = func.get('args', [])
            if len(params) > self.MAX_PARAMS:
                issues.append(CodeIssue(
                    type='info',
                    severity='low',
                    message=f"함수 '{func['name']}'의 매개변수가 많습니다 ({len(params)}개)",
                    line=func.get('line_start', 0),
                    suggestion="매개변수를 객체나 딕셔너리로 묶는 것을 고려하세요"
                ))
                
        # TypeScript의 console 사용 검사
        if structure.get('language') == 'typescript':
            for i, line in enumerate(lines):
                if 'console.' in line:
                    issues.append(CodeIssue(
                        type='warning',
                        severity='medium',
                        message=f"console 사용 감지",
                        line=i + 1,
                        suggestion="logger를 사용하세요"
                    ))
                    
        return metrics, issues
        
    def _generate_summary(self, result: FileAnalysisResult) -> str:
        """분석 결과 요약 생성"""
        parts = []
        
        # 구조 정보
        if result.classes:
            parts.append(f"{len(result.classes)}개 클래스")
        if result.functions:
            parts.append(f"{len(result.functions)}개 함수")
            
        # 품질 정보
        if result.issues:
            high_issues = sum(1 for i in result.issues if i.severity == 'high')
            if high_issues:
                parts.append(f"{high_issues}개 심각한 이슈")
            else:
                parts.append(f"{len(result.issues)}개 이슈")
                
        return ", ".join(parts) if parts else "빈 파일"

# 사용 예시
if __name__ == "__main__":
    analyzer = CodeQualityAnalyzer()
    result = analyzer.analyze_file("example.py")
    
    print(f"파일: {result.file_path}")
    print(f"요약: {result.summary}")
    
    if result.quality_metrics:
        print(f"\n품질 메트릭:")
        print(f"  - 전체 라인: {result.quality_metrics.total_lines}")
        print(f"  - 코드 라인: {result.quality_metrics.code_lines}")
        
    if result.issues:
        print(f"\n발견된 이슈:")
        for issue in result.issues:
            print(f"  [{issue.severity}] {issue.message} (라인 {issue.line})")
            if issue.suggestion:
                print(f"    💡 {issue.suggestion}")
