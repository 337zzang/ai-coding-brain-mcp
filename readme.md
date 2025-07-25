# AI Coding Brain MCP

## 📋 프로젝트 개요
- **생성일**: 2025-07-24
- **최종 업데이트**: 2025-07-25 11:02:42
- **프로젝트 타입**: Node.js + Python Hybrid
- **주요 언어**: TypeScript, Python
- **버전**: 4.2.0

## 🎯 주요 기능
1. **MCP (Model Context Protocol) 서버**: AI 모델과의 통신 인터페이스 제공
2. **Python REPL 세션**: JSON 기반 Python 코드 실행 환경
3. **AI Helpers v2.0**: 파일, 코드, Git, LLM 작업을 위한 통합 헬퍼 시스템
4. **Flow 시스템**: Plan/Task 기반 작업 관리 (극단순화 버전)
5. **프로젝트 관리**: 멀티 프로젝트 지원 및 전환 기능

## 🛠️ 기술 스택
- **백엔드**: Python 3.x, Node.js
- **프론트엔드**: TypeScript
- **빌드 도구**: npm, Python setuptools
- **테스트**: pytest, Jest
- **기타**: Git, JSON-RPC, MCP Protocol

## 📁 프로젝트 구조 요약
```
ai-coding-brain-mcp/
├── python/              # Python 백엔드
│   ├── ai_helpers_new/  # 헬퍼 모듈 패키지
│   └── json_repl_session.py  # REPL 세션
├── src/                 # TypeScript MCP 서버
├── test/                # 테스트 파일
├── docs/                # 문서
└── backups/             # 백업 파일
```

## 🚀 시작하기

### 설치
```bash
# Node.js 의존성 설치
npm install

# Python 의존성 설치 (필요시)
pip install -r requirements.txt
```

### 빌드
```bash
# TypeScript 빌드
npm run build
```

### 실행
```bash
# MCP 서버 시작
npm start
```

## 📌 중요 모듈

### 핵심 모듈 1: AI Helpers New
- **위치**: `python/ai_helpers_new/`
- **역할**: 파일, 코드, 검색, Git, LLM 작업을 위한 통합 헬퍼 시스템
- **주요 모듈**: 
  - `file.py`: 파일 읽기/쓰기/JSON 작업
  - `code.py`: Python 코드 분석 및 수정
  - `git.py`: Git 작업 관리
  - `simple_flow_commands.py`: Flow 명령어 시스템
  - `ultra_simple_flow_manager.py`: Plan/Task 관리

### 핵심 모듈 2: JSON REPL Session
- **위치**: `python/json_repl_session.py`
- **역할**: MCP와 Python 코드 실행 환경 연결
- **특징**: 
  - 영속적 세션 유지
  - 헬퍼 자동 로드
  - 에러 처리 및 보고

### 핵심 모듈 3: MCP Server
- **위치**: `src/`
- **역할**: Model Context Protocol 서버 구현
- **기능**: 
  - Python REPL 세션 관리
  - 도구 등록 및 실행
  - JSON-RPC 통신

## ⚠️ 주의사항
- Python과 Node.js 환경이 모두 필요합니다
- Windows 환경에서 개발되었으며, 경로 구분자 주의 필요
- 모든 헬퍼 함수는 {'ok': bool, 'data': ...} 형식의 응답 반환
- Flow 시스템은 프로젝트별로 독립적으로 관리됨

## 📝 TODO
- [ ] Linux/macOS 호환성 테스트
- [ ] 단위 테스트 커버리지 향상
- [ ] 문서화 개선
- [ ] 성능 최적화
