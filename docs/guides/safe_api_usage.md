
# 🛡️ 안전한 AI Helpers API 사용 가이드

## 1. Manager vs FlowAPI 구분

```python
# ❌ 잘못된 사용
manager = h.get_flow_manager()
current_plan = manager.get_current_plan()  # AttributeError!

# ✅ 올바른 사용
# Option 1: FlowAPI 사용 (ok 키 없음 주의!)
flow_api = h.get_flow_api()
current_plan = flow_api.get_current_plan()  # dict 직접 반환
if current_plan:  # None 체크만
    plan_id = current_plan['id']

# Option 2: Manager로 현재 Plan 찾기
manager = h.get_flow_manager()
plans = manager.list_plans()
# 가장 최근 Plan이나 특정 조건으로 찾기
```

## 2. TaskLogger 올바른 사용

```python
# ❌ 잘못된 사용 (문서 오류)
logger.task_info(
    "제목",
    priority="high",
    estimate="2h",
    dependencies=["Task 1"]  # 지원하지 않음!
)

# ✅ 올바른 사용
logger.task_info(
    "제목",
    priority="high",
    estimate="2h"
    # dependencies는 별도로 기록
)
logger.context("dependencies", "Task 1 완료 필요")
```

## 3. 타입 안전한 코드 작성

```python
# 🛡️ 범용 안전 래퍼
def safe_api_call(func, *args, **kwargs):
    """모든 API 호출을 안전하게 래핑"""
    try:
        result = func(*args, **kwargs)

        # dict 타입이고 ok 키가 있는 경우 (표준 응답)
        if isinstance(result, dict) and 'ok' in result:
            return result

        # dict지만 ok 키가 없는 경우 (FlowAPI 등)
        elif isinstance(result, dict):
            return {'ok': True, 'data': result}

        # 기타 타입
        else:
            return {'ok': True, 'data': result}

    except Exception as e:
        return {'ok': False, 'error': str(e)}

# 사용 예시
result = safe_api_call(h.view, "file.py", "function_name")
if result['ok']:
    content = result.get('data', {}).get('content', '')
```

## 4. FlowAPI 특별 처리

```python
# FlowAPI는 항상 ok 키 없이 반환
flow_api = h.get_flow_api()

# 안전한 래퍼 함수
def safe_flow_api(method_name, *args, **kwargs):
    """FlowAPI 메서드를 표준 형식으로 래핑"""
    try:
        method = getattr(flow_api, method_name)
        result = method(*args, **kwargs)
        return {'ok': True, 'data': result}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

# 사용 예시
result = safe_flow_api('get_current_plan')
if result['ok'] and result['data']:
    plan = result['data']
```
