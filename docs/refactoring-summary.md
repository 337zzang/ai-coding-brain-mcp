# 🔧 AI Coding Brain MCP - 리팩토링 종합 분석

## 📊 현재 상태 (o3 + 추가 분석)

### 복잡도 메트릭
- **FlowCommandRouter**: 복잡도 점수 130 (최고)
  - handle_flow_status: 538줄 (!)
  - 메서드 수: 22개
  - 조건문: 89개
- **LegacyFlowAdapter**: 복잡도 점수 85
  - restore_flow: 81줄
  - 메서드 수: 31개
- **FlowManager**: 복잡도 점수 59

### 주요 문제점
1. **God Method**: handle_flow_status (538줄)
2. **데이터 일관성**: dict vs object 혼재
3. **의존성 문제**: 메서드 내부 직접 import
4. **중복 코드**: 에러 처리 22회 반복
5. **SOLID 위반**: SRP, OCP, DIP 모두 위반

## 🎯 o3 제안 리팩토링 전략

### STEP 0: 가드레일 구축
- 현재 동작 스냅샷 테스트 작성
- 로깅 & 모니터링 추가

### STEP 1: 데이터 모델 통합 (최우선)
```python
@dataclass
class Flow:
    id: str
    state: FlowState
    plans: Dict[str, Plan] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict) -> "Flow":
        # dict → Flow 변환

    def to_dict(self) -> Dict:
        # Flow → dict 변환
```

### STEP 2: 서비스 계층 분리
- **FlowService**: 비즈니스 로직만
- **CommandService**: 명령어 처리만
- **의존성 주입**: 인터페이스 기반

### STEP 3: Command 패턴 도입
```python
class FlowStatusCommand(Command):
    name = "flow status"

    def execute(self, args, services):
        return services.flow.get_status(args.flow_id)
```

### STEP 4: 중복 제거
- `@exception_handler` 데코레이터
- 타입 판별 로직 통합

### STEP 5: 모듈 재구성
```
packages/
  models/      # 데이터 모델
  services/    # 비즈니스 로직
  commands/    # 명령어 핸들러
  routers/     # 라우팅
  adapters/    # 레거시 호환
```

## 📅 실행 계획

### Week 1-2: 기반 작업
- [ ] 테스트 스위트 구축
- [ ] 데이터 모델 정의
- [ ] 레거시 어댑터 준비

### Week 3-4: 핵심 리팩토링
- [ ] 서비스 계층 분리
- [ ] handle_flow_status 분해
- [ ] Command 패턴 적용

### Week 5-6: 마무리
- [ ] 중복 코드 제거
- [ ] 문서화
- [ ] 성능 최적화

## 📈 기대 효과
- 복잡도 75% 감소
- 코드량 40% 감소 (59KB → 35KB)
- 신규 명령 추가 시 30줄 이하
- 타입 안정성 90% 향상
- 테스트 커버리지 증가

## ⚠️ 위험 관리
- API 호환성: LegacyAdapter 유지
- 점진적 마이그레이션
- 충분한 테스트 커버리지
- 단계별 PR 분리

## 🚀 즉시 실행 가능한 개선
1. handle_flow_status 메서드 분리
2. 에러 처리 데코레이터 도입
3. 데이터 모델 정의 시작

---
상세 내용: `docs/o3-architecture-analysis.md` 참조
