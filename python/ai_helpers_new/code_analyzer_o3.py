"""
Code Analyzer with O3 Integration
O3 LLM을 내부적으로 활용하는 강화된 코드 분석기
"""
import os
import sys
import json
import time
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# AI Helpers 임포트
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import ai_helpers_new as h

class CodeAnalyzerWithO3:
    """O3 통합 코드 분석기 - 자동 병렬 실행"""
    
    def __init__(self, auto_o3: bool = True):
        """
        Args:
            auto_o3: O3 분석 자동 실행 여부 (기본값: True)
        """
        self.auto_o3 = auto_o3
        self.analysis_cache = {}
        self.o3_tasks = {}
        self.start_time = None
        
    def analyze(self, file_path: str, deep_analysis: bool = True) -> Dict[str, Any]:
        """
        메인 분석 함수 - O3와 정적 분석 병렬 실행
        
        Args:
            file_path: 분석할 파일 경로
            deep_analysis: O3 심층 분석 포함 여부
            
        Returns:
            통합 분석 결과
        """
        self.start_time = time.time()
        print(f"🔍 코드 분석 시작: {file_path}")
        
        # 1. 코드 읽기
        code_content = self._read_code(file_path)
        if not code_content:
            return {'error': '파일을 읽을 수 없습니다.'}
        
        # 2. 병렬 분석 시작
        results = {
            'file': file_path,
            'timestamp': datetime.now().isoformat(),
            'analysis_mode': 'parallel_with_o3' if self.auto_o3 else 'static_only'
        }
        
        # 3. 정적 분석 (즉시 실행)
        print("  📊 정적 분석 시작...")
        static_analysis = self._perform_static_analysis(code_content, file_path)
        results['static_analysis'] = static_analysis
        
        # 4. O3 분석 (비동기 실행)
        if self.auto_o3 and deep_analysis:
            print("  🧠 O3 심층 분석 시작...")
            o3_task_id = self._start_o3_analysis(code_content, static_analysis)
            results['o3_task_id'] = o3_task_id
            
            # 5. O3 진행 중 추가 분석
            print("  ⚡ 병렬 처리 중...")
            runtime_analysis = self._perform_runtime_analysis(file_path)
            results['runtime_analysis'] = runtime_analysis
            
            # 6. O3 결과 수집 (타임아웃 설정)
            o3_result = self._wait_for_o3_result(o3_task_id, timeout=30)
            if o3_result:
                results['o3_analysis'] = o3_result
                print("  ✅ O3 분석 완료")
            else:
                results['o3_analysis'] = {'status': 'pending', 'message': 'O3 분석 진행 중...'}
                print("  ⏳ O3 분석 계속 진행 중...")
        
        # 7. 결과 통합
        results['integrated_insights'] = self._integrate_results(results)
        results['execution_time'] = time.time() - self.start_time
        
        print(f"✨ 분석 완료: {results['execution_time']:.2f}초")
        return results
    
    def _read_code(self, file_path: str) -> Optional[str]:
        """코드 파일 읽기"""
        try:
            result = h.read(file_path)
            if result['ok']:
                return result['data']
        except:
            pass
        
        # 대체 방법
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return None
    
    def _perform_static_analysis(self, code: str, file_path: str) -> Dict[str, Any]:
        """정적 코드 분석"""
        analysis = {
            'lines_of_code': len(code.split('\n')),
            'character_count': len(code),
            'issues': [],
            'metrics': {}
        }
        
        # 1. 코드 패턴 분석
        patterns = {
            'memory_leak': ['global_cache', 'data_buffer.append', 'self.children.append'],
            'performance': ['for i in range.*for j in range.*for k in range', 'sleep\\(', 'while True'],
            'security': ['eval\\(', 'exec\\(', '__import__', 'pickle\\.loads'],
            'concurrency': ['threading\\.Lock', 'asyncio', 'thread_local'],
            'quality': ['except:', 'pass', 'TODO', 'FIXME', 'XXX']
        }
        
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                import re
                matches = re.findall(pattern, code, re.IGNORECASE)
                if matches:
                    analysis['issues'].append({
                        'category': category,
                        'pattern': pattern,
                        'occurrences': len(matches),
                        'severity': self._calculate_severity(category, len(matches))
                    })
        
        # 2. 복잡도 계산
        analysis['metrics']['cyclomatic_complexity'] = self._calculate_complexity(code)
        analysis['metrics']['nesting_depth'] = self._calculate_nesting_depth(code)
        analysis['metrics']['function_count'] = code.count('def ')
        analysis['metrics']['class_count'] = code.count('class ')
        
        # 3. 의존성 분석
        imports = re.findall(r'^(?:from|import)\s+(\S+)', code, re.MULTILINE)
        analysis['dependencies'] = imports
        
        # 4. 문제점 요약
        analysis['total_issues'] = len(analysis['issues'])
        analysis['critical_issues'] = sum(1 for i in analysis['issues'] if i['severity'] == 'critical')
        
        return analysis
    
    def _start_o3_analysis(self, code: str, static_analysis: Dict) -> str:
        """O3 심층 분석 시작 (비동기)"""
        
        # 정적 분석 결과를 포함한 프롬프트 생성
        issues_summary = "\n".join([
            f"- {issue['category']}: {issue['occurrences']}개 ({issue['severity']})"
            for issue in static_analysis.get('issues', [])
        ])
        
        prompt = f"""
이 코드에 대한 심층 분석을 수행해주세요. 정적 분석에서 다음 문제들이 발견되었습니다:

{issues_summary}

코드 일부:
{code[:1500]}

다음 관점에서 추가 분석해주세요:
1. 아키텍처 수준의 문제점과 개선 방안
2. 디자인 패턴 적용 기회
3. 성능 최적화 구체적 방법
4. 보안 취약점 및 해결책
5. 테스트 가능성 개선 방안
6. 리팩토링 우선순위와 단계별 계획

각 항목에 대해 구체적인 코드 예시와 함께 제시해주세요.
"""
        
        # O3 비동기 분석 시작
        try:
            if hasattr(h, 'ask_o3_async'):
                result = h.ask_o3_async(prompt, reasoning_effort="high")
            elif hasattr(h, 'llm') and hasattr(h.llm, 'ask_async'):
                result = h.llm.ask_async(prompt, reasoning_effort="high")
            else:
                # O3 사용 불가 시 태스크 ID 시뮬레이션
                result = {'ok': True, 'data': f"simulated_o3_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"}
            
            if result['ok']:
                task_id = result['data']
                self.o3_tasks[task_id] = {
                    'started_at': datetime.now().isoformat(),
                    'status': 'running'
                }
                return task_id
        except Exception as e:
            print(f"  ⚠️ O3 분석 시작 실패: {e}")
        
        return None
    
    def _perform_runtime_analysis(self, file_path: str) -> Dict[str, Any]:
        """런타임 분석 (O3 처리 중 병렬 실행)"""
        runtime_data = {
            'analyzable': False,
            'execution_test': None,
            'import_check': None
        }
        
        try:
            # AST 파싱 시도
            if hasattr(h, 'code') and hasattr(h.code, 'parse'):
                parsed = h.code.parse(file_path)
                if parsed['ok']:
                    runtime_data['analyzable'] = True
                    runtime_data['ast_data'] = {
                        'functions': len(parsed['data'].get('functions', [])),
                        'classes': len(parsed['data'].get('classes', [])),
                        'imports': parsed['data'].get('imports', [])
                    }
        except:
            pass
        
        # 순환 참조 체크
        runtime_data['circular_reference_risk'] = self._check_circular_references(file_path)
        
        # 메모리 사용 예측
        runtime_data['memory_usage_prediction'] = self._predict_memory_usage(file_path)
        
        return runtime_data
    
    def _wait_for_o3_result(self, task_id: str, timeout: int = 30) -> Optional[Dict]:
        """O3 결과 대기 (타임아웃 포함)"""
        if not task_id:
            return None
        
        start_wait = time.time()
        check_interval = 2  # 2초마다 확인
        
        while time.time() - start_wait < timeout:
            try:
                # O3 상태 확인
                if hasattr(h, 'check_o3_status'):
                    status = h.check_o3_status(task_id)
                    if status['ok'] and status['data'] == 'completed':
                        # 결과 가져오기
                        if hasattr(h, 'get_o3_result'):
                            result = h.get_o3_result(task_id)
                            if result['ok']:
                                return self._parse_o3_result(result['data'])
                elif hasattr(h, 'llm'):
                    # llm 네임스페이스 사용
                    if hasattr(h.llm, 'check_status'):
                        status = h.llm.check_status(task_id)
                        if status['ok'] and status['data'] == 'completed':
                            result = h.llm.get_result(task_id)
                            if result['ok']:
                                return self._parse_o3_result(result['data'])
            except:
                pass
            
            time.sleep(check_interval)
        
        # 타임아웃 - 나중에 결과 확인 가능
        return None
    
    def _parse_o3_result(self, raw_result: str) -> Dict[str, Any]:
        """O3 결과 파싱"""
        return {
            'raw_insights': raw_result,
            'processed_at': datetime.now().isoformat(),
            'recommendations': self._extract_recommendations(raw_result)
        }
    
    def _extract_recommendations(self, o3_text: str) -> List[Dict]:
        """O3 텍스트에서 권장사항 추출"""
        recommendations = []
        
        # 간단한 파싱 (실제로는 더 정교한 파싱 필요)
        lines = o3_text.split('\n')
        current_rec = {}
        
        for line in lines:
            if '개선' in line or '최적화' in line or '리팩토링' in line:
                if current_rec:
                    recommendations.append(current_rec)
                current_rec = {'description': line.strip(), 'details': []}
            elif current_rec and line.strip():
                current_rec['details'].append(line.strip())
        
        if current_rec:
            recommendations.append(current_rec)
        
        return recommendations
    
    def _integrate_results(self, results: Dict) -> Dict[str, Any]:
        """모든 분석 결과 통합"""
        integrated = {
            'summary': {},
            'critical_findings': [],
            'optimization_opportunities': [],
            'action_items': []
        }
        
        # 정적 분석 결과 통합
        if 'static_analysis' in results:
            static = results['static_analysis']
            integrated['summary']['total_issues'] = static.get('total_issues', 0)
            integrated['summary']['critical_issues'] = static.get('critical_issues', 0)
            integrated['summary']['code_metrics'] = static.get('metrics', {})
            
            # 중요 발견사항
            for issue in static.get('issues', []):
                if issue['severity'] in ['critical', 'high']:
                    integrated['critical_findings'].append({
                        'type': issue['category'],
                        'description': f"{issue['pattern']} 패턴 {issue['occurrences']}회 발견",
                        'severity': issue['severity']
                    })
        
        # O3 분석 결과 통합
        if 'o3_analysis' in results and results['o3_analysis']:
            o3 = results['o3_analysis']
            for rec in o3.get('recommendations', []):
                integrated['optimization_opportunities'].append(rec)
        
        # 런타임 분석 결과 통합
        if 'runtime_analysis' in results:
            runtime = results['runtime_analysis']
            if runtime.get('circular_reference_risk'):
                integrated['critical_findings'].append({
                    'type': 'architecture',
                    'description': '순환 참조 위험 감지',
                    'severity': 'high'
                })
        
        # 액션 아이템 생성
        integrated['action_items'] = self._generate_action_items(integrated)
        
        return integrated
    
    def _generate_action_items(self, integrated: Dict) -> List[Dict]:
        """통합 결과에서 액션 아이템 생성"""
        action_items = []
        
        # 우선순위별 액션 아이템
        for finding in integrated.get('critical_findings', []):
            action_items.append({
                'priority': 'immediate',
                'action': f"{finding['type']} 문제 해결",
                'description': finding['description'],
                'estimated_effort': '1-2 hours'
            })
        
        for opp in integrated.get('optimization_opportunities', [])[:3]:  # 상위 3개
            action_items.append({
                'priority': 'high',
                'action': '성능 최적화',
                'description': opp.get('description', '최적화 기회'),
                'estimated_effort': '2-4 hours'
            })
        
        return action_items
    
    def _calculate_severity(self, category: str, count: int) -> str:
        """문제 심각도 계산"""
        severity_map = {
            'security': {'threshold': 1, 'high': 'critical'},
            'memory_leak': {'threshold': 2, 'high': 'critical'},
            'performance': {'threshold': 3, 'high': 'high'},
            'concurrency': {'threshold': 2, 'high': 'high'},
            'quality': {'threshold': 5, 'high': 'medium'}
        }
        
        if category in severity_map:
            if count >= severity_map[category]['threshold']:
                return severity_map[category]['high']
        
        return 'low'
    
    def _calculate_complexity(self, code: str) -> int:
        """사이클로매틱 복잡도 계산 (간단한 버전)"""
        complexity = 1  # 기본값
        
        # 분기문 카운트
        complexity += code.count('if ')
        complexity += code.count('elif ')
        complexity += code.count('for ')
        complexity += code.count('while ')
        complexity += code.count('except')
        complexity += code.count('case ')  # Python 3.10+
        
        return complexity
    
    def _calculate_nesting_depth(self, code: str) -> int:
        """최대 중첩 깊이 계산"""
        max_depth = 0
        current_depth = 0
        
        for line in code.split('\n'):
            # 들여쓰기 레벨 계산
            indent = len(line) - len(line.lstrip())
            depth = indent // 4  # 4 spaces = 1 level
            
            if depth > max_depth:
                max_depth = depth
        
        return max_depth
    
    def _check_circular_references(self, file_path: str) -> bool:
        """순환 참조 위험 체크"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
                
            # 간단한 패턴 체크
            patterns = [
                'self.parent = self',
                'self.children.append(self)',
                '.parent = .*\n.*\.children.append'
            ]
            
            import re
            for pattern in patterns:
                if re.search(pattern, code):
                    return True
        except:
            pass
        
        return False
    
    def _predict_memory_usage(self, file_path: str) -> str:
        """메모리 사용량 예측"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # 메모리 집약적 패턴 체크
            if 'global_cache' in code and 'clear()' not in code:
                return 'high_risk'
            elif any(pattern in code for pattern in ['data_buffer.append', 'list.append', 'dict[']):
                return 'medium_risk'
            else:
                return 'low_risk'
        except:
            return 'unknown'


# 사용 예시
def main():
    """테스트 실행"""
    analyzer = CodeAnalyzerWithO3(auto_o3=True)
    
    # 테스트 파일 분석
    test_file = "test_complex_code.py"
    if os.path.exists(test_file):
        print("="*60)
        print("🚀 O3 통합 코드 분석기 테스트")
        print("="*60)
        
        results = analyzer.analyze(test_file, deep_analysis=True)
        
        # 결과 출력
        print("\n📊 분석 결과:")
        print(f"  • 총 문제점: {results['integrated_insights']['summary'].get('total_issues', 0)}")
        print(f"  • 중요 문제: {results['integrated_insights']['summary'].get('critical_issues', 0)}")
        print(f"  • 실행 시간: {results['execution_time']:.2f}초")
        
        print("\n🔴 중요 발견사항:")
        for finding in results['integrated_insights']['critical_findings'][:3]:
            print(f"  • [{finding['severity']}] {finding['description']}")
        
        print("\n✅ 권장 조치:")
        for item in results['integrated_insights']['action_items'][:3]:
            print(f"  • [{item['priority']}] {item['action']}: {item['description']}")
        
        print("\n" + "="*60)
        
        # 결과 저장
        output_file = "analysis_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"💾 전체 결과 저장: {output_file}")


if __name__ == "__main__":
    main()