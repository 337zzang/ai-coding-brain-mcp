# Memory 폴더 격리 문제 해결 보고서

## 📋 이슈 설명
`flow_project`가 memory 폴더를 복사하는 문제로 인해 새 프로젝트를 만들 때 기존 프로젝트의 워크플로우 파일이 따라가는 현상이 있었습니다.

## 🔧 수정 내용

### 1. **enhanced_flow.py** 수정

#### 1.1 `_load_context` 함수 개선
- 로드된 context의 `project_name`이 현재 프로젝트와 일치하는지 확인
- 다른 프로젝트의 context인 경우 새로 생성하도록 수정

```python
# 중요: 로드된 context의 project_name이 현재 프로젝트와 일치하는지 확인
if loaded_context.get('project_name') == project_name:
    return loaded_context
else:
    # 다른 프로젝트의 context인 경우 새로 생성
    logger.warning(f"기존 context가 다른 프로젝트({loaded_context.get('project_name')})의 것임. 새 context 생성.")
```

#### 1.2 `cmd_flow_with_context` 함수 개선
- 프로젝트 전환 시 memory 폴더 체크 및 정리 로직 추가
- 다른 프로젝트의 context 발견 시 백업 후 새 context 생성

```python
# 다른 프로젝트의 context인 경우 백업 후 정리
if old_project and old_project != project_name:
    logger.warning(f"[WARN] 다른 프로젝트({old_project})의 memory 발견. 정리 중...")
    # 기존 context만 백업 (다른 파일들은 그대로 유지)
    backup_name = f'context_backup_{old_project}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
```

#### 1.3 `_load_and_show_workflow` 함수 개선
- 프로젝트별 독립적인 워크플로우 파일 관리
- `{project_name}_workflow.json` 형식으로 프로젝트별 파일 사용
- 워크플로우의 `project_name` 일치 여부 확인

### 2. **project_initializer.py** 수정

#### 2.1 `_initialize_context` 메서드 개선
- 새 프로젝트 생성 시 완전히 깨끗한 memory 폴더 보장
- 기존 파일 발견 시 백업 폴더로 이동

```python
# memory 폴더에 기존 파일들이 있다면 백업
if existing_files:
    backup_path = memory_path / "backup" / f"pre_init_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_path.mkdir(parents=True, exist_ok=True)
```

### 3. **워크플로우 V3 시스템** (이미 프로젝트별 격리 지원)
- `WorkflowStorage`는 이미 `{project_name}_workflow.json` 형식 사용
- `WorkflowDispatcher`는 프로젝트별 인스턴스 관리
- `update_dispatcher_project` 함수로 프로젝트 전환 시 업데이트

## ✅ 개선 효과

1. **프로젝트 격리**: 각 프로젝트의 memory 폴더가 완전히 독립적으로 관리됨
2. **데이터 보호**: 프로젝트 전환 시 기존 데이터는 백업되어 보존됨
3. **충돌 방지**: 다른 프로젝트의 context/workflow가 섞이지 않음
4. **깨끗한 시작**: 새 프로젝트는 항상 깨끗한 memory 폴더로 시작

## 🧪 테스트 결과

```
현재 디렉토리: C:\Users\Administrator\Desktop\ai-coding-brain-mcp
프로젝트명: ai-coding-brain-mcp

📁 memory 폴더 내용:
  - context.json → project_name: ai-coding-brain-mcp
  
  📂 workflow_v3 폴더:
    - ai-coding-brain-mcp_workflow.json  ← 프로젝트별 파일
    - test_project_workflow.json         ← 다른 프로젝트 파일
```

## 📌 주의사항

1. 기존 프로젝트들은 첫 전환 시 context 백업이 생성됩니다
2. 워크플로우 V3는 자동으로 프로젝트별 파일을 사용합니다
3. 백업 파일들은 `memory/backup/` 폴더에 보관됩니다

## 🚀 사용법

변경사항은 자동으로 적용되며, 별도의 조치가 필요하지 않습니다:

```python
# 새 프로젝트 생성
helpers.start_project("my-new-project")

# 프로젝트 전환 (memory 자동 격리)
helpers.flow_project("my-new-project")
```

---
수정일: 2025-07-09
작성자: AI Coding Brain MCP Assistant
