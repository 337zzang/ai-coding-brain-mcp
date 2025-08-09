# 웹 자동화 시스템 API

## 📋 개요
Client-Server 아키텍처 기반 웹 자동화 시스템

## 🏗️ 아키텍처
- **BrowserManager**: 중앙 브라우저 관리
- **SessionRegistry**: 세션 정보 저장/복구
- **ActivityLogger**: 활동 추적 및 로깅

## 📁 파일 구조
```
api/
├── __init__.py           # 패키지 초기화
├── browser_manager.py    # 브라우저 관리 핵심
├── session_registry.py   # 세션 레지스트리
├── activity_logger.py    # 활동 로거
├── fix_bugs.py          # 버그 수정 유틸리티
├── test_browser_manager.py  # 테스트 스크립트
└── README.md            # 이 문서
```

## 🚀 사용법

### 기본 사용
```python
from api import BrowserManager

# 매니저 생성
manager = BrowserManager()

# 세션 생성
session = manager.create_session("user_123")

# 다른 프로세스에서 재연결
browser = manager.connect("user_123")
```

### 세션 관리
```python
# 세션 목록
sessions = manager.list_sessions()

# 세션 종료
manager.terminate_session(session_id)

# 고아 프로세스 정리
manager.cleanup_orphans()
```

## 🧪 테스트
```bash
python api/test_browser_manager.py
```

## 🐛 버그 수정
```bash
python api/fix_bugs.py
```

## 📝 버전
- v2.0.0: Client-Server 아키텍처 전환
- v1.0.0: Thread 기반 (deprecated)
