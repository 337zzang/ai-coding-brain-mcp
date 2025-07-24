# Flow 시스템 개선 실행 계획

## 🎯 o3 분석 결과 요약

### 핵심 개선사항
1. **모듈 통합**: 5개 → 3개 (Facade-Service-Repository)
2. **레거시 제거**: FlowManagerUnified + LegacyFlowAdapter → FlowFacade
3. **상태 단순화**: 5단계 → 3단계 (TODO, DOING, DONE)
4. **파일 Lock**: FileLock으로 동시성 문제 해결
5. **Context 통합**: 별도 Wrapper 제거, 객체 내부로 통합

### 새로운 아키텍처
```
┌──────────────┐
│ FlowFacade   │  ← 통합 진입점
└──────────────┘
       │
       ▼
┌──────────────┐
│ FlowService  │  ← 비즈니스 로직
└──────────────┘
       │
       ▼
┌──────────────┐
│JsonRepository│  ← 파일 I/O + Lock
└──────────────┘
```

## 📋 단계별 실행 계획

### Phase 0: 준비 (오늘)
- [ ] 현재 코드 백업
- [ ] 테스트 시나리오 작성
- [ ] 기존 flows.json 백업

### Phase 1: 도메인 모델 구현 (1일차)
- [ ] domain/models.py 생성
  - Flow, Plan, Task 데이터클래스
  - Status 열거형 (TODO, DOING, DONE)
  - to_dict/from_dict 메서드
- [ ] JsonRepository 구현
  - FileLock 추가
  - Atomic 파일 저장
  - 자동 백업 기능

### Phase 2: FlowService 구현 (2일차)
- [ ] 기존 FlowManager 로직 이관
- [ ] 상태 관리 단순화
- [ ] Context 통합

### Phase 3: FlowFacade 구현 (3일차)
- [ ] 레거시 호환 API
- [ ] 새로운 간소화된 API
- [ ] Deprecation 경고

### Phase 4: 명령어 라우터 개선 (4일차)
- [ ] 데코레이터 기반 라우팅
- [ ] elif 체인 제거
- [ ] 명령어 파서 분리

### Phase 5: 마이그레이션 (5일차)
- [ ] 기존 데이터 변환
- [ ] 레거시 모듈 제거
- [ ] 테스트 및 검증

## 🚀 즉시 시작할 작업

### 1. 도메인 모델 생성
