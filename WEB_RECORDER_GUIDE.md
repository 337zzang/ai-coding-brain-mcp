# 🎯 WebRecorder 통합 사용 가이드

## 📚 개요
WebRecorder는 REPL과 브라우저 간 양방향 통신을 제공하는 웹 자동화 시스템입니다.
이제 `h.web` 네임스페이스를 통해 모든 기능에 접근할 수 있습니다.

## 🚀 빠른 시작

```python
import ai_helpers_new as h

# 1. 브라우저 시작
h.web.start("my_session", headless=False)
h.web.goto("https://example.com")

# 2. 레코더 생성 및 시작
h.web.create_recorder("my_session")
h.web.start_recording("my_session")

# 3. 사용자에게 가이드 제공
h.web.set_recorder_guidance("검색창을 클릭하세요")

# 4. 레코딩된 액션 확인
actions = h.web.get_recorded_actions("my_session")
print(f"캡처된 액션: {len(actions['data'])}개")

# 5. 액션 재실행
h.web.replay_actions(actions['data'], "my_session")

# 6. 레코딩 중지
h.web.stop_recording("my_session")
```

## 📋 주요 함수 레퍼런스

### 🔴 레코더 관리

#### `h.web.create_recorder(session_id)`
레코더를 생성하고 가이드 UI를 브라우저에 주입합니다.
- **매개변수**: `session_id` - 브라우저 세션 ID
- **반환값**: `{'ok': True, 'data': {'session_id': ..., 'recorder_id': ...}}`

#### `h.web.start_recording(session_id)`
레코딩을 시작합니다. 레코더가 없으면 자동으로 생성됩니다.
- **매개변수**: `session_id` - 브라우저 세션 ID
- **반환값**: `{'ok': True, 'data': {'recording': True}}`

#### `h.web.stop_recording(session_id)`
레코딩을 중지하고 캡처된 액션을 반환합니다.
- **매개변수**: `session_id` - 브라우저 세션 ID
- **반환값**: `{'ok': True, 'data': {'actions': [...]}}`

### 📝 액션 관리

#### `h.web.get_recorded_actions(session_id)`
현재까지 레코딩된 모든 액션을 가져옵니다.
- **매개변수**: `session_id` - 브라우저 세션 ID
- **반환값**: `{'ok': True, 'data': [액션 목록]}`

#### `h.web.replay_actions(actions, session_id, delay=0.5)`
레코딩된 액션을 재실행합니다.
- **매개변수**:
  - `actions` - 재실행할 액션 목록 (None이면 레코딩된 액션 사용)
  - `session_id` - 브라우저 세션 ID
  - `delay` - 액션 간 지연 시간(초)
- **반환값**: `{'ok': True, 'data': {'replayed': n, 'total': n}}`

### 💬 사용자 가이드

#### `h.web.set_recorder_guidance(message, session_id)`
브라우저에 가이드 메시지를 표시합니다.
- **매개변수**:
  - `message` - 표시할 가이드 메시지
  - `session_id` - 브라우저 세션 ID
- **반환값**: `{'ok': True, 'data': {'message': ...}}`

## 🎨 브라우저 UI

레코더가 활성화되면 브라우저 오른쪽 상단에 다음과 같은 UI가 표시됩니다:

```
┌─────────────────────────┐
│ 🔴 Web Recorder         │
│                         │
│ [가이드 메시지]         │
│                         │
│ ⏸️ Stopped | Actions: 0 │
└─────────────────────────┘
```

- **가이드 메시지**: REPL에서 설정한 지시사항 표시
- **상태 표시**: 레코딩 중/중지 상태
- **액션 카운터**: 캡처된 액션 수 실시간 표시

## 💡 실용적 사용 예제

### 예제 1: 로그인 자동화

```python
# 브라우저 시작
h.web.start("login_session", headless=False)
h.web.goto("https://myapp.com/login")

# 레코딩 시작
h.web.start_recording("login_session")

# 단계별 가이드
h.web.set_recorder_guidance("사용자명 입력란을 클릭하세요")
time.sleep(3)

h.web.set_recorder_guidance("사용자명을 입력하세요")
time.sleep(5)

h.web.set_recorder_guidance("비밀번호 입력란을 클릭하세요")
time.sleep(3)

h.web.set_recorder_guidance("비밀번호를 입력하세요")
time.sleep(5)

h.web.set_recorder_guidance("로그인 버튼을 클릭하세요")
time.sleep(3)

# 액션 저장
actions = h.web.get_recorded_actions("login_session")
print(f"로그인 프로세스: {len(actions['data'])}개 액션 캡처됨")

# 나중에 재사용
h.web.replay_actions(actions['data'], "login_session")
```

### 예제 2: 검색 자동화

```python
def automated_search(query):
    """검색 자동화 함수"""
    
    # 브라우저 준비
    session_id = f"search_{int(time.time())}"
    h.web.start(session_id, headless=False)
    h.web.goto("https://google.com")
    
    # 레코딩 시작
    h.web.create_recorder(session_id)
    h.web.start_recording(session_id)
    
    # 검색 수행
    h.web.set_recorder_guidance(f"'{query}' 검색을 수행하세요")
    
    # 사용자가 검색하도록 대기
    time.sleep(10)
    
    # 결과 수집
    actions = h.web.stop_recording(session_id)
    
    return actions['data']['actions']

# 사용
search_actions = automated_search("Python tutorial")
print(f"검색 액션 {len(search_actions)}개 레코딩됨")
```

### 예제 3: 워크플로우 저장 및 재사용

```python
import json

class WorkflowManager:
    """워크플로우 관리 클래스"""
    
    def __init__(self):
        self.workflows = {}
    
    def record_workflow(self, name, url):
        """새 워크플로우 레코딩"""
        session_id = f"workflow_{name}"
        
        # 브라우저 시작
        h.web.start(session_id, headless=False)
        h.web.goto(url)
        
        # 레코딩
        h.web.start_recording(session_id)
        h.web.set_recorder_guidance(f"'{name}' 워크플로우를 수행하세요")
        
        # 사용자 작업 대기
        input("작업을 완료한 후 Enter를 누르세요...")
        
        # 액션 저장
        actions = h.web.stop_recording(session_id)
        self.workflows[name] = {
            'url': url,
            'actions': actions['data']['actions'],
            'created': time.time()
        }
        
        # 파일로 저장
        with open(f'workflow_{name}.json', 'w') as f:
            json.dump(self.workflows[name], f, indent=2)
        
        h.web.close(session_id)
        return len(actions['data']['actions'])
    
    def execute_workflow(self, name):
        """저장된 워크플로우 실행"""
        if name not in self.workflows:
            # 파일에서 로드
            with open(f'workflow_{name}.json', 'r') as f:
                self.workflows[name] = json.load(f)
        
        workflow = self.workflows[name]
        session_id = f"replay_{name}_{int(time.time())}"
        
        # 브라우저 시작
        h.web.start(session_id, headless=False)
        h.web.goto(workflow['url'])
        
        # 액션 재실행
        result = h.web.replay_actions(workflow['actions'], session_id)
        
        return result

# 사용 예
wf = WorkflowManager()

# 워크플로우 레코딩
wf.record_workflow("shopping_checkout", "https://shop.example.com")

# 나중에 재실행
wf.execute_workflow("shopping_checkout")
```

## 🔧 고급 기능

### 액션 필터링 및 수정

```python
# 액션 가져오기
actions = h.web.get_recorded_actions("session1")

# 특정 타입만 필터링
click_actions = [a for a in actions['data'] if a['type'] == 'click']

# 액션 수정
for action in actions['data']:
    if action['type'] == 'input' and 'password' in action.get('selector', ''):
        action['value'] = '***'  # 비밀번호 마스킹

# 수정된 액션 재실행
h.web.replay_actions(actions['data'], "session1")
```

### 조건부 레코딩

```python
def conditional_recording(session_id, condition_func):
    """조건에 따라 레코딩 시작/중지"""
    
    h.web.start_recording(session_id)
    
    while True:
        # 현재 페이지 상태 확인
        url = h.web.execute_js("return window.location.href", session_id)
        
        if condition_func(url['data']):
            break
        
        time.sleep(1)
    
    return h.web.stop_recording(session_id)

# 특정 페이지 도달 시 중지
def reached_success_page(url):
    return 'success' in url or 'complete' in url

actions = conditional_recording("session1", reached_success_page)
```

## ⚠️ 주의사항

1. **asyncio 환경**: MCP REPL에서 직접 실행 시 asyncio 충돌 가능. 독립 스크립트 사용 권장
2. **선택자 안정성**: 동적 웹사이트에서는 선택자가 변경될 수 있음
3. **타이밍**: 페이지 로드 시간을 고려한 적절한 delay 설정 필요
4. **메모리**: 장시간 레코딩 시 액션 배열이 커질 수 있음

## 🚨 문제 해결

### 레코더가 작동하지 않을 때
```python
# 1. 세션 상태 확인
sessions = h.web.list_sessions()
print(sessions)

# 2. 레코더 재생성
h.web.create_recorder("session_id")

# 3. 브라우저 콘솔 확인
h.web.execute_js("console.log(window.replBridge)", "session_id")
```

### 액션이 캡처되지 않을 때
```python
# Bridge 상태 확인
result = h.web.execute_js("""
    return {
        bridgeExists: typeof window.replBridge !== 'undefined',
        recording: window.replBridge?.recording,
        actionCount: window.replBridge?.actions?.length || 0
    }
""", "session_id")
print(result)
```

## 📊 성능 최적화

- **배치 처리**: 여러 액션을 한 번에 재실행
- **병렬 세션**: 여러 브라우저 세션 동시 운영
- **선택적 레코딩**: 필요한 이벤트만 캡처하도록 필터링

## 🎉 결론

WebRecorder 통합으로 이제 하나의 통합된 인터페이스(`h.web`)를 통해:
- 브라우저 제어
- 사용자 액션 레코딩
- 워크플로우 자동화
- 양방향 REPL-브라우저 통신

모든 기능을 사용할 수 있습니다. 31개의 웹 자동화 함수가 완벽하게 통합되어 
강력하고 직관적인 웹 자동화 시스템을 제공합니다.