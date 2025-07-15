
# 🚀 Execute Code 프로젝트 관리 Quick Reference

## 프로젝트 전환
```python
# 안전한 전환 (권장)
result = safe_flow_project("project-name", timeout=30)

# 표준 전환
result = project_switch("project-name")

# 빠른 전환
result = quick_switch("project-name")
```

## 새 프로젝트
```python
# 생성
result = project_create("new-project", init_git=True)
```

## 문서 생성
```python
# 전체 업데이트
result = project_build_context()

# README만
result = project_build_context(update_readme=True, update_context=False)
```

## 상태 확인
```python
# 상태 체크
status = check_project_status()

# 현재 프로젝트
current = helpers.get_current_project()
```

## helpers 직접 사용
```python
# 프로젝트 전환
helpers.cmd_flow_with_context("project-name")

# 파일 목록
files = helpers.scan_directory_dict(".")

# 컨텍스트 저장
helpers.save_context({"key": "value"})
```
