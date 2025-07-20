# 글로벌 컨텍스트 시스템 구현 완료

## 구현된 기능
1. **GlobalContextManager** (`python/workflow/global_context.py`)
   - ~/.ai-coding-brain/에 프로젝트 컨텍스트 영속화
   - 프로젝트별 상세 정보 저장
   - 프로젝트 이동 히스토리 관리

2. **flow_project 통합** (`python/flow_project_wrapper.py`)
   - 프로젝트 전환 시 자동으로 컨텍스트 저장
   - AI 컨텍스트 파일(.ai_context.md) 생성

3. **세션 초기화** (`python/json_repl_session.py`)
   - 새 세션 시작 시 이전 작업 히스토리 표시
   - gc(), project_history() 명령어 추가

## 사용 방법
```python
# 프로젝트 전환
fp("project-name")

# 모든 프로젝트 컨텍스트 보기
gc()

# 프로젝트 이동 히스토리
project_history(10)
```

## 테스트 완료
- [x] GlobalContextManager 클래스 생성
- [x] flow_project_wrapper.py 수정
- [x] json_repl_session.py 수정
- [ ] 실제 프로젝트 전환 테스트
- [ ] 새 세션에서 히스토리 로드 테스트
