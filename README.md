# AI Coding Brain MCP - FlowManagerUnified

## 개요
AI Coding Brain MCP는 통합 워크플로우 관리 시스템입니다. 
FlowManagerUnified를 통해 프로젝트, 태스크, 컨텍스트를 효율적으로 관리합니다.

## 주요 기능

### 1. Flow 관리 (다중 프로젝트)
- `/flow create <name>` - 새 프로젝트(Flow) 생성
- `/flow list` - 모든 Flow 목록
- `/flow switch <id>` - Flow 전환
- `/flow` - 현재 Flow 정보

### 2. Plan 관리 (프로젝트 단계)
- `/plan add <name>` - 새 Plan 추가
- `/plan list` - Plan 목록

### 3. Task 관리
- `/task add <name>` - 새 태스크 추가
- `/list` - 태스크 목록
- `/start <id>` - 태스크 시작
- `/done <id>` - 태스크 완료
- `/skip <id>` - 태스크 건너뛰기

### 4. Context 시스템
- `/context` - 현재 컨텍스트 표시
- `/session save <name>` - 세션 저장
- `/session list` - 세션 목록
- `/history <n>` - 최근 히스토리
- `/stats` - 통계 정보

### 5. 기본 명령어
- `/help` - 도움말
- `/status` - 현재 상태
- `/report` - 전체 리포트

## 시스템 구조

```
python/
├── ai_helpers_new/
│   ├── flow_manager_unified.py  # 통합 매니저
│   └── __init__.py
└── workflow_wrapper.py          # 명령어 인터페이스
```

## 사용 예시

```python
from python.workflow_wrapper import wf

# 새 프로젝트 생성
wf("/flow create My Project")

# 태스크 추가
wf("/task add 코드 작성")
wf("/task add 테스트 작성")

# 태스크 시작 및 완료
wf("/start task_001")
wf("/done task_001")

# 상태 확인
wf("/status")
```

## 환경 설정

```bash
# Context 시스템 활성화
export CONTEXT_SYSTEM=on
```

## 변경 이력

### v27.1 (2025-07-21)
- FlowManagerUnified로 완전 통합
- 레거시 WorkflowManager 제거
- Flow v2 기능 완전 구현
- Context 시스템 통합

---
AI Coding Brain MCP v27.1 - Unified Workflow System
