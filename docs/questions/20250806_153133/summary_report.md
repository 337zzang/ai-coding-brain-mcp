# 웹 자동화 세션 유지 시스템 - 종합 검토 보고서

**작성일**: 2025-08-06 15:35  
**프로젝트**: ai-coding-brain-mcp  
**작성자**: Claude + O3 AI

## 📌 Executive Summary

여러 프로세스/터미널 간 웹 브라우저 세션 공유 문제에 대한 종합적인 검토를 수행했습니다.
Chrome 디버깅 모드 방식은 사용자 불편으로 제거했으며, 더 실용적인 대안을 모색 중입니다.

## 🔍 현재 상태

### ✅ 구현 완료
- BrowserManager 싱글톤 클래스 (단일 프로세스용)
- 프로젝트별 세션 관리
- 기본적인 세션 시작/종료/확인 기능

### ❌ 제거된 기능
- connect_to_existing_browser() - CDP 연결
- launch_browser_with_debugging() - 디버깅 포트
- get_browser_ws_endpoint() - WebSocket 엔드포인트
- save_browser_session() - 실수로 함께 삭제됨

### ⚠️ 미해결 문제
- 프로세스 간 브라우저 공유
- 세션 영속화
- 간편한 연결 방법

## 💡 제안 솔루션

### 1. 🥇 **Playwright Browser Server** (추천)

```python
# 서버 모드로 브라우저 실행
browser_server = playwright.chromium.launch_server(port=3000)
ws_endpoint = browser_server.ws_endpoint

# 다른 프로세스에서 연결
browser = playwright.chromium.connect(ws_endpoint)
```

**장점**:
- Playwright 네이티브 지원
- 안정적인 WebSocket 통신
- 여러 클라이언트 동시 연결 가능

**구현 방안**:
1. 백그라운드 프로세스로 Browser Server 실행
2. 포트/endpoint 정보를 파일에 저장
3. 세션 ID로 endpoint 매핑 관리
4. 헬퍼 함수로 복잡도 숨김

### 2. 🥈 **중앙 제어 서버**

```python
# FastAPI 기반 제어 서버
@app.post("/session/{session_id}/goto")
async def goto_url(session_id: str, url: str):
    browser = get_browser(session_id)
    browser.goto(url)
```

**장점**:
- 완전한 제어 가능
- RESTful API
- 로깅/모니터링 용이

**단점**:
- 구현 복잡도 높음
- 별도 서버 프로세스 필요

### 3. 🥉 **파일 기반 명령 큐**

```python
# 명령을 파일에 저장
command = {"action": "goto", "url": "https://example.com"}
save_command(session_id, command)

# 브라우저 프로세스가 파일 모니터링
execute_pending_commands()
```

**장점**:
- 단순한 구현
- 외부 의존성 없음

**단점**:
- 실시간성 부족
- 파일 I/O 오버헤드

## 🛠️ 구현 로드맵

### Phase 1: 기본 기능 복구 (1일)
- [ ] save_browser_session() 함수 재구현
- [ ] 세션 메타데이터 관리 개선
- [ ] 에러 처리 강화

### Phase 2: Browser Server 통합 (3일)
- [ ] launch_browser_server() 구현
- [ ] connect_to_server() 구현
- [ ] 세션 ID ↔ WebSocket 매핑
- [ ] 자동 재연결 로직

### Phase 3: 사용성 개선 (2일)
- [ ] 간편한 API 설계
- [ ] 자동 서버 시작/종료
- [ ] 세션 목록 UI
- [ ] 문서화

## 📊 비교 분석

| 방법 | 복잡도 | 안정성 | 성능 | 사용성 |
|------|--------|--------|------|--------|
| CDP 디버깅 | 낮음 | 높음 | 높음 | 낮음 |
| Browser Server | 중간 | 높음 | 높음 | 높음 |
| 제어 서버 | 높음 | 높음 | 중간 | 높음 |
| 파일 큐 | 낮음 | 중간 | 낮음 | 중간 |

## 🎯 최종 추천

**Playwright Browser Server 방식**을 기본으로 구현하되,
사용자에게는 간단한 세션 ID 기반 API만 노출하는 것을 추천합니다.

```python
# 사용자가 보는 API
h.web_start_shared(session_id="my_work")  # 서버 자동 시작
h.web_connect_shared(session_id="my_work")  # 간단히 연결

# 내부에서는 Browser Server 활용
```

## 📎 참고 자료

- 질문 폴더: `docs/questions/20250806_153133`
- 관련 코드: `docs/questions/20250806_153133/related_code/`
- O3 분석: `docs/questions/20250806_153133/o3_analysis.md`
- 시니어 질문: `docs/questions/20250806_153133/senior_question.md`

---

**다음 단계**: O3 분석 완료 후 구체적인 구현 계획 수립
