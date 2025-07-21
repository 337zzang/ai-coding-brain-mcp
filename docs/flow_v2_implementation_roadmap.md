# Flow Project v2 구현 로드맵

## Phase 0: 준비 단계 (1일)
- [ ] WorkflowManager 테스트 작성
- [ ] 현재 workflow.json 백업
- [ ] v2 설계 문서 최종 검토

## Phase 1: FlowManager 기본 구조 (1일)
- [ ] models.py - Task, Plan dataclass
- [ ] flow_manager.py - 기본 클래스
- [ ] v1/v2 데이터 로드 로직
- [ ] 단위 테스트

## Phase 2: Plan/Task 관리 (2일)
- [ ] add_plan, update_plan, delete_plan
- [ ] Plan 내 Task 관리
- [ ] 계층적 진행률 계산
- [ ] 통합 테스트

## Phase 3: Context 시스템 (1일)
- [ ] context.json 스키마 정의
- [ ] 세션 저장/복원 로직
- [ ] 자동 요약 생성
- [ ] 컨텍스트 복원 테스트

## Phase 4: 명령어 시스템 (1일)
- [ ] /flow 명령어 파서
- [ ] 자동 완성 지원
- [ ] 도움말 시스템
- [ ] 하위 호환성 테스트

## Phase 5: 고급 기능 (1일)
- [ ] documents/ 관리
- [ ] snapshots/ 버전관리
- [ ] o3 분석 자동 연결
- [ ] 전체 통합 테스트
