# /flow 프로젝트명 명령어 구현

## 구현 일자
2025-07-21

## 구현 내용

### 1. 명령어 형식
- 기존: `/flow switch <flow_id>`
- 추가: `/flow <프로젝트명>` - 프로젝트명으로 직접 전환

### 2. 구현된 기능
1. **Flow 검색 및 전환**
   - 프로젝트명으로 Flow 검색
   - 동일한 이름의 Flow가 여러 개일 때 플랜이 가장 많은 것 선택
   - 선택된 Flow로 자동 전환

2. **작업 디렉토리 변경**
   - `~/Desktop/프로젝트명`으로 자동 이동
   - Windows와 Unix 시스템 모두 지원

3. **프로젝트 파일 자동 읽기**
   - README.md: 프로젝트 개요 확인
   - filedirectory.md: 파일 구조 확인
   - 파일이 없으면 건너뜀

4. **프로젝트 상태 표시**
   - 최신 플랜 정보
   - 플랜의 태스크 개수 및 완료 상태
   - 최근 3개 태스크 표시

5. **작업 이력 확인**
   - 최근 작업한 Task
   - Task의 context에서 최근 작업 내역 표시

### 3. 수정된 파일
- `python/ai_helpers_new/flow_manager_unified.py`
  - `_handle_flow_command` 메서드: 프로젝트명 처리 로직 추가
  - `_switch_to_project` 메서드: 새로 추가된 핵심 기능

### 4. 사용 예시
```bash
# 프로젝트로 직접 전환
/flow ai-coding-brain-mcp

# 출력 예시:
✅ 프로젝트 'ai-coding-brain-mcp' 전환 완료
📁 Flow ID: flow_20250721_161550
📂 작업 디렉토리: C:\Users\Administrator\Desktop\ai-coding-brain-mcp

📄 README.md:
[프로젝트 설명...]

📁 File Directory:
[파일 구조...]

📋 최신 플랜: 문서화
   Tasks: 0개 (완료: 0개)

🔄 최근 작업 Task: update_task_context와 add_task_action 테스트
   최근 작업 내역:
   - 테스트 환경 준비
     → Python 환경 및 의존성 확인 완료
   - 모듈 스캔 시작
     → 15개 파일 발견
```

### 5. 개선 사항
- 플랜이 있는 Flow를 우선적으로 선택하도록 개선
- 여러 Flow가 있을 때 사용자에게 알림
- 에러 처리 강화 (파일 읽기 실패 시 계속 진행)
