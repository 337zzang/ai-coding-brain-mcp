# 워크플로우 시스템 개선 방안 (o3 조언)

## 질문

[상황 설명]
프로젝트: ai-coding-brain-mcp
목적: 워크플로우 시스템을 개선하여 작업 기록과 결과물을 체계적으로 관리
문제: 현재 워크플로우 시스템이 너무 단순해서 중요한 정보들이 누락됨

[현재 코드 구조]
1. workflow.json 구조:
```json
{
  "v": "1.0",          // 버전
  "p": "프로젝트명",    // 프로젝트
  "s": "R",            // 상태 (R=running)
  "st": "시작시간",     // 시작 시간
  "t": [               // 태스크 목록
    {"i": 1, "n": "태스크명", "d": false}  // id, name, done만 저장
  ],
  "g": [],             // goals (사용 안함)
  "c": null,           // completion
  "f": "포커스"        // 현재 포커스
}
```

2. 이벤트/히스토리: 단순 리스트로 저장, 구조화되지 않음

[발견된 문제점]
1. Task 정보 부족
   - 현재: id, name, done만 저장
   - 필요: 시작/완료시간, 결과요약, 생성문서, 작업자 등

2. 이벤트 추적 정보 부족
   - 현재: type, timestamp만 저장
   - 필요: 상세 컨텍스트, 변경 전후 상태

3. 작업 결과물 추적 없음
   - 완료된 작업의 산출물(파일, 문서, 커밋 등) 기록 없음

4. 누락된 기능들
   - 작업 완료 시 결과 요약 저장
   - 생성된 문서/파일 링크 저장
   - 작업 소요 시간 계산
   - 태스크 간 의존성 관리
   - 결과물 검색 기능

[제약 조건]
- 기존 데이터와의 호환성 유지 필요
- JSON 파일 기반 저장 방식 유지
- 간단하고 직관적인 구조 선호
- 성능 저하 최소화

[구체적 요청]
1. 개선된 워크플로우 데이터 구조 설계
   - Task 스키마 확장
   - Event/History 통합 구조
   - 결과물 추적 방법

2. 기존 데이터 마이그레이션 전략

3. 주요 기능 구현 방법
   - 작업 완료 시 자동 요약
   - 결과물 자동 추적
   - 효율적인 검색

4. 단계별 구현 계획

5. 예상되는 문제점과 해결 방법


## o3의 답변
1. 개선된 워크플로우 데이터 구조 설계
────────────────────────────
(1) 상위 레벨
{
  "v"        : "2.0",                     // 스키마 버전
  "p"        : "ai-coding-brain-mcp",      // 프로젝트
  "status"   : "running|paused|done",
  "createdAt": "2024-05-01T10:00:12Z",
  "updatedAt": "2024-05-01T12:30:22Z",
  "focus"    : 3,                         // 현재 집중중인 task id
  "tasks"    : […],                       // 확장된 Task 목록
  "events"   : […],                       // 모든 변경/행위 로그
  "artifacts": […],                       // (옵션) 다수 태스크가 공유하는 결과물
  "meta"     : { "owner":"dev-team" }
}

(2) Task 스키마
{
  "id"          : 3,
  "name"        : "데이터 구조 설계",
  "status"      : "pending|running|blocked|done",
  "assignee"    : "alice",               // 작업자
  "tags"        : ["design","json"],
  "dependencies": [1,2],                 // 선행 task id
  "createdAt"   : "2024-05-01T10:05:23Z",
  "startedAt"   : "2024-05-01T10:10:00Z",
  "completedAt" : "2024-05-01T11:40:12Z",
  "durationSec" : 5400,                  // 계산값(선택)
  "summary"     : "필드 확장 및 이벤트 스키마 설계 완료.",
  "artifacts"   : ["A12","F23"],         // deliverable id 목록
  "meta"        : { "priority": "high" }
}

(3) Artifact(결과물) 스키마  
(태스크 안에 중첩 저장해도 되지만, 재사용·검색 편의를 위해 전역 배열 권장)
{
  "id"        : "F23",
  "taskId"    : 3,                       // 생성한 주 태스크
  "type"      : "file|doc|commit|url|img",
  "path"      : "docs/workflow_v2.md",   // git repo 내부 경로 or URL
  "hash"      : "7f9…e1",                // 내용 체크섬(선택)
  "size"      : 13345,                   // bytes
  "createdAt" : "2024-05-01T11:38:10Z",
  "summary"   : "v2 스키마 문서 초안"
}

(4) Event / History 통합 스키마
{
  "id"        : "2024-05-01T11:40:12Z#003",
  "timestamp" : "2024-05-01T11:40:12Z",
  "type"      : "task.status.changed",   // 네임스페이스식
  "actor"     : "system|alice",
  "taskId"    : 3,
  "before"    : { "status":"running" },
  "after"     : { "status":"done", "completedAt":"…" },
  "message"   : "Task completed.",
  "meta"      : { "durationSec":5400 }
}
→ 모든 기능 개선 요구사항(상태 변경, 파일 생성, 커밋, 오류 등)을 단일 events 배열로 통합·저장.

2. 기존 데이터 마이그레이션 전략
────────────────────────────
Step 0) 백업: workflow.json → workflow_legacy.json  
Step 1) 버전 확인 후 분기
• v==1.0 → 마이그레이션 수행  
• 그 외 → 그대로 유지 or 경고

Step 2) 변환 로직
for oldTask in data.t:
  newTask = {
    id          : oldTask.i,
    name        : oldTask.n,
    status      : oldTask.d ? "done" : "pending",
    createdAt   : data.st ?? now(),
    // 나머지는 null/undefined 로 채워 두고 추후 갱신
  }
  tasks.push(newTask)

Step 3) 루트 필드 변경
data.v        = "2.0"
data.tasks    = tasks
delete data.t
data.events   = []                // 최초 상태 스냅샷을 event 로 기록
data.updatedAt= now()

Step 4) 첫 이벤트 기록
events.push({
  id        : now()+"#mig",
  timestamp : now(),
  type      : "migration.v1to2",
  actor     : "system",
  message   : "Auto-migrated legacy v1.0 → v2.0"
})

Step 5) 파일 덮어쓰기 또는 workflow_v2.json 으로 저장

3. 주요 기능 구현 방법
────────────────────────────
A) 작업 완료 시 자동 요약
--------------------------------
trigger: task.status.changed && after.status=="done"
logic:
  • 시스템이 task.artifacts 에서 주요 파일 diff 또는 커밋 메시지 가져옴
  • GPT 등 LLM에 프롬프트:
    “아래 파일 목록·변경 요약에서 핵심을 2-3문장으로 정리…”
  • 결과를 task.summary, event.message 에 저장

B) 결과물 자동 추적
--------------------------------
1) Git 훅 (post-commit)
   - 커밋 hash, 변경 파일 목록 파싱
   - 새 Artifact 객체 생성(type:"commit")
2) FS Watcher (Node fs.watch / chokidar)
   - docs/, output/ 등 지정 폴더 감시
   - 새 파일 생성 시 Artifact 등록
3) IDE/CLI 래퍼
   - `workflow add-file <taskId> <path>` 단축 커맨드 제공

C) 효율적인 검색
--------------------------------
데이터량이 수-백 개 수준이면 메모리 인메모리 인덱스(Fuse.js)로 충분.  
규모가 커질 경우:
  • lightweight SQLite (json1 확장) 를 파일 기반으로 두고
    → JSON 덤프 시 to/from sqlite 변환 스크립트 제공  
  • 인덱싱 대상: tasks.name, tasks.summary, artifacts.path, events.message  
  • CLI 예: `workflow search "스키마" --type task --done`

4. 단계별 구현 계획
────────────────────────────
Phase 1  (1일)  스키마 확정 & 문서화
  - v2.0 JSON 예시 작성
  - 데이터 사전(schema.md) 업데이트

Phase 2  (1~2일)  마이그레이션 스크립트
  - Node/TS `migrate_v1_to_v2.ts`
  - 유닛 테스트(레거시 샘플 → 결과 검증)

Phase 3  (2~3일)  Core 라이브러리 리팩터링
  - load(), save(), addEvent(), updateTask(), addArtifact() API

Phase 4  (2일)  자동 요약·결과물 추적
  - post-commit 훅, fs watcher
  - GPT 호출 래퍼(`summarize(text):Promise<string>`)

Phase 5  (1일)  검색/조회 CLI
  - `workflow ls`, `workflow grep`, `workflow view <taskId>`

Phase 6  (1일)  문서·배포
  - README, 변경 로그, 마이그레이션 안내
  - 버전 태깅(v2.0.0)

총 소요: 약 8~10 인일

5. 예상되는 문제점과 해결 방법
────────────────────────────
1) 파일 커지면서 I/O 지연  
   → events, artifacts 를 월별 분할 파일(ex: events_2024-05.json) + 메타에 인덱스만 보관

2) 동시 쓰기 충돌  
   → atomic write(임시 파일 → rename), 파일 락(fcntl/flock), Git single-writer 정책

3) GPT 요약 품질·비용  
   → 길이 제한(4k 토큰) 전처리, 중요한 diff만 추출, 캐싱  
   → OSS LLM(Llama3, Phi)에 fallback

4) 누락된 결과물  
   → 커밋 누락 방지용 pre-commit 검사(“현재 focus task 없음” 경고)  
   → CLI `workflow attach <file>` 수동 보강 명령

5) 레거시 호환성 요구  
   → v1 로더 유지: v1 로 읽되 메모리에선 v2 객체로 변환  
   → 저장 시 항상 v2 로만 기록, 필요 시 `--export-v1` 옵션 제공

이상으로 요구된 5가지 항목에 대해 구조, 방법론, 일정, 리스크까지 정리했습니다.

## 메타 정보
- 질문 시각: 2025-07-18 22:55:11.444420
- 추론 시간: 69.88초
- 사용 토큰: 3584
