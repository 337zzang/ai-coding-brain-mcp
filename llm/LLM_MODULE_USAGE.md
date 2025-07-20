# LLM 모듈 사용 가이드

## 🚀 백그라운드 실행 (권장)

```python
import ai_helpers_new as h

# 1. 비동기로 o3 시작
result = h.ask_o3_async("""
복잡한 코드 리팩토링 문제:
현재 13개 파일로 분산된 헬퍼를 4개로 통합하는 방법은?
""")

task_id = result['data']
print(f"✅ 작업 시작: {task_id}")

# 2. 다른 작업 진행 (o3가 백그라운드에서 실행 중)
# 파일 수정, 코드 작성 등...
content = h.read('file.py')['data']
h.write('backup.py', content)

# 3. 상태 확인
status = h.check_o3_status(task_id)
print(f"상태: {status['data']['status']}")  # pending, running, completed, error

# 4. 진행 상황 보기
h.show_o3_progress()
# 🔄 [o3_task_0001] running     - 복잡한 코드 리팩토링 문제...
# ✅ [o3_task_0002] completed   - 간단한 질문...

# 5. 결과 확인 (완료되면)
result = h.get_o3_result(task_id)
if result['ok']:
    answer = result['data']['answer']
    print(f"o3 답변: {answer}")
```

## ⏳ 동기 실행 (기다림)

```python
# 간단한 질문은 그냥 기다려도 됨
result = h.ask_o3("Python에서 데코레이터 설명해줘")
if result['ok']:
    print(result['data']['answer'])
```

## 📋 컨텍스트 포함

```python
# 파일들과 함께 질문
context = h.prepare_o3_context(
    "버그 수정 도움 요청",
    ["bug.py", "test_bug.py"]
)

task_id = h.ask_o3_async(
    "이 버그를 어떻게 수정할까요?",
    context=context
)['data']
```

## 🎯 실제 워크플로우

```python
# 1. 복잡한 설계 질문은 백그라운드로
design_task = h.ask_o3_async("""
새로운 캐싱 시스템 설계:
- 메모리 효율적
- 스레드 안전
- TTL 지원
구체적인 구현 방법은?
""")['data']

# 2. 그 동안 다른 작업
files = h.search_files("*.py", ".")
for file in files['data'][:5]:
    # 파일 분석...
    info = h.parse(file)

# 3. 주기적으로 확인
import time
while True:
    status = h.check_o3_status(design_task)
    if status['data']['status'] in ['completed', 'error']:
        break
    print(f"⏳ 진행 중... ({status['data']['duration']})")
    time.sleep(5)

# 4. 결과 활용
result = h.get_o3_result(design_task)
if result['ok']:
    # o3의 설계안을 파일로 저장
    h.write('caching_design.md', result['data']['answer'])
```

## 📊 작업 관리

```python
# 모든 작업 보기
tasks = h.list_o3_tasks()
for task in tasks['data']:
    print(f"{task['id']}: {task['status']}")

# 실행 중인 것만 보기
running = h.list_o3_tasks('running')

# 완료된 작업 정리
h.clear_completed_tasks()
```

## ⚡ 팁

1. **긴 작업은 항상 async로**
   - 설계, 분석, 리팩토링 제안 등

2. **짧은 질문은 동기로**
   - 간단한 설명, 문법 질문 등

3. **컨텍스트 활용**
   - 관련 파일을 함께 전달하면 더 정확한 답변

4. **진행 상황 확인**
   - `show_o3_progress()`로 한눈에 보기
