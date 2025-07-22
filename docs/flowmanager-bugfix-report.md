# FlowManagerUnified 버그 수정 보고서

## 개요
FlowManagerUnified 리팩토링 후 발생한 버그들을 분석하고 수정했습니다.

## 발견된 버그들

### 1. TypeError: _save_current_flow_id() missing required argument
- **위치**: `switch_flow` 메서드 (라인 1592)
- **원인**: 메서드 호출 시 필수 인자 `flow_id` 누락
- **해결**: `self._save_current_flow_id(flow_id)` 로 수정

### 2. Property 'flows' 동작 불능
- **위치**: 라인 170
- **원인**: `@flows.setter` 선언 후 setter 메서드 구현 없음
- **해결**: setter 선언 주석 처리

### 3. Flow v2 의존성 문제
- **위치**: `_handle_flow_command`, `_handle_plan_command`
- **원인**: Flow v2 모듈이 없을 때 기능 차단
- **해결**: Flow v2 체크 로직 주석 처리

### 4. 자료구조 불일치 (리스트 vs 딕셔너리)
- **위치**: `create_plan`, `_list_plans` 등
- **원인**: FlowRegistry는 plans를 딕셔너리로, 코드는 리스트로 처리
- **해결**: 모든 관련 코드를 딕셔너리 방식으로 통일

## 수정 결과

모든 명령어가 정상 작동합니다:
- ✅ `/flow <project>` - 프로젝트 전환
- ✅ `/plan add <name>` - Plan 추가
- ✅ `/plan list` - Plan 목록 조회
- ✅ `/task add <plan_id> <name>` - Task 추가

## 테스트 완료
- 4개의 Plan 생성 성공
- Task 추가 성공
- 중복 이름 체크 정상 작동

## 향후 개선사항
1. Flow v2 모듈 정리 또는 통합
2. 자료구조 일관성 개선 (리스트 vs 딕셔너리 명확히)
3. 에러 핸들링 강화
4. 단위 테스트 추가

작성일: 2025-07-22
작성자: AI Coding Brain
