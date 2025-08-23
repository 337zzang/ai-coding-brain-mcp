"""
Code Execution Analyzer
execute_code 실행 후 직접 호출하여 분석 및 가이드 제공
"""

from datetime import datetime
from typing import Dict, Any, Optional

class CodeAnalyzer:
    """코드 실행 결과 분석 및 가이드 제공"""
    
    def __init__(self):
        self.last_analysis = None
        self.timestamp = datetime.now()
    
    def analyze_last_execution(self, code: str = "", output: str = "") -> Dict[str, Any]:
        """마지막 실행 결과 분석"""
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'code_metrics': {
                'lines': len(code.split('\n')) if code else 0,
                'size': len(code) if code else 0,
                'complexity': self._assess_complexity(code)
            },
            'status': self._check_status(output),
            'recommendations': self._generate_recommendations(code, output)
        }
        
        self.last_analysis = analysis
        return analysis
    
    def _assess_complexity(self, code: str) -> str:
        """코드 복잡도 평가"""
        if not code:
            return 'none'
        
        lines = len(code.split('\n'))
        
        # 복잡도 지표
        has_loops = any(kw in code for kw in ['for ', 'while '])
        has_conditions = any(kw in code for kw in ['if ', 'elif ', 'else:'])
        has_functions = 'def ' in code or 'lambda' in code
        has_classes = 'class ' in code
        
        complexity_score = sum([
            has_loops * 2,
            has_conditions * 1,
            has_functions * 2,
            has_classes * 3,
            (lines > 50) * 2,
            (lines > 100) * 3
        ])
        
        if complexity_score >= 5:
            return 'high'
        elif complexity_score >= 2:
            return 'medium'
        return 'low'
    
    def _check_status(self, output: str) -> Dict[str, Any]:
        """실행 상태 체크"""
        output_lower = output.lower() if output else ""
        
        return {
            'has_errors': any(err in output_lower for err in ['error', 'exception', 'failed', 'traceback']),
            'has_warnings': 'warning' in output_lower,
            'is_successful': '✅' in output or 'success' in output_lower or 'completed' in output_lower,
            'error_type': self._identify_error_type(output) if 'error' in output_lower else None
        }
    
    def _identify_error_type(self, output: str) -> Optional[str]:
        """오류 유형 식별"""
        error_patterns = {
            'AttributeError': 'attribute_error',
            'NameError': 'name_error',
            'SyntaxError': 'syntax_error',
            'KeyError': 'key_error',
            'FileNotFoundError': 'file_not_found',
            'ImportError': 'import_error',
            'TypeError': 'type_error',
            'ValueError': 'value_error'
        }
        
        for pattern, error_type in error_patterns.items():
            if pattern in output:
                return error_type
        
        return 'unknown_error'
    
    def _generate_recommendations(self, code: str, output: str) -> list:
        """권장사항 생성"""
        recommendations = []
        status = self._check_status(output)
        
        if status['has_errors']:
            error_type = status['error_type']
            
            if error_type == 'attribute_error':
                recommendations.append("✏️ 메서드명 확인: h.search.files() (O) vs h.search.search_files() (X)")
                recommendations.append("📚 API 문서 참조 권장")
            elif error_type == 'name_error':
                recommendations.append("📦 import 문 확인: import ai_helpers_new as h")
                recommendations.append("🔍 변수 정의 여부 확인")
            elif error_type == 'syntax_error':
                recommendations.append("🔧 f-string 중괄호 처리 확인")
                recommendations.append("📐 들여쓰기 일관성 체크")
            else:
                recommendations.append("🔍 전체 에러 메시지 분석 필요")
                recommendations.append("💡 Think 도구로 심층 분석 권장")
        
        else:
            complexity = self._assess_complexity(code)
            
            if complexity == 'high':
                recommendations.append("🎯 Think 도구로 코드 검증 권장")
                recommendations.append("♻️ 리팩토링 기회 검토")
            elif complexity == 'medium':
                recommendations.append("✅ 테스트 케이스 추가 고려")
                recommendations.append("📝 문서화 업데이트")
            else:
                recommendations.append("✨ 정상 실행 완료")
                recommendations.append("➡️ 다음 작업 진행 가능")
        
        # Flow 관련 추천
        if code and 'flow' in code.lower():
            recommendations.append("📊 Flow 시스템 상태 업데이트 확인")
        
        return recommendations
    
    def get_next_action_prompt(self) -> str:
        """다음 액션을 위한 프롬프트 생성"""
        
        if not self.last_analysis:
            return "먼저 analyze_last_execution()을 실행하세요."
        
        status = self.last_analysis.get('status', {})
        
        if status.get('has_errors'):
            return (
                "Think 도구를 사용하여 다음을 분석해주세요:\n"
                "1. 오류의 근본 원인\n"
                "2. 단계별 해결 방법\n"
                "3. 유사 오류 방지 방안"
            )
        
        complexity = self.last_analysis['code_metrics']['complexity']
        
        if complexity == 'high':
            return (
                "Think 도구로 다음을 검토해주세요:\n"
                "1. 코드 실행 결과 검증\n"
                "2. 성능 최적화 기회\n"
                "3. 코드 품질 개선점"
            )
        
        return "실행이 정상적으로 완료되었습니다. 다음 작업을 진행하세요."
    
    def print_guide(self):
        """분석 결과를 보기 좋게 출력"""
        
        if not self.last_analysis:
            print("❌ 분석할 데이터가 없습니다.")
            return
        
        analysis = self.last_analysis
        
        print("\n" + "="*60)
        print(f"📊 코드 실행 분석 결과 [{analysis['timestamp'][:19]}]")
        print("="*60)
        
        # 메트릭스
        metrics = analysis['code_metrics']
        print(f"\n📈 코드 메트릭스:")
        print(f"   • 라인 수: {metrics['lines']}")
        print(f"   • 복잡도: {metrics['complexity'].upper()}")
        
        # 상태
        status = analysis['status']
        status_icon = "❌" if status['has_errors'] else "✅"
        print(f"\n{status_icon} 실행 상태:")
        print(f"   • 오류: {'있음' if status['has_errors'] else '없음'}")
        if status['error_type']:
            print(f"   • 오류 유형: {status['error_type']}")
        
        # 권장사항
        print(f"\n💡 권장사항:")
        for rec in analysis['recommendations']:
            print(f"   {rec}")
        
        # 다음 액션
        print(f"\n🎯 다음 액션:")
        print(f"   {self.get_next_action_prompt()}")
        
        print("\n" + "="*60 + "\n")

# 전역 인스턴스 생성 (쉽게 접근하기 위해)
_analyzer = CodeAnalyzer()

def analyze(code: str = "", output: str = "") -> Dict[str, Any]:
    """간편 분석 함수"""
    return _analyzer.analyze_last_execution(code, output)

def guide():
    """간편 가이드 출력 함수"""
    _analyzer.print_guide()

def next_action() -> str:
    """다음 액션 프롬프트 반환"""
    return _analyzer.get_next_action_prompt()