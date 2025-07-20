# LLM Ops 리팩토링 계획

## 🎯 핵심 목표

1. **백그라운드 실행**: ask_o3를 비차단 방식으로 실행
2. **진행 상황 추적**: 실행 상태 확인 가능
3. **결과 수집**: 완료된 결과를 나중에 확인
4. **단순화**: 불필요한 기능 제거

## 🔧 제안하는 새로운 구조

### 1. 백그라운드 작업 시스템

```python
# 새로운 llm.py 구조
class O3Task:
    def __init__(self, task_id, question, status='pending'):
        self.id = task_id
        self.question = question
        self.status = status  # pending, running, completed, error
        self.result = None
        self.error = None
        self.start_time = None
        self.end_time = None
        self.thread = None

# 전역 작업 관리
_tasks = {}
_task_counter = 0

def ask_o3_async(question, context=None):
    '''비동기로 o3 실행'''
    task_id = _generate_task_id()
    task = O3Task(task_id, question)
    _tasks[task_id] = task

    # 백그라운드 스레드에서 실행
    thread = threading.Thread(
        target=_run_o3_task,
        args=(task, question, context)
    )
    thread.daemon = True
    thread.start()

    return ok(task_id, status='started')

def check_o3_status(task_id):
    '''작업 상태 확인'''
    if task_id not in _tasks:
        return err(f"Task {task_id} not found")

    task = _tasks[task_id]
    return ok({
        'id': task_id,
        'status': task.status,
        'question': task.question[:100] + '...',
        'duration': _calculate_duration(task)
    })

def get_o3_result(task_id):
    '''완료된 결과 가져오기'''
    if task_id not in _tasks:
        return err(f"Task {task_id} not found")

    task = _tasks[task_id]
    if task.status == 'completed':
        return ok(task.result)
    elif task.status == 'error':
        return err(task.error)
    else:
        return ok(None, status=task.status)

def list_o3_tasks():
    '''모든 작업 목록'''
    tasks = []
    for task_id, task in _tasks.items():
        tasks.append({
            'id': task_id,
            'status': task.status,
            'question': task.question[:50] + '...'
        })
    return ok(tasks)
```

### 2. 사용 워크플로우

```python
# 1. 비동기 실행 시작
result = h.ask_o3_async("복잡한 질문...")
task_id = result['data']
print(f"작업 시작됨: {task_id}")

# 2. 다른 작업 진행
# ... 코드 작성, 파일 수정 등 ...

# 3. 상태 확인
status = h.check_o3_status(task_id)
print(f"상태: {status['data']['status']}")

# 4. 결과 확인 (완료되면)
result = h.get_o3_result(task_id)
if result['ok'] and result['data']:
    print(f"o3 답변: {result['data']['answer']}")
```

### 3. 동기 버전도 유지

```python
def ask_o3(question, context=None, timeout=300):
    '''동기 버전 (기다림)'''
    # 비동기 시작
    result = ask_o3_async(question, context)
    task_id = result['data']

    # 완료 대기 (타임아웃 있음)
    start = time.time()
    while time.time() - start < timeout:
        status = check_o3_status(task_id)
        if status['data']['status'] in ['completed', 'error']:
            return get_o3_result(task_id)
        time.sleep(1)

    return err(f"Timeout after {timeout}s")
```

## 📦 구현 세부사항

### 1. 작업 영속성 (선택)
```python
def save_tasks():
    '''작업을 파일로 저장 (REPL 재시작 대비)'''
    tasks_data = {}
    for task_id, task in _tasks.items():
        if task.status in ['completed', 'error']:
            tasks_data[task_id] = {
                'question': task.question,
                'status': task.status,
                'result': task.result,
                'error': task.error
            }
    write_json('.o3_tasks.json', tasks_data)

def load_tasks():
    '''저장된 작업 불러오기'''
    if exists('.o3_tasks.json'):
        tasks_data = read_json('.o3_tasks.json')['data']
        # ... 복원 로직 ...
```

### 2. 진행 표시
```python
def show_o3_progress():
    '''모든 작업의 진행 상황 표시'''
    tasks = list_o3_tasks()['data']

    print("🤖 o3 작업 현황:")
    for task in tasks:
        icon = {
            'pending': '⏳',
            'running': '🔄',
            'completed': '✅',
            'error': '❌'
        }.get(task['status'], '❓')

        print(f"{icon} [{task['id']}] {task['status']} - {task['question']}")
```

## 🚀 구현 우선순위

1. **Phase 1** (즉시)
   - 기본 백그라운드 실행 (threading)
   - 상태 확인 함수
   - 결과 수집 함수

2. **Phase 2** (선택)
   - 작업 영속성
   - 진행률 표시
   - 작업 취소 기능

3. **제거할 기능**
   - analyze_code (너무 단순함)
   - 복잡한 옵션들
   - 중복 기능

## 💡 주요 이점

1. **비차단 실행**: o3 실행 중에도 다른 작업 가능
2. **상태 추적**: 언제든지 진행 상황 확인
3. **유연성**: 동기/비동기 모두 지원
4. **단순함**: 복잡한 비동기 문법 없음
