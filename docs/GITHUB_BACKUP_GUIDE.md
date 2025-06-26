# GitHub MCP 백업 가이드

## 📌 v24.0 변경사항

기존의 로컬 백업 시스템(`helpers.backup_file()`)이 GitHub MCP를 사용하도록 개선되었습니다.

### 🔄 변경 전후 비교

#### 이전 방식 (로컬 백업)
```python
# 백업
backup_path = helpers.backup_file("file.py", "수정 전")
# → memory/backups/2025-06-26/file.py.수정_전.123456.bak

# 복원
result = helpers.restore_backup(backup_path)
```

#### 새로운 방식 (GitHub 백업)
```python
# 1. 백업 준비
backup_info = helpers.backup_file("file.py", "수정 전")
# → "github://20250626_123456/file.py" 반환

# 2. 실제 백업 (MCP 도구 사용)
github:create_or_update_file(
    owner="337zzang",
    repo="ai-coding-brain-mcp",
    path="file.py",
    content=content,
    message="[Backup] file.py - 수정 전 (20250626_123456)",
    branch="main"
)

# 3. 복원 준비
restore_info = helpers.restore_backup("github://20250626_123456/file.py")

# 4. 실제 복원 (MCP 도구 사용)
restored_content = github:get_file_contents(
    owner="337zzang",
    repo="ai-coding-brain-mcp",
    path="file.py",
    ref="커밋SHA"  # 또는 branch
)

# 5. 파일 작성
helpers.create_file("file.py", restored_content)
```

## 🛠️ 실제 사용 예시

### 파일 수정 전 백업
```python
# execute_code에서:
import os
content = helpers.read_file("important_file.py")

# GitHub 백업 정보 생성
backup_info = helpers.backup_file("important_file.py", "대규모 리팩토링 전")
print(backup_info)  # "github://20250626_140523/important_file.py"

# MCP 도구로 실제 백업:
github:create_or_update_file(
    owner="337zzang",
    repo="ai-coding-brain-mcp",
    path="important_file.py",
    content=content,
    message="[Backup] important_file.py - 대규모 리팩토링 전",
    branch="main"
)
```

### 백업에서 복원
```python
# GitHub에서 이전 버전 가져오기:
previous_content = github:get_file_contents(
    owner="337zzang",
    repo="ai-coding-brain-mcp",
    path="important_file.py",
    ref="이전_커밋_SHA"
)

# 파일 복원:
helpers.create_file("important_file.py", previous_content)
```

## 📊 장점

1. **영구 보관**: GitHub에 모든 백업이 영구 저장
2. **버전 추적**: Git 히스토리로 모든 변경사항 추적
3. **원격 백업**: 로컬 파일 손실 시에도 복구 가능
4. **협업 가능**: 팀원들과 백업 공유
5. **무료**: GitHub 무료 플랜으로 충분

## ⚠️ 주의사항

1. **민감한 정보**: 비밀번호, API 키 등은 백업하지 마세요
2. **대용량 파일**: 100MB 이상 파일은 Git LFS 필요
3. **API 제한**: GitHub API 호출 제한 고려
4. **커밋 메시지**: 의미 있는 백업 설명 작성

## 🔄 마이그레이션 가이드

### 기존 코드 수정 불필요
`helpers.backup_file()`과 `helpers.restore_backup()`은 호환성을 위해 유지됩니다.
다만 실제 백업/복원은 GitHub MCP 도구를 사용해야 합니다.

### 권장 워크플로우
1. 중요한 작업 전 GitHub 백업
2. 작업 중 주기적으로 커밋
3. 문제 발생 시 GitHub에서 복원
4. 로컬 백업은 임시 용도로만 사용

## 📚 참고 자료

- [GitHub MCP 문서](https://github.com/modelcontextprotocol/servers/tree/main/src/github)
- [Git 커밋 베스트 프랙티스](https://chris.beams.io/posts/git-commit/)
