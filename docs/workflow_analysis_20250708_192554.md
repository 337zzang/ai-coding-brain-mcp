# 워크플로우 시스템 현재 구조 분석 보고서

생성일: 2025-07-08 19:26:37
백업 위치: backups/workflow_refactoring_20250708_192554

## 1. 현재 구조 개요

### 핵심 모듈
- **WorkflowCommands** (python/workflow/commands.py): 명령어 파싱 및 처리
- **WorkflowManager** (python/workflow/workflow_manager.py): 워크플로우 비즈니스 로직
- **Models** (python/workflow/models.py): 데이터 모델 (Task, Plan, TaskStatus 등)
- **ContextManager** (python/core/context_manager.py): 프로젝트 컨텍스트 관리

### 지원 명령어 (13개)
- /plan, /task, /approve, /next, /status, /history
- /build, /done, /complete, /list, /start, /current, /tasks

## 2. 현재 아키텍처의 문제점

1. **분산된 책임**: 명령어 처리가 WorkflowCommands와 WorkflowManager에 분산
2. **문자열 의존성**: 모든 명령이 문자열 파싱을 거쳐야 함
3. **통합 어려움**: execute_code와 직접 연동 불가
4. **확장성 부족**: 새 명령어 추가 시 여러 파일 수정 필요
5. **복잡한 인스턴스 관리**: 프로젝트별 WorkflowManager 인스턴스 관리 복잡

## 3. 제안된 개선 사항

### 핵심 개선점
1. **함수형 API**: `helpers.workflow_plan()` 같은 직접 호출 가능한 함수
2. **중앙 디스패처**: 모든 명령어를 처리하는 단일 진입점
3. **HelperResult 통합**: 일관된 반환 형식
4. **자동 컨텍스트 관리**: 명령 실행 후 자동 저장/동기화
5. **플러그인 아키텍처**: 쉬운 명령어 추가/제거

### 예상 효과
- 유지보수성 향상
- AI 에이전트와의 통합 용이
- 코드 재사용성 증가
- 테스트 작성 용이

## 4. 다음 단계
- 핸들러 통합 구조 설계 (태스크 2)
- execute_code 연동 구현 (태스크 3)
