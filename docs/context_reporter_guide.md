# ContextReporter 사용 가이드

## 📋 개요
ContextReporter는 auto_record로 자동 기록된 Context 데이터를 분석하여 유용한 통계와 리포트를 생성하는 도구입니다.

## 🚀 빠른 시작

### 기본 사용법
```python
from ai_helpers_new.context_reporter import ContextReporter

# Reporter 생성
reporter = ContextReporter()

# 특정 Flow의 리포트 생성
report = reporter.create_report("flow_id_here")
print(report)
```

### 간편 테스트 함수
```python
from ai_helpers_new.context_reporter import test_context_reporter

# 가장 최근 Flow 자동 분석
test_context_reporter()

# 특정 Flow 분석
test_context_reporter("flow_20250724_123456_abcdef")
```

## 📊 주요 기능

### 1. Context 로드
```python
context_data = reporter.load_context(flow_id)
events = context_data.get('events', [])
```

### 2. 통계 생성
```python
stats = reporter.generate_stats(events)
# 결과:
# {
#   'total_events': 150,
#   'auto_events': 120,
#   'manual_events': 30,
#   'method_stats': {...},
#   'error_count': 2
# }
```

### 3. 느린 작업 찾기
```python
# 1초(1000ms) 이상 걸린 작업
slow_ops = reporter.get_slow_operations(events, threshold_ms=1000)
```

### 4. 종합 리포트
```python
report = reporter.create_report(flow_id)
# Markdown 형식의 종합 리포트 생성
```

## 📈 리포트 구성

생성되는 리포트는 다음 섹션을 포함합니다:

1. **Overview**: 전체 이벤트 통계
2. **Method Statistics**: 메서드별 호출 횟수, 실행 시간, 성공률
3. **Slow Operations**: 느린 작업 상세 정보
4. **Recommendations**: 성능 및 안정성 개선 제안

## 💡 활용 예시

### 일일 리포트 생성
```python
import os
from datetime import datetime
from ai_helpers_new.context_reporter import ContextReporter

reporter = ContextReporter()

# 모든 Flow 리포트 생성
reports_dir = 'reports/daily'
os.makedirs(reports_dir, exist_ok=True)

context_dir = '.ai-brain/contexts'
for flow_dir in os.listdir(context_dir):
    if flow_dir.startswith('flow_'):
        flow_id = flow_dir.replace('flow_', '')
        report = reporter.create_report(flow_id)

        # 리포트 저장
        filename = f"{reports_dir}/{flow_id}_{datetime.now().strftime('%Y%m%d')}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
```

### 성능 모니터링
```python
# 평균 실행 시간이 높은 메서드 찾기
stats = reporter.generate_stats(events)
slow_methods = []

for method, stat in stats['method_stats'].items():
    if stat['avg_ms'] > 100:  # 100ms 이상
        slow_methods.append({
            'method': method,
            'avg_ms': stat['avg_ms'],
            'calls': stat['count']
        })

# 실행 시간 순으로 정렬
slow_methods.sort(key=lambda x: x['avg_ms'], reverse=True)
```

## ⚙️ 고급 설정

### Context 디렉토리 변경
```python
# 다른 위치의 Context 파일 분석
reporter = ContextReporter(context_dir='/custom/path/contexts')
```

### 커스텀 임계값
```python
# 500ms 이상을 느린 작업으로 정의
slow_ops = reporter.get_slow_operations(events, threshold_ms=500)
```

## 🔍 문제 해결

### Context 파일을 찾을 수 없음
- Flow ID가 정확한지 확인
- Context 시스템이 활성화되어 있는지 확인 (`CONTEXT_SYSTEM=on`)
- `.ai-brain/contexts/` 디렉토리 확인

### 통계가 비어있음
- auto_record가 적용된 메서드가 호출되었는지 확인
- Context 파일에 이벤트가 기록되었는지 확인

## 📝 참고사항
- ContextReporter는 읽기 전용이며 Context 파일을 수정하지 않습니다
- 대용량 Context 파일(>10MB)의 경우 처리 시간이 길어질 수 있습니다
- 리포트는 Markdown 형식으로 생성되어 다양한 도구에서 활용 가능합니다
