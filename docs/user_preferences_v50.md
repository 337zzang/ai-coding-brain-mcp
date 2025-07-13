# 🧠 AI Coding Brain MCP - Workflow Automation v50.0

## 🎯 핵심 철학
**"워크플로우와 완벽한 동기화 - 메시지가 곧 액션이다"**

## 🤖 자동화 규칙

### 1. 메시지 모니터링 및 자동 액션
워크플로우 메시지를 실시간으로 감지하고 자동으로 작업을 수행합니다.

#### 📌 st:state_changed 감지 시
```
task→completed: 
  1. 태스크 결과 보고서 생성
  2. 파일명: {project}_{plan}_{phase}_{task}_report_{YYYYMMDD}.md
  3. 다음 태스크 준비

task→in_progress:
  1. 작업 설계서 생성 (design_template.md 사용)
  2. 반드시 포함:
     - 설계 목적 명확히
     - AI가 이해한 내용 상세히
     - 구현 방향성 구체적으로
     - 타 모듈 영향도 분석
  3. 사용자 승인 대기

plan→completed:
  1. 페이즈 완료 보고서 생성
  2. 파일명: {project}_{plan}_phase_{phase}_complete_{YYYYMMDD}.md
  3. 성과 분석 및 다음 페이즈 제안

any→error:
  1. 즉시 에러 분석 시작
  2. logs/ 폴더 자동 스캔
  3. 수정 방안 제시
```

#### 📌 st:error_occurred 감지 시
```
1. 로그 파일 자동 분석 (logs/*.log)
2. 에러 발생 코드 위치 파악
3. 스택 트레이스 분석
4. 근본 원인 진단
5. 수정 코드 제안 (edit_block 사용)
6. 테스트 케이스 작성
```

### 2. 프로젝트 지식 활용
```
필수 검색 경로:
- code: python/**/*.py (현재 코드)
- memory: memory/**/*.json (상태/컨텍스트)
- docs: docs/**/*.md (문서)
- logs: logs/**/*.log (로그)

작업 전 반드시:
1. project_knowledge_search로 관련 정보 검색
2. 최근 변경사항 확인
3. 이전 에러 이력 확인
```

### 3. 설계 시 필수 요소
```python
# 모든 설계에 포함되어야 할 내용
design_context = {
    "purpose": "왜 이 작업이 필요한가?",
    "understanding": "내가 이해한 요구사항은...",
    "current_state": "현재 시스템 상태는...",
    "approach": "이렇게 접근하겠다...",
    "impact": {
        "direct": "직접 변경되는 모듈",
        "indirect": "영향받는 모듈",
        "breaking": "호환성 깨지는 부분"
    },
    "risks": "예상되는 위험 요소",
    "validation": "검증 방법"
}
```

### 4. 컨텍스트 지속성
```
작업 간 컨텍스트 유지:
1. 매 작업 후 context.json 업데이트
2. 태스크별 task_context.json 생성
3. 에러 발생 시 error_context.json 추가
4. 페이즈 완료 시 phase_summary.json 생성
```

### 5. 문서화 규칙
```
파일명 규칙 (AI가 쉽게 찾을 수 있도록):
- 설계: {project}_{plan}_{task}_design_v{N}.md
- 보고: {project}_{plan}_{task}_report_{YYYYMMDD}.md
- 에러: {project}_{plan}_error_{task}_{timestamp}.md
- 완료: {project}_{plan}_phase_{phase}_complete_{YYYYMMDD}.md

내용 구조:
- 명확한 제목과 목차
- 코드 블록은 언어 명시
- 변경사항은 diff 형식
- 이미지/다이어그램 적극 활용
```

### 6. 로그 분석 자동화
```python
# 에러 발생 시 자동 실행
def analyze_logs():
    1. 최근 로그 파일 검색
    2. 에러 패턴 매칭
    3. 타임스탬프 기준 정렬
    4. 연관 로그 그룹핑
    5. 근본 원인 추적
```

## 🚀 워크플로우 명령어
```
/start [계획] - 새 워크플로우 시작
/task [작업] - 태스크 추가
/next - 다음 작업으로
/error - 에러 분석 모드
/report - 현재 상태 보고
/design - 설계 모드 진입
```

## ⚡ 자동화 트리거
1. 메시지 출력 감지 → 즉시 액션
2. 파일 변경 감지 → 영향도 분석
3. 에러 로그 감지 → 자동 디버깅
4. 진행률 변경 → 보고서 업데이트

## 🎯 최종 목표
**"개발자는 명령만, AI는 실행과 보고를"**

---
v50.0 - 완전 자동화된 워크플로우 시스템
