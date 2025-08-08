# Execute_code 실행 문제 해결 가이드

## 🔴 자주 발생하는 오류와 해결법

### 1. FlowAPI 사용 패턴

#### ❌ 잘못된 사용
```python
# 1. 존재하지 않는 메서드
api.show_status()  # AttributeError

# 2. 체이닝 메서드의 반환값 확인
result = api.select_plan(plan_id)
if result['ok']:  # TypeError: FlowAPI not subscriptable
```

#### ✅ 올바른 사용
```python
# 1. flow 명령어 사용
status = h.flow("/status")
if status['ok']:
    print(status['data'])

# 2. 체이닝 메서드는 반환값 확인 불필요
api.select_plan(plan_id)  # 바로 사용
api.set_context('key', 'value')  # 체이닝 가능
```

### 2. Task 데이터 접근

#### ❌ 잘못된 접근
```python
task['name']  # KeyError
task['number']  # None 반환
```

#### ✅ 올바른 접근
```python
task['title']  # 'Task 1: 환경 준비'
task['id']     # 'task_20250805_xxx'
task['status'] # 'todo'

# number가 필요한 경우
task_number = int(task['id'].split('_')[2][:6])  # 날짜에서 추출
```

### 3. 표준 응답 형식 처리

#### ❌ 잘못된 처리
```python
# 직접 data 접근
data = h.read('file.py')  # 잘못됨
```

#### ✅ 올바른 처리
```python
# 항상 ok 확인 후 data 접근
result = h.read('file.py')
if result['ok']:
    data = result['data']
else:
    print(f"오류: {result['error']}")
```

### 4. Git 상태 확인

#### ❌ 예상과 다른 구조
```python
git_status['data']['modified']  # KeyError
git_status['data']['added']     # KeyError
```

#### ✅ 실제 구조
```python
git_status['data'] = {
    'files': [...],      # 모든 변경 파일
    'count': 594,        # 변경 파일 수
    'branch': 'refactor/...',
    'clean': False
}
```

## 📋 API 빠른 참조

### FlowAPI 주요 메서드
```python
api = h.get_flow_api()

# Plan 관리
api.create_plan(name, description="")
api.list_plans(status=None, limit=10)
api.get_plan(plan_id)
api.select_plan(plan_id)  # 체이닝, 반환값 확인 불필요

# Task 관리
api.create_task(plan_id, name, description="")
api.list_tasks(plan_id, status=None)
api.get_task(plan_id, task_id)
api.update_task_status(plan_id, task_id, status)

# 컨텍스트
api.get_current_plan()  # 현재 플랜 정보
api.set_context(key, value)  # 체이닝
```

### 자주 쓰는 헬퍼 함수
```python
# 파일 작업
h.read(path)['data']
h.write(path, content)
h.exists(path)['data']  # bool
h.get_file_info(path)['data']

# 코드 분석
h.parse(path)['data']  # {'classes': [], 'functions': []}
h.view(path, name)['data']

# 검색
h.search_files(path, pattern)['data']
h.search_code(path, pattern, file_pattern="*.py")['data']

# Git
h.git_status()['data']
h.git_add(".")
h.git_commit("message")
```

## 🛡️ 안전한 코딩 패턴

### 1. 항상 결과 확인
```python
result = h.any_function()
if not result['ok']:
    print(f"오류: {result['error']}")
    return
data = result['data']
```

### 2. 키 존재 확인
```python
# get() 사용으로 KeyError 방지
task_desc = task.get('description', 'No description')
task_num = task.get('number', 0)
```

### 3. 타입 확인
```python
if isinstance(result['data'], list):
    for item in result['data']:
        # 처리
elif isinstance(result['data'], dict):
    # 딕셔너리 처리
```

## 📈 개선 추적

- Task 모델에 number 필드 자동 설정 필요
- FlowAPI 문서화 개선 필요
- 헬퍼 함수 이름 일관성 개선 필요
- 타입 힌트 추가로 자동완성 개선 필요
