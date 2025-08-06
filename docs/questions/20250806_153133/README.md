# 웹 자동화 세션 유지 시스템 설계 문제

**생성일**: 2025-08-06 15:33  
**긴급도**: HIGH  
**작성자**: AI Coding Brain MCP

## 📌 문제 개요

여러 대화 세션(터미널)에서 동일한 웹 브라우저를 제어해야 하는 요구사항이 있습니다.
현재 구현된 시스템은 단일 프로세스 내에서만 작동하며, 프로세스 간 브라우저 인스턴스 공유가 어렵습니다.

## 🎯 요구사항

1. **다중 세션 제어**: 다른 터미널/대화에서 동일 브라우저 제어
2. **간단한 사용법**: 세션 번호/ID로 쉽게 연결
3. **상태 유지**: 작업 중단 후 재개 시 이전 상태 유지
4. **사용자 친화적**: 복잡한 설정 없이 바로 사용

## 🔍 현재 구현 상태

### 구현된 기능
- `BrowserManager`: 싱글톤 패턴으로 인스턴스 관리
- `web_connect()`: 세션 시작/재사용
- `web_disconnect()`: 세션 종료
- `web_check_session()`: 세션 상태 확인
- `web_list_sessions()`: 활성 세션 목록

### 제거된 기능 (복잡도 때문에)
- Chrome 디버깅 모드 연결
- WebSocket endpoint 연결
- CDP(Chrome DevTools Protocol) 연결

## ❌ 문제점

1. **프로세스 격리**: Python 프로세스 간 객체 공유 불가
2. **직렬화 불가**: Playwright 브라우저 객체는 pickle 불가
3. **복잡한 대안**: 디버깅 포트 방식은 사용자에게 부담

## 🚀 시도한 해결책

1. **Chrome 디버깅 모드**
   - 문제: Chrome 재시작 필요, 포트 설정 복잡
   - 결과: 사용자 불편으로 제거

2. **세션 파일 저장/로드**
   - 문제: 브라우저 객체 직렬화 불가
   - 결과: 부분적으로만 작동

3. **BrowserManager 싱글톤**
   - 문제: 단일 프로세스 내에서만 작동
   - 결과: 프로세스 간 공유 불가

## 💡 검토 필요 사항

1. **아키텍처 설계**
   - 프로세스 간 통신 방법 (IPC, 소켓, 파이프?)
   - 중앙 서버 방식 vs P2P 방식
   - 세션 ID 관리 체계

2. **기술적 접근**
   - Selenium Grid 같은 기존 솔루션 활용?
   - 자체 프록시 서버 구현?
   - 브라우저 원격 제어 프로토콜 활용?

3. **사용성 고려**
   - 최소한의 설정으로 작동
   - 직관적인 API 설계
   - 에러 처리 및 복구

## 📁 폴더 구조

```
docs/questions/20250806_153133/
├── README.md                    # 이 문서
├── related_code/               # 관련 코드
│   ├── api/
│   │   ├── web_automation_helpers.py
│   │   ├── web_automation_manager.py
│   │   └── web_automation_integrated.py
│   └── ai_helpers_new/
│       ├── wrappers.py
│       └── __init__.py
├── system_info.json            # 시스템 정보
├── structure.txt               # 디렉토리 구조
├── o3_task_id.txt             # O3 분석 작업 ID
└── o3_analysis.md             # O3 분석 결과 (대기 중)

## 🔧 재현 방법

```python
# 세션 1에서
import ai_helpers_new as h
h.web_start()
h.web_goto("https://example.com")
# 브라우저 열림

# 세션 2에서 (다른 터미널)
import ai_helpers_new as h
# 어떻게 세션 1의 브라우저에 연결? <- 문제!
```

## 📞 연락처

프로젝트: ai-coding-brain-mcp
경로: C:\Users\Administrator\Desktop\ai-coding-brain-mcp
