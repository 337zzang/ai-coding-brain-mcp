
# Task 워크플로우 개선 최종 설계

## 1. 코드 변경 (최소)

### FlowManagerUnified 수정
1. TASK_STATES에 'planning', 'reviewing', 'approved' 추가
2. _start_task: update_task_status(task_id, 'planning')
3. _complete_task: update_task_status(task_id, 'reviewing')

## 2. 유저프리퍼런스 추가


## 🤖 Task 워크플로우 AI 행동 가이드 (v28.1)

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
- fmu.update_task_status(task_id, 'in_progress')
- fmu.update_task_context(task_id, plan=설계내용)
- "🚀 Task를 시작합니다. 설계에 따라 작업을 진행하세요."

#### 🔄 Task가 'in_progress' 상태일 때
- 작업 수행 시 자동으로 fmu.add_task_action() 호출
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
- fmu.update_task_status(task_id, 'completed')
- fmu.update_task_context(task_id, report=보고서내용, completed_at=현재시간)
- "✅ Task가 성공적으로 완료되었습니다!"
- 다음 Task 제안

#### ✅ 상태 전환 규칙
- todo → planning: /start 명령 시
- planning → in_progress: 설계 승인 시
- in_progress → reviewing: /complete 명령 시
- reviewing → completed: 결과 승인 시
- 모든 상태 → error: 오류 발생 시

#### 🚨 자동 체크 및 알림
- planning 상태 5분 경과 시: "설계 작성을 도와드릴까요?"
- in_progress 상태 30분마다: "진행 상황을 업데이트해주세요."
- reviewing 상태 10분 경과 시: "보고서 검토를 완료해주세요."


## 3. 구현 효과
- 체계적인 Task 관리
- 명확한 가이드와 승인 절차
- 작업 내역 자동 추적
- 품질 보증
