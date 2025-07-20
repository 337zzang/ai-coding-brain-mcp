# AI Coding Brain MCP - Flow Project 가이드

## 🎯 개선 내용
1. **바탕화면 우선 프로젝트 관리**
   - 기본값으로 바탕화면에서 프로젝트를 찾고 생성
   - `desktop=False` 옵션으로 ~/projects 사용 가능

2. **워크플로우 자동 연동**
   - 프로젝트 전환 시 워크플로우도 함께 전환
   - 프로젝트별 독립적인 워크플로우 관리
   - 자동 백업 기능

3. **영구 적용**
   - flow_project_fix.py 파일로 구현 저장
   - startup_script.py로 자동 패치 적용

## 📋 사용법

### 프로젝트 전환
```python
# 바탕화면에서 프로젝트 찾기 (기본값)
fp("프로젝트명")
helpers.flow_project("프로젝트명")

# ~/projects에서 찾기
fp("프로젝트명", desktop=False)
```

### 워크플로우 관리
```python
# 상태 확인
wf("/status")

# 작업 추가
wf("/task 작업 내용")

# 다음 작업 시작
wf("/next")

# 작업 완료
wf("/done")
```

### 프로젝트 구조
```
프로젝트명/
├── src/          # 소스 코드
├── docs/         # 문서
├── tests/        # 테스트
├── memory/       # 프로젝트 상태
│   ├── workflow.json         # 워크플로우
│   ├── workflow_history.json # 히스토리
│   ├── checkpoints/         # 체크포인트
│   └── backups/            # 백업
└── README.md
```

## 🔧 파일 구조
- `flow_project_fix.py` - 개선된 flow_project 구현
- `startup_script.py` - 자동 패치 스크립트
- `memory/workflow.json` - 현재 워크플로우 상태

생성일: 2025-07-19 19:31
