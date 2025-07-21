# AI Coding Brain MCP - 유저프리퍼런스 v29.0


## 📝 v29.0 주요 변경사항

1. **파일 저장 규칙 추가**
   - 문서는 docs/, 테스트는 test/, 백업은 backups/
   - .ai-brain은 AI 작업 상태만
   - 체계적인 디렉토리 구조 정의

2. **Task 워크플로우 AI 행동 가이드 추가**
   - planning, reviewing 상태 추가
   - 각 상태별 AI 자동 행동 정의
   - 설계 템플릿과 보고서 양식 제공

3. **통합 개선사항**
   - 파일 저장과 Task 작업의 연계
   - 더 명확한 승인 포인트
   - 자동 체크 및 알림 기능


## 🎯 핵심 작업 원칙

### 1. **상세 작업 계획 및 설계 (최우선)**
[기존 v28.0 내용 유지...]

### 2. **Task별 상세 실행 및 결과 보고**
[기존 v28.0 내용 유지...]

### 3. **명확한 승인 포인트**
[기존 v28.0 내용 유지...]

### 4. **오류 처리 및 보고 체계**
[기존 v28.0 내용 유지...]

## 🌊 Flow Project v2 & Context System 활용
[기존 v28.0 내용 유지...]

## 🤖 o3 병렬 처리 전략 (v28.0 개선)
[기존 v28.0 내용 유지...]

## 🛠️ AI Helpers v2.0 - 실제 작동 API
[기존 v28.0 내용 유지...]

## 🧠 Extended Thinking을 활용한 REPL 작업 전략
[기존 v28.0 내용 유지...]


## 📁 파일 저장 규칙

### 디렉토리 구조 및 파일 저장 위치

```
ai-coding-brain-mcp/
├── docs/                    # 📄 모든 문서 (설계, 분석, 가이드)
│   ├── task-workflow/       # Task 워크플로우 관련 문서
│   ├── flow-improvement/    # Flow 개선 관련 문서
│   └── o3-analysis/         # o3 분석 결과
│
├── test/                    # 🧪 테스트 파일 및 결과
│   ├── unit/               # 단위 테스트
│   ├── integration/        # 통합 테스트
│   └── results/            # 테스트 결과 JSON
│
├── backups/                 # 💾 백업 파일
│   └── YYYYMMDD/           # 날짜별 백업
│
├── python/                  # 🐍 소스 코드
│   └── ai_helpers_new/     # 메인 모듈
│
└── .ai-brain/              # 🧠 AI 작업 상태 (임시)
    ├── flows.json          # Flow 상태
    └── o3_tasks/           # o3 작업 추적
```

### 파일 저장 규칙

1. **문서 저장**
   - 설계 문서: `docs/[기능명]/[문서명]_design.md`
   - 분석 문서: `docs/[기능명]/[문서명]_analysis.md`
   - 보고서: `docs/[기능명]/[문서명]_report.md`
   - o3 분석: `docs/o3-analysis/[주제]_analysis.md`

2. **테스트 파일**
   - 테스트 코드: `test/test_[모듈명].py`
   - 테스트 결과: `test/results/[테스트명]_result.json`

3. **백업 파일**
   - 코드 백업: `backups/[파일명].backup_YYYYMMDD_HHMMSS`
   - 일일 백업: `backups/YYYYMMDD/[파일명]`

4. **AI 작업 상태** (.ai-brain만 사용)
   - Flow 상태: `.ai-brain/flows.json`
   - o3 작업: `.ai-brain/o3_task_[ID].json`
   - 체크포인트: `.ai-brain/checkpoints/[작업명]_checkpoint.json`

### ❌ 하지 말아야 할 것
- 모든 파일을 .ai-brain에 저장
- 백업 파일을 소스 디렉토리에 저장
- 문서를 코드 디렉토리에 저장

### ✅ 파일 생성 시 필수 확인
- 문서인가? → `docs/`
- 테스트인가? → `test/`
- 백업인가? → `backups/`
- 임시 상태인가? → `.ai-brain/`



## 🤖 Task 워크플로우 AI 행동 가이드

### Task 상태별 AI 자동 행동

AI는 Task 상태 변경을 감지하고 자동으로 다음과 같이 행동합니다:

#### 📐 Task가 'planning' 상태로 변경될 때
```markdown
📋 Task '[Task명]'의 설계 단계입니다.

아래 템플릿을 활용하여 상세 설계를 작성해주세요:

## 🎯 목표 (Goal)
[이 Task로 달성하고자 하는 구체적인 목표를 작성해주세요]

## 🔧 접근 방법 (Approach)
[어떤 방법과 도구를 사용할 예정인지 설명해주세요]

## 📋 실행 단계 (Steps)
1. [첫 번째 단계: 구체적인 작업 내용]
2. [두 번째 단계: 구체적인 작업 내용]
3. [세 번째 단계: 구체적인 작업 내용]

## 📊 예상 결과물 (Expected Results)
- [생성될 파일/문서]
- [달성될 기능/개선사항]

## ⚠️ 위험 요소 및 대응 (Risks & Mitigation)
- 위험: [예상되는 문제점]
  대응: [해결 방안]

## ⏱️ 예상 소요 시간
- 전체: [예: 2시간]
- 단계별: Step 1 (30분), Step 2 (1시간), Step 3 (30분)

---
설계 작성 완료 후 승인해주세요.
**✅ 이 설계대로 진행하시겠습니까?**
```

승인 시 → AI가 자동으로:
- `fmu.update_task_status(task_id, 'in_progress')`
- `fmu.update_task_context(task_id, plan=설계내용)`
- "🚀 Task를 시작합니다. 설계에 따라 작업을 진행하세요."

#### 🔄 Task가 'in_progress' 상태일 때
- 작업 수행 시 자동으로 `fmu.add_task_action()` 호출
- 중요 결정이나 파일 수정 시 승인 요청
- 오류 발생 시 자동 기록 및 보고
- 진행률 자동 업데이트

#### 🔍 Task가 'reviewing' 상태로 변경될 때
```markdown
📊 Task '[Task명]'의 완료 보고서입니다.

## 📋 작업 내역
[context.actions 기반 자동 생성]
1. ✅ [작업1] → [결과1]
2. ✅ [작업2] → [결과2]
...

## 📈 달성 결과
[context.results 기반 자동 생성]
- [지표1]: [값1]
- [지표2]: [값2]

## 📁 파일 작업
[context.files 기반 자동 생성]
- 생성: [파일 목록]
- 수정: [파일 목록]
- 분석: [파일 목록]

## 🎯 목표 달성도
- 계획된 목표: [context.plan에서 추출]
- 달성 여부: [평가]

## 💡 개선 사항 및 다음 단계
- [발견된 개선점]
- [권장 다음 작업]

---
**✅ 이 결과를 승인하시겠습니까?**
```

승인 시 → AI가 자동으로:
- `fmu.update_task_status(task_id, 'completed')`
- `fmu.update_task_context(task_id, report=보고서내용, completed_at=현재시간)`
- "✅ Task가 성공적으로 완료되었습니다!"
- 다음 Task 제안

#### ✅ 상태 전환 규칙
- todo → planning: `/start` 명령 시
- planning → in_progress: 설계 승인 시
- in_progress → reviewing: `/complete` 명령 시
- reviewing → completed: 결과 승인 시
- 모든 상태 → error: 오류 발생 시

#### 🚨 자동 체크 및 알림
- planning 상태 5분 경과 시: "설계 작성을 도와드릴까요?"
- in_progress 상태 30분마다: "진행 상황을 업데이트해주세요."
- reviewing 상태 10분 경과 시: "보고서 검토를 완료해주세요."

### Task 작업 시 파일 저장 규칙
- 설계 문서: `docs/[기능명]/task_[ID]_design.md`
- 작업 보고서: `docs/[기능명]/task_[ID]_report.md`
- 테스트 결과: `test/results/task_[ID]_test_result.json`
- 백업: `backups/task_[ID]_backup_YYYYMMDD.zip`


## 📋 작업 수행 체크리스트

### 작업 시작 전
□ 환경 설정: `os.environ['CONTEXT_SYSTEM'] = 'on'`
□ 프로젝트 확인: `h.get_current_project()`
□ Git 상태: `h.git_status()`
□ 상태 디렉토리 생성: `os.makedirs('.ai-brain', exist_ok=True)`
□ Flow 생성: `wf("/flow create 작업명")`
□ 전체 설계 작성 및 승인

### 각 Task 수행 시
□ Task 시작: `wf("/start task_id")` → planning 상태
□ 설계 템플릿 작성 및 승인
□ 상태가 in_progress로 변경 확인
□ 체크포인트 생성: `create_checkpoint('task_start')`
□ 백업 생성: `h.git_commit("작업 전 백업")`
□ 작은 단위로 코드 실행
□ 각 단계마다 검증
□ 오류 발생 시 상세 보고 및 상태 저장
□ Task 완료: `wf("/complete task_id")` → reviewing 상태
□ 보고서 검토 및 승인
□ 상태가 completed로 변경 확인

### 작업 완료 후
□ 전체 테스트 실행
□ 상태 파일 정리
□ 최종 보고서 작성 → `docs/[기능명]/`에 저장
□ Git 커밋: `h.git_commit("작업 완료")`
□ Flow 요약: `wf("/flow summary ai")`

## 📝 보고서 템플릿
[기존 v28.0 내용 유지...]

## ⚠️ 주의사항 (v29.0 업데이트)

### 파일 저장 위치
- **문서**: 항상 `docs/` 디렉토리에 저장
- **테스트**: 항상 `test/` 디렉토리에 저장
- **백업**: 항상 `backups/` 디렉토리에 저장
- **.ai-brain**: AI 작업 상태만 (flows.json, o3_tasks 등)

### Task 상태 관리
- 새로운 상태: planning, reviewing, approved
- 각 상태 전환 시 AI가 자동으로 가이드 제공
- 승인 없이는 다음 단계로 진행되지 않음

### 모듈 경로 확인
[기존 v28.0 내용 유지...]

### REPL 재시작
[기존 v28.0 내용 유지...]

### API 반환값
[기존 v28.0 내용 유지...]

### Extended Thinking 필수 적용
[기존 v28.0 내용 유지...]

### REPL 환경 특성 활용
[기존 v28.0 내용 유지...]

## 🎯 목표

1. **체계적인 설계와 실행**
2. **상세한 오류 추적 및 해결**
3. **투명한 진행 상황 공유**
4. **재사용 가능한 작업 패턴**
5. **완전한 테스트와 검증**
6. **사용자 통제권 보장**
7. **안전한 점진적 작업** (Extended Thinking)
8. **상태 보존과 복구 가능성**
9. **체계적인 파일 관리** (v29.0 추가)
10. **자동화된 Task 워크플로우** (v29.0 추가)
