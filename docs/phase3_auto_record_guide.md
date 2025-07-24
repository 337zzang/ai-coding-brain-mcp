# Phase 3: Context 자동 기록 사용 가이드

## 🎯 개요
Phase 3에서는 FlowManager의 주요 메서드에 `@auto_record` decorator를 적용하여 모든 작업이 자동으로 Context에 기록됩니다.

## 🔧 적용된 메서드
- `create_flow` - Flow 생성
- `delete_flow` - Flow 삭제
- `select_flow` - Flow 선택
- `create_plan` - Plan 생성
- `update_plan_status` - Plan 상태 업데이트
- `create_task` - Task 생성
- `update_task_status` - Task 상태 업데이트
- `delete_task` - Task 삭제

## 📊 자동 기록되는 정보
각 메서드 호출 시 다음 정보가 자동으로 기록됩니다:
- **call_id**: 고유 호출 ID
- **source**: "auto" (자동 기록 표시)
- **method**: 메서드 이름
- **params**: 전달된 파라미터 (JSON 직렬화 가능한 형태로)
- **elapsed_ms**: 실행 시간 (밀리초)
- **result**: 반환값 (capture_result=True인 경우)
- **error**: 에러 정보 (실패 시)

## 🚀 사용 방법

### 기본 사용
```python
# Context는 자동으로 기록됩니다
manager = FlowManager()
flow = manager.create_flow("my_flow")  # 자동 기록됨
```

### Context 비활성화
```python
# 완전 비활성화
os.environ['CONTEXT_OFF'] = '1'

# 또는 FlowManager 레벨에서
manager._context_enabled = False
```

## 📈 Context 분석

### Context 파일 위치
```
.ai-brain/contexts/
├── flow_[flow_id]/
│   └── context.json
└── flow_system/
    └── context.json
```

### 간단한 통계 확인
```python
# Context 파일 읽기
context_data = h.read_json('.ai-brain/contexts/flow_xxx/context.json')
events = context_data['data']['events']

# 자동 기록만 필터링
auto_events = [e for e in events if e['details']['source'] == 'auto']

# 메서드별 통계
method_stats = {}
for event in auto_events:
    method = event['details']['method']
    elapsed = event['details'].get('elapsed_ms', 0)

    if method not in method_stats:
        method_stats[method] = {'count': 0, 'total_ms': 0}

    method_stats[method]['count'] += 1
    method_stats[method]['total_ms'] += elapsed

# 평균 실행 시간 계산
for method, stats in method_stats.items():
    avg_ms = stats['total_ms'] / stats['count']
    print(f"{method}: {stats['count']}회, 평균 {avg_ms:.1f}ms")
```

## ⚠️ 주의사항
1. **성능**: decorator overhead는 일반적으로 1ms 미만이지만, 초당 수천 번 호출되는 메서드에서는 고려 필요
2. **파일 크기**: Context 파일이 너무 커지면 주기적으로 정리 필요
3. **민감한 정보**: 파라미터가 자동 기록되므로 민감한 정보는 주의

## 💡 활용 예시
- **성능 모니터링**: 느린 작업 찾기
- **사용 패턴 분석**: 어떤 기능을 많이 사용하는지
- **에러 추적**: 실패한 작업과 원인 파악
- **감사 로그**: 누가 언제 무엇을 했는지 추적
