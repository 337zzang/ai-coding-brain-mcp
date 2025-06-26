# GitHub 브랜치 정리 가이드 🔧

## 📊 현재 상황
- **main 브랜치**: 9개 커밋 (초기 설정만 있음)
- **master 브랜치**: 51개 커밋 (모든 실제 개발 작업)
- **문제**: 두 브랜치가 서로 다른 히스토리를 가지고 있음

## ❓ 왜 이런 일이 발생했나?
1. GitHub에서 저장소 생성 시 `main`이 기본 브랜치로 생성됨 (2020년부터 GitHub 정책)
2. 로컬에서 작업 시 `master` 브랜치 사용 (Git 기본값)
3. 두 브랜치가 독립적으로 발전하여 현재 상태가 됨

## ✅ 해결 방법 (단계별)

### 🎯 방법 1: GitHub에서 기본 브랜치 변경 (권장) ⭐

1. **GitHub 저장소 페이지 접속**
   - https://github.com/337zzang/ai-coding-brain-mcp

2. **Settings 탭 클릭**
   - 저장소 상단 메뉴에서 ⚙️ Settings 클릭

3. **기본 브랜치 변경**
   - 왼쪽 메뉴에서 "General" 선택
   - "Default branch" 섹션 찾기
   - 🔄 스위치 아이콘 클릭
   - 드롭다운에서 `master` 선택
   - "Update" 버튼 클릭
   - ⚠️ 경고 메시지가 나오면 "I understand, update the default branch" 클릭

4. **main 브랜치 삭제**
   - 저장소 메인 페이지로 돌아가기
   - 브랜치 드롭다운 클릭 → "View all branches"
   - `main` 브랜치 옆 🗑️ 휴지통 아이콘 클릭
   - 확인 팝업에서 삭제 확인

### 🔧 방법 2: 명령줄에서 처리

```bash
# 1. 먼저 GitHub에서 기본 브랜치를 master로 변경 (위 방법 1의 1-3단계)

# 2. 로컬에서 main 브랜치 삭제
git push origin --delete main

# 3. 로컬 원격 브랜치 정보 정리
git remote prune origin

# 4. 확인
git branch -r
# remotes/origin/master만 보여야 함
```

## 📋 정리 후 최종 상태
- ✅ 브랜치: `master` (유일한 브랜치)
- ✅ 커밋: 51개 (모든 작업 보존)
- ✅ GitHub 기본 브랜치: `master`
- ✅ 깔끔한 단일 브랜치 구조

## ⚠️ 주의사항
- main 브랜치에 보호 규칙이 설정되어 있다면 먼저 해제 필요
- 열려있는 Pull Request가 있다면 먼저 처리
- 다른 팀원이 있다면 사전에 공지

## 💡 추가 팁
- 향후 새 프로젝트 생성 시 로컬과 GitHub 브랜치명 통일 권장
- `git config --global init.defaultBranch main` 명령으로 Git 기본 브랜치를 main으로 설정 가능
