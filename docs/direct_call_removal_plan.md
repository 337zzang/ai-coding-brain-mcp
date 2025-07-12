# 직접 호출 제거 마이그레이션 계획

## Phase 1: 리스너 구현 (완료)
- ✅ ContextSyncListener
- ✅ AutoSaveListener
- ✅ GitCommitListener
- ✅ AuditLogListener

## Phase 2: 점진적 마이그레이션
1. 리스너들을 EventBus에 등록
2. 직접 호출과 이벤트 발행 병행 (과도기)
3. 동작 검증
4. 직접 호출 코드 제거

## Phase 3: 최적화
- 이벤트 배치 처리
- 비동기 처리 고려
- 성능 모니터링

## 예상 효과
- 📉 코드 결합도 감소
- 📈 확장성 향상
- 🔧 유지보수 용이
- 🎯 단일 책임 원칙 준수
