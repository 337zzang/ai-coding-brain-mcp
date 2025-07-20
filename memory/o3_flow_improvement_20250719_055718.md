# o3 조언: Flow 시스템 개선
날짜: 2025-07-19T05:57:18.284190

## 질문

[🎯 핵심 질문]
AI Coding Brain MCP의 flow 시스템에서 불필요한 워크플로우 백업 로직을 어떻게 개선해야 할까요?

[📊 현재 상황]
- 프로젝트: ai-coding-brain-mcp (MCP 서버)
- 파일: python/json_repl_session.py:342
- 현상: 각 프로젝트가 독립된 memory/ 폴더를 가지는데도 workflow_backup.json으로 백업

[🔍 코드 분석 결과]
1. **현재 구조**
   ```
   Desktop/
   ├── project-a/
   │   └── memory/
   │       └── workflow.json (A의 워크플로우)
   └── project-b/
       └── memory/
           └── workflow.json (B의 워크플로우)
   ```

2. **프로젝트 전환 시 동작**
   - os.chdir()로 프로젝트 디렉토리 이동
   - 해당 프로젝트의 memory/workflow.json 사용
   - 전환 전 workflow.json을 같은 폴더의 workflow_backup.json으로 복사

3. **문제점**
   - 각 프로젝트가 독립된 memory/를 가지므로 백업이 무의미
   - A→B 전환 시 A의 백업이 A/memory/에 남음
   - B→A 재전환 시 백업 사용 안하고 원래 workflow.json 사용

[💻 관련 코드]
```python
# json_repl_session.py:342
current_workflow = Path("memory/workflow.json")
if current_workflow.exists():
    backup_path = current_memory / "workflow_backup.json"
    shutil.copy2(current_workflow, backup_path)
```

[⚡ 긴급도]
□ 오늘 중 (개발 진행 필요)

[🎯 요청사항]
1. 백업 로직을 제거해야 할까요, 아니면 다른 용도가 있을까요?
2. 만약 제거한다면 어떤 부분을 주의해야 할까요?
3. 더 나은 워크플로우 상태 관리 방법이 있을까요?
4. 프로젝트 간 워크플로우 마이그레이션이 필요한 경우는?


## o3의 답변
1. 백업 로직을 없애도 될까?
   • 목적을 다시 생각해 보면  
     – “프로젝트 전환 시 다른 프로젝트가 워크플로우를 덮어쓰는 것”을 막으려던 흔적입니다.  
     – 현재는 프로젝트마다 memory/ 디렉터리를 독립적으로 갖고 있어 이 위험이 사라졌습니다.  
     – 따라서 “전환-보호” 용도로는 완전히 불필요합니다.  
   • 단, “파일 손상·예기치 않은 종료에 대비한 안전판” 역할까지 수행하고 있었다면(실행 중 전원 OFF, 충돌 등) 그 기능은 사라집니다.  
   • 결론: 전환-보호만을 위해서라면 과감히 제거하되, 파일 무결성·히스토리 용 백업이 필요하면 다른 형태(아래 3번)로 대체합니다.

2. 제거 시 체크포인트
   ① 코드 의존성  
      ‑ grep ‑R "workflow_backup\.json" 전체 프로젝트 검색 → 읽거나 롤백하는 코드가 없다면 바로 삭제.  
   ② 테스트 수정  
      ‑ 백업 파일 존재 여부를 assert 하던 테스트 케이스 제거.  
   ③ 문서/README 업데이트  
      ‑ “프로젝트 전환 시 …backup.json 생성” 부분 삭제.  
   ④ 마이그레이션 스크립트  
      ‑ 기존 backup.json 이 남아 있어도 작동에는 문제 없지만, 깨끗이 하려면 .gitignore 서 삭제 or cleanup 스크립트 제공.

3. 더 나은 워크플로우 상태 관리
   • 원칙: “무결성과 히스토리”를 제공하되 “프로젝트 간 간섭”이 없도록.
   a) 원자적 저장(Atomic write)  
      ```
      import json, os, tempfile, shutil
      def safe_write(path, payload):
          with tempfile.NamedTemporaryFile('w', delete=False, dir=path.parent) as tmp:
              json.dump(payload, tmp)
              tmp.flush(); os.fsync(tmp.fileno())
          os.replace(tmp.name, path)   # atomic on POSIX
      ```
   b) 타임스탬프 기반 스냅샷  
      memory/history/2023-10-01T15-06-32.workflow.json  
      – 필요 시 diff, 롤백 가능.  
      – rotation 정책(최근 N개 유지) 적용.  
   c) Git 을 그대로 활용  
      – memory/ 디렉터리를 레포에 포함 & `post_write()` 에서 `git add/commit -m "update workflow"` 실행.  
      – 브랜치=프로젝트 (혹은 태그=timestamp) 모델이면 시각적 diff·rollback이 가장 편리.  
   d) SQLite 나 TinyDB 저장  
      – “프로젝트ID, revision, json_blob, created_ts” 스키마.  
      – 파일 시스템 의존성을 줄이고 동시 접근(lock) 지원.

4. 프로젝트 간 워크플로우 “마이그레이션”이 필요할 때
   • 사례  
     – 템플릿 프로젝트 A를 복제해서 B를 만들고, 이후 A의 최신 워크플로우를 B에 반영하고 싶을 때  
     – 하나의 거대한 프로젝트를 여러 모듈(폴더)로 쪼갤 때  
   • 구현 아이디어  
     ```
     mcp workflow export --project A  > a.flow.json
     mcp workflow import --project B  a.flow.json
     ```  
     – export 시 워크플로우 내부에서 절대 경로·프로젝트명 등을 변수화(placeholder) 해서 portability 확보.  
     – import 시 매핑 테이블(placeholder → B 값) 적용.  

요약
• “디렉터리 전환 보호”라는 초기 목적은 사라졌으므로 백업 로직은 제거해도 안전.  
• 단, 충돌·손상 대비 히스토리 기능이 필요하면 타임스탬프 스냅샷, git 커밋, 혹은 DB 방식으로 대체한다.  
• 코드·테스트·문서에서 backup.json 의존 부분을 모두 정리한 뒤 커밋하면 끝.

## 적용 계획
- [ ] 백업 로직 검토
- [ ] 코드 수정
- [ ] 테스트
- [ ] 문서 업데이트
