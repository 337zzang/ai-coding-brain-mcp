
## 📊 긴급 수정 완료 보고

### ✅ 수정 내역

#### 1. Flow Task 명령어 추가
- FlowCommandRouter에 'task' 명령어 매핑 추가
- handle_task, handle_task_list 메서드 구현
- /task list, /task start, /task complete 명령어 사용 가능

#### 2. git_status 함수 수정  
- branch 정보 추가 (--porcelain -b 옵션 사용)
- changes 배열로 변경된 파일 목록 제공
- 기존 files/count는 호환성을 위해 유지

### 📁 수정된 파일
- python/ai_helpers_new/flow_command_router.py
- python/ai_helpers_new/git.py

### 💡 개선 효과
- Task 관련 작업 흐름 정상화
- Git 상태 정보가 더 풍부해짐 (브랜치 포함)
