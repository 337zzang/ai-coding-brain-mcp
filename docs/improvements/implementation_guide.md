
# 웹 자동화 시스템 구현 가이드

## 📊 현황 분석 요약

### 문제점
1. **Thread 기반 구조** - 세션 공유 불가능
2. **치명적 버그** - .h.append, true/false 오류
3. **로깅 미비** - 세션 ID 추적 불가
4. **코드 파편화** - 1300+ 라인의 helpers.py

### 해결 방안
1. **Client-Server 전환** - 독립 프로세스 + WebSocket
2. **버그 수정** - 자동화 스크립트 제공
3. **구조화 로깅** - SessionLogger 구현
4. **모듈화** - 책임별 파일 분리

## 🚀 즉시 시작 가능한 작업

### 1단계: 버그 수정 (오늘)
```python
# bug_fix.py
import re

def fix_critical_bugs(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # .h.append 오타 수정
    content = content.replace('.h.append(', '.append(')
    content = content.replace('.h.replace(', '.replace(')

    # JavaScript boolean 수정
    content = re.sub(r'\b=\s*true\b', '= True', content)
    content = re.sub(r'\b=\s*false\b', '= False', content)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"✅ {filepath} 수정 완료")

# 실행
files_to_fix = [
    "api/web_automation_helpers.py",
    "api/web_automation_errors.py",
    "api/web_automation_recorder.py"
]

for f in files_to_fix:
    if os.path.exists(f):
        fix_critical_bugs(f)
```

### 2단계: BrowserManager 프로토타입 (1-2일)
```python
# browser_manager_prototype.py
import subprocess
import json
import os
import re
from datetime import datetime

class BrowserManagerPrototype:
    def __init__(self):
        self.sessions = {}
        self.base_dir = "browser_sessions"
        os.makedirs(self.base_dir, exist_ok=True)

    def start_browser_server(self, session_id):
        # Playwright CLI 사용
        cmd = [
            "npx", "playwright", "launch-server",
            "--browser=chromium",
            "--port=0"
        ]

        # Windows 처리
        if os.name == 'nt':
            flags = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            flags = 0

        # 프로세스 시작
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=flags
        )

        # 엔드포인트 찾기
        ws_endpoint = None
        for line in proc.stdout:
            if "ws://" in line:
                match = re.search(r'ws://[^\s]+', line)
                if match:
                    ws_endpoint = match.group()
                    break

        if ws_endpoint:
            self.sessions[session_id] = {
                "pid": proc.pid,
                "ws_endpoint": ws_endpoint,
                "created": datetime.now().isoformat()
            }

            # 세션 저장
            with open(f"{self.base_dir}/sessions.json", 'w') as f:
                json.dump(self.sessions, f)

            return ws_endpoint

        return None
```

### 3단계: 클라이언트 헬퍼 (2-3일)
```python
# web_client.py
from playwright.sync_api import sync_playwright

class WebClient:
    def __init__(self, session_id):
        self.session_id = session_id
        self.manager = BrowserManagerPrototype()
        self.browser = None
        self.page = None

    def connect(self):
        # 세션 정보 로드
        with open("browser_sessions/sessions.json", 'r') as f:
            sessions = json.load(f)

        if self.session_id in sessions:
            ws_endpoint = sessions[self.session_id]["ws_endpoint"]
        else:
            # 새 브라우저 시작
            ws_endpoint = self.manager.start_browser_server(self.session_id)

        # 연결
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.connect(ws_endpoint)
        self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()

        return self.page

    def goto(self, url):
        if self.page:
            self.page.goto(url)
            self._log_action("goto", {"url": url})

    def click(self, selector):
        if self.page:
            self.page.click(selector)
            self._log_action("click", {"selector": selector})

    def _log_action(self, action, details):
        # 활동 로깅
        log_file = f"browser_sessions/{self.session_id}_activities.jsonl"
        record = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "action": action,
            "details": details
        }
        with open(log_file, 'a') as f:
            f.write(json.dumps(record) + '\n')
```

## 📋 구현 체크리스트

### 긴급 (오늘-내일)
- [ ] 치명적 버그 수정 스크립트 실행
- [ ] BrowserManager 프로토타입 테스트
- [ ] launch_server 동작 확인

### 단기 (이번 주)
- [ ] SessionRegistry 구현
- [ ] ActivityLogger 구현
- [ ] 기본 헬퍼 함수 작성
- [ ] Windows 환경 테스트

### 중기 (다음 주)
- [ ] 에러 처리 강화
- [ ] 헬스 체크 구현
- [ ] 고아 프로세스 관리
- [ ] 테스트 suite 작성

## 🎉 기대 효과

### 기술적 개선
- **세션 공유**: 여러 REPL에서 동일 브라우저 사용
- **안정성**: 프로세스 격리로 에러 전파 방지
- **추적성**: 모든 액션 로깅 및 분석 가능
- **확장성**: 100+ 동시 세션 지원

### 운영 개선
- **디버깅**: 세션별 로그로 문제 추적 용이
- **모니터링**: 실시간 세션 상태 확인
- **복구**: 크래시 시 자동 재시작
- **관리**: 중앙 집중식 세션 관리

## 📚 참고 문서

### 생성된 문서
1. `docs/improvements/web_automation_master_plan.md` - 종합 계획
2. `docs/design/web_automation_final_design_complete.md` - 최종 설계
3. `docs/analysis/o3_web_automation_analysis_*.md` - O3 분석
4. `docs/improvements/phase1_bugfix_checklist.md` - 버그 수정
5. `docs/improvements/phase2_architecture.md` - 아키텍처
6. `docs/improvements/phase3_tracking.md` - 추적 시스템

### O3 분석 상태
- Task 1: ✅ 완료 (종합 분석)
- Task 2: ⏳ 진행 중 (구현 세부사항)

완료되면 확인:
```python
result = h.llm.get_result('o3_task_0002')
if result['ok'] and 'answer' in result['data']:
    print(result['data']['answer'])
```

## 🏁 결론

Thread 기반 시스템을 Client-Server 아키텍처로 전환하여:
1. **세션 공유 문제 해결**
2. **ID 기반 추적 구현**
3. **크로스 프로세스 재연결 지원**

즉시 시작 가능한 프로토타입 코드와 단계별 구현 가이드를 제공했습니다.
