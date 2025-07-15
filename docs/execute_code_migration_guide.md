
# Execute Code 기반 프로젝트 관리 가이드

## 🎯 핵심 변경사항

MCP 도구 → execute_code 함수로 전환:
- `flow_project` → `project_switch()` 또는 `safe_flow_project()`
- `start_project` → `project_create()`
- `build_project_context` → `project_build_context()`

## 📋 사용법

### 1. 프로젝트 전환
```python
# 기본 사용
result = project_switch("my-project")

# 타임아웃 보호 (권장)
result = safe_flow_project("my-project", timeout=30)

# 빠른 전환 (최소 기능)
result = quick_switch("my-project")
```

### 2. 새 프로젝트 생성
```python
# Git 포함 생성
result = project_create("new-project")

# Git 없이 생성
result = project_create("new-project", init_git=False)
```

### 3. 프로젝트 문서 생성
```python
# 전체 문서 업데이트
result = project_build_context()

# 선택적 업데이트
result = project_build_context(
    update_readme=True,
    update_context=True,
    include_file_directory=True,
    include_stats=True
)
```

### 4. 상태 확인
```python
# 현재 프로젝트 상태
status = check_project_status()

# helpers 직접 사용
current = helpers.get_current_project()
```

## ✅ 장점

1. **더 빠른 실행**: TypeScript 핸들러 오버헤드 없음
2. **Timeout 문제 해결**: 직접 Python 실행
3. **세션 변수 활용**: 상태 유지 및 재사용
4. **유연한 제어**: 에러 처리 및 커스터마이징 가능

## 🚨 주의사항

1. execute_code는 결과가 나올 때까지 기다려야 함
2. 긴 작업은 단계별로 분할 실행
3. 에러 발생 시 try-except로 처리

## 📝 마이그레이션 체크리스트

- [ ] tool-definitions.ts에서 세 도구 제거
- [ ] workflow-handlers.ts 파일 제거/수정
- [ ] build-handlers.ts 파일 제거/수정
- [ ] package.json에서 관련 의존성 정리
- [ ] 문서 업데이트
