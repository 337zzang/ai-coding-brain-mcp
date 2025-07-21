# o3_task_0014 분석 결과

아래는 Flow Project v2를 실제로 개발‧운영할 때 마주칠 가능성이 높은 핵심 기술적 도전 과제들과, 필드에서 검증된 해결 전략을 항목별로 정리한 것입니다.  
(굵게 표기는 과제, ➜ 표기는 해결책)

────────────────────────────────────────
1) Plan/Task 계층 도입에 따른 데이터 마이그레이션
────────────────────────────────────────
· 기존 v1 워크플로(단일 tasks 배열) 데이터를 v2 스키마(plans → tasks)로 옮겨야 함  
· 과제  
  ‑ 부모-자식 관계 재구성  
  ‑ 기존 Task ID 충돌 처리  
  ‑ 실사용 중인 프로젝트를 중단 없이 전환  

➜ 해결 방안  
 1. “1회 실행” 마이그레이션 스크립트
    - v1 workflow.json을 읽어들여 plan_legacy 하나를 만들어 모든 task를 children으로 이관  
    - UUID/ULID로 신규 ID 발급, old_id 필드에 기존 ID 유지(백업 및 레퍼런스)  
 2. 마이그레이션 로그와 스냅샷 동시 생성  
    - 변환 전후 파일을 snapshots/`{timestamp}_migration.json`에 같이 저장  
 3. feature_flag(v1, v2) 공존 전략  
    - WorkflowManager가 version 필드에 따라 두 개의 Adapter 구현 중 하나를 선택  
    - 운영 중 일부 사용자가 v1을 쓰더라도 데이터 손상 위험 최소화  

────────────────────────────────────────
2) documents/ 디렉터리 관리
────────────────────────────────────────
(가) 문서-Plan 연결 관리
· 과제  
  ‑ 문서 파일명이 바뀌거나 이동했을 때 링크가 깨짐  
  ‑ Plan 삭제 시 문서 고아(orphan) 파일 방치  

➜ 해결 방안  
 1. documents_manifest.json  
    - 각 plan_id를 key, 하위에 summary.md·references[] 등 file path를 value로 보관  
    - WorkflowManager → Plan save() 시 파일 경로가 바뀌면 manifest 동기화  
 2. ‘참조 카운트’ 트래킹  
    - 동일한 논문이나 이미지가 여러 Plan에서 쓰이면 ref_count++  
    - ref_count==0 & deleted_at<retention 기한 → 물리 삭제  

(나) 대용량 / 이진 바이너리
· 과제 ‑ PDF·PPT·Dataset 등 수백 MB 파일 저장 시 Git이나 zip 스냅샷이 기형적으로 커짐  

➜ 해결 방안  
 1. documents/ 아래 large/ 서브디렉터리 + Git LFS or S3 presigned-URL 관리  
 2. 워크플로우 JSON에는 “storage_type: s3, lfs, local” 메타를 둬 접근 계층 추상화  

(다) 검색/요약
· 과제 ‑ Plan 간 문서 검색 UX 부재  

➜ 해결 방안  
 1. mdbook-like 검색 인덱스(build 시 전처리)  
 2. LLM embedding + sqlite/pgvector로 간단한 semantic search 제공  

────────────────────────────────────────
3) snapshots/ 버전 관리
────────────────────────────────────────
· 과제  
  ‑ 스냅샷 무제한 증식 → 디스크 폭발  
  ‑ “지정 시점” 복원 시 종속 문서·컨텍스트 동시 재현 필요  
  ‑ Git과 별개로 JSON/문서를 통째로 압축하면 diff tracing 어려움  

➜ 해결 방안  
 1. 증분 스냅샷(Incremental) 모델  
    - baseline.json 만들고 이후 변경분만 diff 저장 (jsonpatch)  
 2. Retention 정책  
    - N일 or M개 초과 시 LRU 삭제 + 중요 마일스톤(label=pinned) 예외  
 3. Git 백엔드 연동  
    - snapshots/ 자체를 git repo 하위 서브트리로 둔 뒤 태그(tag) = timestamp  
    - 복원은 git checkout + context.json 동기화  
 4. CLI 지원  
    /flow snapshot list|create|restore {id}  

────────────────────────────────────────
4) /flow 명령어 파싱 복잡도
────────────────────────────────────────
· 과제  
  ‑ Plan, Task, Snapshot, 문서, 메타데이터까지 모두 명령으로 제어하려니 서브커맨드 폭발  
  ‑ 대화형 프롬프트/스크립트/CI 파이프라인 등 다양한 호출 형태 지원  

➜ 해결 방안  
 1. “단일 진입점 + 확장 가능한 DSL”  
    - /flow <verb> <noun> [--flags] 형태(예: /flow add task …, /flow set plan --status done)  
    - 명사(noun) 테이블: plan, task, doc, snapshot, config  
 2. 표준 CLI 파서 라이브러리 채택  
    - Python Click/Typer → 자동 help, 서브커맨드 트리  
 3. Parser적 스코프 룰(Plan 컨텍스트 유지)  
    - /flow use plan plan_002 입력 시 세션 콤비 컨텍스트 변경  
    - 이후 /flow add task … 는 암묵적으로 current_plan_id에 귀속  
 4. 파싱/실행 분리 Command Bus 패턴  
    - Parser가 Command 객체 → CommandBus → Handler 실행  
    - 테스트 용이, 신규 명령 추가 시 기존 로직 영향 최소화  
 5. 광범위 자동 테스트  
    - 명령어->상태 변화 fixture 기반 스냅샷 테스트 (pytest + approval tests)  
    - “자연어→명령” LLM 트랜스파일러 계획 시에도 필요  

────────────────────────────────────────
5) 세션 컨텍스트 지속성(context.json)
────────────────────────────────────────
· 과제  
  ‑ LLM 호출 비용을 줄이며 “마지막 대화 내용, 의사결정”을 충분히 요약해야 함  
  ‑ 동시 세션 / 다중 사용자 환경에서 충돌  

➜ 해결 방안  
 1. last_context 필드는 ‘chunked conversation summary’ & ‘embedding’ 동시 보관  
 2. read-modify-write시 파일 락(fcntl/flock) 또는 DB를 통한 row-level lock  
 3. Plan 변경과 컨텍스트 변경을 단일 트랜잭션 처리(Atomic write)  

────────────────────────────────────────
6) 기타 운영·품질 이슈
────────────────────────────────────────
① 대규모 JSON 파싱 속도  
   ➜ orjson/rapidjson + Pydantic v2 모델 적용  
② 스키마 진화(2.1, 2.2 …)  
   ➜ $schema version 필드 + jsonschema validation, 자동 업그레이드 스크립트  
③ 플러그인/외부툴 연동  
   ➜ WorkflowManager에 Hook(PointCut) 두어 이벤트-기반 확장 (pre_save, post_save, on_command)  

────────────────────────────────────────
요약
1. 데이터 계층화에 맞춘 마이그레이션 스크립트와 version adapter가 필수.  
2. documents/는 manifest + ref_count + 외부스토리지 레이어로 관리 불확실성 제거.  
3. snapshots/는 증분 저장, Git 통합, 보존정책으로 용량/추적성 문제 해결.  
4. /flow 명령어는 DSL+Command Bus+테스트 자동화로 복잡도 억제.  
5. context.json은 요약+임베딩+락킹으로 “완전 복원” 목표 달성.  
6. 전체적으로 orjson, Click/Typer, Pydantic, Git LFS 등 검증된 도구를 결합해 구현 난이도를 줄인다.