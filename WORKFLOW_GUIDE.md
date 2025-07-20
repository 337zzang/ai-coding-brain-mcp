
## AI Coding Brain MCP - 워크플로우 사용법

### 🔧 기본 명령어 (wf 함수 사용)

```python
# 워크플로우 시작
wf("/v2 start 프로젝트명")

# 작업 추가
wf("/v2 task 작업 설명")

# 상태 확인  
wf("/v2 status")

# 작업 목록
wf("/v2 list")

# 다음 작업 시작
wf("/v2 next")

# 현재 작업 완료
wf("/v2 done 완료 요약")

# 도움말
wf("/v2 help")
```

### ⚠️ 주의사항
- helpers.workflow()는 "get_execution_history not implemented" 오류 발생
- wf() 함수를 대신 사용하세요
- v2 명령어 체계를 사용하세요 (/v2 prefix)

### 📁 파일 위치
- 워크플로우 데이터: memory/workflow.json
- 이벤트 기록: memory/workflow_events.json
- 히스토리: memory/workflow_history.json
