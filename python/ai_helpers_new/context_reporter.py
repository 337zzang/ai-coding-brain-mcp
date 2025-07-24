"""
Context Reporter - Context 데이터 분석 및 리포트 생성
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional


class ContextReporter:
    """Context 데이터를 분석하여 리포트를 생성하는 클래스"""

    def __init__(self, context_dir: str = '.ai-brain/contexts'):
        """
        Args:
            context_dir: Context 파일이 저장된 디렉토리
        """
        self.context_dir = context_dir

    def load_context(self, flow_id: str) -> Optional[Dict[str, Any]]:
        """특정 Flow의 Context 파일을 로드

        Args:
            flow_id: Flow ID

        Returns:
            Context 데이터 딕셔너리 또는 None
        """
        # Flow 디렉토리 찾기
        flow_dir = None
        if os.path.exists(self.context_dir):
            for d in os.listdir(self.context_dir):
                if flow_id in d:
                    flow_dir = os.path.join(self.context_dir, d)
                    break

        if not flow_dir:
            return None

        # Context 파일 읽기
        context_file = os.path.join(flow_dir, 'context.json')
        if not os.path.exists(context_file):
            return None

        try:
            with open(context_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading context: {e}")
            return None

    def generate_stats(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """이벤트 목록에서 통계 생성

        Args:
            events: Context 이벤트 목록

        Returns:
            통계 딕셔너리
        """
        stats = {
            'total_events': len(events),
            'method_stats': {},
            'error_count': 0,
            'auto_events': 0,
            'manual_events': 0
        }

        for event in events:
            details = event.get('details', {})

            # source 구분
            source = details.get('source', 'unknown')
            if source == 'auto':
                stats['auto_events'] += 1
            else:
                stats['manual_events'] += 1

            # 메서드별 통계 (auto 이벤트만)
            if source == 'auto' and 'method' in details:
                method = details['method']
                if method not in stats['method_stats']:
                    stats['method_stats'][method] = {
                        'count': 0,
                        'total_ms': 0,
                        'errors': 0,
                        'min_ms': float('inf'),
                        'max_ms': 0
                    }

                method_stat = stats['method_stats'][method]
                method_stat['count'] += 1

                # 실행 시간
                if 'elapsed_ms' in details:
                    elapsed = details['elapsed_ms']
                    method_stat['total_ms'] += elapsed
                    method_stat['min_ms'] = min(method_stat['min_ms'], elapsed)
                    method_stat['max_ms'] = max(method_stat['max_ms'], elapsed)

                # 에러 여부
                if 'error' in details or '_failed' in event.get('action_type', ''):
                    method_stat['errors'] += 1
                    stats['error_count'] += 1

        # 평균 계산
        for method, stat in stats['method_stats'].items():
            if stat['count'] > 0 and stat['total_ms'] > 0:
                stat['avg_ms'] = stat['total_ms'] / stat['count']
                stat['success_rate'] = (stat['count'] - stat['errors']) / stat['count'] * 100
            else:
                stat['avg_ms'] = 0
                stat['success_rate'] = 100 if stat['errors'] == 0 else 0

        return stats

    def get_slow_operations(self, events: List[Dict[str, Any]], threshold_ms: int = 1000) -> List[Dict[str, Any]]:
        """느린 작업 찾기

        Args:
            events: Context 이벤트 목록
            threshold_ms: 임계값 (밀리초)

        Returns:
            느린 작업 목록
        """
        slow_ops = []

        for event in events:
            details = event.get('details', {})
            if details.get('source') == 'auto' and 'elapsed_ms' in details:
                if details['elapsed_ms'] > threshold_ms:
                    slow_ops.append({
                        'method': details.get('method', 'unknown'),
                        'elapsed_ms': details['elapsed_ms'],
                        'timestamp': event.get('timestamp', ''),
                        'params': details.get('params', {}),
                        'action_type': event.get('action_type', '')
                    })

        # 실행 시간 내림차순 정렬
        slow_ops.sort(key=lambda x: x['elapsed_ms'], reverse=True)
        return slow_ops

    def create_report(self, flow_id: str) -> str:
        """종합 리포트 생성

        Args:
            flow_id: Flow ID

        Returns:
            Markdown 형식의 리포트
        """
        # Context 로드
        context_data = self.load_context(flow_id)
        if not context_data:
            return f"# Context Report\n\nNo context data found for flow: {flow_id}"

        events = context_data.get('events', [])
        if not events:
            return f"# Context Report\n\nNo events recorded for flow: {flow_id}"

        # 통계 생성
        stats = self.generate_stats(events)
        slow_ops = self.get_slow_operations(events)

        # 리포트 작성
        report = f"""# Context Report
**Flow ID**: {flow_id}
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Overview
- **Total Events**: {stats['total_events']}
- **Auto-recorded**: {stats['auto_events']}
- **Manual**: {stats['manual_events']}
- **Errors**: {stats['error_count']}

## 📈 Method Statistics
| Method | Calls | Avg Time | Min | Max | Success Rate |
|--------|-------|----------|-----|-----|--------------|
"""

        # 메서드별 통계 추가
        for method, stat in sorted(stats['method_stats'].items()):
            report += f"| {method} | {stat['count']} | {stat['avg_ms']:.1f}ms | "
            report += f"{stat['min_ms']:.1f}ms | {stat['max_ms']:.1f}ms | "
            report += f"{stat['success_rate']:.1f}% |\n"

        # 느린 작업 추가
        if slow_ops:
            report += f"""
## ⚠️ Slow Operations (>{slow_ops[0]['elapsed_ms']:.0f}ms)
"""
            for i, op in enumerate(slow_ops[:10], 1):  # 상위 10개만
                report += f"{i}. **{op['method']}** - {op['elapsed_ms']:.1f}ms\n"
                if op['params']:
                    report += f"   - Params: {op['params']}\n"
                report += f"   - Time: {op['timestamp']}\n\n"

        # 개선 제안
        report += """
## 💡 Recommendations
"""

        # 느린 메서드 찾기
        slow_methods = []
        for method, stat in stats['method_stats'].items():
            if stat['avg_ms'] > 100:  # 100ms 이상
                slow_methods.append((method, stat['avg_ms']))

        if slow_methods:
            slow_methods.sort(key=lambda x: x[1], reverse=True)
            report += f"- **Performance**: {slow_methods[0][0]} averages {slow_methods[0][1]:.1f}ms - consider optimization\n"

        # 에러율 높은 메서드
        error_methods = []
        for method, stat in stats['method_stats'].items():
            if stat['errors'] > 0:
                error_rate = (stat['errors'] / stat['count']) * 100
                if error_rate > 5:  # 5% 이상
                    error_methods.append((method, error_rate))

        if error_methods:
            error_methods.sort(key=lambda x: x[1], reverse=True)
            report += f"- **Reliability**: {error_methods[0][0]} has {error_methods[0][1]:.1f}% error rate - needs investigation\n"

        return report


# 테스트 헬퍼 함수
def test_context_reporter(flow_id: str = None):
    """ContextReporter 테스트"""
    reporter = ContextReporter()

    # 현재 Flow ID 사용하거나 가장 최근 것 찾기
    if not flow_id:
        # 가장 최근 Flow 찾기
        context_dir = '.ai-brain/contexts'
        if os.path.exists(context_dir):
            dirs = sorted([d for d in os.listdir(context_dir) if d.startswith('flow_')], 
                         reverse=True)
            if dirs:
                flow_id = dirs[0].replace('flow_', '')

    if not flow_id:
        print("No flow ID found")
        return

    print(f"Testing with flow: {flow_id}")

    # 리포트 생성
    report = reporter.create_report(flow_id)
    print(report)

    return report
