# Git 함수 추가 및 개선

## 📋 개요
AI Helpers에 누락된 Git 백업 전략 함수들을 추가했습니다.

## 🎯 추가된 함수들

### 1. git_checkout(branch_or_file)
- **용도**: 브랜치 전환 또는 파일 복원
- **예시**: 
  ```python
  h.git_checkout("main")              # 브랜치 전환
  h.git_checkout("path/to/file.py")   # 파일 복원
  ```

### 2. git_checkout_b(branch_name)
- **용도**: 새 브랜치 생성 및 전환
- **예시**: 
  ```python
  h.git_checkout_b("feature/new-feature")
  ```

### 3. git_stash(message=None)
- **용도**: 작업 내용 임시 저장
- **예시**: 
  ```python
  h.git_stash("WIP: 작업 중 백업")
  h.git_stash()  # 메시지 없이
  ```

### 4. git_stash_pop()
- **용도**: 임시 저장된 작업 복원
- **예시**: 
  ```python
  h.git_stash_pop()
  ```

### 5. git_stash_list()
- **용도**: stash 목록 조회
- **예시**: 
  ```python
  stashes = h.git_stash_list()
  # {'ok': True, 'data': ['stash@{0}: ...', 'stash@{1}: ...']}
  ```

### 6. git_reset_hard(commit="HEAD")
- **용도**: 특정 커밋으로 강제 리셋
- **예시**: 
  ```python
  h.git_reset_hard("HEAD~1")  # 이전 커밋으로
  h.git_reset_hard("abc123")  # 특정 커밋으로
  ```

### 7. git_merge(branch, no_ff=False)
- **용도**: 브랜치 병합
- **예시**: 
  ```python
  h.git_merge("feature/branch")
  h.git_merge("develop", no_ff=True)  # fast-forward 비활성화
  ```

### 8. git_branch_d(branch, force=False)
- **용도**: 브랜치 삭제
- **예시**: 
  ```python
  h.git_branch_d("old-branch")
  h.git_branch_d("unmerged-branch", force=True)  # 강제 삭제
  ```

### 9. git_rebase(branch)
- **용도**: 리베이스 수행
- **예시**: 
  ```python
  h.git_rebase("main")
  ```

## 📊 사용 예시

### 안전한 작업 플로우
```python
# 1. 현재 작업 임시 저장
h.git_stash("작업 중 백업")

# 2. 새 브랜치 생성
h.git_checkout_b("feature/experiment")

# 3. 실험적 작업 수행
# ... 코드 수정 ...

# 4. 실패 시 롤백
h.git_reset_hard("HEAD")

# 5. 원래 브랜치로 복귀
h.git_checkout("main")

# 6. 임시 저장 복원
h.git_stash_pop()

# 7. 실험 브랜치 삭제
h.git_branch_d("feature/experiment", force=True)
```

## 🔧 수정 파일
1. `python/ai_helpers_new/git.py` - 9개 함수 추가
2. `python/ai_helpers_new/__init__.py` - 명시적 export 추가

## ✅ 테스트 결과
- 모든 함수 정상 작동 확인
- 기존 Git 함수와 완벽 호환
- 에러 처리 포함

## 📝 변경 이력
- 백업: `backups/git_functions_20250802_202245/`
- 커밋: "feat: Git 백업 전략 함수들 추가"
