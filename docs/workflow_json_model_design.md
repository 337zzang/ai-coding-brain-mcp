
# 워크플로우 JSON 모델 설계 - O3 조언

## 질문 시각
2025-07-18 22:20:13

## 현재 상황
- 현재 크기: 30.4 KB
- 구조: ['plans', 'active_plan_id', 'events', 'version', 'last_saved', 'metadata', 'project_name', 'events_file', 'current_plan_id']

## O3의 설계안
─────────────────────────────────────────
1. 핵심 JSON 분리 전략
─────────────────────────────────────────
•  workflow.json         : “현재-세션” 1건만 저장(≈ 0.2–0.5 KB)  
•  workflow_history.json : 종료·중단된 세션 누적(순차 append)  
  ↳ 필요 시 날짜·프로젝트별 파일 쪼개기(예: history_2023-10.json)  

이렇게 나누면  
① RAM-같이 자주 읽는 파일은 항상 <1 KB  
② 과거 기록은 별도 관리·압축·아카이브 가능  

─────────────────────────────────────────
2. 워크플로우 스키마(최소화 버전)
─────────────────────────────────────────
A. workflow.json  (ACTIVE SESSION ONLY)

필드 | 키 | 타입 | 의미(길이 최소화)
-----|-----|------|-----------------
schema version | v | int | 구조 변경 감지
project id     | p | str | 예: “proj-A”
session id     | s | str | 한 작업 사이클 UUID/날짜
status         | st| chr | N/R/P/D/X  (New/Running/Paused/Done/Cancelled)
stage          | g | str | 현재 단계 코드(“plan”,”build”…)
checkpoint     | c | str | Git short SHA(최신 커밋)
updated        | u | int | epoch(sec) 마지막 저장 시각
approvals†     | a | arr | 대기중 승인[ {g,by,t} … ]
log†           | l | arr | 직전 N개 단계 변천[ [g,st,t] … ]

† a, l 는 옵션. 1KB 유지 위해 N = 3 정도로 cut-off

예시 (274 B)  
{
 "v":1,"p":"proj-A","s":"231007-001",
 "st":"R","g":"build","c":"a1b2c3d",
 "u":1696671234,
 "a":[{"g":"build","by":"alice"}]
}

B. workflow_history.json  (APPEND-ONLY)

필드 | 키 | 타입 | 의미
-----|-----|------|-----------------
project id | p | str
session id | s | str
finished at | f | int  (epoch)
result      | r | chr  (D/X)
stages      | sg| arr  [ [g,t0,t1,by?] … ]  ⟵ 압축형
head commit | c | str

예시 항목 (1줄)  
{"p":"proj-A","s":"231001-003","f":1696130023,"r":"D",
 "sg":[["plan",1696129820,1696129855,"alice"],
       ["build",1696129856,1696129950]],
 "c":"9f8e7d"}

(한 줄 JSON 을 append → git diff 가 적고 grep ‑J 로 검색 쉬움)

─────────────────────────────────────────
3. 크기 최적화를 위한 규칙
─────────────────────────────────────────
1. 키 1~2 byte : v,p,s,st,g,c,u …  
2. 상태·결과는 한 글자 코드  
3. 타임스탬프 => epoch(int) ⇒ 10byte  
4. 옵션 배열은 ring-buffer 로 N개 유지  
5. history 파일은 gzip 주기적 압축(×⁵~10)  

─────────────────────────────────────────
4. 상태/승인/체크포인트 플로우
─────────────────────────────────────────
┌── start_session() ──────────────────────┐
│ new workflow.json 생성 (st=N)           │
└──────────────────────────────────────────┘
        │
        ▼
┌── stage_progress(stage) ────────────────┐
│ 1. git add/commit → SHA = c            │
│ 2. st = R , g = stage , u=now          │
│ 3. l push([stage,"R",u]) (trim to N)   │
│ 4. 저장                                │
└──────────────────────────────────────────┘
        │
        ▼
┌── request_approval(user) ───────────────┐
│ a append({g,by:user,t})                 │
└──────────────────────────────────────────┘
        │
        ▼
┌── approve(user) ────────────────────────┐
│ a 항목 제거 → stage 계속 진행          │
└──────────────────────────────────────────┘
        │
        ▼
┌── finish_session(result=D/X) ───────────┐
│ 1. st = result                         │
│ 2. history append(…)                   │
│ 3. workflow.json 삭제 or clear         │
└──────────────────────────────────────────┘

─────────────────────────────────────────
5. ‘현재→히스토리’ 이동 트리거
─────────────────────────────────────────
✓ st 이 D(one) 또는 X(cancel) 되면  
✓ 또는 ① 24h 이상 미변경 & st≠R, ② 프로젝트 전환 시  

파일 관리  
• 1만 라인 초과 → 새 history_YYYY-MM.json 생성  
• 오래된 history 파일 gzip → size ▼

─────────────────────────────────────────
6. 프로젝트 간 이동(flow_project)
─────────────────────────────────────────
1. 현재 workflow.json flush → git commit “checkpoint-auto”  
2. finish_session(result=P) ; history 기록(Paused)  
3. 디렉터리 전환  
4. 새 프로젝트의 workflow.json (없으면 템플릿 생성)  
5. 충돌 방지 : session id = <UTC-Date>-<rand4> & file-lock(.lock)

─────────────────────────────────────────
7. 확장/변경 시 가이드
─────────────────────────────────────────
• 새 필드는 1-byte 키 추가, v ++  
• 과거 레코드와 역호환 : 없으면 default 값 사용  
• 특수 이벤트 필요 시 l 배열에 코드만 남기고 세부는 git commit msg 이용  

─────────────────────────────────────────
결론
─────────────────────────────────────────
– 액티브 정보만 가진 workflow.json 은 키 축약·ring-buffer 로 평균 300 B → 1 KB 목표 충족  
– 모든 이력, 승인, 단계별 상세는 append-only 파일로 분리 → 검색·압축·백업 용이  
– Git commit 해시를 “c” 로 상시 동기화하여 코드 상태 = 워크플로우 체크포인트가 되므로 traceability 확보  
– 프로젝트 전환·세션 완료 시 자동으로 history 로 이동하여 메인 파일은 항상 가볍게 유지됨.

## 메타 정보
- 추론 시간: 56.26초
- 사용 토큰: 3304
