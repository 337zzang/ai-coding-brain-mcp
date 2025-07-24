# Flow 시스템 아키텍처 분석 보고서

생성일: 2025-07-23T00:43:18.130835
분석 도구: o3 (high effort)

## 분석 결과

1. 핵심 문제 진단

① 레이어 과다 및 책임 중복  
   • FlowManagerUnified → FlowService → JsonFlowRepository 세 단계를 모두 거쳐야 단순 CRUD-작업을 수행한다.  
   • FlowManagerUnified와 FlowService 모두 ‑ 캐싱, 동기화, 현재 Flow 파일 관리 등의 로직을 포함해 책임이 뒤섞여 있다.  
   • FlowService가 파일 I/O(현재 flow 파일), 데이터 캐싱, 레거시 마이그레이션 책임까지 맡으면서 “서비스”라기보다 “인프라”에 가깝다.

② 데이터 변환 남용  
   • Manager setter에서 dict → Flow 변환, Repository에서 dict ↔ Flow 변환, Service에서도 Flow ↔ dict 변환을 수행한다.  
   • 결국 동일한 객체를 여러 번 직렬화/역직렬화하며 성능 손실과 버그 가능성이 증가한다.

③ 레거시 호환 코드가 전방위에 산재  
   • storage_path 매개변수, global current_flow.txt, 수많은 DeprecationWarn 등이 모든 계층에 퍼져 있다.  
   • 신규 코드 가독성이 떨어지고 테스트 난이도가 올라간다.

④ 경계 모호  
   • “Service”가 인프라(저장소) 로직과 도메인 로직을 동시에 수행.  
   • “Manager”가 실제 비즈니스 흐름 제어인지 캐싱 계층인지 불명확.

2. 개선 목표

A. 계층 최소화 + 역할 명확화  
B. 직렬화/역직렬화는 저장소 계층 단일 책임화  
C. 레거시는 ‘어댑터’로 국한, 신규 코드에서 제거  
D. 테스트·DI(Dependency Injection) 친화 구조

3. 권장 구조 (Clean / Hexagonal 아키텍처 변형 예)

[Presentation]           CLI / API / UI  
        │  
[Application]   FlowApplicationService (유스케이스)  
        │      ├── list_flows()  
        │      ├── create_flow(cmd)  
        │      └── set_current_flow(id)  
        │  
[Domain]        Flow 엔티티(dataclass),  도메인 규칙  
        │  
[Infrastructure] ├─ JsonFlowRepository (FlowRepository 프로토콜 구현)  
                 └─ LegacyFlowAdapter  (storage_path 등 호환 로직 전용)

주요 포인트
• FlowApplicationService는 FlowRepository 인터페이스(ABC/Protocol)만 의존.  
• JsonFlowRepository만 dict ↔ Flow 직렬화 책임.  
• CLI‧UI 등에서 바로 Service 호출 → Manager 계층 제거(필요하면 Facade로 축소).  
• LegacyFlowAdapter는 신규 Repository 규격으로 감싼 채 빈번히 호출되는 코어 코드와 분리.

4. 단계별 리팩터링 로드맵

Step 1 ― Domain 강화  
  a. @dataclass class Flow: …  
  b. Flow.to_dict()/from_dict() 포함 가능하지만 “protected” 수준으로 두고 외부에서 직접 호출 금지.

Step 2 ― Repository 인터페이스 정의  
```python
class FlowRepository(Protocol):
    def load_all(self) -> dict[str, Flow]: ...
    def save(self, flows: dict[str, Flow]) -> None: ...
    def load_current_id(self) -> str | None: ...
    def save_current_id(self, flow_id: str | None) -> None: ...
```

Step 3 ― JsonFlowRepository 구현  
  • Domain 객체 ↔ JSON 파일 직렬화/역직렬화만 담당.  
  • ProjectContext 외 옵션만 받고, storage_path 레거시는 별도 LegacyJsonRepositoryAdapter에서 변환.

Step 4 ― Application Service 작성 및 기존 코드 이식  
```python
class FlowApplicationService:
    def __init__(self, repo: FlowRepository):
        self._repo = repo

    def list_flows(self) -> Mapping[str, Flow]:
        return self._repo.load_all()

    def set_current_flow(self, flow_id: str | None) -> None:
        flows = self._repo.load_all()
        if flow_id and flow_id not in flows:
            raise ValueError(f"{flow_id} not found")
        self._repo.save_current_id(flow_id)
```

Step 5 ― FlowManagerUnified 제거/축소  
  • CLI 등에서 바로 Service 사용.  
  • 혹은 “FlowFacade”로 남겨도 기능은 입·출력 파사드 정도만 유지.

Step 6 ― 레거시 호환 축소  
  • storage_path 사용 시 LegacyAdapter(return JsonFlowRepository(Path))로 감싸고 Deprecation 메시지를 이 어댑터 내부로 한정.  
  • global current_flow.txt → 1회 migration 스크립트로 분리.

Step 7 ― 테스트 및 DI  
  • Application 레이어 단위 테스트 시 FakeFlowRepository 주입해 I/O 제거.  
  • 실제 CLI/웹은 JsonFlowRepository 주입.

5. 추가 개선 아이디어

• 캐싱: Repository 내부에서 LRU·timestamp 캐시 포함(옵션), 호출자 관여 최소화.  
• 타입 안정성: mypy / pydantic 모델 도입해 외부입력 검증.  
• 이벤트/Signal: 현재 Flow 변경 시 워크스페이스 핫리로드 등 필요하면 Domain Event 발행기로 분리.  
• 성능/동기화: 다중 프로세스 환경이면 파일 락, 또는 SQLite 같은 로컬 DB 백엔드 검토.

6. 기대 효과

✓ 호출 스택이 Manager→Service→Repo(3단) → Service→Repo(2단)로 간결.  
✓ 직렬화/역직렬화 1회로 축소, CPU-I/O 절감.  
✓ 레거시 코드와 신규 코드 완전 분리: 신규 기능 개발 속도 ↑, 유지보수 난이도 ↓.  
✓ 테스트 커버리지 확대: 도메인·애플리케이션 레이어는 pure-python으로 단위 테스트.  
✓ 향후 다른 저장소(MySQL, REST API 등) 도입 시 Repository 구현만 추가하면 되므로 확장 용이.

요약  
“Manager + Service + Repository”로 중첩된 구조에서 “Application Service + Repository” 2단으로 단순화하고, 직렬화 책임을 Repository에 집중시키며 레거시 호환을 Adapter에 고립시켜라. 이렇게 하면 코드 가독성, 성능, 테스트 용이성이 모두 개선된다.
