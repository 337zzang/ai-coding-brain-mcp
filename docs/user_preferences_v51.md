# 🧠 AI Coding Brain MCP - User Preferences v51.0

## 🎯 핵심 철학
**"메시지를 보면 즉시 행동하라"**

## 🤖 워크플로우 메시지 자동 인식 및 행동

### 1. 메시지 패턴 인식
코드 실행 결과에서 다음 패턴을 감지하면 즉시 행동:

```
[WORKFLOW-MESSAGE] 로 시작하는 블록
또는
st:로 시작하는 라인
```

### 2. 메시지 타입별 자동 액션

#### 📌 Task Completed (state_changed → completed)
```python
# 자동 실행 액션:
1. 프로젝트 지식에서 관련 코드 검색
2. 변경사항 분석
3. 보고서 생성:
   - 파일명: {project}_{plan}_{task}_report_{YYYYMMDD}.md
   - 내용: 작업 요약, 변경 파일, 테스트 결과, 다음 단계
4. docs/workflow_reports/에 저장
```

#### 📌 Task Started (state_changed → in_progress)
```python
# 자동 실행 액션:
1. 태스크 정보 확인
2. 설계서 작성:
   - 설계 목적 (왜 필요한가?)
   - 내가 이해한 내용
   - 구현 방향성
   - 영향받는 모듈
   - 위험 요소
3. 사용자에게 승인 요청
```

#### 📌 Error Occurred
```python
# 자동 실행 액션:
1. execute_code로 로그 분석:
   log_analyzer = LogAnalyzer(project_name)
   errors = log_analyzer.find_recent_errors()

2. 에러 원인 파악
3. 수정 코드 제안 (edit_block 사용)
4. 테스트 코드 작성
```

#### 📌 Phase Completed (plan → completed)
```python
# 자동 실행 액션:
1. 전체 태스크 결과 수집
2. 페이즈 보고서 생성:
   - 파일명: {project}_{plan}_phase_complete_{YYYYMMDD}.md
   - 내용: 목표 달성도, 주요 성과, 문제점, 개선사항
```

### 3. 프로젝트 지식 활용 규칙

**모든 작업 전 필수 검색:**
```python
# 1. 현재 상태 확인
project_knowledge_search("memory context.json workflow.json")

# 2. 관련 코드 검색
project_knowledge_search("code {module_name}")

# 3. 이전 문서 참조
project_knowledge_search("docs {task_name}")

# 4. 에러 시 로그 검색
project_knowledge_search("logs error {timestamp}")
```

### 4. 문서 작성 규칙

**파일명 (AI가 찾기 쉽게):**
- 항상 프로젝트명으로 시작
- 언더스코어로 구분
- 날짜는 YYYYMMDD 형식
- 예: ai-coding-brain-mcp_auth_jwt_token_report_20250713.md

**내용 구조:**
```markdown
# 제목
## 요약 (한 문단)
## 상세 내용
### 작업 내용
### 변경사항
### 테스트 결과
## 다음 단계
```

### 5. 컨텍스트 유지

**작업 후 항상:**
```python
# context.json 업데이트
helpers.update_context({
    "last_task": task_id,
    "completed_at": timestamp,
    "results": summary,
    "next_steps": recommendations
})
```

### 6. 실행 예시

**워크플로우 명령 실행 시:**
```
User: helpers.workflow("/next 작업 완료")

AI가 보는 출력:
[WORKFLOW-MESSAGE] 2025-07-13 20:45:00
Type: state_changed
Entity: task_001
AI Action: Generate task completion report
Data: {
  "from": "in_progress",
  "to": "completed"
}

AI의 자동 반응:
1. "태스크가 완료되었군요. 보고서를 생성하겠습니다."
2. project_knowledge_search 실행
3. 보고서 작성
4. 파일 저장
5. "보고서가 생성되었습니다: {파일명}"
```

## ⚡ 핵심 규칙
1. **메시지 감지 = 즉시 행동**
2. **프로젝트 지식 우선 검색**
3. **체계적인 문서화**
4. **컨텍스트 지속 유지**
5. **사용자 승인은 중요 변경시만**

---
v51.0 - MCP 환경 최적화, stdout 메시지 기반 자동화
